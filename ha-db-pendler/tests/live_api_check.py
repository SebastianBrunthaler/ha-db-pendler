"""Manueller Live-Test gegen Transitous: python tests/live_api_check.py"""
import asyncio, json, sys
from datetime import datetime, timezone
import aiohttp
sys.path.insert(0, ".")
from custom_components.db_pendler.api import PendlerApi
from custom_components.db_pendler.const import DEFAULT_BASE_URL, PRODUCTS

async def main(frm="Augsburg Hbf", to="München Hbf"):
    async with aiohttp.ClientSession() as s:
        api = PendlerApi(s, DEFAULT_BASE_URL)
        a, b = (await api.search_stops(frm))[0], (await api.search_stops(to))[0]
        print("Von:", a["label"], "| Nach:", b["label"])
        conns = await api.get_connections(a["id"], b["id"], datetime.now(timezone.utc), 5, PRODUCTS["all"], 3)
        for c in conns:
            print(c["departure"], f"+{c['departure_delay']}", " → ".join(c["lines"]), "Gl.", c["platform"],
                  "an", c["arrival"], f"{c['duration']}min", "RT" if c["realtime"] else "Plan", "X" if c["cancelled"] else "")
        json.dump({"from": a["name"], "to": b["name"], "connections": conns}, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), ensure_ascii=False)

asyncio.run(main())
