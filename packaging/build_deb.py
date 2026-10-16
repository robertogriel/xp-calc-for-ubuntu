#!/usr/bin/env python3
"""Build a portable Debian package using only Python and dpkg-deb."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'calc_xp'))
from version import VERSION


def write(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    path.chmod(mode)


def main():
    dist = ROOT / 'dist'; dist.mkdir(exist_ok=True)
    destination = dist / f'calc-xp_{VERSION}_all.deb'
    with tempfile.TemporaryDirectory(prefix='calc-xp-deb-') as temporary:
        stage = Path(temporary)
        stage.chmod(0o755)
        app = stage / 'usr/share/calc-xp'; app.mkdir(parents=True)
        for source in (ROOT / 'calc_xp').glob('*.py'):
            shutil.copyfile(source, app / source.name)
            (app / source.name).chmod(0o644)
        write(stage / 'DEBIAN/control', f'''Package: calc-xp
Version: {VERSION}
Section: math
Priority: optional
Architecture: all
Maintainer: Calc XP Project <calc-xp@localhost>
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0
Installed-Size: {sum(p.stat().st_size for p in app.iterdir()) // 1024 + 20}
Description: Classic desktop calculator inspired by Windows XP
 Standard and scientific modes, decimal arithmetic, memory, statistics,
 hexadecimal, octal and binary operations. Independent Python/GTK 4 app.
''')
        write(stage / 'usr/bin/calc-xp', '''#!/bin/sh
export GSK_RENDERER="${GSK_RENDERER:-cairo}"
exec /usr/bin/python3 /usr/share/calc-xp/app.py "$@"
''',0o755)
        write(stage / 'usr/share/applications/calc-xp.desktop', '''[Desktop Entry]
Version=1.0
Type=Application
Name=Calculadora XP
Name[en]=XP Calculator
Comment=Calculadora clássica com modos padrão e científico
Exec=calc-xp
Icon=/usr/share/icons/hicolor/48x48/apps/calc-xp.png
Terminal=false
Categories=Utility;Calculator;
Keywords=calculator;calculadora;scientific;cientifica;xp;
StartupNotify=true
StartupWMClass=calc-xp
''')
        for size in (16,32,48):
            target = stage / f'usr/share/icons/hicolor/{size}x{size}/apps/calc-xp.png'
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT / f'packaging/icons/calc-xp-{size}.png',target)
            target.chmod(0o644)
        write(stage / 'usr/share/doc/calc-xp/icon-NOTICE.md', (ROOT / 'packaging/icons/NOTICE.md').read_text())
        for name in ('README.md','README.en.md','README.es.md','README.de.md','CHANGELOG.md','LICENSE'):
            write(stage / f'usr/share/doc/calc-xp/{name}',(ROOT / name).read_text())
        write(stage / 'usr/share/doc/calc-xp/copyright', '''Independent reconstruction, 2026 Calc XP contributors.
License: MIT. See /usr/share/doc/calc-xp/LICENSE.
Windows and Microsoft are trademarks of their respective owners.
The application code is independent; no Microsoft executable code is included.
The original Microsoft Calculator icon is identified in icon-NOTICE.md.
The icon is excluded from the MIT license applying to the independent source code.
''')
        subprocess.run(['dpkg-deb','--root-owner-group','--build',str(stage),str(destination)],check=True)
    print(destination)


if __name__ == '__main__': main()
