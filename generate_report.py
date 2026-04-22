#!/usr/bin/env python3
"""Script principal — génère le bilan journalier HTML."""

import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent))

from config import AIRTABLE_TOKEN, REPORT_PATH
from slack_reader import fetch_achat_vente
from airtable_reader import (
    fetch_ct_data,
    fetch_reservees_airtable,
    fetch_car_photos,
    fetch_cars_status,
    fetch_frais_airtable,
    _fetch_all_cars_index,
)

# Statuts autorisés pour afficher une offre acceptée
OFFRES_STATUTS_AUTORISES = {
    "Acompte 👍",
    "In stock 🚗",
    "En travaux 🚧",
    "A envoyer en travaux ",
}
from html_generator import generate_html


def main():
    t0 = time.time()

    reservees = []
    ct_data = []
    car_photos = {}
    frais_by_car = {}

    if AIRTABLE_TOKEN:
        # ── Round 1 : tous les appels indépendants en parallèle ──────────────
        # Slack + index + réservées + CT démarrent simultanément.
        # Dès que l'index est prêt, on lance les frais (qui en dépendent).
        print("⚡ Chargement parallèle : Slack / Airtable index / réservées / CT...")
        with ThreadPoolExecutor(max_workers=6) as ex:
            f_slack     = ex.submit(fetch_achat_vente, 90)
            f_index     = ex.submit(_fetch_all_cars_index)
            f_reservees = ex.submit(fetch_reservees_airtable)
            f_ct        = ex.submit(fetch_ct_data)

            # Dès que l'index est disponible, lancer les frais sans attendre Slack
            cars_index = f_index.result()
            f_frais    = ex.submit(fetch_frais_airtable, cars_index, 30)

            general_msgs, offres, _ = f_slack.result()
            reservees  = f_reservees.result()
            ct_data    = f_ct.result()
            frais_by_car = f_frais.result()

        print(f"  ✓ {len(offres)} offres Slack, {len(cars_index)} véhicules index, "
              f"{len(reservees)} réservées, {len(ct_data)} CT, "
              f"{sum(len(v) for v in frais_by_car.values())} frais")

        # ── Round 2 : filtrage offres (rapide, utilise l'index déjà chargé) ──
        car_names_offres = {o.get("voiture", "") for o in offres if o.get("voiture")}
        cars_status = fetch_cars_status(car_names_offres, index=cars_index)
        before = len(offres)
        offres_filtrees = []
        for o in offres:
            info = cars_status.get(o.get("voiture", ""), {})
            if info.get("statut", "") in OFFRES_STATUTS_AUTORISES:
                o["fiche_url"] = info.get("fiche_url")
                if info.get("acheteur_meca"):
                    o["acheteur"] = info["acheteur_meca"]
                offres_filtrees.append(o)
        offres = offres_filtrees
        print(f"  ✓ {len(offres)} offres retenues sur {before}")

        # ── Round 3 : photos (lookup sur index, instantané) ──────────────────
        car_photos = fetch_car_photos(set(frais_by_car.keys()), index=cars_index)
        print(f"  ✓ {sum(1 for v in car_photos.values() if v.get('photo_url'))} photos")

    else:
        print("Token Airtable absent — données Airtable désactivées")
        general_msgs, offres, _ = fetch_achat_vente(days_back=90)

    print("Génération HTML...")
    html = generate_html(offres, reservees, frais_by_car, ct_data, car_photos)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Rapport généré en {time.time()-t0:.1f}s : {REPORT_PATH}")


if __name__ == "__main__":
    main()
