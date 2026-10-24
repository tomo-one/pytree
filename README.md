# pytree

Interaktiver, tastaturgesteuerter Disk-Usage-Analyzer für die Kommandozeile
(read-only). Zeigt Datei-/Verzeichnisgrößen als auf-/zuklappbaren Baum,
sortiert nach Größe, mit lazy Scanning großer Verzeichnisse.

## Installation

Voraussetzung: Python ab 3.9. Keine Admin-Rechte nötig. Läuft unter Windows,
macOS und Linux.

```bash
python3 install.py        # Windows: python install.py
```

Das installiert die Abhängigkeit textual (`pip install --user`), kopiert
pytree in ein Benutzerverzeichnis und legt das Kommando `pytree` an:

| System        | Programm                          | Startskript                       |
|---------------|-----------------------------------|-----------------------------------|
| Linux / macOS | `~/.local/share/pytree`           | `~/.local/bin/pytree`             |
| Windows       | `%LOCALAPPDATA%\pytree`           | `%LOCALAPPDATA%\pytree\bin\pytree.cmd` |

Liegt das Startskript-Verzeichnis nicht im `PATH`, gibt der Installer den
vollständigen Aufruf und den Befehl zum Eintragen aus. Ohne PATH-Eintrag
funktioniert der Aufruf mit vollem Pfad weiterhin.

Entfernen: `python3 install.py --uninstall`

Ohne Installation direkt aus dem Quellordner (textual muss vorhanden sein):

```bash
python3 start.py [pfad]
```

### Probleme

- **"externally-managed-environment"** (Debian 12, Ubuntu ab 23.04): Der
  Installer erkennt das und legt selbst eine private Umgebung unter
  `~/.local/share/pytree/venv` an. Dafür braucht Debian/Ubuntu das Paket
  `python3-venv` (`apt install python3-venv`, als root).
- **textual lässt sich nicht installieren** (kein pip, kein Internet): Der
  Installer nennt die Ursache. Mit `--no-deps` überspringt er den pip-Schritt,
  textual muss dann anderweitig vorhanden sein.
- **Installation als root:** funktioniert genauso. Das Startskript landet dann
  in `/root/.local/bin`. Für andere Benutzer den Installer unter deren Konto
  ausführen.

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
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # editierbar, braucht setuptools ab Version 64
pytest
```
