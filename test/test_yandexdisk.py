import unittest
from unittest import mock

from test.helper import FakeYDL
from yt_dlp.extractor.yandexdisk import YandexDiskIE
from yt_dlp.utils import ExtractorError


class TestYandexDisk(unittest.TestCase):
    VIDEO_ID = 'PublicVideo123'
    VIDEO_URL = f'https://disk.yandex.ru/i/{VIDEO_ID}'
    SOURCE_URL = 'https://downloader.disk.yandex.ru/disk/signed-video'

    def setUp(self) -> None:
        self.ie = YandexDiskIE(FakeYDL())
        self.resource = {
            'type': 'file',
            'name': 'lesson.mp4',
            'mime_type': 'video/mp4',
            'size': 214580619,
        }

    def test_imports_public_video_without_embedded_store(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', return_value='<html></html>'):
            with mock.patch.object(
                self.ie,
                '_download_json',
                side_effect=[
                    self.resource,
                    {'href': self.SOURCE_URL},
                ],
            ) as download:
                result = self.ie._real_extract(self.VIDEO_URL)

        self.assertEqual(result['id'], self.VIDEO_ID)
        self.assertEqual(result['title'], 'lesson.mp4')
        self.assertEqual(
            result['formats'],
            [
                {
                    'url': self.SOURCE_URL,
                    'format_id': 'source',
                    'ext': 'mp4',
                    'quality': 1,
                    'filesize': 214580619,
                },
            ],
        )
        self.assertEqual(
            [call[0][0] for call in download.call_args_list],
            [
                'https://cloud-api.yandex.net/v1/disk/public/resources',
                'https://cloud-api.yandex.net/v1/disk/public/resources/download',
            ],
        )
        self.assertEqual(
            [call[1]['query'] for call in download.call_args_list],
            [
                {'public_key': self.VIDEO_URL},
                {'public_key': self.VIDEO_URL},
            ],
        )

    def test_preserves_extraction_error_for_public_folder(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', return_value='<html></html>'):
            with mock.patch.object(self.ie, '_download_json', return_value={'type': 'dir'}) as download:
                with self.assertRaisesRegex(ExtractorError, 'Unable to extract store'):
                    self.ie._real_extract(self.VIDEO_URL)

        download.assert_called_once()

    def test_preserves_extraction_error_when_api_cannot_provide_download(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', return_value='<html></html>'):
            with mock.patch.object(self.ie, '_download_json', side_effect=[self.resource, False]) as download:
                with self.assertRaisesRegex(ExtractorError, 'Unable to extract store'):
                    self.ie._real_extract(self.VIDEO_URL)

        self.assertEqual(download.call_count, 2)
