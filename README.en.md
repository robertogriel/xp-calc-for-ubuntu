[Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# XP Calculator for Ubuntu

A desktop calculator with a classic look, Portuguese menus, and standard and scientific modes. Independently implemented in Python and GTK 4.

Developed using [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) to support the investigation of the original executable, with assistance from **OpenAI Codex**, using the **GPT 6.1 Sol** model, for implementation, testing, and Ubuntu packaging.

## Installation

```sh
sudo apt install ./calc-xp_1.0.0_all.deb
calc-xp
```

The application also appears as **XP Calculator** in the application menu when the desktop language is English. Dependencies: `python3` (3.10 or later), `python3-gi`, and `gir1.2-gtk-4.0`. Package architecture: `all`.

## Features

- Standard mode evaluates operations in the order entered; scientific mode supports precedence and parentheses.
- MC, MR, MS, and M+ memory functions, percentages, powers, roots, and trigonometric functions.
- Inverse and hyperbolic functions, decimal/hexadecimal/octal/binary conversions, and bitwise operations.
- Mean, sum, and standard deviation, with a list of statistical data.
- Copying and pasting numbers, thousands grouping, and icons at 16, 32, and 48 pixels.

## Keyboard shortcuts

| Key | Action |
|---|---|
| Enter or `=` | Calculate |
| Esc | Clear |
| Delete | Clear entry |
| Backspace | Delete one character |
| F9 | Change sign |
| Ctrl+C / Ctrl+V | Copy / paste a number |
| F5 / F6 / F7 / F8 | Hexadecimal / decimal / octal / binary |
| F2 / F3 / F4 | Degrees / radians / gradians, or word size in integer bases |

**Exibir → Padrão / Científica** switches modes. Inv enables inverse functions; Hyp enables hyperbolic functions. Dat adds statistical data, and Sta opens the data list. Local help is available with F1. The application interface is in Portuguese, and the display uses a decimal comma.

Preferences are stored in `~/.config/calc-xp/settings.json`, respecting `XDG_CONFIG_HOME`. Memory and statistics last for the current session. Arithmetic supports up to 32 digits; trigonometry provides approximately 15. Not all rounding behavior and limits are guaranteed to match the classic calculator.

## Development

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0 git
python3 -m unittest discover -s tests -v
python3 -m calc_xp.app
```

Optional GUI test, in a graphical session:

```sh
CALC_XP_SCREENSHOTS=dist/screenshots python3 -m calc_xp.app --smoke-test
```

The menu regression test switches modes eight times and verifies that menus reopen and calculations work after each switch:

```sh
GDK_BACKEND=x11 GSK_RENDERER=cairo python3 tests/menu_regression.py
# To test with pointer events, install xdotool and add --pointer.
```

## Packaging

```sh
python3 packaging/build_deb.py
# Build the package, sources, and checksums from files in the Git index:
python3 packaging/build_release.py
```

Artifacts are written to `dist/`. The release build compiles from a clean copy of the source files selected in Git. Ignored files are excluded from both the package and the source archive.

After installing the package, `python3 packaging/verify_installed.py` checks package integrity, installed files, icons, and the application launcher.

## License and credits

The independent source code is licensed under [MIT](LICENSE). The original Windows XP Calculator icon is a Microsoft graphic asset, identified separately in [NOTICE.md](packaging/icons/NOTICE.md); it is not covered by this project's MIT license. This project is not affiliated with Microsoft.
