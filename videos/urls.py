
from django.urls import path
from .views import VideoListView, VideoDetailView, search_subtitles


urlpatterns = [
    path('', VideoListView.as_view(), name='list'),
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='detail'),
    path('videos/<int:pk>/search', search_subtitles, name='search_subtitles'),
]
