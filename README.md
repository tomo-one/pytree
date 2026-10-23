# pytree

Interaktiver, tastaturgesteuerter Disk-Usage-Analyzer für die Kommandozeile
(read-only). Zeigt Datei-/Verzeichnisgrößen als auf-/zuklappbaren Baum,
sortiert nach Größe, mit lazy Scanning großer Verzeichnisse.

## Installation

Voraussetzung: Python ab 3.9.

```bash
pip install --user .
```

Falls das `pytree`-Kommando nicht im `PATH` liegt (z.B. auf Windows unter
`%APPDATA%\Python\PythonXY\Scripts`), funktioniert immer:

```bash
python -m pytree [pfad]
```

### Linux (Ubuntu/Debian)

Das System-pip und -setuptools sind dort oft veraltet. Ein Fehler wie
"build backend ... build_editable" tritt auf, wenn ein `-e`-Install mit
setuptools unter Version 64 versucht wird. Daher ohne `-e` installieren,
am besten in einer virtuellen Umgebung (auch nötig ab Ubuntu 23.04 wegen
PEP 668):

```bash
python3 -m venv ~/.venvs/pytree
~/.venvs/pytree/bin/pip install --upgrade pip setuptools
~/.venvs/pytree/bin/pip install .
~/.venvs/pytree/bin/pytree
```

Ohne jede Installation (nur textual muss vorhanden sein) geht es auch direkt
aus dem Quellordner:

```bash
PYTHONPATH=src python3 -m pytree [pfad]
```

## Nutzung

```bash
pytree [pfad]      # default: aktuelles Verzeichnis
pytree --help
pytree --version
```

Beim Start wird eine kurze Statuszeile ausgegeben (Version, analysierter
Pfad, Kurzhinweis auf `?`/`q`), bevor die Baumansicht den Bildschirm
übernimmt. Ein unerwarteter Fehler wird mit Traceback auf stderr ausgegeben
statt das Fenster stillschweigend zu schließen.

### Tastenkürzel

| Taste            | Aktion                          |
|------------------|----------------------------------|
| ↑/↓, j/k         | Navigation                       |
| →, Enter, l       | Verzeichnis aufklappen (scannt bei Bedarf) |
| ←, h              | Verzeichnis zuklappen             |
| r                 | Markierten Knoten neu scannen     |
| s                 | Sortierung umschalten (Größe/Name) |
| e                 | Übersprungene Einträge anzeigen   |
| ?, F1             | Hilfe                             |
| q, Ctrl+C         | Beenden                           |

## Entwicklung

```bash
pip install --user -e ".[dev]"
pytest
```
