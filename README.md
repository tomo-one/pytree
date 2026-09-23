# pytree

Interaktiver, tastaturgesteuerter Disk-Usage-Analyzer für die Kommandozeile
(read-only). Zeigt Datei-/Verzeichnisgrößen als auf-/zuklappbaren Baum,
sortiert nach Größe, mit lazy Scanning großer Verzeichnisse.

## Installation

```bash
pip install --user -e .
```

Falls das `pytree`-Kommando nicht im `PATH` liegt (z.B. auf Windows unter
`%APPDATA%\Python\PythonXY\Scripts`), funktioniert immer:

```bash
python -m pytree [pfad]
```

## Nutzung

```bash
pytree [pfad]      # default: aktuelles Verzeichnis
```

### Tastenkürzel

| Taste            | Aktion                          |
|------------------|----------------------------------|
| ↑/↓, j/k         | Navigation                       |
| →, Enter, l       | Verzeichnis aufklappen (scannt bei Bedarf) |
| ←, h              | Verzeichnis zuklappen             |
| r                 | Markierten Knoten neu scannen     |
| e                 | Übersprungene Einträge anzeigen   |
| ?, F1             | Hilfe                             |
| q, Ctrl+C         | Beenden                           |

## Entwicklung

```bash
pip install --user -e ".[dev]"
pytest
```
