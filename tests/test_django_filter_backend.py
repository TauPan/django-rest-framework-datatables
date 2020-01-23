from unittest import mock, SkipTest

from django.conf.urls import include, url
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import routers, viewsets
from rest_framework.test import APIClient, APIRequestFactory

from albums.models import Album
from albums.serializers import AlbumSerializer

# Skip this module if django-filter is not available
try:
    from django_filters import rest_framework as filters
    from rest_framework_datatables.django_filters.backends import (
        DatatablesFilterBackend)
except ImportError:
    raise SkipTest('django-filter not available')


factory = APIRequestFactory()


class TestDFBackendTestCase(TestCase):

    fixtures = ['test_data']
    backend = DatatablesFilterBackend()


class TestNotDataTablesFormat(TestDFBackendTestCase):

    def test_format(self):
        qs = Album.objects.all()
        req = factory.get('ignored')
        req.accepted_renderer = mock.Mock()
        req.accepted_renderer.format = 'json'
        res = self.backend.filter_queryset(req, qs, None)
        self.assertEqual(res, qs)


class AlbumFilter(filters.FilterSet):

    class Meta:
        model = Album
        fields = '__all__'


# Most things are much easier to test with client and viewset, even
# though we're testing the backend here
class AlbumFilterViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    filter_backends = [DatatablesFilterBackend]
    filterset_class = AlbumFilter


@override_settings(ROOT_URLCONF=__name__)
class TestWithViewSet(TestDFBackendTestCase):

    def setUp(self):
        self.client = APIClient()


router = routers.DefaultRouter()
router.register(r'albums', AlbumFilterViewSet)


urlpatterns = [
    url('^api/', include(router.urls)),
]


class TestUnfiltered(TestWithViewSet):

    def setUp(self):
        self.result = self.client.get('/api/albums/?format=datatables')
        self.view = self.result.renderer_context.get('view')


class TestCount(TestUnfiltered):

    def test_count_before(self):
        self.assertEqual(self.view._datatables_total_count, 15)

    def test_count_after(self):
        self.assertEqual(self.view._datatables_filtered_count, 15)


class TestFiltered(TestWithViewSet):

    def setUp(self):
        self.result = self.client.get('/api/albums/?format=datatables&length=10&columns[0][data]=year&columns[0][searchable]=true&columns[0][search][value]=1971')

    def test_count_before(self):
        self.assertEqual(self.result.json()['recordsTotal'], 15)

    def test_count_after(self):
        self.assertEqual(self.result.json()['recordsFiltered'], 1)


class TestInvalid(TestWithViewSet):
    """Test handling invalid data

    Our artist (and genre) fields will automatically be multiple
    choice fields (assigned by django-filter), so we can test what
    happens if we pass an invalid (missing) choice

    """

    def setUp(self):
        self.result = self.client.get(
            '/api/albums/?format=datatables&length=10'
            '&columns[0][data]=artist'
            '&columns[0][searchable]=true'
            '&columns[0][search][value]=Genesis')

    def test(self):
        self.assertEqual(self.result.status_code, 400)
        self.assertEqual(
            self.result.json()['data'],
            {'artist': [
                'Select a valid choice. '
                'That choice is not one of the available choices.']})
