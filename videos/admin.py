from django.contrib import admin
from .models import Video, Subtitle, VideoSubtitle, VideoQuality

admin.site.register(Video)
admin.site.register(Subtitle)
admin.site.register(VideoSubtitle)
admin.site.register(VideoQuality)
