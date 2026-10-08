import importlib.resources
import pathlib

from yt_dlp.extractor.youtube.jsc._builtin.vendor._info import HASHES, VERSION

__all__ = ['HASHES', 'VERSION', 'load_script']


def load_script(filename, error_hook=None):
    file = (
        importlib.resources.files(__package__)
        if hasattr(importlib.resources, 'files')
        else pathlib.Path(__file__).parent
    ) / filename
    if file.is_file():
        try:
            return file.read_text(encoding='utf-8')
        except (OSError, FileNotFoundError, ModuleNotFoundError) as e:
            if error_hook:
                error_hook(e)
            return None
    return None
