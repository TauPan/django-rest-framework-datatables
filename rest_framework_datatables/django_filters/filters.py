from rest_framework_datatables import filters
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.rest_framework.filters import CharFilter
from django_filters import utils


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


class GlobalFilterMixin(CharFilter):

    def filter(self, qs, value):
        ret = super(GlobalFilterMixin, self).filter(
                qs, value
        )
        search_value = getattr(self, 'search_value', None)
        if search_value:
            global_qs = super(GlobalFilterMixin, self).filter(
                qs, search_value)
            return ret and global_qs
        return ret


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
