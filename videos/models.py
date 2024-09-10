import uuid

from django.db import models


class Video(models.Model):
    original_name = models.CharField(max_length=255)
    name = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    video_file = models.FileField(upload_to="videos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name + "--" + self.name.hex

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        db_table = "video"


class VideoQuality(models.Model):
    video = models.ForeignKey(Video, related_name="video_qualities", on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return self.label + "--" + self.source

    class Meta:
        verbose_name = "Video Quality"
        verbose_name_plural = "Video Qualities"
        db_table = "video_quality"


class VideoSubtitle(models.Model):
    video = models.ForeignKey(Video, related_name="video_subtitles", on_delete=models.CASCADE)
    src = models.CharField(max_length=255)
    kind = models.CharField(max_length=255)
    src_lang = models.CharField(max_length=255)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.src + "--" + self.src_lang

    class Meta:
        db_table = "video_subtitle"
        verbose_name = "Video Subtitle"
        verbose_name_plural = "Video Subtitles"


class Subtitle(models.Model):
    video = models.ForeignKey(Video, related_name='subtitles', on_delete=models.CASCADE)
    language = models.CharField(max_length=10)
    start = models.CharField(max_length=10)
    end = models.CharField(max_length=10)
    text = models.TextField()
    format = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.video.name} -- {self.language}"

    class Meta:
        verbose_name = "Subtitle"
        verbose_name_plural = "Subtitles"
        db_table = "subtitle"
