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
    DatatablesFilterSet
)


class NumberYADCFDelimFilter(filters.RangeFilter):

    field_class = forms.CharField

    @staticmethod
    def _int_or_none(v):
        if v == "":
            return None
        else:
            return int(v)

    def filter(self, qs, value):
        vals = value.split('-yadcf_delim-')
        if len(vals) == 1:
            r = slice(int(vals[0]), int(vals[0]))
        else:
            r = slice(self._int_or_none(vals[0]), self._int_or_none(vals[1]))
        return super(NumberYADCFDelimFilter, self).filter(qs, r)


class AlbumFilter(DatatablesFilterSet):
    year = NumberYADCFDelimFilter()

    class Meta:
        model = Album
        fields = ['year']


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


router = DefaultRouter()
router.register(r'^api/albumsfilter', AlbumFilterViewSet)
urlpatterns = router.urls
