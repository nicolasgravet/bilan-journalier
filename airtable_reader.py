import re
import requests
from datetime import datetime, timedelta
from config import AIRTABLE_TOKEN, AIRTABLE_BASE_ID

H = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
BASE = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"

GENERAL_TABLE = "tbl2sejmIc7VpQpBx"
FRAIS_TABLE   = "tblK1cZkrKh8kFysK"

VIEW_URL    = "https://airtable.com/appNb6Bh5KUwwmBXL/pagcpxVe8Fr2ySxip/{record_id}?home=pagnonVqycMtn6zK4"
TRAVAUX_URL = "https://airtable.com/appNb6Bh5KUwwmBXL/pagcpxVe8Fr2ySxip/{record_id}?BchDq=b%3AeyJZZUhDTSI6W1sxMSwiYXF1YSJdXSwiN1BXYnAiOltbOSxbInNlbElrSmY0amZ0UThobENwIiwic2VsV0x1amlzVWRXZGcwN3IiLCJzZWx1OE9lVjBKTUJjWkdxRiIsInNlbDFVc2hTVGZXdk0xS082Il1dXX0&home=pagnonVqycMtn6zK4"

CT_STATUTS = [
    "A envoyer en travaux ",
    "En travaux 🚧",
    "In stock 🚗",
    "Acompte 👍",
]
ACOMPTE_STATUT = "Acompte 👍"

# Statuts valides pour la logistique (hors Inspection)
LOGISTIQUE_STATUTS_EXCLUS = {"Inspection 🕵️"}


def _get_records(table, params):
    if not AIRTABLE_TOKEN:
        return []
    records, offset = [], None
    while True:
        p = dict(params)
        if offset:
            p["offset"] = offset
        try:
            r = requests.get(f"{BASE}/{table}", headers=H, params=p, timeout=15)
            r.raise_for_status()
            d = r.json()
            records.extend(d.get("records", []))
            offset = d.get("offset")
            if not offset:
                break
        except Exception as e:
            print(f"Airtable error ({table}): {e}")
            break
    return records


def _get_ct_value(field_data):
    """Extrait la première valeur d'un champ lookup CT."""
    if not field_data:
        return None
    if isinstance(field_data, list):
        for v in field_data:
            if v is None:
                continue
            if isinstance(v, dict):
                if v.get("error"):
                    return None
                return v.get("name")
            return v
        return None
    if isinstance(field_data, dict):
        linked = field_data.get("valuesByLinkedRecordId", {})
        for vals in linked.values():
            if vals:
                v = vals[0]
                if isinstance(v, dict):
                    if v.get("error"):
                        return None
                    return v.get("name")
                return v
    return None


def _fmt_date(d):
    if not d or isinstance(d, dict):
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(d)


def _photo_url(fields):
    photos = fields.get("Photo", [])
    if photos and isinstance(photos, list) and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


def fetch_ct_data():
    """
    Retourne la liste des voitures avec alerte CT.
    - Exclut les voitures de moins de 4 ans (pas de CT obligatoire)
    - Acompte avec CT OK : inclus mais marqués 'acompte-ok' (masqués dans vue Tous)
    - Acompte sans CT : inclus et visibles partout
    - Autres statuts : inclus selon criticité CT
    Triées par criticité : Expiré(0) > Manquant(1) > Bientôt(2) > OK(3)
    """
    if not AIRTABLE_TOKEN:
        return []

    formula_parts = [f'{{Statut}} = "{s}"' for s in CT_STATUTS]
    formula = "OR(" + ",".join(formula_parts) + ")"

    records = _get_records(GENERAL_TABLE, {
        "filterByFormula": formula,
        "fields[]": [
            "Voiture", "Statut",
            "Date CT (from CT)", "Date échéance CT (from CT)", "Status (from CT)",
            "Record ID", "Date PMC (from CG Infos)",
        ],
        "maxRecords": 500,
    })

    cars = []
    today = datetime.now().date()
    four_years_ago = today.replace(year=today.year - 4)

    for rec in records:
        f = rec.get("fields", {})
        voiture = f.get("Voiture", "—")
        statut_raw = f.get("Statut", {})
        statut = statut_raw.get("name", "") if isinstance(statut_raw, dict) else str(statut_raw)
        record_id = rec["id"]

        # Exclure les voitures de moins de 4 ans
        pmc_raw = f.get("Date PMC (from CG Infos)", [])
        if isinstance(pmc_raw, list) and pmc_raw and pmc_raw[0]:
            try:
                date_pmc = datetime.strptime(pmc_raw[0], "%Y-%m-%d").date()
                if date_pmc > four_years_ago:
                    continue  # Moins de 4 ans, pas de CT requis
            except Exception:
                pass

        date_ct  = _get_ct_value(f.get("Date CT (from CT)"))
        date_ech = _get_ct_value(f.get("Date échéance CT (from CT)"))
        ct_status = _get_ct_value(f.get("Status (from CT)"))

        has_ct = bool(date_ct or date_ech or ct_status)
        is_acompte = (statut == ACOMPTE_STATUT)

        # Criticité
        if not has_ct:
            criticite = 1
        elif ct_status and "expiré" in ct_status.lower() and "bientôt" not in ct_status.lower():
            criticite = 0
        elif ct_status and "bientôt" in ct_status.lower():
            criticite = 2
        else:
            criticite = 3

        # Jours restants
        jours_restants = None
        if date_ech and isinstance(date_ech, str):
            try:
                ech = datetime.strptime(date_ech, "%Y-%m-%d").date()
                jours_restants = (ech - today).days
            except Exception:
                pass

        # Type pour le filtre JS
        if is_acompte and has_ct:
            ct_filter_type = "acompte-ok"   # Réservée avec CT OK → masqué par défaut
        elif is_acompte:
            ct_filter_type = "acompte"       # Réservée sans CT → toujours visible
        else:
            ct_filter_type = "other"

        cars.append({
            "voiture": voiture,
            "statut": statut,
            "record_id": record_id,
            "date_ct": _fmt_date(date_ct),
            "date_echeance": _fmt_date(date_ech),
            "ct_status": ct_status or ("Manquant ❌" if not has_ct else "—"),
            "jours_restants": jours_restants,
            "criticite": criticite,
            "fiche_url": VIEW_URL.format(record_id=record_id),
            "ct_filter_type": ct_filter_type,
        })

    cars.sort(key=lambda x: x["criticite"])
    return cars


def fetch_reservees_airtable():
    """Retourne toutes les voitures avec statut Acompte 👍 depuis Airtable."""
    if not AIRTABLE_TOKEN:
        return []
    records = _get_records(GENERAL_TABLE, {
        "filterByFormula": f'{{Statut}} = "{ACOMPTE_STATUT}"',
        "fields[]": ["Voiture", "Photo", "Prix vente", "Marge (€)", "Record ID", "Acheteur meca", "N° bon commande (from Bon de commande)"],
        "maxRecords": 200,
    })
    result = []
    for rec in records:
        f = rec.get("fields", {})
        prix = f.get("Prix vente")
        marge = f.get("Marge (€)")
        prix_fmt = f"{float(prix):,.0f} €".replace(",", "\u202f") if prix else "—"
        marge_fmt = f"{float(marge):,.0f} €".replace(",", "\u202f") if marge else "—"
        marge_val = float(marge) if marge else 0
        created_raw = rec.get("createdTime", "")
        try:
            created_ts = int(datetime.fromisoformat(created_raw.replace("Z", "+00:00")).timestamp()) if created_raw else 0
        except Exception:
            created_ts = 0
        acheteurs_raw = f.get("Acheteur meca", [])
        commerciaux = [a.get("name", "").split()[0].capitalize() for a in acheteurs_raw if a.get("name")]
        is_francois = (len(acheteurs_raw) == 1 and any("françois" in a.get("name", "").lower() for a in acheteurs_raw))
        bc_raw = f.get("N° bon commande (from Bon de commande)", "")
        if isinstance(bc_raw, list):
            bc_raw = bc_raw[0] if bc_raw else ""
        bc_str = str(bc_raw).strip() if bc_raw else ""
        bc_digits = re.sub(r"[^0-9]", "", bc_str)
        bc_num = int(bc_digits) if bc_digits else 0
        result.append({
            "voiture": f.get("Voiture", "—"),
            "prix_fmt": prix_fmt,
            "marge_fmt": marge_fmt,
            "marge_val": marge_val,
            "created_ts": created_ts,
            "bc_num": bc_num,
            "bc_str": bc_str,
            "photo_url": _photo_url(f),
            "fiche_url": VIEW_URL.format(record_id=rec["id"]),
            "travaux_url": TRAVAUX_URL.format(record_id=rec["id"]),
            "commerciaux": commerciaux,
            "is_francois": is_francois,
        })
    result.sort(key=lambda x: x["voiture"])
    return result


def fetch_inspection_car_names():
    """Retourne l'ensemble des noms de voitures avec statut Inspection."""
    if not AIRTABLE_TOKEN:
        return set()
    records = _get_records(GENERAL_TABLE, {
        "filterByFormula": '{Statut} = "Inspection 🕵️"',
        "fields[]": ["Voiture"],
        "maxRecords": 200,
    })
    return {rec.get("fields", {}).get("Voiture", "") for rec in records}


def _fetch_all_cars_index():
    """
    Charge uniquement les voitures avec statuts actifs (les 4 statuts autorisés).
    Retourne une liste de dicts {rec_id, voiture_lower, voiture, photo_url, statut, fiche_url}.
    """
    statuts = list(LOGISTIQUE_STATUTS_AUTORISES)
    formula = "OR(" + ",".join(f'{{Statut}} = "{s}"' for s in statuts) + ")"
    records = _get_records(GENERAL_TABLE, {
        "filterByFormula": formula,
        "fields[]": ["Voiture", "Photo", "Statut", "Acheteur meca"],
        "maxRecords": 2000,
    })
    index = []
    for rec in records:
        f = rec.get("fields", {})
        voiture = f.get("Voiture", "")
        statut_raw = f.get("Statut", {})
        statut = statut_raw.get("name", "") if isinstance(statut_raw, dict) else str(statut_raw)
        acheteur_meca_raw = f.get("Acheteur meca", [])
        acheteur_meca = acheteur_meca_raw[0].get("name", "") if acheteur_meca_raw else ""
        is_francois = (len(acheteur_meca_raw) == 1 and "françois" in acheteur_meca.lower())
        index.append({
            "rec_id": rec["id"],
            "voiture_lower": voiture.lower(),
            "voiture": voiture,
            "photo_url": _photo_url(f),
            "statut": statut,
            "fiche_url": VIEW_URL.format(record_id=rec["id"]),
            "acheteur_meca": acheteur_meca,
            "is_francois": is_francois,
        })
    return index


def _match_car(name, index):
    """
    Trouve le meilleur enregistrement Airtable pour un nom Slack.
    Essaie : nom complet → 4 premiers mots → 3 premiers mots.
    """
    name_clean = name.strip().lower()
    words = name_clean.split()

    candidates = [name_clean] + [
        " ".join(words[:n]) for n in (4, 3) if len(words) >= n and " ".join(words[:n]) != name_clean
    ]

    for candidate in candidates:
        for row in index:
            if candidate in row["voiture_lower"]:
                return row
    return None


def fetch_car_photos(car_names, index=None):
    """
    Retourne {nom_slack: {photo_url, fiche_url}} — utilise l'index pré-chargé si disponible.
    """
    if not AIRTABLE_TOKEN or not car_names:
        return {}
    if index is None:
        index = _fetch_all_cars_index()
    result = {}
    for name in car_names:
        row = _match_car(name, index)
        if row:
            result[name] = {"photo_url": row["photo_url"], "fiche_url": row["fiche_url"], "statut": row["statut"]}
    return result


def fetch_cars_status(car_names, index=None):
    """
    Retourne {nom_slack: {statut, fiche_url}} pour une liste de noms.
    Accepte un index pré-chargé pour éviter un appel Airtable supplémentaire.
    """
    if not AIRTABLE_TOKEN or not car_names:
        return {}
    if index is None:
        index = _fetch_all_cars_index()
    result = {}
    for name in car_names:
        row = _match_car(name, index)
        if row:
            result[name] = {"statut": row["statut"], "fiche_url": row["fiche_url"], "acheteur_meca": row.get("acheteur_meca", "")}
    return result


LOGISTIQUE_STATUTS_AUTORISES = {
    "A envoyer en travaux ",
    "En travaux 🚧",
    "In stock 🚗",
    "Acompte 👍",
}


def fetch_frais_airtable(cars_index=None, days_back=30):
    """Lit les frais directement depuis Airtable, filtrés par statut et période."""
    if not AIRTABLE_TOKEN:
        return {}
    cutoff_dt = datetime.now() - timedelta(days=days_back)
    records = _get_records(FRAIS_TABLE, {
        "fields[]": ["Voiture", "Cout HT", "Cout TTC", "Frais ? ", "Catégorie", "Lien facture", "Statut travaux"],
        "sort[0][field]": "Created time",
        "sort[0][direction]": "desc",
        "maxRecords": 2000,
    })
    # Index rec_id → car info pour correspondance directe
    rec_id_to_car = {row["rec_id"]: row for row in (cars_index or [])}

    frais_by_car = {}
    for rec in records:
        created_raw = rec.get("createdTime", "")
        try:
            date_ts = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            date_ts = datetime.now()
        # Filtre côté Python — on s'arrête dès qu'on dépasse la période
        if date_ts < cutoff_dt:
            break
        f = rec.get("fields", {})
        voiture_links = f.get("Voiture", [])
        if not voiture_links:
            continue
        # Récupérer l'ID du record voiture lié
        v = voiture_links[0]
        voiture_rec_id = v if isinstance(v, str) else v.get("id", "")
        # Chercher le nom dans l'index par rec_id, sinon fallback sur le nom direct
        car_info = rec_id_to_car.get(voiture_rec_id)
        if car_info:
            voiture_name = car_info["voiture"]
            # Filtrer par statut autorisé directement ici
            if car_info["statut"] not in LOGISTIQUE_STATUTS_AUTORISES:
                continue
        else:
            # Si pas dans l'index, on ne peut pas vérifier le statut — on ignore
            continue
        # Exclure les frais avec statut travaux "Terminé"
        statut_travaux_raw = f.get("Statut travaux")
        statut_travaux = statut_travaux_raw.get("name", "") if isinstance(statut_travaux_raw, dict) else str(statut_travaux_raw or "")
        if statut_travaux == "Terminé":
            continue

        objet = f.get("Frais ? ") or "—"
        cat_raw = f.get("Catégorie")
        categorie = cat_raw.get("name", "—") if isinstance(cat_raw, dict) else "—"
        airtable_url = f.get("Lien facture") or None
        cout_ttc = f.get("Cout TTC")
        cout_ht = f.get("Cout HT")
        montant = cout_ttc or cout_ht
        try:
            montant_val = float(montant) if montant is not None else None
            montant_fmt = f"{montant_val:,.2f} €".replace(",", "\u202f") if montant_val is not None else "—"
        except (ValueError, TypeError):
            montant_val = None
            montant_fmt = "—"
        frais_by_car.setdefault(voiture_name, []).append({
            "date": date_ts.strftime("%d/%m/%Y"),
            "date_ts": date_ts,
            "categorie": categorie,
            "objet": objet,
            "montant": montant_val,
            "montant_fmt": montant_fmt,
            "airtable_record_id": rec["id"],
            "airtable_url": airtable_url,
        })
    for car in frais_by_car:
        frais_by_car[car].sort(key=lambda x: x["date_ts"])
    return frais_by_car


def enrich_frais_with_costs(frais_by_car):
    if not AIRTABLE_TOKEN:
        return frais_by_car
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    records = _get_records(FRAIS_TABLE, {
        "filterByFormula": f"IS_AFTER({{Created time}}, '{cutoff}')",
        "fields[]": ["Name", "Created time", "Voiture", "Cout HT", "Cout TTC"],
        "maxRecords": 500,
    })
    cost_by_id = {}
    for rec in records:
        f = rec.get("fields", {})
        cost_by_id[rec["id"]] = {
            "cout_ht": f.get("Cout HT"),
            "cout_ttc": f.get("Cout TTC"),
        }
    for car, frais_list in frais_by_car.items():
        for frais in frais_list:
            rec_id = frais.get("airtable_record_id")
            if rec_id and rec_id in cost_by_id:
                cost = cost_by_id[rec_id]
                ttc = cost.get("cout_ttc") or cost.get("cout_ht")
                if ttc is not None:
                    try:
                        frais["montant"] = float(ttc)
                        frais["montant_fmt"] = f"{float(ttc):,.2f} €".replace(",", "\u202f")
                    except (ValueError, TypeError):
                        pass
    return frais_by_car


def search_car_by_name(search_term):
    if not AIRTABLE_TOKEN:
        return None, {}
    search_lower = search_term.lower().strip()[:50]
    records = _get_records(GENERAL_TABLE, {
        "filterByFormula": f'SEARCH(LOWER("{search_lower}"), LOWER({{Voiture}}))',
        "maxRecords": 5,
        "fields[]": ["Voiture"],
    })
    if records:
        rec = records[0]
        return rec["id"], rec.get("fields", {})
    words = search_lower.split()
    if len(words) >= 2:
        formula = f'AND(SEARCH(LOWER("{words[0]}"),LOWER({{Marque}})),SEARCH(LOWER("{words[1]}"),LOWER({{Modèle}})))'
        records = _get_records(GENERAL_TABLE, {
            "filterByFormula": formula,
            "maxRecords": 5,
            "fields[]": ["Voiture"],
        })
        if records:
            rec = records[0]
            return rec["id"], rec.get("fields", {})
    return None, {}


def get_car_url(record_id):
    return VIEW_URL.format(record_id=record_id) if record_id else None
