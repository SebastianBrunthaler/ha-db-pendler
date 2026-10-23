<p align="center">
  <img src="https://raw.githubusercontent.com/SebastianBrunthaler/ha-db-pendler/main/docs/banner.svg" alt="DB Pendler – Dein Arbeitsweg auf einen Blick" width="100%">
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white" alt="HACS Custom"></a>
  <img src="https://img.shields.io/github/manifest-json/v/SebastianBrunthaler/ha-db-pendler?filename=custom_components%2Fdb_pendler%2Fmanifest.json&style=for-the-badge&label=Version&color=ec0016" alt="Version">
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.11%2B-18BCF2?style=for-the-badge&logo=homeassistant&logoColor=white" alt="Home Assistant 2024.11+">
  <img src="https://img.shields.io/github/last-commit/SebastianBrunthaler/ha-db-pendler?style=for-the-badge" alt="Letzter Commit">
  <a href="https://buymeacoffee.com/sebastian.brunthaler"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy me a coffee"></a>
</p>

<p align="center">
  <b>Morgens kurz aufs Dashboard schauen und wissen, ob der Zug pünktlich ist.</b><br>
  Nächste Verbindungen mit Echtzeit-Verspätungen, Gleiswechseln, Umstiegen und Ausfällen –<br>
  ohne API-Key, eingerichtet in einer Minute.
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/SebastianBrunthaler/ha-db-pendler/main/docs/screenshot.png" alt="DB Pendler Karte in hellem und dunklem Design" width="820">
  <br><sub>Beispielansicht: Pfaffenhofen (Ilm) → München Hbf, hell und dunkel</sub>
</p>

---

## ✨ Features

| | |
|---|---|
| 🚆 **Echtzeit** | Verspätungen bei Abfahrt und Ankunft, durchgestrichene Planzeit, Countdown „in 12 min“ |
| 🔀 **Umstiege** | Verbindungen mit Umstieg, jede Teilstrecke mit Zug, Richtung und Gleis aufklappbar |
| 🛤️ **Gleiswechsel** | Geändertes Gleis wird rot hervorgehoben |
| ❌ **Ausfälle & Störungen** | Ausgefallene Züge durchgestrichen, Störungsmeldungen direkt an der Verbindung |
| 🎫 **Deutschlandticket-Filter** | Nur Nahverkehr, nur Züge oder nur Regionalzüge & S-Bahn |
| 🚶 **Vorlaufzeit** | Fußweg zum Bahnhof einstellen – es erscheinen nur Züge, die du noch erreichst |
| 🌙 **Zeitfenster** | Nur morgens häufig aktualisieren, sonst alle 30 Minuten |
| 🔔 **Automationen** | Eigener Verspätungs-Sensor, z. B. für eine Push-Nachricht aufs Handy |
| 🎨 **Eingebaute Karte** | Wird automatisch geladen, passt sich hellem und dunklem Theme an |
| 🔑 **Kein API-Key** | Keine Registrierung, keine Zugangsdaten |

## 🚀 Installation

### Über HACS (empfohlen)

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SebastianBrunthaler&repository=ha-db-pendler&category=integration)

Oder manuell in HACS:

1. **HACS → ⋮ → Benutzerdefinierte Repositories**
2. `https://github.com/SebastianBrunthaler/ha-db-pendler` eintragen, Typ **Integration**
3. **DB Pendler** suchen, herunterladen und Home Assistant **neu starten**

### Manuell

Ordner `custom_components/db_pendler` nach `/config/custom_components/` kopieren und Home Assistant neu starten.

## ⚙️ Einrichtung

[![Integration hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=db_pendler)

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → DB Pendler**
2. Start und Ziel eingeben, z. B. `Pfaffenhofen (Ilm)` und `München Hbf`
3. Passende Haltestelle aus der Liste wählen und Optionen setzen:

| Option | Bedeutung | Standard |
|---|---|---|
| Vorlaufzeit | Fußweg zum Bahnhof in Minuten | 0 |
| Anzahl Verbindungen | 1–10 | 5 |
| Verkehrsmittel | Alle · Nur Nahverkehr (Deutschlandticket) · Nur Züge · Nur Regionalzüge & S-Bahn | Alle |
| Max. Umstiege | 0 = nur Direktverbindungen | 3 |
| Aktualisierungsintervall | in Minuten | 3 |
| Zeitfenster | Nur in diesem Zeitraum häufig aktualisieren | aus (05:00–10:00) |

> 💡 Für den Heimweg einfach eine zweite Strecke anlegen (Arbeit → Zuhause).
> Optionen lassen sich jederzeit über **Konfigurieren** ändern.

## 🃏 Dashboard-Karte

Im Dashboard-Editor: **Karte hinzufügen → „DB Pendler“** suchen. Oder per YAML:

```yaml
type: custom:db-pendler-card
entity: sensor.pfaffenhofen_ilm_munchen_hbf_nachste_abfahrt
title: Arbeit
max_connections: 4
show_legs: true
warn_delay: 5
```

| Option | Beschreibung | Standard |
|---|---|---|
| `entity` | Sensor „Nächste Abfahrt“ einer Strecke | – |
| `title` | Überschrift | „Start → Ziel“ |
| `max_connections` | Anzahl angezeigter Verbindungen | 5 |
| `show_legs` | Teilstrecken aufklappbar anzeigen | `true` |
| `warn_delay` | Ab so vielen Minuten Verspätung rot statt orange | 5 |

> ⚠️ Wichtig ist `type: custom:db-pendler-card`. Wählt man im Editor nur den Sensor aus, legt
> Home Assistant eine normale Kachel (`type: tile`) an, die nur „In 10 Minuten“ zeigt.

Die Karte muss **nicht** als Dashboard-Ressource eingetragen werden – die Integration liefert sie selbst aus.

## 📊 Sensoren

Pro Strecke entstehen zwei Sensoren:

| Sensor | Wert | Wichtige Attribute |
|---|---|---|
| `sensor.<strecke>_nachste_abfahrt` | Abfahrtszeit der nächsten Verbindung, die nicht ausfällt | `lines`, `platform`, `departure_delay`, `arrival`, `duration`, `transfers`, `connections` |
| `sensor.<strecke>_verspatung` | Verspätung dieser Verbindung in Minuten | `line`, `cancelled_connections` |

## 🔔 Beispiel: Push-Nachricht bei Verspätung

```yaml
alias: Zug verspätet
triggers:
  - trigger: numeric_state
    entity_id: sensor.pfaffenhofen_ilm_munchen_hbf_verspatung
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
        {{ state_attr('sensor.pfaffenhofen_ilm_munchen_hbf_verspatung', 'line') }}
        hat +{{ states('sensor.pfaffenhofen_ilm_munchen_hbf_verspatung') }} min.
```

## 🛟 Fehlerbehebung

**„Custom element doesn't exist: db-pendler-card“**

1. Ist die Integration eingerichtet? Die Karte wird nur ausgeliefert, wenn mindestens eine Strecke angelegt ist.
2. Nach jedem Update Home Assistant **neu starten**.
3. Dashboard hart neu laden (<kbd>Cmd</kbd>/<kbd>Strg</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd>).
   In der Companion-App: *Einstellungen → Companion App → Fehlerbehebung → Frontend-Cache leeren*.
4. In der Browser-Konsole (<kbd>F12</kbd>) sollte `DB-PENDLER-CARD <Version>` stehen.

**Update wird in HACS nicht angezeigt** – In HACS „DB Pendler“ öffnen → ⋮ → **Erneut herunterladen**, danach neu starten.

**„Plan“ statt Verspätung** – Für diese Verbindung liegen (noch) keine Echtzeitdaten vor.

## 📡 Datenquelle

Die Fahrplandaten kommen von [**Transitous**](https://transitous.org), einem offenen, kostenlosen
Routing-Dienst auf Basis von [MOTIS](https://github.com/motis-project/motis). Er nutzt die bundesweiten
DELFI-Fahrplandaten inklusive DB-Echtzeitdaten.

<sub>Warum nicht direkt bahn.de? Die Verbindungssuche von bahn.de und DB Navigator blockt automatisierte
Abfragen, und der Community-Dienst `v6.db.transport.rest` ist häufig nicht erreichbar. Wer einen eigenen
MOTIS-Server betreibt, kann ihn bei der Einrichtung eintragen.</sub>

Bitte die Abfragefrequenz moderat halten – Transitous ist ein Community-Projekt. 🙏

## 🧑‍💻 Entwicklung

```bash
pip install pytest-homeassistant-custom-component
pytest tests                      # Config-Flow, Sensoren, Kartenauslieferung
python tests/live_api_check.py    # Live-Abfrage gegen Transitous
```

Fehler und Ideen gerne als [Issue](https://github.com/SebastianBrunthaler/ha-db-pendler/issues).

## ☕ Unterstützen

Wenn dir DB Pendler den Morgen ein bisschen entspannter macht, freue ich mich über einen Kaffee:

<a href="https://buymeacoffee.com/sebastian.brunthaler">
  <img src="https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=%E2%98%95&slug=sebastian.brunthaler&button_colour=FFDD00&font_colour=000000&font_family=Inter&outline_colour=000000&coffee_colour=ffffff" alt="Buy me a coffee" height="48">
</a>

---

<sub>Kein offizielles Produkt der Deutschen Bahn AG. Fahrplandaten: Transitous / DELFI, ohne Gewähr.</sub>
