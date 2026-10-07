# Stepik Python 3.7 fork

This branch starts at upstream yt-dlp commit
`51bab8a0116f4d8004c315706d809782607d5847` and adds Python 3.7 compatibility.
The upstream Google Drive playback API and Odnoklassniki fixes are included.
The previous Stepik fork is not used as the source tree.

## Compatibility changes

- Assignment expressions are lowered to scoped helpers with `python-walrus`
  0.1.5rc1, using Python 3.11. Positional-only parameters are lowered to
  private parameter names and local aliases to preserve calls with keyword data.
- `_compat_py37.py` provides module-local standard-library facades for cached
  properties, caching, pairwise iteration, shell argument joining, floating-point
  helpers, and strict zip. It does not replace global standard-library modules.
- HTTP adapters support requests 2.31.0 and urllib3 1.26.20, including TLS hostname
  validation, incomplete response detection, and partial reads of compressed data.
- WebSocket adapters support websockets 11.0.3. ZIP plugin loading supports the
  import APIs available in Python 3.7.
- Packaging supports Python 3.7 build backends. YouTube's bundled JavaScript
  solver remains available; the optional Python EJS package requires Python 3.10.
- Existing files retain upstream formatting to keep the compatibility diff small.
  Preview rules must be selected explicitly to avoid enabling unrelated new rules
  when the tool is upgraded.

## Verification

Install dependencies before running checks. For the legacy runtime:

```sh
python3.7 -m pip install 'pip==24.0' 'pytest<8' 'build<1.1' \
    'requests==2.31.0' 'urllib3==1.26.20' 'websockets==11.0.3' \
    brotli certifi mutagen pycryptodomex
python3.7 -m compileall -q yt_dlp test devscripts
python3.7 -m pytest -q -m 'not download'
python3.7 -m build --wheel
```

The full local suite also requires ffmpeg and curl. Run Linux tests on a native
container filesystem: file-locking tests do not work reliably on a macOS bind mount.
Download tests contact external providers and are excluded from the core suite.
Google Drive has separate deterministic regression tests in `test/test_googledrive.py`.

Use a modern Python environment for the configured development tools:

```sh
python -m pip install 'ruff~=0.16.0' 'autopep8~=2.0'
ruff format yt_dlp/_compat_py37.py test/test_py37_compat.py test/test_googledrive.py
ruff check --fix --unsafe-fixes --preview .
autopep8 --diff .
```

Release the reviewed wheel through Stepik's release process, then update the EDY
requirement URL and SHA-256 together. Do not use upstream's automatic updater to
replace this fork with a Python 3.10+ release.
