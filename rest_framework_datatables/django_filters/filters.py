from rest_framework_datatables import filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.rest_framework.filters import CharFilter
from django_filters import utils

is_valid_regex = filters.is_valid_regex


class DatatablesFilterSet(FilterSet):

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None,
                 datatables_query=None):
        super().__init__(data=data, queryset=queryset,
                         request=request, prefix=prefix)
        self.datatables_query = datatables_query
        # Propagate the datatables information to the filters:
        for filter_ in self.filters.values():
            filter_.datatables_query = next(
                x for x
                in datatables_query['fields']
                if x['data'] == filter_.field_name
            )
            filter_.search_value = datatables_query['search_value']
            filter_.search_regex = datatables_query['search_regex']


class GlobalFilterMixin(CharFilter):

    def filter(self, qs, value):
        ret = super(GlobalFilterMixin, self).filter(
            qs, value
        )
        search_value = getattr(self, 'search_value', None)
        if search_value:
            return qs and (self.filter_global(qs, search_value) or ret)
        return ret

    def filter_global(self, qs, search_value):
        if search_value:
            return qs.filter(**{self.field_name + '__icontains': search_value})
        return qs


class GlobalRegexFilterMixin(GlobalFilterMixin):

    def filter(self, qs, value):
        f_regex = self.datatables_query.get('search_regex', False) is True
        f_search_value = self.datatables_query.get('search_value', None)
        search_value = getattr(self, 'search_value', None)
        re_q = None
        if f_regex:
            if is_valid_regex(f_search_value):
                re_q = qs.filter(
                    **{self.field_name + '__iregex': f_search_value})
        global_q = self.filter_global(
            qs,
            search_value,
            getattr(self, 'search_regex', False) is True)
        if re_q and search_value:
            return qs and (global_q or re_q)
        if re_q:
            return re_q
        if global_q:
            return global_q
        return qs

    def filter_global(self, qs, search_value, search_regex):
        if search_value:
            if search_regex:
                if is_valid_regex(search_value):
                    return qs.filter(
                        **{self.field_name + '__iregex': search_value})
            else:
                return super(GlobalRegexFilterMixin, self).filter_global(
                    qs, search_value)
        return qs


class DatatablesFilterBackend(filters.DatatablesFilterBackend,
                              DjangoFilterBackend):

    filterset_base = DatatablesFilterSet

    def filter_queryset(self, request, queryset, view):
        if request.accepted_renderer.format != 'datatables':
            return queryset
        filtered_count_before = self.count_before(queryset, view)

        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            self.count_after(view, filtered_count_before)
            return queryset

        if not filterset.is_valid() and self.raise_exception:
            raise utils.translate_validation(filterset.errors)
        # TODO combine the global search with OR for every field
        queryset = filterset.qs

        self.count_after(view, queryset.count())
        return queryset

    def get_filterset_kwargs(self, request, queryset, view):
        # parse query params
        query = self.parse_query_params(request, view)
        return {
            'data': query['form_fields'],
            'queryset': queryset,
            'request': request,
            'datatables_query': query
        }

    def parse_query_params(self, request, view):
        query = super(DatatablesFilterBackend,
                      self).parse_query_params(request, view)
        form_fields = {}
        for f in query['fields']:
            form_fields[f['data']] = f['search_value']
        query['form_fields'] = form_fields
        return query
