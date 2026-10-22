/* DB Pendler Card – zeigt die nächsten Verbindungen einer DB-Pendler-Strecke. */

const CARD_VERSION = "1.0.1";

const MODE_ICONS = {
  HIGHSPEED_RAIL: "mdi:train-variant",
  LONG_DISTANCE: "mdi:train-variant",
  NIGHT_RAIL: "mdi:train-variant",
  REGIONAL_FAST_RAIL: "mdi:train",
  REGIONAL_RAIL: "mdi:train",
  RAIL: "mdi:train",
  SUBURBAN: "mdi:subway-variant",
  SUBWAY: "mdi:subway",
  TRAM: "mdi:tram",
  BUS: "mdi:bus",
  COACH: "mdi:bus",
  FERRY: "mdi:ferry",
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Die Klasse wird erst erzeugt, wenn HA bereit ist (siehe unten).
function createCardClass() {
  return class DbPendlerCard extends HTMLElement {
    static getConfigForm() {
      return {
        schema: [
          { name: "entity", required: true, selector: { entity: { domain: "sensor" } } },
          { name: "title", selector: { text: {} } },
          { name: "max_connections", selector: { number: { min: 1, max: 10, mode: "box" } } },
          { name: "show_legs", selector: { boolean: {} } },
          { name: "warn_delay", selector: { number: { min: 1, max: 60, mode: "box", unit_of_measurement: "min" } } },
        ],
        computeLabel: (s) =>
          ({
            entity: "Sensor „Nächste Abfahrt“",
            title: "Titel (optional)",
            max_connections: "Max. Verbindungen",
            show_legs: "Teilstrecken aufklappbar anzeigen",
            warn_delay: "Ab dieser Verspätung rot markieren",
          })[s.name],
      };
    }

    static getStubConfig(hass) {
      const entity = Object.keys(hass.states).find(
        (id) => id.startsWith("sensor.") && hass.states[id].attributes.db_pendler
      );
      return { entity: entity || "" };
    }

    setConfig(config) {
      if (!config.entity) throw new Error("Bitte einen DB-Pendler-Sensor als 'entity' angeben.");
      this._config = { max_connections: 5, show_legs: true, warn_delay: 5, ...config };
      this._lastState = undefined;
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      const state = hass.states[this._config?.entity];
      if (state !== this._lastState) {
        this._lastState = state;
        this._render();
      }
    }

    connectedCallback() {
      this._timer = setInterval(() => this._render(), 30000);
    }

    disconnectedCallback() {
      clearInterval(this._timer);
    }

    getCardSize() {
      return 1 + Math.min(this._config?.max_connections ?? 5, 5);
    }

    getGridOptions() {
      return { columns: 12, min_columns: 6, rows: "auto" };
    }

    _fmtTime(iso) {
      if (!iso) return "–";
      return new Date(iso).toLocaleTimeString(this._hass?.locale?.language || "de", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    _delayHtml(delay, warn) {
      if (delay === null || delay === undefined || delay === 0) return "";
      const cls = delay < 0 ? "early" : delay >= warn ? "late" : "slight";
      return `<span class="delay ${cls}">${delay > 0 ? "+" : ""}${delay}</span>`;
    }

    _countdown(iso) {
      const min = Math.round((new Date(iso) - Date.now()) / 60000);
      if (min <= 0) return "jetzt";
      if (min < 60) return `in ${min} min`;
      return `in ${Math.floor(min / 60)} h ${min % 60} min`;
    }

    _refresh() {
      this._hass.callService("homeassistant", "update_entity", { entity_id: this._config.entity });
      const btn = this.shadowRoot.querySelector(".refresh");
      btn?.classList.add("spin");
      setTimeout(() => btn?.classList.remove("spin"), 1000);
    }

    _render() {
      if (!this._config || !this._hass) return;
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      const openDetails = new Set(
        [...this.shadowRoot.querySelectorAll("details[open]")].map((d) => d.dataset.key)
      );

      const state = this._hass.states[this._config.entity];
      if (!state) {
        this.shadowRoot.innerHTML = `<ha-card><div class="msg">Entität ${esc(this._config.entity)} nicht gefunden.</div></ha-card>`;
        return;
      }

      const a = state.attributes;
      const warn = this._config.warn_delay;
      const now = Date.now();
      const conns = (a.connections || [])
        .filter((c) => new Date(c.departure) > now - 60000)
        .slice(0, this._config.max_connections);
      const title = this._config.title || `${a.from_station ?? "?"} → ${a.to_station ?? "?"}`;

      const rows = conns
        .map((c) => {
          const key = `${c.legs[0]?.trip_id}|${c.departure_planned}`;
          const planned = c.departure_planned && c.departure_delay ? `<s>${this._fmtTime(c.departure_planned)}</s>` : "";
          const lines = c.legs
            .map((l) => `<span class="line"><ha-icon icon="${MODE_ICONS[l.mode] || "mdi:train"}"></ha-icon>${esc(l.line)}</span>`)
            .join('<ha-icon class="chev" icon="mdi:chevron-right"></ha-icon>');
          const platform = c.platform
            ? `<span class="platform ${c.platform_changed ? "changed" : ""}" title="${c.platform_changed ? "Gleiswechsel, geplant: " + esc(c.platform_planned) : ""}">Gl. ${esc(c.platform)}</span>`
            : "";
          const transfers = c.transfers === 0 ? "direkt" : c.transfers === 1 ? "1 Umstieg" : `${c.transfers} Umstiege`;
          const alerts = c.alerts?.length
            ? `<div class="alert"><ha-icon icon="mdi:alert-circle-outline"></ha-icon>${esc(c.alerts[0])}</div>`
            : "";
          const legs =
            this._config.show_legs && c.legs.length
              ? `<details data-key="${esc(key)}" ${openDetails.has(key) ? "open" : ""}><summary>Details</summary>${c.legs
                  .map(
                    (l) => `<div class="leg ${l.cancelled ? "cancelled" : ""}">
                      <div><b>${this._fmtTime(l.departure)}</b>${this._delayHtml(l.departure_delay, warn)} ${esc(l.from)}${l.platform ? ` · Gl. ${esc(l.platform)}` : ""}</div>
                      <div class="legline">${esc(l.name)}${l.direction ? ` → ${esc(l.direction)}` : ""}</div>
                      <div><b>${this._fmtTime(l.arrival)}</b>${this._delayHtml(l.arrival_delay, warn)} ${esc(l.to)}${l.arrival_platform ? ` · Gl. ${esc(l.arrival_platform)}` : ""}</div>
                    </div>`
                  )
                  .join("")}</details>`
              : "";

          return `<div class="conn ${c.cancelled ? "cancelled" : ""}">
            <div class="dep">
              <div class="time">${this._fmtTime(c.departure)}${this._delayHtml(c.departure_delay, warn)}</div>
              <div class="sub">${planned} ${c.cancelled ? '<span class="late">fällt aus</span>' : this._countdown(c.departure)}</div>
            </div>
            <div class="info">
              <div class="lines">${lines}</div>
              <div class="sub">an ${this._fmtTime(c.arrival)}${this._delayHtml(c.arrival_delay, warn)} · ${c.duration ?? "?"} min · ${transfers}${c.realtime ? "" : ' · <span title="Keine Echtzeitdaten">Plan</span>'}</div>
            </div>
            <div class="right">${platform}</div>
            ${alerts}${legs}
          </div>`;
        })
        .join("");

      const updated = state.last_updated ? this._fmtTime(state.last_updated) : "";
      const empty =
        state.state === "unavailable"
          ? "Fahrplan gerade nicht erreichbar."
          : "Keine Verbindungen gefunden.";

      this.shadowRoot.innerHTML = `
        <style>${DbPendlerCard.styles}</style>
        <ha-card>
          <div class="header">
            <ha-icon icon="mdi:train-car"></ha-icon>
            <div class="title">${esc(title)}</div>
            <span class="updated">${updated}</span>
            <ha-icon-button class="refresh" label="Aktualisieren"><ha-icon icon="mdi:refresh"></ha-icon></ha-icon-button>
          </div>
          <div class="list">${rows || `<div class="msg">${empty}</div>`}</div>
        </ha-card>`;
      this.shadowRoot.querySelector(".refresh").addEventListener("click", () => this._refresh());
    }

    static styles = `
      ha-card { padding: 12px 16px 8px; }
      .header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
      .header > ha-icon { color: var(--primary-color); }
      .title { flex: 1; font-size: 1.1em; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .updated { font-size: 0.8em; color: var(--secondary-text-color); }
      .refresh { --mdc-icon-button-size: 36px; color: var(--secondary-text-color); }
      .refresh.spin ha-icon { animation: spin 1s linear; }
      @keyframes spin { to { transform: rotate(360deg); } }
      .conn { display: grid; grid-template-columns: auto 1fr auto; gap: 2px 12px; padding: 10px 0; border-top: 1px solid var(--divider-color); align-items: center; }
      .conn:first-child { border-top: none; }
      .conn.cancelled .time, .conn.cancelled .lines { text-decoration: line-through; opacity: 0.6; }
      .dep { min-width: 76px; }
      .time { font-size: 1.35em; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }
      .sub { font-size: 0.85em; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .lines { display: flex; flex-wrap: wrap; align-items: center; gap: 2px; }
      .line { display: inline-flex; align-items: center; gap: 2px; padding: 1px 6px; border-radius: 6px; background: var(--secondary-background-color); font-size: 0.85em; font-weight: 500; }
      .line ha-icon { --mdc-icon-size: 14px; }
      .chev { --mdc-icon-size: 16px; color: var(--secondary-text-color); }
      .delay { font-size: 0.75em; font-weight: 600; margin-left: 4px; vertical-align: super; }
      .late { color: var(--error-color, #db4437); font-weight: 600; }
      .delay.late { color: var(--error-color, #db4437); }
      .delay.slight { color: var(--warning-color, #ffa600); }
      .delay.early { color: var(--success-color, #43a047); }
      .platform { padding: 2px 8px; border-radius: 6px; border: 1px solid var(--divider-color); font-size: 0.85em; font-weight: 600; white-space: nowrap; }
      .platform.changed { border-color: var(--error-color, #db4437); color: var(--error-color, #db4437); }
      .alert, details { grid-column: 1 / -1; font-size: 0.82em; color: var(--secondary-text-color); }
      .alert { display: flex; gap: 4px; align-items: flex-start; color: var(--warning-color, #ffa600); }
      .alert ha-icon { --mdc-icon-size: 16px; flex: none; }
      summary { cursor: pointer; width: fit-content; }
      .leg { margin: 6px 0 0 4px; padding-left: 8px; border-left: 3px solid var(--primary-color); }
      .leg.cancelled { border-left-color: var(--error-color, #db4437); text-decoration: line-through; }
      .legline { color: var(--primary-text-color); padding: 2px 0; }
      .msg { padding: 12px 0; color: var(--secondary-text-color); }
      s { opacity: 0.7; }
    `;
  };
}

function registerCard() {
  if (customElements.get("db-pendler-card")) return;
  customElements.define("db-pendler-card", createCardClass());
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "db-pendler-card",
    name: "DB Pendler",
    description: "Nächste Bahnverbindungen für den Arbeitsweg",
    preview: true,
  });
  console.info(`%c DB-PENDLER-CARD %c ${CARD_VERSION} `, "background:#ec0016;color:#fff", "");
}

// HA lädt dieses Skript parallel zum eigenen Frontend. Das Frontend ersetzt beim Start
// window.customElements durch eine Scoped Registry (Polyfill). Würde die Karte vorher
// registriert, fände Lovelace sie nicht („Custom element doesn't exist“). Deshalb warten,
// bis <home-assistant> definiert ist – dann ist die Registry sicher ausgetauscht.
customElements.whenDefined("home-assistant").then(registerCard);
