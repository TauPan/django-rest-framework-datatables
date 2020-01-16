from django.db.models import Q

from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from django_filters.rest_framework.filters import CharFilter
from django_filters import utils

from rest_framework_datatables import filters

is_valid_regex = filters.is_valid_regex


class DatatablesFilterSet(FilterSet):
    """Basic FilterSet used by default in DatatablesFilterBackend (see below)

    Datatables parameters are parsed and only the relevant parts are
    stored as in the `datatables_query` attribute of every filter.

    The complete information is available in the `datatables_query`
    attribute of the FilterSet itself, which is available via the
    `parent` attribute of the Filter.
    """

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


class DatatablesFilterBackend(filters.DatatablesFilterBackend,
                              DjangoFilterBackend):
    """Filter Backend for compatibility with DataTables *and* django-filters

    """

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


class ChainedQ(object):

    def __get__(self, obj, type=None):
        return getattr(obj.parent, '_chained_q_object', Q())

    def __set__(self, obj, value):
        return setattr(obj.parent, '_chained_q_object', value)


class ChainedFilterMixin(object):

    q = ChainedQ()

    def filter(self, qs, value):
        return qs.filter(self.chain_query(value))

    def chain_query(self, value):
        self.q &= self.filter_q(value)
        return self.q

    def filter_q(self, value):
        return Q(**{'{}__{}'.format(self.field_name, self.lookup_expr): value})


class GlobalFilterMixin(ChainedFilterMixin, CharFilter):
    """Simple mixin for adding addition support for global search to a filter

    The search filter for the column value is delegated to the
    concrete filter class (which must come *first* in the declaration
    of base classes) and the global search is simply a direct string
    match.

    """

    lookup_expr = 'icontains'

    def chain_query(self, value):
        search_value = getattr(self, 'search_value', None)
        self.q |= self.filter_q(search_value)
        self.q &= self.filter_q(value)
        return self.q


class GlobalRegexFilterMixin(GlobalFilterMixin):
    """Adds regex filtering in addition to global filtering to a filter
    class.

    The base filter class (if given) must come first in the
    declaration of base classes.
    """

    lookup_expr = 'icontains'

    def chain_query(self, value):
        search_value = getattr(self, 'search_value', None)
        search_regex = getattr(self, 'search_regex', False) is True
        f_regex = self.datatables_query.get('search_regex', False) is True
        f_search_value = self.datatables_query.get('search_value', None)
        self.q |= filters.f_search_q(self.datatables_query,
                                     search_value,
                                     search_regex)
        self.q &= filters.f_search_q(self.datatables_query,
                                     f_search_value,
                                     f_regex)
        return self.q
