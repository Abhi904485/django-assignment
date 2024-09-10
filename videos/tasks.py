import re
from uuid import uuid4

import ffmpeg_streaming
from celery import shared_task
from ffmpeg_streaming import Formats

from .models import Video, Subtitle, VideoQuality, VideoSubtitle
import subprocess
import os


def get_subtitle_languages(video_path):
    result = subprocess.run(
        f"ffprobe {video_path} -show_entries stream=index:stream_tags=language -select_streams a -of compact=p=0:nk=1",
        stderr=subprocess.PIPE, text=True, check=True, shell=True)
    output = result.stderr
    subtitle_pattern = re.compile(r'Stream #\d+:\d+\((\w+)\): Subtitle')
    languages = subtitle_pattern.findall(output)
    return set(languages)


def extract_subtitles(video_path, location, language):
    command = [
        'ffmpeg', '-i', video_path,
        '-map', f'0:s:m:language:{language}',
        '-c:s', 'webvtt', location
    ]
    subprocess.run(command, check=True)
    pattern = re.compile(
        r'(?P<start>\d{2}:\d{2}\.\d{3})\s-->\s(?P<end>\d{2}:\d{2}\.\d{3})\n(?P<text>.+?)(?=\n\d{2}:\d{2}|\Z)',
        re.DOTALL)

    matches = pattern.finditer(open(location).read())
    result = []
    for match in matches:
        start = match.group('start')
        end = match.group('end')
        text = match.group('text').replace('\n', ' ').strip()
        result.append({
            "start": start,
            "end": end,
            "text": text,
            "language": language,
            "format": "vtt"
        })
    return result


@shared_task
def process_video_into_chunks(video_id):
    result = {}
    video = Video.objects.get(id=video_id)
    video_path = video.video_file.path
    new_video_folder = uuid4().hex
    video_dir = os.path.join(os.path.dirname(video_path), new_video_folder)
    stream_video = ffmpeg_streaming.input(video_path)
    representations = {
        1080: "1080", 720: "720", 360: "360", 480: "480", 144: "144"
    }
    for rep_k, rep_v in representations.items():
        folder_path = os.path.join(video_dir, rep_v)
        os.makedirs(folder_path, exist_ok=True)
        hls = stream_video.hls(Formats.h264())
        hls.auto_generate_representations([rep_k])
        output_path = os.path.join(folder_path, f"{rep_v}.m3u8")
        hls.output(output_path)
        result[rep_k] = rep_v
        if rep_k == 1080:
            selected = True
        else:
            selected = False
        VideoQuality.objects.create(video=video,
                                    source=os.path.join(os.path.sep, "media", "videos", new_video_folder, rep_v,
                                                        f"{rep_v}.m3u8"),
                                    type="application/x-mpegURL", label=rep_v, selected=selected)
    languages = get_subtitle_languages(video_path)
    for lang in languages:
        result = extract_subtitles(video_path=video_path, location=os.path.join(video_dir, lang + ".vtt"),
                                   language=lang)
        VideoSubtitle.objects.create(video=video,
                                     src=os.path.join(os.path.sep, "media", "videos", new_video_folder, lang + ".vtt"),
                                     src_lang=lang, kind="caption", label=lang)
        Subtitle.objects.bulk_create([Subtitle(**{**res, 'video_id': video_id}) for res in result])

    os.remove(video_path)

    return result
