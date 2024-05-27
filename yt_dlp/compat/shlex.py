# flake8: noqa: F405
from shlex import *  # noqa: F403

from .compat_utils import passthrough_module

passthrough_module(__name__, 'shlex')
del passthrough_module


try:
    join
except NameError:
    def join(split_command):
        """Return a shell-escaped string from *split_command*."""
        return ' '.join(quote(arg) for arg in split_command)
