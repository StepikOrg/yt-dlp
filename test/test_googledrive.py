import io
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree

from test.helper import FakeYDL
from yt_dlp.extractor.googledrive import GoogleDriveIE
from yt_dlp.networking.common import Response
from yt_dlp.utils import ExtractorError


class TestGoogleDrive(unittest.TestCase):
    VIDEO_ID = '0ByeS4oOUV-49Zzh4R1J6R09zazQ'
    VIDEO_URL = f'https://drive.google.com/file/d/{VIDEO_ID}/view'

    def setUp(self) -> None:
        self.ie = GoogleDriveIE(FakeYDL({'writesubtitles': True}))
        self.playback = {
            'mediaMetadata': {'title': 'test.mp4', 'duration': '45.069s'},
            'mediaStreamingData': {
                'formatStreamingData': {
                    'progressiveTranscodes': [
                        {
                            'itag': 18,
                            'url': 'https://video.example/progressive.mp4',
                            'transcodeMetadata': {
                                'mimeType': 'video/mp4',
                                'width': 640,
                                'height': 360,
                                'videoFps': 30,
                                'contentLength': '1234',
                                'videoCodecString': 'avc1.42001E',
                                'audioCodecString': 'mp4a.40.2',
                            },
                        }
                    ],
                    'adaptiveTranscodes': [
                        {
                            'itag': 140,
                            'url': 'https://video.example/audio.m4a',
                            'transcodeMetadata': {
                                'mimeType': 'audio/mp4',
                                'audioCodecString': 'mp4a.40.2',
                            },
                        }
                    ],
                }
            },
            'thumbnails': [{'url': 'https://image.example/thumbnail.jpg', 'mimeType': 'image/jpeg'}],
        }

    def test_playback_api_replaces_removed_video_info_endpoint(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', side_effect=ExtractorError('HTTP Error 404')):
            with mock.patch.object(self.ie, '_download_json', return_value=self.playback) as download:
                with mock.patch.object(self.ie, '_request_webpage', return_value=None):
                    result = self.ie._real_extract(self.VIDEO_URL)

        self.assertEqual(
            download.call_args[0][0],
            f'https://content-workspacevideo-pa.googleapis.com/v1/drive/media/{self.VIDEO_ID}/playback',
        )
        self.assertEqual(download.call_args[1]['headers'], {'Referer': 'https://drive.google.com/'})
        self.assertEqual(result['title'], 'test.mp4')
        self.assertEqual(result['duration'], 45.069)
        formats = {fmt['format_id']: fmt for fmt in result['formats']}
        self.assertEqual(formats['18']['filesize'], 1234)
        self.assertEqual(formats['18']['height'], 360)
        self.assertEqual(formats['18']['acodec'], 'mp4a.40.2')
        self.assertEqual(formats['140']['vcodec'], 'none')

    def test_downloadable_original_is_preserved(self) -> None:
        response = Response(
            fp=io.BytesIO(),
            url='https://video.example/original.mp4',
            headers={'Content-Disposition': 'attachment; filename="original.mp4"'},
        )
        with mock.patch.object(self.ie, '_download_webpage', side_effect=ExtractorError('HTTP Error 404')):
            with mock.patch.object(self.ie, '_download_json', return_value=self.playback):
                with mock.patch.object(self.ie, '_request_webpage', return_value=response):
                    result = self.ie._real_extract(self.VIDEO_URL)

        source = next(fmt for fmt in result['formats'] if fmt['format_id'] == 'source')
        self.assertEqual(source['url'], response.url)
        self.assertEqual(source['quality'], 1)

    def test_subtitle_kind_is_preserved(self) -> None:
        self.playback['timedTextDetails'] = {'timedTextBaseUrl': 'https://video.example/timedtext'}
        subtitles = ElementTree.fromstring(
            '<transcript_list><format fmt_code="vtt"/>'
            '<track lang_code="en" lang_original="English" kind="asr"/></transcript_list>'
        )
        with mock.patch.object(self.ie, '_download_webpage', side_effect=ExtractorError('HTTP Error 404')):
            with mock.patch.object(self.ie, '_download_json', return_value=self.playback):
                with mock.patch.object(self.ie, '_request_webpage', return_value=None):
                    with mock.patch.object(self.ie, '_download_xml', return_value=subtitles):
                        result = self.ie._real_extract(self.VIDEO_URL)

        subtitle = result['subtitles']['en'][0]
        self.assertEqual(subtitle['ext'], 'vtt')
        self.assertEqual(parse_qs(urlsplit(subtitle['url']).query)['kind'], ['asr'])

    def test_private_file_failure_is_propagated(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', side_effect=ExtractorError('HTTP Error 404')):
            with mock.patch.object(self.ie, '_download_json', side_effect=ExtractorError('HTTP Error 403')):
                with self.assertRaisesRegex(ExtractorError, 'HTTP Error 403'):
                    self.ie._real_extract(self.VIDEO_URL)
