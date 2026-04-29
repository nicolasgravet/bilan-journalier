#!/usr/bin/env python3
"""Script principal — génère le bilan journalier HTML."""

import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent))

from config import AIRTABLE_TOKEN, GCAL_ICS_URL, REPORT_PATH
from calendar_reader import fetch_livraisons
from airtable_reader import (
    fetch_ct_data,
    fetch_reservees_airtable,
    fetch_car_photos,
    fetch_frais_airtable,
    fetch_prestataires,
    _fetch_all_cars_index,
    build_plate_index,
)
from html_generator import generate_html


def main():
    t0 = time.time()

    reservees    = []
    ct_data      = []
    car_photos   = {}
    frais_by_car = {}
    prestataires = []
    livraisons   = []
    francois_cars = set()

    if AIRTABLE_TOKEN:
        # ── Chargement parallèle : index + réservées + CT + prestataires + calendrier ──
        print("⚡ Chargement parallèle : Airtable index / réservées / CT / prestataires / livraisons...")
        with ThreadPoolExecutor(max_workers=6) as ex:
            f_index     = ex.submit(_fetch_all_cars_index)
            f_reservees = ex.submit(fetch_reservees_airtable)
            f_ct        = ex.submit(fetch_ct_data)
            f_prest     = ex.submit(fetch_prestataires)
            f_livr      = ex.submit(fetch_livraisons, GCAL_ICS_URL, 14)

            # Dès que l'index est disponible, lancer les frais (dépendent de l'index)
            cars_index   = f_index.result()
            f_frais      = ex.submit(fetch_frais_airtable, cars_index, 30)

            reservees    = f_reservees.result()
            ct_data      = f_ct.result()
            frais_by_car = f_frais.result()
            prestataires = f_prest.result()
            livraisons   = f_livr.result()

        print(f"  ✓ {len(cars_index)} véhicules index, {len(reservees)} réservées, "
              f"{len(ct_data)} CT, {sum(len(v) for v in frais_by_car.values())} frais, "
              f"{len(prestataires)} prestataires, {len(livraisons)} livraisons")

        # Photos (lookup instantané sur l'index)
        car_photos = fetch_car_photos(set(frais_by_car.keys()), index=cars_index)
        print(f"  ✓ {sum(1 for v in car_photos.values() if v.get('photo_url'))} photos")

        # Enrichir les livraisons avec la fiche Airtable via la plaque
        if livraisons:
            plate_idx = build_plate_index(cars_index)
            matched = sum(
                1 for ev in livraisons
                if ev.get("plate", "").upper() in plate_idx
                and not ev.update({"airtable_url": plate_idx[ev["plate"].upper()]})
            )
            print(f"  ✓ {matched}/{len(livraisons)} livraisons matchées par plaque")

        # Voitures dont François Prisset est le seul acheteur
        francois_cars = {row["voiture"] for row in cars_index if row.get("is_francois")}
        if francois_cars:
            print(f"  🖕 {len(francois_cars)} voiture(s) de François détectée(s)")

    else:
        print("Token Airtable absent — données Airtable désactivées")

    print("Génération HTML...")
    html = generate_html([], reservees, frais_by_car, ct_data, car_photos,
                         francois_cars=francois_cars, prestataires=prestataires,
                         livraisons=livraisons)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Rapport généré en {time.time()-t0:.1f}s : {REPORT_PATH}")


if __name__ == "__main__":
    main()
