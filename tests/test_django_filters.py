from django.conf.urls import url
from django.test.utils import override_settings
from django.test import TestCase
from django import forms

from django_filters import rest_framework as filters
from rest_framework.routers import DefaultRouter
from rest_framework.test import (
    APIClient,
)

from albums.models import Album
from albums.views import AlbumViewSet
from rest_framework_datatables.django_filters.filters import (
    DatatablesFilterBackend,
    DatatablesFilterSet,
    GlobalFilterMixin,
    GlobalRegexFilterMixin
)


class NumberYADCFDelimFilter(filters.RangeFilter, GlobalFilterMixin):

    field_class = forms.CharField

    @staticmethod
    def _slice_or_none(v, delim='-'):

        def _int_or_none(v):
            if v == "":
                return None
            else:
                return int(v)

        vals = v.split(delim)
        val0 = _int_or_none(vals[0])
        if len(vals) == 2:  # one delimiter was in the string
            return slice(val0, _int_or_none(vals[1]))
        if len(vals) == 1 and vals[0]:  # it wasn't, but there was one value
            return slice(val0, val0)
        # empty string, multiple separators or other
        return None

    def filter(self, qs, value):
        return super(NumberYADCFDelimFilter, self).filter(
            qs, self._slice_or_none(value, '-yadcf_delim-'))


class AlbumFilter(DatatablesFilterSet):
    year = NumberYADCFDelimFilter()
    name = GlobalRegexFilterMixin()

    class Meta:
        model = Album
        fields = ['year', 'name']


class AlbumFilterViewSet(AlbumViewSet):

    filter_backends = [DatatablesFilterBackend]
    filterset_class = AlbumFilter


@override_settings(ROOT_URLCONF=__name__)
class TestDjangoFilterBackend(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.client = APIClient()

    def test_column_range(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=1959-yadcf_delim-1965')
        expected = (3, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue', "Highway 61 Revisited", "Rubber Soul"})

    def test_column_single(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=1971')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {"What's Going On"})

    def test_column_start_range(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=1979-yadcf_delim-')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'London Calling'})

    def test_end_range(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=-yadcf_delim-1959')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue'})

    def test_global_number(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&search[value]=1959&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue'})

    def test_global_string(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&search[regex]=false&search[value]=blue&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue'})

    def test_global_regex(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&search[regex]=true&search[value]=.*blue.*&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue'})

    def test_column_regex(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&search[regex]=false&search[value]=&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=.*blue.*&columns[0][search][regex]=true&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=')
        expected = (1, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue'})


router = DefaultRouter()
router.register(r'^api/albumsfilter', AlbumFilterViewSet)
urlpatterns = router.urls
