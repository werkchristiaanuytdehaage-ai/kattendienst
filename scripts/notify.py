#!/usr/bin/env python3
"""Stuurt web-push meldingen voor de Kattendienst-app.
Draait periodiek via GitHub Actions: leest de gedeelde stand uit Firebase,
bepaalt welke meldingen nodig zijn en verstuurt ze naar alle aangemelde apparaten.
Dedup via /pushflags zodat elke toestand maar één keer een melding geeft."""

import os, json, time, urllib.request, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pywebpush import webpush, WebPushException

DB_URL   = os.environ["DB_URL"].rstrip("/")
SUBJECT  = os.environ.get("VAPID_SUBJECT", "mailto:noreply@example.com")
PEM      = os.environ["VAPID_PRIVATE"]
AMS      = ZoneInfo("Europe/Amsterdam")

MAX_FEEDS = 4
LITTER_DIRTY_H = 12
LITTER_EMERGENCY_H = 24
DEFAULT_FEED_TIMES = [{"h": 7, "m": 0}, {"h": 18, "m": 15}]

PEM_PATH = "/tmp/vapid_private.pem"
with open(PEM_PATH, "w") as f:
    f.write(PEM)


def get(path):
    try:
        with urllib.request.urlopen(f"{DB_URL}/{path}.json", timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print("GET fout", path, e)
        return None


def put(path, value):
    data = json.dumps(value).encode()
    req = urllib.request.Request(f"{DB_URL}/{path}.json", data=data, method="PUT",
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print("PUT fout", path, e)


def delete(path):
    req = urllib.request.Request(f"{DB_URL}/{path}.json", method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print("DELETE fout", path, e)


def feeds_used_since(filled_ms, now_ms, feed_times):
    """Aantal verstreken voedertijden (wandklok Amsterdam) sinds filled_ms."""
    count = 0
    filled_dt = datetime.fromtimestamp(filled_ms / 1000, AMS)
    day = filled_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.fromtimestamp(now_ms / 1000, AMS) + timedelta(days=1)
    while day <= end:
        for t in feed_times:
            slot_ms = day.replace(hour=t["h"], minute=t["m"]).timestamp() * 1000
            if filled_ms < slot_ms <= now_ms:
                count += 1
        day += timedelta(days=1)
    return min(MAX_FEEDS, count)


def name_for(cfg_list, idx, fallback):
    try:
        n = cfg_list[idx].get("name")
        return n if n else fallback
    except Exception:
        return fallback


def main():
    subs = get("subscriptions") or {}
    if not subs:
        print("Geen aanmeldingen — niets te sturen.")
        return

    # testmodus: stuur direct een proefmelding naar alle apparaten
    if str(os.environ.get("TEST", "")).lower() in ("1", "true", "yes"):
        payload = {"title": "🔔 Testmelding", "body": "Top! Achtergrond-meldingen werken. 🐱",
                   "tag": "test", "url": "./index.html"}
        for subkey, sub in list(subs.items()):
            if not isinstance(sub, dict) or "endpoint" not in sub:
                continue
            info = {"endpoint": sub["endpoint"], "keys": sub.get("keys", {})}
            try:
                claims = {"sub": SUBJECT, "exp": int(time.time()) + 12 * 3600}
                webpush(subscription_info=info, data=json.dumps(payload),
                        vapid_private_key=PEM_PATH, vapid_claims=claims)
                print("testmelding verstuurd naar", subkey)
            except WebPushException as e:
                code = getattr(e.response, "status_code", None)
                print("test push fout", subkey, code, e)
                if code in (404, 410):
                    delete(f"subscriptions/{subkey}")
        return

    # ---- "iemand heeft een taak gedaan" → melding naar de ánder ----
    events = get("events") or {}
    if isinstance(events, dict):
        now = time.time() * 1000
        for ekey, ev in list(events.items()):
            if not isinstance(ev, dict):
                delete(f"events/{ekey}"); continue
            who = ev.get("who", "Iemand")
            etype = ev.get("type")
            at = ev.get("at", 0)
            if now - at > 60 * 60 * 1000:   # ouder dan een uur: overslaan
                delete(f"events/{ekey}"); continue
            if etype == "voer":
                title, body = "✅ Voederbak gevuld", f"Gedaan door {who} 🥣"
            elif etype == "bak":
                title, body = "✅ Kattenbak verschoond", f"Gedaan door {who} 🧽"
            else:
                delete(f"events/{ekey}"); continue
            payload = {"title": title, "body": body, "tag": "action-" + ekey, "url": "./index.html"}
            for subkey, sub in list(subs.items()):
                if not isinstance(sub, dict) or "endpoint" not in sub:
                    continue
                if sub.get("name") == who:   # niet naar de uitvoerder zelf
                    continue
                info = {"endpoint": sub["endpoint"], "keys": sub.get("keys", {})}
                try:
                    claims = {"sub": SUBJECT, "exp": int(time.time()) + 12 * 3600}
                    webpush(subscription_info=info, data=json.dumps(payload),
                            vapid_private_key=PEM_PATH, vapid_claims=claims)
                    print("actie-melding naar", subkey, "-", title)
                except WebPushException as e:
                    code = getattr(e.response, "status_code", None)
                    print("actie push fout", subkey, code, e)
                    if code in (404, 410):
                        delete(f"subscriptions/{subkey}"); subs.pop(subkey, None)
            delete(f"events/{ekey}")

    state = get("state") or {}
    config = get("config") or {}
    flags = get("pushflags") or {}
    feed_times = config.get("feedTimes") or DEFAULT_FEED_TIMES
    feeders_cfg = config.get("feeders") or []
    litters_cfg = config.get("litters") or []
    now_ms = time.time() * 1000

    # ---- bepaal welke meldingen nodig zijn ----
    due = []  # (flagkey, sourcets, title, body, tag)

    for key, val in state.items():
        if not isinstance(val, dict):
            continue
        if key.startswith("feeder") and "filledAt" in val:
            try:
                idx = int(key.replace("feeder", "")) - 1
            except ValueError:
                idx = 0
            nm = name_for(feeders_cfg, idx, "Voederbak")
            filled = val["filledAt"]
            left = MAX_FEEDS - feeds_used_since(filled, now_ms, feed_times)
            if left <= 0:
                due.append((f"{key}_empty", filled, "🚨 NOOD: bak leeg",
                            f"{nm} is helemaal leeg! Vul direct bij.", key))
            elif left == 1:
                due.append((f"{key}_low", filled, "🍽️ Bijna leeg",
                            f"{nm}: nog maar 1 voeding over. Tijd om bij te vullen!", key))

        if key.startswith("litter") and "cleanedAt" in val:
            try:
                idx = int(key.replace("litter", "")) - 1
            except ValueError:
                idx = 0
            nm = name_for(litters_cfg, idx, "Kattenbak")
            cleaned = val["cleanedAt"]
            hours = (now_ms - cleaned) / 3600000
            if hours >= LITTER_EMERGENCY_H:
                due.append((f"{key}_emergency", cleaned, "🚨 NOOD: verschoon nu",
                            f"{nm} is 24 uur oud en moet direct verschoond worden!", key))
            elif hours >= LITTER_DIRTY_H:
                due.append((f"{key}_dirty", cleaned, "🚽 Bak is vuil",
                            f"{nm} is na 12 uur vuil. Verschonen wanneer het uitkomt.", key))

    # ---- filter wat al gestuurd is voor deze toestand ----
    to_send = [d for d in due if flags.get(d[0]) != d[1]]
    if not to_send:
        print("Niets nieuws te melden.")
        return

    for flagkey, sourcets, title, body, tag in to_send:
        payload = {"title": title, "body": body, "tag": tag, "url": "./index.html"}
        sent_any = False
        for subkey, sub in list(subs.items()):
            if not isinstance(sub, dict) or "endpoint" not in sub:
                continue
            info = {"endpoint": sub["endpoint"], "keys": sub.get("keys", {})}
            try:
                # verse claims per verzending: pywebpush vult zelf de juiste 'aud' per push-dienst aan
                claims = {"sub": SUBJECT, "exp": int(time.time()) + 12 * 3600}
                webpush(subscription_info=info, data=json.dumps(payload),
                        vapid_private_key=PEM_PATH, vapid_claims=claims)
                sent_any = True
            except WebPushException as e:
                code = getattr(e.response, "status_code", None)
                print("push fout", subkey, code, e)
                if code in (404, 410):
                    delete(f"subscriptions/{subkey}")
                    subs.pop(subkey, None)
        # markeer als verstuurd zodat dezelfde toestand niet opnieuw meldt
        put(f"pushflags/{flagkey}", sourcets)
        print(("verstuurd" if sent_any else "geen ontvangers"), flagkey, "-", title)


if __name__ == "__main__":
    main()
