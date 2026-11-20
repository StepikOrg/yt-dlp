import json
import unittest
from typing import Any, Optional, Union
from unittest import mock
from urllib.parse import quote

from test.helper import FakeYDL
from yt_dlp.extractor.yandexdisk import YandexDiskIE
from yt_dlp.utils import ExtractorError


class TestYandexDisk(unittest.TestCase):
    VIDEO_ID = 'PublicVideo123'
    VIDEO_URL = f'https://disk.yandex.ru/i/{VIDEO_ID}'
    SOURCE_URL = 'https://downloader.disk.yandex.ru/disk/signed-video'
    FOLDER_URL = 'https://disk.yandex.ru/d/PublicFolder123'
    FILE_PATH = '/Lesson videos/\u0423\u0440\u043e\u043a %20.mov'
    FOLDER_PAGE = '<script id="store-prefetch">{}</script>'.format(
        json.dumps(
            {
                'rootResourceId': 'folder',
                'resources': {'folder': {'name': 'Lesson videos', 'hash': 'public-folder-hash'}},
                'environment': {'sk': 'session-key', 'yandexuid': '1'},
            },
        ),
    )

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

    def test_downloads_the_file_inside_public_folder(self) -> None:
        api = 'https://cloud-api.yandex.net/v1/disk/public/resources'
        expected_query = {'public_key': self.FOLDER_URL, 'path': self.FILE_PATH}
        responses = {
            api: {
                'type': 'file',
                'name': self.FILE_PATH.rsplit('/', 1)[1],
                'mime_type': 'video/quicktime',
                'size': 3796504,
            },
            f'{api}/download': {'href': self.SOURCE_URL},
        }

        def download_json(
            endpoint: str, _video_id: str, *, query: Optional[dict] = None, **_kwargs: Any,
        ) -> Union[dict, bool]:
            if query == expected_query:
                return responses[endpoint]
            if endpoint.endswith('/public/api/download-url'):
                return {'data': {'url': 'https://downloader.disk.yandex.ru/disk/folder.zip'}}
            return False

        with mock.patch.object(self.ie, '_download_webpage', return_value=self.FOLDER_PAGE) as webpage:
            with mock.patch.object(self.ie, '_download_json', side_effect=download_json) as download:
                result = self.ie._real_extract(self.FOLDER_URL + quote(self.FILE_PATH) + '?from=share#preview')

        self.assertEqual(result['formats'][0]['url'], self.SOURCE_URL)
        self.assertEqual(result['formats'][0]['ext'], 'mov')
        self.assertEqual(result['formats'][0]['filesize'], 3796504)
        self.assertEqual([call[1]['query'] for call in download.call_args_list], [expected_query] * 2)
        webpage.assert_not_called()

    def test_missing_nested_file_does_not_fall_back_to_the_folder(self) -> None:
        with mock.patch.object(self.ie, '_download_webpage', return_value=self.FOLDER_PAGE) as webpage:
            with mock.patch.object(self.ie, '_download_json', return_value=False) as download:
                with self.assertRaisesRegex(ExtractorError, 'Unable to download the file from the public folder'):
                    self.ie._real_extract(self.FOLDER_URL + '/missing.mov')

        download.assert_called_once()
        webpage.assert_not_called()
