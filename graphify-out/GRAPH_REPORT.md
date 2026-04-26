# Graph Report - .  (2026-04-25)

## Corpus Check
- Corpus is ~18,875 words - fits in a single context window. You may not need a graph.

## Summary
- 103 nodes · 176 edges · 15 communities detected
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.81)
- Token cost: 8,500 input · 2,100 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Slack Integration|Slack Integration]]
- [[_COMMUNITY_HTML Report Generator|HTML Report Generator]]
- [[_COMMUNITY_Web Frontend & Dashboard|Web Frontend & Dashboard]]
- [[_COMMUNITY_Sales Team Directory|Sales Team Directory]]
- [[_COMMUNITY_Car Inventory Reader|Car Inventory Reader]]
- [[_COMMUNITY_Cost & Inspection Data|Cost & Inspection Data]]
- [[_COMMUNITY_HTTP Server|HTTP Server]]
- [[_COMMUNITY_CT Data Fetching|CT Data Fetching]]
- [[_COMMUNITY_CT Status Classification|CT Status Classification]]
- [[_COMMUNITY_Airtable References|Airtable References]]
- [[_COMMUNITY_Reserved Cars KPIs|Reserved Cars KPIs]]
- [[_COMMUNITY_Report Entry Point|Report Entry Point]]
- [[_COMMUNITY_Reserved Cars Reader|Reserved Cars Reader]]
- [[_COMMUNITY_Cloudflare Worker|Cloudflare Worker]]
- [[_COMMUNITY_SSL Dependency|SSL Dependency]]

## God Nodes (most connected - your core abstractions)
1. `Section Offres Acceptees` - 14 edges
2. `Tracking Logistique Dashboard` - 13 edges
3. `generate_html()` - 11 edges
4. `_get_records()` - 9 edges
5. `Section Controle Technique` - 8 edges
6. `fetch_achat_vente()` - 7 edges
7. `_fetch_all_cars_index()` - 7 edges
8. `_extract_field()` - 6 edges
9. `parse_offre_acceptee()` - 6 edges
10. `parse_voiture_reservee()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Mecanicus Redirect Page` --semantically_similar_to--> `Tracking Logistique Dashboard`  [INFERRED] [semantically similar]
  public/index.html → report.html
- `slack-sdk 3.41.0` --conceptually_related_to--> `Tracking Logistique Dashboard`  [INFERRED]
  requirements.txt → report.html
- `pyairtable 3.3.0` --conceptually_related_to--> `Airtable Base appNb6Bh5KUwwmBXL`  [INFERRED]
  requirements.txt → report.html
- `requests 2.33.1` --conceptually_related_to--> `GitHub Actions Workflow generate.yml`  [INFERRED]
  requirements.txt → report.html
- `main()` --calls--> `fetch_achat_vente()`  [INFERRED]
  /Users/nico/Desktop/bilan_journalier/generate_report.py → /Users/nico/Desktop/bilan_journalier/slack_reader.py

## Hyperedges (group relationships)
- **Airtable to Python Backend to HTML Report Pipeline** — requirements_pyairtable, report_airtable_base, report_dashboard [INFERRED 0.85]
- **Dashboard Refresh Cycle via GitHub Actions** — report_trigger_refresh, report_github_workflow, report_dashboard [EXTRACTED 0.95]
- **CT Monitoring KPI Section and Status Classification** — report_kpi_alertes_ct_global, report_section_ct, report_ct_status_expire, report_ct_status_manquant, report_ct_status_bientot, report_ct_status_ok [EXTRACTED 0.92]

## Communities

### Community 0 - "Slack Integration"
Cohesion: 0.32
Nodes (13): _extract_field(), fetch_achat_vente(), fetch_logistique(), _find_all_channels(), get_channel_id(), get_messages(), _parse_amount(), parse_offre_acceptee() (+5 more)

### Community 1 - "HTML Report Generator"
Cohesion: 0.47
Nodes (9): _css(), generate_html(), _js(), _offres_commercial_filter(), _offres_type_filter(), _render_ct(), _render_frais(), _render_offres() (+1 more)

### Community 2 - "Web Frontend & Dashboard"
Cohesion: 0.2
Nodes (10): Cloudflare Tunnel Endpoint, Mecanicus Redirect Page, Tracking Logistique Dashboard, GitHub Actions Workflow generate.yml, KPI Alertes CT Reservees (2), KPI Offres Acceptees (62), Mecanicus Brand Logo CDN, triggerRefresh GitHub Actions Dispatch (+2 more)

### Community 3 - "Sales Team Directory"
Cohesion: 0.22
Nodes (9): Commercial Alexandre, Commercial Hadrien, Commercial Louis, Commercial Matthieu, Commercial Pierre, Commercial Theodore, Offre Type Achat, Offre Type Depot Vente (+1 more)

### Community 4 - "Car Inventory Reader"
Cohesion: 0.29
Nodes (8): _fetch_all_cars_index(), fetch_car_photos(), fetch_cars_status(), _match_car(), Charge uniquement les voitures avec statuts actifs (les 4 statuts autorisés)., Trouve le meilleur enregistrement Airtable pour un nom Slack.     Essaie : nom c, Retourne {nom_slack: {photo_url, fiche_url}} — utilise l'index pré-chargé si dis, Retourne {nom_slack: {statut, fiche_url}} pour une liste de noms.     Accepte un

### Community 5 - "Cost & Inspection Data"
Cohesion: 0.39
Nodes (7): enrich_frais_with_costs(), fetch_frais_airtable(), fetch_inspection_car_names(), _get_records(), Retourne l'ensemble des noms de voitures avec statut Inspection., Lit les frais directement depuis Airtable, filtrés par statut et période., search_car_by_name()

### Community 6 - "HTTP Server"
Cohesion: 0.33
Nodes (3): BaseHTTPRequestHandler, Handler, _run_refresh()

### Community 7 - "CT Data Fetching"
Cohesion: 0.38
Nodes (6): fetch_ct_data(), _fmt_date(), get_car_url(), _get_ct_value(), Extrait la première valeur d'un champ lookup CT., Retourne la liste des voitures avec alerte CT.     - Exclut les voitures de moin

### Community 8 - "CT Status Classification"
Cohesion: 0.33
Nodes (6): CT Status Bientot Expire, CT Status Expire, CT Status Manquant, CT Status OK, KPI Alertes CT Global (74), Section Controle Technique

### Community 9 - "Airtable References"
Cohesion: 0.4
Nodes (6): Airtable Base appNb6Bh5KUwwmBXL, Airtable Fiche Page pagcpxVe8Fr2ySxip, Airtable Table tblK1cZkrKh8kFysK Frais, Section Logistique Frais, toggleSection Collapsible UI, pyairtable 3.3.0

### Community 10 - "Reserved Cars KPIs"
Cohesion: 0.5
Nodes (4): Commercial Francois, Commercial Victor, KPI Voitures Reservees (17), Section Voitures Reservees

### Community 11 - "Report Entry Point"
Cohesion: 0.67
Nodes (1): main()

### Community 12 - "Reserved Cars Reader"
Cohesion: 0.67
Nodes (3): fetch_reservees_airtable(), _photo_url(), Retourne toutes les voitures avec statut Acompte 👍 depuis Airtable.

### Community 13 - "Cloudflare Worker"
Cohesion: 0.67
Nodes (1): fetch()

### Community 16 - "SSL Dependency"
Cohesion: 1.0
Nodes (1): certifi 2026.2.25

## Knowledge Gaps
- **33 isolated node(s):** `Extrait la valeur après ':emoji_code: :' dans un message Slack.`, `Format Slack:     Offre acceptée ! :gift_heart:     :racing_car: : Porsche 996 T`, `Format Slack:     Voiture réservée !     :racing_car: : Ferrari 360 Modena     :`, `Format Slack logistique :     *Nouveaux frais à programmer*     :racing_car: : P`, `Extrait la première valeur d'un champ lookup CT.` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Report Entry Point`** (3 nodes): `main()`, `generate_report.py`, `generate_report.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Cloudflare Worker`** (3 nodes): `index.js`, `fetch()`, `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SSL Dependency`** (1 nodes): `certifi 2026.2.25`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Report Entry Point` to `Slack Integration`, `HTML Report Generator`, `Car Inventory Reader`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Why does `fetch_achat_vente()` connect `Slack Integration` to `Report Entry Point`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `generate_html()` connect `HTML Report Generator` to `Report Entry Point`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Tracking Logistique Dashboard` (e.g. with `slack-sdk 3.41.0` and `Mecanicus Redirect Page`) actually correct?**
  _`Tracking Logistique Dashboard` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Extrait la valeur après ':emoji_code: :' dans un message Slack.`, `Format Slack:     Offre acceptée ! :gift_heart:     :racing_car: : Porsche 996 T`, `Format Slack:     Voiture réservée !     :racing_car: : Ferrari 360 Modena     :` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._