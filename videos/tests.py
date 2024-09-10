from uuid import uuid4
from .models import VideoQuality, VideoSubtitle
from unittest.mock import patch, MagicMock
from .tasks import process_video_into_chunks
from rest_framework.test import APIClient
from rest_framework import status

from django.test import Client

from django.urls import reverse
from django.test import TestCase
from videos.models import Video, Subtitle

import warnings

# Suppress specific warning
warnings.filterwarnings("ignore", category=SyntaxWarning)


class VideoModelTest(TestCase):
    @patch('videos.models.Video.objects.create')
    def setUp(self, mock_create):
        # Configure the mock to return a specific Video instance
        self.mock_video_instance = Video(
            original_name="Sample Video",
            name=uuid4(),
            video_file="path/to/video.mp4"
        )
        mock_create.return_value = self.mock_video_instance
        self.video = Video.objects.create(
            name=self.mock_video_instance.name,
            original_name="Sample Video",
            video_file="path/to/video.mp4"
        )

    def test_video_creation(self):
        self.assertTrue(isinstance(self.video, Video))
        self.assertEqual(str(self.video), f"{self.video.original_name}--{self.video.name.hex}")

    def test_video_str(self):
        expected_str = f"{self.video.original_name}--{self.video.name.hex}"
        self.assertEqual(str(self.video), expected_str)


class VideoQualityModelTest(TestCase):
    @patch('videos.models.Video.objects.create')
    @patch('videos.models.VideoQuality.objects.create')
    def setUp(self, mock_quality_create, mock_video_create):
        # Configure the mocks
        self.mock_video_instance = Video(
            original_name="Sample Video",
            name=uuid4(),
            video_file="path/to/video.mp4"
        )
        self.mock_quality_instance = VideoQuality(
            video=self.mock_video_instance,
            source="source1",
            type="type1",
            label="label1"
        )
        mock_video_create.return_value = self.mock_video_instance
        mock_quality_create.return_value = self.mock_quality_instance
        self.video = Video.objects.create(
            name=self.mock_video_instance.name,
            original_name="Sample Video",
            video_file="path/to/video.mp4"
        )
        self.video_quality = VideoQuality.objects.create(
            video=self.video,
            source="source1",
            type="type1",
            label="label1"
        )

    def test_video_quality_creation(self):
        self.assertTrue(isinstance(self.video_quality, VideoQuality))
        self.assertEqual(str(self.video_quality), f"{self.video_quality.label}--{self.video_quality.source}")

    def test_video_quality_str(self):
        expected_str = f"{self.video_quality.label}--{self.video_quality.source}"
        self.assertEqual(str(self.video_quality), expected_str)


class VideoSubtitleModelTest(TestCase):
    @patch('videos.models.Video.objects.create')
    @patch('videos.models.VideoSubtitle.objects.create')
    def setUp(self, mock_subtitle_create, mock_video_create):
        # Configure the mocks
        self.mock_video_instance = Video(
            original_name="Sample Video",
            name=uuid4(),
            video_file="path/to/video.mp4"
        )
        self.mock_subtitle_instance = VideoSubtitle(
            video=self.mock_video_instance,
            src="source1",
            kind="kind1",
            src_lang="en",
            label="label1"
        )
        mock_video_create.return_value = self.mock_video_instance
        mock_subtitle_create.return_value = self.mock_subtitle_instance
        self.video = Video.objects.create(
            name=self.mock_video_instance.name,
            original_name="Sample Video",
            video_file="path/to/video.mp4"
        )
        self.video_subtitle = VideoSubtitle.objects.create(
            video=self.video,
            src="source1",
            kind="kind1",
            src_lang="en",
            label="label1"
        )

    def test_video_subtitle_creation(self):
        self.assertTrue(isinstance(self.video_subtitle, VideoSubtitle))
        self.assertEqual(str(self.video_subtitle), f"{self.video_subtitle.src}--{self.video_subtitle.src_lang}")

    def test_video_subtitle_str(self):
        expected_str = f"{self.video_subtitle.src}--{self.video_subtitle.src_lang}"
        self.assertEqual(str(self.video_subtitle), expected_str)


class SubtitleModelTest(TestCase):
    @patch('videos.models.Video.objects.create')
    @patch('videos.models.Subtitle.objects.create')
    def setUp(self, mock_subtitle_create, mock_video_create):
        # Configure the mocks
        self.mock_video_instance = Video(
            original_name="Sample Video",
            name=uuid4(),
            video_file="path/to/video.mp4"
        )
        self.mock_subtitle_instance = Subtitle(
            video=self.mock_video_instance,
            language="en",
            start="00:00:00,000",
            end="00:00:05,000",
            text="Sample subtitle text",
            format="SRT"
        )
        mock_video_create.return_value = self.mock_video_instance
        mock_subtitle_create.return_value = self.mock_subtitle_instance
        self.video = Video.objects.create(
            original_name="Sample Video",
            video_file="path/to/video.mp4"
        )
        self.subtitle = Subtitle.objects.create(
            video=self.video,
            language="en",
            start="00:00:00,000",
            end="00:00:05,000",
            text="Sample subtitle text",
            format="SRT"
        )

    def test_subtitle_creation(self):
        self.assertTrue(isinstance(self.subtitle, Subtitle))
        self.assertEqual(str(self.subtitle), f"{self.subtitle.video.name} -- {self.subtitle.language}")

    def test_subtitle_str(self):
        expected_str = f"{self.subtitle.video.name} -- {self.subtitle.language}"
        self.assertEqual(str(self.subtitle), expected_str)


class ProcessVideoIntoChunksTaskTest(TestCase):
    @patch('videos.tasks.Video.objects.get')
    @patch('videos.tasks.subprocess.run')
    @patch('videos.tasks.ffmpeg_streaming.input')
    @patch('videos.tasks.VideoQuality.objects.create')
    @patch('videos.tasks.VideoSubtitle.objects.create')
    @patch('videos.tasks.Subtitle.objects.bulk_create')
    @patch('videos.tasks.get_subtitle_languages')
    @patch('videos.tasks.extract_subtitles')
    @patch('os.makedirs')
    @patch('os.remove')
    def test_process_video_into_chunks(self, mock_remove, mock_makedirs, mock_extract_subtitles,
                                       mock_get_subtitle_languages, mock_bulk_create, mock_video_subtitle_create,
                                       mock_quality_create, mock_ffmpeg_input, mock_subprocess_run, mock_video_get):
        # Mock the Video instance
        video_instance = MagicMock()
        video_instance.id = 1
        video_instance.video_file.path = '/path/to/video.mp4'
        mock_video_get.return_value = video_instance

        # Mock subprocess.run to simulate ffprobe and ffmpeg behavior
        mock_subprocess_run.return_value = MagicMock(
            stderr='Stream #0:0(eng): Subtitle: English\nStream #0:1(eng): Subtitle: English')

        # Mock ffmpeg_streaming input
        mock_ffmpeg_input.return_value = MagicMock()
        mock_ffmpeg_input.return_value.hls.return_value = MagicMock()
        mock_ffmpeg_input.return_value.hls.return_value.auto_generate_representations.return_value = None
        mock_ffmpeg_input.return_value.hls.return_value.output.return_value = None

        # Mock get_subtitle_languages
        mock_get_subtitle_languages.return_value = {'eng'}

        # Mock extract_subtitles
        mock_extract_subtitles.return_value = [
            {"start": "00:00:00.000", "end": "00:00:05.000", "text": "Sample subtitle text", "language": "eng",
             "format": "vtt"}
        ]

        # Mock model creations
        mock_quality_create.return_value = None
        mock_video_subtitle_create.return_value = None
        mock_bulk_create.return_value = None

        # Mock os.makedirs to not raise any errors
        mock_makedirs.side_effect = None

        # Mock os.remove to ensure it is called
        mock_remove.return_value = None

        # Run the task
        process_video_into_chunks(1)

        # Verify that os.remove was called to delete the video file
        mock_remove.assert_called_once_with('/path/to/video.mp4')

        # Verify that other methods were called as expected
        mock_video_get.assert_called_once_with(id=1)
        mock_ffmpeg_input.assert_called_once_with('/path/to/video.mp4')
        mock_quality_create.assert_called()
        mock_video_subtitle_create.assert_called()
        mock_bulk_create.assert_called()
        mock_get_subtitle_languages.assert_called_once_with('/path/to/video.mp4')
        mock_extract_subtitles.assert_called()


class SearchSubtitlesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.video = Video.objects.create(original_name="Sample Video", video_file="path/to/video.mp4")
        self.subtitle = Subtitle.objects.create(
            video=self.video,
            language='en',
            start='00:00:00.000',
            end='00:00:05.000',
            text='Sample subtitle text',
            format='vtt'
        )

    def test_search_subtitles_success(self):
        response = self.client.get(f'/videos/{self.video.pk}/search', {'phrase': 'Sample', 'lang': 'en'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['text'], 'Sample subtitle text')

    def test_search_subtitles_missing_phrase(self):
        response = self.client.get(f'/videos/{self.video.pk}/search?lang=en')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Phrase parameter is required.')

    def test_search_subtitles_missing_language(self):
        response = self.client.get(f'/videos/{self.video.pk}/search?phrase=Sample')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Language parameter is required.')

    def test_search_subtitles_no_results(self):
        response = self.client.get(f'/videos/{self.video.pk}/search?phrase=Nonexistent&lang=en')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'No matching subtitles found.')


class VideoListViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.video1 = Video.objects.create(original_name="Video 1", video_file="path/to/video1.mp4")
        self.video2 = Video.objects.create(original_name="Video 2", video_file="path/to/video2.mp4")

    def test_get_video_list(self):
        response = self.client.get(reverse('list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Video 1")
        self.assertContains(response, "Video 2")

    def test_post_video_create(self):
        with open('test_video.mp4', 'w') as f:
            f.write('dummy content')
        with open('test_video.mp4', 'rb') as video_file:
            response = self.client.post(reverse('list'), {'name': 'New Video', 'video_file': video_file})
        self.assertEqual(response.status_code, 302)  # Redirects after POST
        self.assertTrue(Video.objects.filter(original_name="New Video").exists())


class VideoDetailViewTestCase(TestCase):
    def setUp(self):
        self.video = Video.objects.create(original_name="Sample Video", video_file="path/to/video.mp4")
        Subtitle.objects.create(video=self.video, language="en", start="00:00:00", end="00:00:05",
                                text="Sample subtitle")
        self.client = Client()

    def test_video_detail_view(self):
        response = self.client.get(reverse('detail', kwargs={'pk': self.video.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Video")
        self.assertContains(response, "en")
