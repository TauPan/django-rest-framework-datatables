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
from rest_framework_datatables.django_filter.filters import (
    DatatablesFilterBackend,
)


class NumberDashFilter(filters.RangeFilter):

    field_class = forms.CharField

    def filter(self, qs, value):
        vals = value.split('-')
        if len(vals) == 1:
            r = range(int(vals[0]), int(vals[0]))
        else:
            r = range(int(vals[0]) or None, int(vals[1]) or None)
        return super(NumberDashFilter, self).filter(qs, r)


class AlbumFilter(filters.FilterSet):
    year = NumberDashFilter()

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

    def test_range(self):
        response = self.client.get(
            '/api/albumsfilter/?format=datatables&length=10&columns[0][data]=name&columns[0][name]=name&columns[0][searchable]=true&columns[0][search][value]=&columns[1][data]=year&columns[1][searchable]=true&columns[1][search][value]=1959-1965')
        expected = (3, 15)
        result = response.json()
        self.assertEquals((result['recordsFiltered'], result['recordsTotal']),
                          expected)
        self.assertEquals(
            set(x['name'] for x in result['data']),
            {'Kind of Blue', "Highway 61 Revisited", "Rubber Soul"})


router = DefaultRouter()
router.register(r'^api/albumsfilter', AlbumFilterViewSet)
urlpatterns = router.urls
