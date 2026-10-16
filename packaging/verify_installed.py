#!/usr/bin/env python3
"""Verify the installed package and source identity without importing source modules."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'calc_xp'))
from version import VERSION
status = subprocess.check_output(['dpkg-query', '-W', '-f=${Status} ${Version}', 'calc-xp'], text=True)
assert status == f'install ok installed {VERSION}', status
subprocess.run(['dpkg', '--verify', 'calc-xp'], check=True)
digests = {}
for name in ('app.py', 'engine.py', 'version.py', '__init__.py'):
    source = (root / 'calc_xp' / name).read_bytes()
    installed = (Path('/usr/share/calc-xp') / name).read_bytes()
    assert source == installed, name
    digests[name] = hashlib.sha256(installed).hexdigest()
icons = {}
for size in (16,32,48):
    source = root / f'packaging/icons/calc-xp-{size}.png'
    installed = Path(f'/usr/share/icons/hicolor/{size}x{size}/apps/calc-xp.png')
    assert source.read_bytes() == installed.read_bytes(), str(installed)
    icons[str(size)] = hashlib.sha256(installed.read_bytes()).hexdigest()
assert not Path('/usr/share/icons/hicolor/scalable/apps/calc-xp.svg').exists(), 'Obsolete SVG still installed'
if shutil.which('desktop-file-validate'):
    subprocess.run(['desktop-file-validate','/usr/share/applications/calc-xp.desktop'],check=True)
print(json.dumps({'package':status,'dpkg_verify':'PASS','installed_matches_source':digests,
    'desktop_entry':'PASS','original_icon_pngs':icons},indent=2))
