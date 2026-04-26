#!/usr/bin/env python3
"""Lecture des livraisons depuis le calendrier Google via URL iCal."""

import re
import requests
from datetime import datetime, date, timedelta

try:
    import pytz
    PARIS_TZ = pytz.timezone("Europe/Paris")
    _has_pytz = True
except ImportError:
    _has_pytz = False
    PARIS_TZ = None

# Mapping email → prénom affiché
_EMAIL_NAMES = {
    "victor":        "Victor",
    "louis":         "Louis",
    "nicolas":       "Nicolas",
    "matthieuvincent": "Matthieu",
    "firmin":        "Firmin",
    "stanislas":     "Stanislas",
    "lucas":         "Lucas",
    "lucaschagnot":  "Lucas",
    "pierre":        "Pierre",
    "romain":        "Romain",
}

# Regex pour plaque française standard (ex: DW-362-TW)
_PLATE_RE = re.compile(r'\b[A-Z]{2}-\d{3}-[A-Z]{2}\b')


def _to_paris(dt):
    """Convertit un dt naive ou aware en Paris TZ."""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
    if _has_pytz:
        if dt.tzinfo is None:
            return PARIS_TZ.localize(dt)
        return dt.astimezone(PARIS_TZ)
    # Sans pytz : on traite comme UTC+2
    if dt.tzinfo is None:
        from datetime import timezone, timedelta as td
        return dt.replace(tzinfo=timezone(td(hours=2)))
    return dt


def _parse_name_from_email(email: str) -> str:
    """Extrait un prénom depuis une adresse email Mecanicus."""
    local = email.split("@")[0].lower()
    return _EMAIL_NAMES.get(local, local.capitalize())


def _extract_plate(text: str) -> str:
    m = _PLATE_RE.search(text)
    return m.group(0) if m else ""


def _parse_car_name(summary: str, plate: str) -> str:
    """Extrait le nom de la voiture depuis le titre de l'événement."""
    car = summary
    for prefix in [
        "Livraison chez le client ",
        "Livraison et inspection reprise ",
        "Livraison ",
    ]:
        if car.startswith(prefix):
            car = car[len(prefix):]
            break
    if plate:
        # Essayer avec tiret, sans tiret, et juste la plaque en fin
        for sep in [f" - {plate}", f"- {plate}", f" {plate}"]:
            car = car.replace(sep, "")
    car = re.sub(r"\s*#\d+$", "", car).strip()
    car = car.rstrip("- ").strip()
    return car


def _parse_ics_events(ics_text: str, start_dt: datetime, end_dt: datetime) -> list:
    """Parse brut d'un fichier ICS sans dépendance externe."""
    import re as _re

    events = []
    # Split en composants VEVENT
    vevent_blocks = _re.findall(
        r"BEGIN:VEVENT(.*?)END:VEVENT", ics_text, _re.DOTALL
    )

    def _unfold(text):
        """Unfold les lignes continuation ICS (RFC 5545)."""
        return _re.sub(r"\r?\n[ \t]", "", text)

    def _get(block, key):
        m = _re.search(
            rf"^{key}(?:;[^:]*)?:(.*)$", block, _re.MULTILINE | _re.IGNORECASE
        )
        return m.group(1).strip() if m else ""

    def _parse_dt(val):
        val = val.strip()
        # DATE-TIME avec Z (UTC)
        if val.endswith("Z"):
            try:
                dt = datetime.strptime(val, "%Y%m%dT%H%M%SZ")
                if _has_pytz:
                    import pytz as _pytz
                    return _pytz.utc.localize(dt).astimezone(PARIS_TZ)
                from datetime import timezone, timedelta as td
                return dt.replace(tzinfo=timezone.utc).astimezone(
                    timezone(td(hours=2))
                )
            except ValueError:
                pass
        # DATE-TIME local ou avec TZID (on ignore le TZID, on traite comme Paris)
        if "T" in val:
            val = val.split("T")
            try:
                dt = datetime.strptime(val[0] + "T" + val[1][:6], "%Y%m%dT%H%M%S")
                return _to_paris(dt)
            except ValueError:
                pass
        # DATE seule
        try:
            dt = datetime.strptime(val[:8], "%Y%m%d")
            return _to_paris(dt)
        except ValueError:
            return None

    def _unescape(val):
        return val.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")

    for block in vevent_blocks:
        block = _unfold(block)

        summary_raw = _get(block, "SUMMARY")
        summary = _unescape(summary_raw)
        if "livraison" not in summary.lower():
            continue

        dtstart_str = _get(block, r"DTSTART(?:;[^:]*)?")
        if not dtstart_str:
            m = _re.search(r"^DTSTART(?:;[^:]*)?:(.+)$", block, _re.MULTILINE | _re.IGNORECASE)
            dtstart_str = m.group(1).strip() if m else ""
        dtend_str = _get(block, r"DTEND(?:;[^:]*)?")
        if not dtend_str:
            m = _re.search(r"^DTEND(?:;[^:]*)?:(.+)$", block, _re.MULTILINE | _re.IGNORECASE)
            dtend_str = m.group(1).strip() if m else ""

        start = _parse_dt(dtstart_str)
        end   = _parse_dt(dtend_str)
        if start is None:
            continue

        # Filtre plage temporelle
        # Compare en ignorant tzinfo si nécessaire
        try:
            if start < start_dt or start > end_dt:
                continue
        except TypeError:
            # Mélange naive/aware
            pass

        location    = _unescape(_get(block, "LOCATION"))
        description = _unescape(_get(block, "DESCRIPTION"))

        # Récupérer les attendees (noms)
        attendees_raw = _re.findall(
            r"^ATTENDEE(?:;[^:]*)?:(.+)$", block, _re.MULTILINE | _re.IGNORECASE
        )
        assignees = []
        for att in attendees_raw:
            # essayer d'extraire le CN
            cn_m = _re.search(r"CN=([^;:]+)", att, _re.IGNORECASE)
            if cn_m:
                name = cn_m.group(1).strip().strip('"')
                # Si c'est un email, extraire le prénom
                if "@" in name:
                    name = _parse_name_from_email(name)
                assignees.append(name)
            elif "@mecanicus" in att.lower() or "@" in att:
                email = att.strip().replace("mailto:", "")
                assignees.append(_parse_name_from_email(email))

        # Client : première ligne de la description non vide
        desc_lines = [l.strip() for l in description.split("\n") if l.strip()]
        client = desc_lines[0] if desc_lines else ""
        # Exclure si c'est une URL ou un numéro de tel seul
        if client.startswith("http") or _re.match(r"^[\d\s+]{8,}$", client):
            client = ""

        plate    = _extract_plate(summary)
        car_name = _parse_car_name(summary, plate)
        is_client_delivery = "chez le client" in summary.lower()
        is_inspection      = "inspection" in summary.lower()

        events.append({
            "title":          summary,
            "car_name":       car_name,
            "plate":          plate,
            "start":          start,
            "end":            end,
            "location":       location,
            "client":         client,
            "is_client":      is_client_delivery,
            "is_inspection":  is_inspection,
            "assignees":      assignees,
        })

    events.sort(key=lambda e: e["start"])
    return events


def fetch_livraisons(ics_url: str, days_ahead: int = 14) -> list:
    """
    Récupère les événements Livraison des 14 prochains jours
    depuis une URL iCal secrète Google Calendar.

    Args:
        ics_url:   URL secrète iCal de l'agenda Sales
        days_ahead: Nombre de jours à scanner (défaut 14)

    Returns:
        Liste de dicts {title, car_name, plate, start, end,
                        location, client, is_client, is_inspection, assignees}
    """
    if not ics_url:
        print("⚠️  GCAL_ICS_URL non configuré — livraisons désactivées")
        return []

    try:
        resp = requests.get(ics_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️  Erreur fetch calendrier : {e}")
        return []

    now      = _to_paris(datetime.utcnow())
    cutoff   = now + timedelta(days=days_ahead)

    events = _parse_ics_events(resp.text, now, cutoff)
    print(f"  ✓ {len(events)} livraison(s) dans les {days_ahead} prochains jours")
    return events
