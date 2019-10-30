from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.response import Response

from albums.models import Album, Artist
from albums.serializers import AlbumSerializer, ArtistSerializer
from albums.views import get_album_options


def index(request):
    return render(request, 'albums/albums.html')


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all().order_by('rank')
    serializer_class = AlbumSerializer

    def get_options(self):
        return get_album_options()

    class Meta:
        datatables_extra_json = ('get_options', )


class ArtistViewSet(viewsets.ViewSet):
    queryset = Artist.objects.all().order_by('name')
    serializer_class = ArtistSerializer

    def list(self, request):
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    def get_options(self):
        return get_album_options()

    class Meta:
        datatables_extra_json = ('get_options', )
