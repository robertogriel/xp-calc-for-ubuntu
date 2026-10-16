[Português](README.md) | [English](README.en.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# XP-Rechner für Ubuntu

Ein Desktop-Taschenrechner im klassischen Design mit portugiesischen Menüs sowie Standard- und Wissenschaftsmodus. Eigenständige Implementierung in Python und GTK 4.

Entwickelt mit [REA (Reverse Engineer Anything)](https://github.com/morluto/rea) zur Unterstützung der Untersuchung der ursprünglichen ausführbaren Datei sowie mit Unterstützung von **OpenAI Codex** und dem Modell **GPT 6.1 Sol** bei Implementierung, Tests und Paketerstellung für Ubuntu.

## Installation

```sh
sudo apt install ./calc-xp_1.0.0_all.deb
calc-xp
```

Die Anwendung erscheint auch als **Calculadora XP** im Anwendungsmenü. Abhängigkeiten: `python3` (3.10 oder neuer), `python3-gi` und `gir1.2-gtk-4.0`. Paketarchitektur: `all`.

## Funktionen

- Der Standardmodus berechnet Operationen in der Eingabereihenfolge; der Wissenschaftsmodus berücksichtigt Vorrangregeln und Klammern.
- Speicherfunktionen MC, MR, MS und M+, Prozentrechnung, Potenzen, Wurzeln und trigonometrische Funktionen.
- Umkehrfunktionen und hyperbolische Funktionen, Umrechnung zwischen Dezimal-, Hexadezimal-, Oktal- und Binärsystem sowie bitweise Operationen.
- Mittelwert, Summe und Standardabweichung mit einer Liste statistischer Daten.
- Kopieren und Einfügen von Zahlen, Tausendergruppierung und Symbole in 16, 32 und 48 Pixeln.

## Tastenkürzel

| Taste | Aktion |
|---|---|
| Eingabetaste oder `=` | Berechnen |
| Esc | Löschen |
| Entf | Eingabe löschen |
| Rücktaste | Ein Zeichen löschen |
| F9 | Vorzeichen wechseln |
| Ctrl+C / Ctrl+V | Eine Zahl kopieren / einfügen |
| F5 / F6 / F7 / F8 | Hexadezimal / Dezimal / Oktal / Binär |
| F2 / F3 / F4 | Grad / Radiant / Gon oder Wortbreite in den Ganzzahlbasen |

**Exibir → Padrão / Científica** wechselt zwischen den Modi. Inv aktiviert Umkehrfunktionen, Hyp die hyperbolischen Funktionen. Dat fügt statistische Daten hinzu, Sta öffnet die Datenliste. Die lokale Hilfe ist über F1 verfügbar. Die Oberfläche ist auf Portugiesisch und die Anzeige verwendet ein Dezimalkomma.

Die Einstellungen werden in `~/.config/calc-xp/settings.json` gespeichert; `XDG_CONFIG_HOME` wird berücksichtigt. Speicher und statistische Daten bleiben während der Sitzung erhalten. Die Arithmetik verwendet bis zu 32 Stellen, die Trigonometrie ungefähr 15. Es wird nicht garantiert, dass sämtliche Rundungen und Grenzwerte mit denen des klassischen Rechners übereinstimmen.

## Entwicklung

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0 git
python3 -m unittest discover -s tests -v
python3 -m calc_xp.app
```

Optionaler Oberflächentest in einer grafischen Sitzung:

```sh
CALC_XP_SCREENSHOTS=dist/screenshots python3 -m calc_xp.app --smoke-test
```

Der Regressionstest für die Menüs wechselt achtmal den Modus und prüft nach jedem Wechsel, ob sich die Menüs wieder öffnen lassen und Berechnungen funktionieren:

```sh
GDK_BACKEND=x11 GSK_RENDERER=cairo python3 tests/menu_regression.py
# Für Tests mit Zeigerereignissen xdotool installieren und --pointer hinzufügen.
```

## Paketerstellung

```sh
python3 packaging/build_deb.py
# Paket, Quelltextarchiv und Prüfsummen aus den Dateien im Git-Index erstellen:
python3 packaging/build_release.py
```

Die Ergebnisse werden in `dist/` gespeichert. Die Erstellung der Veröffentlichung erfolgt aus einer sauberen Kopie der in Git ausgewählten Quelldateien. Ignorierte Dateien sind weder im Paket noch im Quelltextarchiv enthalten.

Nach der Installation prüft `python3 packaging/verify_installed.py` die Integrität des Pakets, die installierten Dateien, die Symbole und den Eintrag im Anwendungsmenü.

## Lizenz und Danksagung

Der eigenständige Quellcode steht unter der [MIT-Lizenz](LICENSE). Das ursprüngliche Symbol des Windows-XP-Rechners ist eine Grafik von Microsoft und wird gesondert in [NOTICE.md](packaging/icons/NOTICE.md) beschrieben; es fällt nicht unter die MIT-Lizenz dieses Projekts. Das Projekt ist nicht mit Microsoft verbunden.
