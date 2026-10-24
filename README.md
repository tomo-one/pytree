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

### Aktualisieren

```bash
pytree --check-update     # nur prüfen, ob eine neuere Version existiert
pytree --update           # neueste Version von GitHub holen und installieren
```

`--update` lädt das Archiv des neuesten Tags (`vX.Y.Z`) von GitHub, entpackt
es temporär und führt dessen `install.py` mit demselben Python aus. Dadurch
bleiben Interpreter bzw. private venv der Installation erhalten. Gebraucht
wird nur ein Internetzugang zu github.com (Proxy-Variablen werden beachtet).
Das Update funktioniert nur für eine mit `install.py` installierte Version.
Eine vor v0.6 installierte Version hat die Funktion noch nicht und muss
einmalig mit `python3 install.py` aus der neuen Quelle aktualisiert werden.

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
pytree --update           # siehe Abschnitt "Aktualisieren"
```

Beim Start wird eine kurze Statuszeile ausgegeben (Version, analysierter
Pfad, Kurzhinweis auf `?`/`q`), bevor die Baumansicht den Bildschirm
übernimmt. Ein unerwarteter Fehler wird mit Traceback auf stderr ausgegeben
statt das Fenster stillschweigend zu schließen.

Als erster Eintrag der Wurzel steht `..`. Mit Enter oder → darauf (oder mit
`u`/Backspace) wird das Elternverzeichnis zur neuen Wurzel. Der bisher
gescannte Baum bleibt dabei erhalten, nur die Nachbarordner werden neu
gelesen. Im obersten Verzeichnis fehlt der Eintrag.

### Tastenkürzel

| Taste            | Aktion                          |
|------------------|----------------------------------|
| ↑/↓, j/k         | Navigation                       |
| →, Enter, l       | Verzeichnis aufklappen (scannt bei Bedarf) |
| ←, h              | Verzeichnis zuklappen             |
| u, Backspace      | Eine Ebene höher (Wurzel wird zum Elternverzeichnis) |
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
