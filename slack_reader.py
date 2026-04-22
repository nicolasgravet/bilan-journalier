import re
import ssl
import certifi
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import SLACK_BOT_TOKEN, CHANNEL_IDS, CHANNEL_NAMES

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())
client = WebClient(token=SLACK_BOT_TOKEN, ssl=_ssl_ctx)

_channel_id_cache = dict(CHANNEL_IDS)


def _find_all_channels():
    channels = {}
    cursor = None
    try:
        while True:
            kwargs = dict(types="public_channel,private_channel", limit=200, exclude_archived=True)
            if cursor:
                kwargs["cursor"] = cursor
            result = client.conversations_list(**kwargs)
            for ch in result["channels"]:
                channels[ch["name"].lower()] = ch
            if not result.get("has_more"):
                break
            cursor = result["response_metadata"]["next_cursor"]
    except SlackApiError as e:
        print(f"Erreur liste canaux: {e}")
    return channels


def get_channel_id(key):
    if _channel_id_cache.get(key):
        return _channel_id_cache[key]
    name = CHANNEL_NAMES.get(key, key).lower()
    all_ch = _find_all_channels()
    ch = all_ch.get(name)
    if ch:
        _channel_id_cache[key] = ch["id"]
        return ch["id"]
    # Recherche partielle
    for ch_name, ch_data in all_ch.items():
        if name in ch_name and ch_data.get("is_member"):
            _channel_id_cache[key] = ch_data["id"]
            return ch_data["id"]
    return None


def get_messages(channel_id, days_back=1, limit=200):
    oldest = (datetime.now() - timedelta(days=days_back)).timestamp()
    messages = []
    try:
        cursor = None
        while True:
            kwargs = dict(channel=channel_id, oldest=str(oldest), limit=limit)
            if cursor:
                kwargs["cursor"] = cursor
            result = client.conversations_history(**kwargs)
            messages.extend(result["messages"])
            if not result.get("has_more"):
                break
            cursor = result["response_metadata"]["next_cursor"]
    except SlackApiError as e:
        print(f"Erreur lecture messages ({channel_id}): {e}")
    return messages


def _extract_field(text, emoji_code):
    """Extrait la valeur après ':emoji_code: :' dans un message Slack."""
    pattern = rf":{re.escape(emoji_code)}:\s*:?\s*(.+?)(?:\n|$)"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def _parse_amount(raw):
    if not raw:
        return None, None
    # Nettoyer: 68.500,00€ → 68500.00 ou 68500€ → 68500
    cleaned = raw.replace(".", "").replace(",", ".").replace("€", "").replace(" ", "")
    try:
        val = float(cleaned)
        return val, f"{val:,.0f} €".replace(",", "\u202f")
    except ValueError:
        return None, raw.strip()


def parse_offre_acceptee(text):
    """
    Format Slack:
    Offre acceptée ! :gift_heart:
    :racing_car: : Porsche 996 Turbo...
    :male-mechanic: : Pierre guibert
    :calendar: : 27/03/2026
    :eight_pointed_black_star: : Achat
    :euro: : 68500€
    :moneybag: : 16400€
    """
    voiture = _extract_field(text, "racing_car") or "—"
    acheteur = _extract_field(text, "male-mechanic") or _extract_field(text, "bust_in_silhouette") or "—"
    type_vente = _extract_field(text, "eight_pointed_black_star") or "—"

    prix_raw = _extract_field(text, "euro")
    marge_raw = _extract_field(text, "moneybag")

    prix_val, prix_fmt = _parse_amount(prix_raw)
    marge_val, marge_fmt = _parse_amount(marge_raw)

    return {
        "voiture": voiture.strip("* "),
        "acheteur": acheteur.strip('"'),
        "type": type_vente,
        "prix_vente": prix_fmt or "—",
        "marge": marge_fmt or "—",
        "prix_val": prix_val or 0,
        "marge_val": marge_val or 0,
    }


def parse_voiture_reservee(text):
    """
    Format Slack:
    Voiture réservée !
    :racing_car: : Ferrari 360 Modena
    :page_facing_up: : BC000953
    :bust_in_silhouette: : "AP Corse, s.r.o"
    :calendar: : 01/04/2026
    :euro: : 79.000,00€
    :moneybag: :990€
    """
    voiture = _extract_field(text, "racing_car") or "—"
    acheteur = _extract_field(text, "bust_in_silhouette") or "—"
    ref = _extract_field(text, "page_facing_up") or ""
    date_livraison = _extract_field(text, "calendar") or "—"

    marge_raw = _extract_field(text, "moneybag")
    prix_raw = _extract_field(text, "euro")

    _, marge_fmt = _parse_amount(marge_raw)
    _, prix_fmt = _parse_amount(prix_raw)

    return {
        "voiture": voiture.strip("* "),
        "acheteur": acheteur.strip('"'),
        "ref": ref,
        "date_livraison": date_livraison,
        "marge": marge_fmt or "—",
        "prix": prix_fmt or "—",
    }


def fetch_achat_vente(days_back=1):
    ch_id = get_channel_id("achat_vente")
    if not ch_id:
        print("Canal achat_vente introuvable")
        return [], [], []

    messages = get_messages(ch_id, days_back=days_back)
    offres, reservees, general = [], [], []

    for msg in messages:
        text = msg.get("text", "")
        ts = datetime.fromtimestamp(float(msg.get("ts", 0)))
        if not text or msg.get("subtype") in ("channel_join", "channel_leave"):
            continue

        tl = text.lower()
        if "offre accept" in tl:
            parsed = parse_offre_acceptee(text)
            parsed.update({"ts": ts, "raw": text})
            offres.append(parsed)
        elif re.search(r"voiture\s+r[eé]serv[eé]e\s*!", tl):
            parsed = parse_voiture_reservee(text)
            parsed.update({"ts": ts, "raw": text})
            reservees.append(parsed)
        elif len(text) > 10 and not text.startswith("<"):
            general.append({"text": text, "ts": ts, "user": msg.get("user", "")})

    # Dédupliquer : par voiture, garder uniquement la plus récente
    latest_by_car = {}
    for o in offres:
        voiture = o.get("voiture", "")
        ts = o.get("ts")
        if voiture not in latest_by_car or (ts and ts > latest_by_car[voiture].get("ts")):
            latest_by_car[voiture] = o
    offres = sorted(latest_by_car.values(), key=lambda x: x.get("ts") or 0, reverse=True)

    return general, offres, reservees


def fetch_logistique(days_back=30):
    """
    Format Slack logistique :
    *Nouveaux frais à programmer*
    :racing_car: : Porsche 991.1...
    :card_file_box: : Catégorie
    :toolbox: : Objet du frais
    https://airtable.com/.../recXXXXX|Voir détail
    """
    ch_id = get_channel_id("logistique")
    if not ch_id:
        print("Canal logistique introuvable — vérifiez l'invitation du bot")
        return {}

    messages = get_messages(ch_id, days_back=days_back)
    frais_by_car = {}

    for msg in messages:
        text = msg.get("text", "")
        ts = datetime.fromtimestamp(float(msg.get("ts", 0)))

        if "nouveaux frais" not in text.lower() and "frais à programmer" not in text.lower():
            continue

        voiture = _extract_field(text, "racing_car") or "Non spécifié"
        categorie = _extract_field(text, "card_file_box") or "—"
        objet = _extract_field(text, "toolbox") or "—"

        # Extraire le record ID Airtable depuis l'URL
        airtable_match = re.search(r"airtable\.com/[^|]+/(rec[A-Za-z0-9]+)", text)
        airtable_record_id = airtable_match.group(1) if airtable_match else None

        # Extraire l'URL complète pour lien direct
        url_match = re.search(r"<(https://airtable\.com/[^|>]+)\|Voir détail>", text)
        airtable_url = url_match.group(1) if url_match else None

        frais_by_car.setdefault(voiture, []).append({
            "date": ts.strftime("%d/%m/%Y"),
            "date_ts": ts,
            "categorie": categorie,
            "objet": objet,
            "montant": None,
            "montant_fmt": "Voir Airtable",
            "airtable_record_id": airtable_record_id,
            "airtable_url": airtable_url,
        })

    for car in frais_by_car:
        frais_by_car[car].sort(key=lambda x: x["date_ts"])

    return frais_by_car
