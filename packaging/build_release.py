#!/usr/bin/env python3
"""Build a release from public Git index contents, excluding all local files."""
import gzip
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'calc_xp'))
from version import VERSION


def main():
    paths = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    paths = [p for p in paths if p]
    if 'packaging/build_deb.py' not in paths:
        raise SystemExit('Source files must be added to the Git index before building a release.')
    dist = ROOT / 'dist'; dist.mkdir(exist_ok=True)
    source = dist / f'calc-xp-{VERSION}.tar.gz'
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH','0'))
    with tempfile.TemporaryDirectory(prefix='calc-xp-release-') as temporary:
        clean = Path(temporary) / f'calc-xp-{VERSION}'
        clean.mkdir()
        with source.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as archive:
                for relative in sorted(paths):
                    data = subprocess.check_output(['git','show',f':{relative}'],cwd=ROOT)
                    target = clean / relative
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(data)
                    entry = tarfile.TarInfo(f'calc-xp-{VERSION}/{relative}')
                    entry.size=len(data); entry.mode=0o644; entry.mtime=epoch
                    archive.addfile(entry,io.BytesIO(data))
        environment = dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=clean,env=environment,check=True)
        subprocess.run([sys.executable,'packaging/build_deb.py'],cwd=clean,env=environment,check=True)
        deb = clean / 'dist' / f'calc-xp_{VERSION}_all.deb'
        shutil.copyfile(deb,dist / deb.name)
    artifacts = [dist / f'calc-xp_{VERSION}_all.deb', source]
    checksums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in artifacts)
    (dist/'SHA256SUMS').write_text(checksums)
    print(checksums,end='')


if __name__ == '__main__': main()
