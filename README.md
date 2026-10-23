# DB Pendler – Home Assistant

Zeigt morgens auf einen Blick die nächsten Bahnverbindungen von zu Hause zur Arbeit –
mit Echtzeit-Verspätungen, Gleis(-wechseln), Umstiegen und Ausfällen.

Die Integration besteht aus:

- **Sensoren** pro Strecke
  - `sensor.<strecke>_nachste_abfahrt` – Abfahrtszeit der nächsten Verbindung (Zeitstempel), alle Verbindungen im Attribut `connections`
  - `sensor.<strecke>_verspatung` – Verspätung der nächsten Verbindung in Minuten (ideal für Automationen)
- **Dashboard-Karte** `custom:db-pendler-card` – wird automatisch mitgeliefert, keine separate Ressource nötig

## Datenquelle

Die Fahrplandaten kommen von [Transitous](https://transitous.org) (offener, kostenloser
MOTIS-Routing-Dienst). Er nutzt die bundesweiten DELFI-Daten inkl. DB-Echtzeitdaten.
Kein API-Key, keine Registrierung.

> Warum nicht direkt bahn.de? Die Verbindungssuche von bahn.de/DB Navigator blockt
> automatisierte Abfragen, und der Community-Dienst `v6.db.transport.rest` ist häufig
> nicht erreichbar. Wer möchte, kann in der Einrichtung einen eigenen MOTIS-Server eintragen.

Bitte die Abfragefrequenz moderat halten (Standard: alle 3 Minuten). Mit dem Zeitfenster
(z. B. 05:00–10:00) wird außerhalb davon nur alle 30 Minuten abgefragt.

## Installation über HACS

1. HACS → ⋮ → **Benutzerdefinierte Repositories** →
   `https://github.com/SebastianBrunthaler/ha-db-pendler` eintragen, Typ **Integration**.
2. „DB Pendler“ in HACS installieren und Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → DB Pendler**.

**Update:** In HACS „DB Pendler“ → ⋮ → **Erneut herunterladen** (HACS erkennt neue Commits
ohne Release nicht immer als Update), danach Home Assistant neu starten.

### Manuell (ohne HACS)

Ordner `custom_components/db_pendler` nach `/config/custom_components/` kopieren und HA neu starten.

## Einrichtung

1. Start und Ziel eingeben, z. B. `Augsburg Hbf` und `München Hbf`.
2. Passende Haltestelle aus der Liste wählen und Optionen setzen:

| Option | Bedeutung |
|---|---|
| Vorlaufzeit | Fußweg zum Bahnhof – es werden nur Züge gezeigt, die du noch erreichst |
| Anzahl Verbindungen | 1–10 |
| Verkehrsmittel | Alle · Nur Nahverkehr (Deutschlandticket) · Nur Züge · Nur Regionalzüge & S-Bahn |
| Max. Umstiege | 0 = nur Direktverbindungen |
| Aktualisierungsintervall | in Minuten |
| Zeitfenster | nur in diesem Zeitraum häufig aktualisieren |

Für den Heimweg einfach eine zweite Strecke (Arbeit → Zuhause) anlegen.
Optionen lassen sich später über **Konfigurieren** ändern.

## Karte

Die Karte erscheint im Dashboard-Editor unter **Karte hinzufügen → DB Pendler**. Oder per YAML:

> Wichtig: `type: custom:db-pendler-card` verwenden. Wählt man im Editor nur den Sensor aus,
> legt Home Assistant eine normale Kachel (`type: tile`) an, die nur „In 10 Minuten“ zeigt.

```yaml
type: custom:db-pendler-card
entity: sensor.augsburg_hbf_munchen_hbf_nachste_abfahrt
title: Arbeit            # optional, Standard: „Start → Ziel“
max_connections: 4       # optional
show_legs: true          # aufklappbare Teilstrecken
warn_delay: 5            # ab so vielen Minuten Verspätung rot
```

Die Karte zeigt pro Verbindung: Abfahrt (mit Verspätung und durchgestrichener Planzeit),
Countdown („in 12 min“), Linien mit Umstiegen, Gleis (rot bei Gleiswechsel), Ankunft,
Fahrtdauer, Störungsmeldungen und auf Wunsch alle Teilstrecken. Der ↻-Button lädt sofort neu.

## Beispiel-Automation: Push bei Verspätung

```yaml
alias: Zug verspätet
triggers:
  - trigger: numeric_state
    entity_id: sensor.augsburg_hbf_munchen_hbf_verspatung
    above: 5
conditions:
  - condition: time
    after: "06:00:00"
    before: "08:30:00"
    weekday: [mon, tue, wed, thu, fri]
actions:
  - action: notify.mobile_app_mein_handy
    data:
      title: "🚆 Zug verspätet"
      message: >
        {{ state_attr('sensor.augsburg_hbf_munchen_hbf_verspatung', 'line') }}
        hat +{{ states('sensor.augsburg_hbf_munchen_hbf_verspatung') }} min.
```

## Fehlerbehebung

**„Custom element doesn't exist: db-pendler-card“**

1. Prüfen, ob die Integration eingerichtet ist (Einstellungen → Geräte & Dienste). Die Karte
   wird nur ausgeliefert, wenn die Integration geladen ist.
2. Home Assistant nach jedem Update neu starten.
3. Dashboard hart neu laden (Cmd/Strg + Shift + R). In der Companion-App:
   Einstellungen → Companion App → Fehlerbehebung → Frontend-Cache leeren.
4. In der Browser-Konsole (F12) sollte `DB-PENDLER-CARD <Version>` erscheinen.

Die Karte muss **nicht** als Dashboard-Ressource eingetragen werden. Ein zusätzlicher
manueller Eintrag unter `/db_pendler/db-pendler-card.js` ist unnötig, schadet aber nicht.

## Entwicklung

```bash
pip install pytest-homeassistant-custom-component
pytest tests
python tests/live_api_check.py   # Live-Abfrage gegen Transitous
```

## Hinweise

- Benötigt Home Assistant 2024.11 oder neuer.
- „Plan“ in der Karte bedeutet: für diese Verbindung liegen (noch) keine Echtzeitdaten vor.
- Daten: Transitous / DELFI. Keine Gewähr.
