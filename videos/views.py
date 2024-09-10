# videos/views.py
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Video


@api_view(['GET'])
def search_subtitles(request, pk):
    phrase = request.query_params.get('phrase', '')
    language = request.query_params.get('lang', '')
    if not phrase:
        return Response({"error": "Phrase parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    if not language:
        return Response({"error": "Language parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    video = get_object_or_404(Video, pk=pk)
    subtitles = video.subtitles.annotate(lower_text=Lower('text')).filter(Q(language=language)).filter(
        Q(lower_text__icontains=phrase.lower()) | Q(lower_text__istartswith=phrase.lower()) | Q(
            lower_text__iendswith=phrase.lower())).only('start', 'end', 'text')
    results = []
    for subtitle in subtitles:
        results.append({
            "start": subtitle.start,
            "end": subtitle.end,
            "text": subtitle.text,
        })
    if results:
        return Response({"results": results})
    else:
        return Response({"message": "No matching subtitles found."}, status=status.HTTP_404_NOT_FOUND)


class VideoListView(View):
    def get(self, request):
        videos = Video.objects.all().order_by('-uploaded_at')
        return render(request, 'list.html', {'videos': videos})

    def post(self, request):
        name = request.POST.get('name')
        video_file = request.FILES.get('video_file')
        if name and video_file:
            Video.objects.create(original_name=name, video_file=video_file)
            return redirect('list')
        return render(request, 'list.html', {'videos': Video.objects.all()})


class VideoDetailView(View):
    def get(self, request, pk):
        video = Video.objects.get(pk=pk)
        languages = video.subtitles.distinct().values_list('language', flat=True)
        return render(request, 'detail.html', {'video': video, 'languages': languages})
