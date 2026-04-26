import json as _json
from datetime import datetime
from config import PRESTATAIRES_TOKEN, PRESTATAIRES_BASE_ID, PRESTATAIRES_TABLE_ID

JOURS_FR = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
MOIS_FR  = ["janvier","février","mars","avril","mai","juin",
             "juillet","août","septembre","octobre","novembre","décembre"]

def generate_html(offres, reservees, frais_by_car, ct_data=None, car_photos=None, francois_cars=None, prestataires=None):
    now = datetime.utcnow()
    gen_ts = int(now.timestamp())  # timestamp UTC → JS le convertit en heure locale
    date_str = f"{JOURS_FR[now.weekday()]} {now.day} {MOIS_FR[now.month-1]} {now.year}"
    time_str = now.strftime("%H:%M")
    ct_data = ct_data or []
    car_photos = car_photos or {}
    francois_cars = francois_cars or set()
    prestataires = prestataires or []

    # CT global = toutes les voitures sans CT valide (expiré + manquant + bientôt), réservées ou non
    ct_alert_count = sum(1 for c in ct_data if c.get("criticite", 3) != 3)
    # CT réservées = voitures en Acompte avec CT non-OK (manquant, expiré, bientôt)
    ct_reservees_count = sum(1 for c in ct_data if c.get("ct_filter_type") == "acompte")
    # Données marge pour JS (voitures réservées Airtable)
    marges_data = _json.dumps([
        {"marge": r.get("marge_val", 0), "ts": r.get("created_ts", 0)}
        for r in reservees
    ])

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tracking Logistique — {date_str}</title>
  <style>{_css()}</style>
</head>
<body>
<div class="app">

  <!-- Header -->
  <header class="glass-card header">
    <img class="header-car-bg" src="https://cdn.prod.website-files.com/637dd83cd93444d7a965962c/69b3fc8216369c578418acbc_DSC09651.jpg" alt="" draggable="false">
    <div class="header-content">
      <div>
        <img src="https://cdn.prod.website-files.com/637b81e6d60031889cd403dc/640df2434b3f34dca527d1bb_logo_desktop_black_center.svg"
             alt="Mecanicus" class="mecanicus-logo">
      </div>
      <div class="header-meta">
        <div class="time-badge" id="live-clock"></div>
        <button class="refresh-btn" onclick="triggerRefresh(this)">↺ Actualiser</button>
        <div class="refresh-note" id="refresh-status"></div>
      </div>
      <script>
      var JOURS = ['Dimanche','Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi'];
      var MOIS  = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
      (function() {{
        // Horloge live
        function updateClock() {{
          var now = new Date();
          var h = String(now.getHours()).padStart(2,'0');
          var m = String(now.getMinutes()).padStart(2,'0');
          document.getElementById('live-clock').textContent = h + ':' + m;
        }}
        updateClock();
        setInterval(updateClock, 1000);
        // Timestamp de génération converti en heure locale
        var gen = new Date({gen_ts} * 1000);
        var genH = String(gen.getHours()).padStart(2,'0');
        var genM = String(gen.getMinutes()).padStart(2,'0');
        var genLabel = 'Mis à jour le ' + JOURS[gen.getDay()] + ' ' + gen.getDate() + ' ' + MOIS[gen.getMonth()] + ' ' + gen.getFullYear() + ' à ' + genH + ':' + genM;
        document.getElementById('refresh-status').textContent = genLabel;
      }})();
      function triggerRefresh(btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ En cours…';
        document.getElementById('refresh-status').textContent = 'Génération en cours…';
        var currentTs = {gen_ts};
        fetch('https://mecanicus-refresh.nicolas-0ce.workers.dev', {{method:'POST'}})
        .then(r => {{
          if (r.ok) {{
            var dots = 0;
            var pollInterval = setInterval(function() {{
              dots = (dots % 3) + 1;
              document.getElementById('refresh-status').textContent = 'Mise à jour en cours' + '.'.repeat(dots);
              fetch(location.href + '?_=' + Date.now(), {{cache:'no-store'}})
              .then(r => r.text())
              .then(html => {{
                var m = html.match(/new Date\((\d+) \* 1000\)/);
                if (m && parseInt(m[1]) > currentTs) {{
                  clearInterval(pollInterval);
                  window.location.href = location.pathname + '?t=' + Date.now();
                }}
              }}).catch(() => {{}});
            }}, 3000);
            setTimeout(function() {{ clearInterval(pollInterval); window.location.href = location.pathname + '?t=' + Date.now(); }}, 60000);
          }} else {{
            btn.disabled = false;
            btn.textContent = '↺ Actualiser';
            document.getElementById('refresh-status').textContent = 'Erreur — réessaie dans quelques secondes';
          }}
        }}).catch(() => {{
          btn.disabled = false;
          btn.textContent = '↺ Actualiser';
          document.getElementById('refresh-status').textContent = 'Erreur réseau';
        }});
      }}
      </script>
    </div>
  </header>

  <!-- KPI -->
  <div class="kpi-row">
    <div class="glass-card kpi">
      <div class="kpi-icon-wrap kpi-blue">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2FAEE0" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      </div>
      <div class="kpi-body">
        <div class="kpi-value">{len(reservees)}</div>
        <div class="kpi-label">Voitures réservées</div>
      </div>
    </div>
    <div class="glass-card kpi kpi-clickable" onclick="jumpToCT()" title="Voir les alertes CT">
      <div class="kpi-icon-wrap kpi-orange">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="kpi-body">
        <div class="kpi-value">{ct_alert_count}</div>
        <div class="kpi-label">Alertes CT — Global</div>
      </div>
      <span class="kpi-arrow">→</span>
    </div>
    <div class="glass-card kpi">
      <div class="kpi-icon-wrap kpi-red">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      </div>
      <div class="kpi-body">
        <div class="kpi-value">{ct_reservees_count}</div>
        <div class="kpi-label">Alertes CT — Réservées</div>
      </div>
    </div>
  </div>

  <div class="grid">

    <!-- Logistique -->
    <section id="section-frais" class="glass-card section col-span-3">
      <div class="section-header collapsible-header" onclick="toggleSection('frais')">
        <span class="section-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></span>
        <h2>Logistique — Frais</h2>
        <span class="count-badge" id="frais-count">{sum(len(v) for v in frais_by_car.values())}</span>
        <div class="header-filters" onclick="event.stopPropagation()">
          <div class="filter-bar" data-target="frais">
            <button class="filter-btn active" data-days="0">Tout (30j)</button>
          </div>
          <div class="filter-bar frais-statut-filter">
            <button class="filter-btn active" data-frais-statut="tous">Tous</button>
            <button class="filter-btn" data-frais-statut="reservees">Réservées</button>
          </div>
        </div>
        <button class="collapse-btn" id="collapse-frais"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>
      </div>
      <div class="section-body" id="body-frais">
        <div class="section-search-wrap" onclick="event.stopPropagation()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#adb5c2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" class="section-search" id="search-frais" placeholder="Rechercher une voiture…" oninput="filterBySearch('frais', this.value)" autocomplete="off">
          <button class="search-clear-btn" onclick="clearSearch('frais')">✕</button>
        </div>
        {_render_frais(frais_by_car, car_photos, francois_cars)}
      </div>
    </section>

    <!-- Contrôle Technique -->
    <section class="glass-card section col-span-3" id="section-ct">
      <div class="section-header collapsible-header" onclick="toggleSection('ct')">
        <span class="section-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
        <h2>Contrôle Technique</h2>
        <span class="count-badge" id="ct-count">{ct_alert_count}</span>
        <div class="header-filters" onclick="event.stopPropagation()">
          <div class="filter-bar ct-filter">
            <button class="filter-btn active" data-ct="tous">Tous</button>
            <button class="filter-btn" data-ct="reservees">Réservées (Acompte)</button>
          </div>
        </div>
        <button class="collapse-btn" id="collapse-ct"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>
      </div>
      <div class="section-body" id="body-ct">
        <div class="section-search-wrap" onclick="event.stopPropagation()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#adb5c2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" class="section-search" id="search-ct" placeholder="Rechercher une voiture…" oninput="filterBySearch('ct', this.value)" autocomplete="off">
          <button class="search-clear-btn" onclick="clearSearch('ct')">✕</button>
        </div>
        <div class="module-sub-filters">
          <div class="filter-bar ct-status-filter">
            <button class="filter-btn active" data-ct-status="tous">Tous statuts</button>
            <button class="filter-btn" data-ct-status="0">Expiré</button>
            <button class="filter-btn" data-ct-status="1">Manquant</button>
            <button class="filter-btn" data-ct-status="2">Bientôt</button>
            <button class="filter-btn" data-ct-status="3">OK</button>
          </div>
        </div>
        {_render_ct(ct_data, francois_cars)}
      </div>
    </section>

    <!-- Voitures réservées -->
    <section class="glass-card section col-span-3" id="section-reservees">
      <div class="section-header collapsible-header" onclick="toggleSection('reservees')">
        <span class="section-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
        <h2>Voitures Réservées</h2>
        <span class="count-badge">{len(reservees)}</span>
        <div class="header-filters" onclick="event.stopPropagation()">
          <button class="sort-toggle-btn" id="sort-reservees" onclick="toggleSortReservees(this)">↓ Plus récent</button>
        </div>
        <button class="collapse-btn" id="collapse-reservees"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>
      </div>
      <div class="section-body" id="body-reservees">
        <div class="section-search-wrap" onclick="event.stopPropagation()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#adb5c2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" class="section-search" id="search-reservees" placeholder="Rechercher une voiture…" oninput="filterBySearch('reservees', this.value)" autocomplete="off">
          <button class="search-clear-btn" onclick="clearSearch('reservees')">✕</button>
        </div>
        {_render_reservees(reservees, francois_cars, ct_data)}
      </div>
    </section>

  </div>

  <!-- Prestataires -->
  <section class="glass-card section prest-section" id="section-prest" style="margin-top:18px">
    <div class="section-header collapsible-header" onclick="toggleSection('prest')">
      <span class="section-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></span>
      <h2>Prestataires</h2>
      <span class="count-badge" id="prest-count">{len(prestataires)}</span>
      <div class="header-filters" onclick="event.stopPropagation()">
        <button class="prest-add-btn" onclick="openPrestAddModal()">+ Ajouter</button>
      </div>
      <button class="collapse-btn" id="collapse-prest"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>
    </div>
    <div class="section-body" id="body-prest">
      <div class="prest-controls" onclick="event.stopPropagation()">
        <div class="section-search-wrap prest-search-wrap">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#adb5c2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" class="section-search" id="search-prest" placeholder="Rechercher un prestataire, ville, contact…" oninput="applyPrestFilters()" autocomplete="off">
          <button class="search-clear-btn" onclick="clearPrestSearch()">✕</button>
        </div>
        <div class="prest-filter-row">
          <div class="filter-bar" id="prest-type-filters">
            <button class="filter-btn active" data-prest-type="tous" onclick="setPrestTypeFilter(this)">Tous</button>
          </div>
          <div class="filter-bar" id="prest-marque-filters">
            <button class="filter-btn active" data-prest-marque="tous" onclick="setPrestMarqueFilter(this)">Toutes marques</button>
          </div>
        </div>
      </div>
      <div id="prest-content">
        {_render_prestataires(prestataires)}
      </div>
    </div>
  </section>

  <footer class="footer">
    Généré le {date_str} à {time_str} · Données Slack & Airtable · Rafraîchissement quotidien à 19h
  </footer>
</div>
<div id="res-modal" class="res-modal-overlay" onclick="closeResModal(event)">
  <div class="res-modal-card">
    <button class="res-modal-close" onclick="closeResModal()">✕</button>
    <img id="res-modal-photo" class="res-modal-photo" src="" alt="">
    <div class="res-modal-body">
      <div class="res-modal-header">
        <span id="res-modal-name" class="res-modal-name"></span>
        <span id="res-modal-bc" class="bc-badge res-modal-bc"></span>
      </div>
      <div class="res-modal-amounts">
        <div class="res-modal-amount-block">
          <span class="res-modal-label">Prix</span>
          <span id="res-modal-prix" class="res-modal-value-prix"></span>
        </div>
        <div class="res-modal-amount-block">
          <span class="res-modal-label">Marge</span>
          <span id="res-modal-marge" class="res-modal-value-marge"></span>
        </div>
      </div>
      <span id="res-modal-ct" class="ct-res-badge" style="display:none"></span>
      <div id="res-modal-commerciaux" class="res-modal-commerciaux"></div>
      <a id="res-modal-fiche" class="fiche-btn res-modal-fiche-btn" href="#" target="_blank" onclick="event.stopPropagation()">Accéder à la fiche →</a>
    </div>
  </div>
</div>
<div id="prest-add-modal" class="prest-modal-overlay" onclick="closePrestAddModal(event)">
  <div class="prest-modal-card">
    <div class="prest-modal-header">
      <h3>Ajouter un prestataire</h3>
      <button class="prest-modal-close" onclick="closePrestAddModal()">✕</button>
    </div>
    <form id="prest-add-form" onsubmit="submitNewPrestataire(event)">
      <div class="pf-row">
        <label class="pf-label">Nom du garage *</label>
        <input class="pf-input" id="pf-nom" type="text" placeholder="Ex : Garage Dupont" required>
      </div>
      <div class="pf-row pf-row-2">
        <div>
          <label class="pf-label">Spécialité</label>
          <select class="pf-input" id="pf-type">
            <option value="">— Choisir —</option>
            <option>Mécanique</option>
            <option>Carrosserie</option>
            <option>Pièces détachées</option>
            <option>Débosselage</option>
            <option>Sellerie</option>
            <option>Detailling</option>
            <option>Transporteur</option>
          </select>
        </div>
        <div>
          <label class="pf-label">Marque(s)</label>
          <div class="pf-marques-wrap" id="pf-marques">
            <label class="pf-marque-check"><input type="checkbox" value="Généraliste"> Généraliste</label>
            <label class="pf-marque-check"><input type="checkbox" value="Porsche"> Porsche</label>
            <label class="pf-marque-check"><input type="checkbox" value="Ferrari"> Ferrari</label>
            <label class="pf-marque-check"><input type="checkbox" value="BMW"> BMW</label>
            <label class="pf-marque-check"><input type="checkbox" value="Mercedes-Benz"> Mercedes-Benz</label>
            <label class="pf-marque-check"><input type="checkbox" value="Aston Martin"> Aston Martin</label>
            <label class="pf-marque-check"><input type="checkbox" value="Jaguar"> Jaguar</label>
            <label class="pf-marque-check"><input type="checkbox" value="Austin Healey"> Austin Healey</label>
          </div>
        </div>
      </div>
      <div class="pf-row">
        <label class="pf-label">Note</label>
        <div class="pf-stars-input" id="pf-stars">
          <span class="pf-star" data-v="1">★</span>
          <span class="pf-star" data-v="2">★</span>
          <span class="pf-star" data-v="3">★</span>
          <span class="pf-star" data-v="4">★</span>
          <span class="pf-star" data-v="5">★</span>
        </div>
        <input type="hidden" id="pf-rating" value="0">
      </div>
      <div class="pf-row pf-row-2">
        <div>
          <label class="pf-label">Téléphone</label>
          <input class="pf-input" id="pf-tel" type="tel" placeholder="06 12 34 56 78">
        </div>
        <div>
          <label class="pf-label">Email</label>
          <input class="pf-input" id="pf-email" type="email" placeholder="contact@garage.fr">
        </div>
      </div>
      <div class="pf-row pf-row-2">
        <div>
          <label class="pf-label">Contact</label>
          <input class="pf-input" id="pf-contact" type="text" placeholder="Prénom Nom">
        </div>
        <div>
          <label class="pf-label">Ville</label>
          <input class="pf-input" id="pf-ville" type="text" placeholder="Paris">
        </div>
      </div>
      <div class="pf-row">
        <label class="pf-label">Adresse</label>
        <input class="pf-input" id="pf-adresse" type="text" placeholder="12 rue de la Paix, 75001 Paris">
      </div>
      <div class="pf-row">
        <label class="pf-label">Site web</label>
        <input class="pf-input" id="pf-site" type="url" placeholder="https://...">
      </div>
      <div class="pf-row">
        <label class="pf-label">Notes</label>
        <textarea class="pf-input pf-textarea" id="pf-notes" placeholder="Informations complémentaires…" rows="3"></textarea>
      </div>
      <div class="pf-actions">
        <button type="button" class="pf-cancel-btn" onclick="closePrestAddModal()">Annuler</button>
        <button type="submit" class="pf-submit-btn" id="pf-submit-btn">Ajouter le prestataire</button>
      </div>
    </form>
  </div>
</div>
<script>var MARGES_DATA = {marges_data};</script>
<script>var PREST_API_URL = "https://api.airtable.com/v0/{PRESTATAIRES_BASE_ID}/{PRESTATAIRES_TABLE_ID}"; var PREST_TOKEN = "{PRESTATAIRES_TOKEN}";</script>
<script>{_js()}</script>
</body>
</html>"""


# ─── Renderers ────────────────────────────────────────────────────────────────

def _render_reservees(reservees, francois_cars=None, ct_data=None):
    francois_cars = francois_cars or set()
    # Index CT par nom de voiture (réservées = statut "acompte" ou "acompte-ok")
    ct_by_car = {}
    for c in (ct_data or []):
        if c.get("ct_filter_type") in ("acompte", "acompte-ok"):
            ct_by_car[c["voiture"]] = c
    if not reservees:
        return '<div class="empty-state">Aucune voiture réservée</div>'
    # Criticité CT → classe CSS et libellé
    CT_CLS  = {0: "ct-expire-badge", 1: "ct-manquant-badge", 2: "ct-bientot-badge", 3: "ct-ok-badge"}
    items = ""
    for r in reservees:
        photo = r.get("photo_url")
        photo_html = f'<img class="res-photo" src="{photo}" alt="">' if photo else '<div class="res-photo-placeholder"></div>'
        commerciaux = r.get("commerciaux", [])
        commerciaux_html = "".join(
            f'<span class="commercial-badge">{c}</span>' for c in commerciaux
        )
        voiture = r.get('voiture', '—')
        fck = ' <span class="fck-badge">🖕</span>' if (voiture in francois_cars or r.get("is_francois")) else ''
        fck_data = '🖕' if (voiture in francois_cars or r.get("is_francois")) else ''
        ts = r.get('bc_num', 0)
        bc_str = r.get('bc_str', '')
        bc_html = f'<span class="bc-badge">{bc_str}</span>' if bc_str else ''
        photo_src = r.get('photo_url') or ''
        commerciaux_json = _json.dumps(r.get("commerciaux", []))
        fiche_url    = r.get('fiche_url', '#')
        travaux_url  = r.get('travaux_url', fiche_url)

        # Badge CT
        ct_info = ct_by_car.get(voiture)
        if ct_info:
            ct_cls   = CT_CLS.get(ct_info.get("criticite", 3), "ct-badge-ok")
            ct_label = ct_info.get("ct_status", "—")
            ct_badge = f'<span class="ct-res-badge {ct_cls}">{ct_label}</span>'
            ct_data_attr = f'data-ct="{ct_label}" data-ct-cls="{ct_cls}"'
        else:
            ct_badge = ''
            ct_data_attr = 'data-ct="" data-ct-cls=""'

        items += f"""<div class="reservation-card" data-ts="{ts}" data-voiture="{voiture}" data-fck="{fck_data}" data-bc="{bc_str}" data-prix="{r.get('prix_fmt','—')}" data-marge="{r.get('marge_fmt','—')}" data-fiche="{fiche_url}" data-travaux="{travaux_url}" data-photo="{photo_src}" data-commerciaux='{commerciaux_json}' {ct_data_attr} onclick="openResModal(this)">
          {photo_html}
          <div class="res-info">
            <div class="res-header">
              <div class="res-header-top">
                <span class="car-name">{voiture}{fck}</span>
                {bc_html}
              </div>
              {ct_badge}
            </div>
            <div class="res-amounts">
              <span class="res-prix">Prix : <strong>{r.get('prix_fmt','—')}</strong></span>
              <span class="res-marge">Marge : <strong>{r.get('marge_fmt','—')}</strong></span>
            </div>
            <div class="res-footer">
              <a class="fiche-btn" href="{fiche_url}" target="_blank" onclick="event.stopPropagation()">Accéder à la fiche →</a>
              {commerciaux_html}
            </div>
          </div>
        </div>"""
    return f'<div class="reservations-grid">{items}</div>'


def _render_ct(ct_data, francois_cars=None):
    francois_cars = francois_cars or set()
    if not ct_data:
        return '<div class="empty-state">Aucune alerte CT</div>'

    crit_cls = {0: "ct-expire", 1: "ct-manquant", 2: "ct-bientot", 3: "ct-ok"}

    rows = ""
    for c in ct_data:
        crit = c.get("criticite", 3)
        cls = crit_cls.get(crit, "ct-ok")
        statut = c.get("statut", "—")
        ct_filter_type = c.get("ct_filter_type", "other")
        ct_status = c.get("ct_status", "—")
        date_ct = c.get("date_ct") or "—"
        date_ech = c.get("date_echeance") or "—"
        jours = c.get("jours_restants")

        # Masquer par défaut les acompte-ok (visibles seulement dans filtre Réservées)
        default_hidden = ' style="display:none"' if ct_filter_type == "acompte-ok" else ""

        if jours is not None:
            if jours < 0:
                jours_cell = f'<span class="jours-expire">Expiré ({abs(jours)}j)</span>'
            elif jours <= 30:
                jours_cell = f'<span class="jours-bientot">{jours}j</span>'
            else:
                jours_cell = f'<span class="jours-ok">{jours}j</span>'
        else:
            jours_cell = '<span class="jours-manquant">—</span>'

        # Badge CT status avec JUL si Expiré
        is_expire = (crit == 0)
        jul_span = ' <span class="jul">✌🏼✌🏼</span>' if is_expire else ""
        ct_badge = f'<span class="ct-status-badge {cls}-badge">{ct_status}{jul_span}</span>'

        fiche_url = c.get("fiche_url", "")
        fiche = f'<a class="fiche-btn-sm" href="{fiche_url}" target="_blank">Fiche →</a>' if fiche_url else ""

        voiture_ct = c.get('voiture', '—')
        fck_ct = ' <span class="fck-badge">🖕</span>' if voiture_ct in francois_cars else ''
        rows += f"""<div class="ct-row {cls}" data-ct-type="{ct_filter_type}" data-ct-crit="{crit}"{default_hidden}>
          <div class="ct-car"><span class="car-name">{voiture_ct}{fck_ct}</span></div>
          <div><span class="statut-pill">{statut}</span></div>
          <div>{ct_badge}</div>
          <div class="ct-date">{date_ct}</div>
          <div class="ct-date">{date_ech}</div>
          <div class="ct-jours">{jours_cell}</div>
          <div>{fiche}</div>
        </div>"""

    return f"""<div class="ct-table-header">
      <div>Véhicule</div><div>Statut</div><div>CT Status</div>
      <div>Date CT</div><div>Échéance</div><div>Jours restants</div><div></div>
    </div>
    <div id="ct-table-body">{rows}</div>"""


def _render_frais(frais_by_car, car_photos, francois_cars=None):
    francois_cars = francois_cars or set()
    if not frais_by_car:
        return '<div class="empty-state">Aucun frais enregistré ce mois</div>'
    blocks = ""
    for car, frais_list in sorted(frais_by_car.items()):
        total = sum(f["montant"] for f in frais_list if f.get("montant") is not None)
        total_fmt = f"{total:,.2f} €".replace(",", "\u202f") if total else "—"
        max_ts = max((int(f["date_ts"].timestamp()) for f in frais_list if f.get("date_ts")), default=0)

        car_info = car_photos.get(car, {})
        photo_url = car_info.get("photo_url")
        fiche_url = car_info.get("fiche_url")

        photo_html = f'<img class="car-thumb" src="{photo_url}" alt="">' if photo_url else '<div class="car-thumb-placeholder"></div>'
        fck_frais = ' <span class="fck-badge">🖕</span>' if car in francois_cars else ''
        car_title = f'<span class="car-frais-name-text">🚗 {car}{fck_frais}</span>'
        fiche_btn_car = f'<a class="fiche-btn-sm" href="{fiche_url}" target="_blank">Fiche →</a>' if fiche_url else ""

        rows = ""
        for frais in frais_list:
            ts_unix = int(frais["date_ts"].timestamp()) if frais.get("date_ts") else 0
            link = frais.get("airtable_url", "")
            cat = frais.get("categorie", "")
            objet = frais.get("objet", "—")
            objet_display = f"{cat} · {objet}" if cat and cat != "—" else objet
            montant_cell = frais["montant_fmt"]
            if link:
                montant_cell = f'<a class="airtable-link" href="{link}" target="_blank">{frais["montant_fmt"]}</a>'
            rows += f"""<div class="frais-row" data-ts="{ts_unix}" data-section="frais">
              <span class="frais-date">{frais['date']}</span>
              <span class="frais-objet">{objet_display}</span>
              <span class="frais-montant">{montant_cell}</span>
            </div>"""

        statut = car_info.get("statut", "")
        blocks += f"""<div class="car-frais-block" data-max-ts="{max_ts}" data-statut="{statut}">
          <div class="car-frais-header">
            {photo_html}
            <span class="car-frais-name">{car_title}</span>
            <span class="car-frais-total">{total_fmt}</span>
            {fiche_btn_car}
          </div>
          <div class="frais-list">{rows}</div>
        </div>"""

    return f'<div class="frais-container" id="frais-container">{blocks}</div>'



def _render_prestataires(prestataires):
    """Génère le HTML du répertoire prestataires, groupé par spécialité."""
    if not prestataires:
        return '<div class="empty-state prest-empty">Aucun prestataire chargé — vérifie le token PRESTATAIRES_TOKEN dans config.py</div>'

    _TYPE_ORDER = [
        "Mécanique", "Carrosserie", "Pièces détachées",
        "Débosselage", "Sellerie", "Detailling", "Transporteur",
    ]
    _TYPE_COLORS = {
        "Mécanique":         ("#2563eb", "#eff6ff", "#bfdbfe"),
        "Carrosserie":       ("#ea580c", "#fff7ed", "#fed7aa"),
        "Pièces détachées":  ("#7c3aed", "#f5f3ff", "#ddd6fe"),
        "Débosselage":       ("#059669", "#f0fdf4", "#bbf7d0"),
        "Sellerie":          ("#0891b2", "#ecfeff", "#a5f3fc"),
        "Detailling":        ("#db2777", "#fdf2f8", "#fbcfe8"),
        "Transporteur":      ("#6b7280", "#f9fafb", "#e5e7eb"),
        "Autre":             ("#374151", "#f3f4f6", "#d1d5db"),
    }

    # Grouper par type (premier type de chaque prestataire)
    groups = {}
    for p in prestataires:
        primary_type = p["types"][0] if p["types"] else "Autre"
        groups.setdefault(primary_type, []).append(p)

    ordered_keys = [k for k in _TYPE_ORDER if k in groups]
    for k in groups:
        if k not in ordered_keys:
            ordered_keys.append(k)

    # Collecte les marques distinctes pour les filtres JS
    all_marques = sorted({m for p in prestataires for m in p["marques"] if m})

    # Rendre les groupes
    def stars_html(rating, cls="prest-stars"):
        s = ""
        for i in range(1, 6):
            s += f'<span class="{"star-on" if i <= rating else "star-off"}">★</span>'
        return f'<span class="{cls}">{s}</span>'

    groups_html = ""
    for gtype in ordered_keys:
        items = groups[gtype]
        color, bg_light, bg_border = _TYPE_COLORS.get(gtype, _TYPE_COLORS["Autre"])
        cards_html = ""
        for p in items:
            type_pills = "".join(
                f'<span class="prest-type-pill" style="background:{bg_light};color:{color};border-color:{bg_border}">{t}</span>'
                for t in p["types"]
            )
            marque_pills = "".join(
                f'<span class="prest-marque-pill">{m}</span>'
                for m in p["marques"]
            )
            # Contact info
            contacts_html = ""
            if p.get("telephone"):
                contacts_html += f'<div class="prest-contact-item"><span class="pci-icon">📞</span><a href="tel:{p["telephone"]}" class="pci-link">{p["telephone"]}</a></div>'
            if p.get("email"):
                contacts_html += f'<div class="prest-contact-item"><span class="pci-icon">✉</span><a href="mailto:{p["email"]}" class="pci-link">{p["email"]}</a></div>'
            if p.get("ville") or p.get("adresse"):
                loc = p.get("ville") or p.get("adresse", "")
                contacts_html += f'<div class="prest-contact-item"><span class="pci-icon">📍</span><span class="pci-text">{loc}</span></div>'
            if p.get("contact"):
                contacts_html += f'<div class="prest-contact-item"><span class="pci-icon">👤</span><span class="pci-text">{p["contact"]}</span></div>'
            if p.get("site"):
                site_display = p["site"].replace("https://", "").replace("http://", "").rstrip("/")
                contacts_html += f'<div class="prest-contact-item"><span class="pci-icon">🌐</span><a href="{p["site"]}" class="pci-link" target="_blank">{site_display}</a></div>'

            notes_html = ""
            if p.get("notes"):
                notes_safe = p["notes"].replace("<", "&lt;").replace(">", "&gt;")
                notes_html = f'<p class="prest-notes">{notes_safe}</p>'

            # Data attrs pour filtrage JS
            types_json = _json.dumps(p["types"])
            marques_json = _json.dumps(p["marques"])
            nom_lower = p["nom"].lower()
            contact_lower = (p.get("contact") or "").lower()
            ville_lower = (p.get("ville") or "").lower()
            notes_lower = (p.get("notes") or "").lower()

            cards_html += f"""<div class="prest-card" data-types='{types_json}' data-marques='{marques_json}' data-searchtext="{nom_lower} {contact_lower} {ville_lower} {notes_lower}">
              <div class="prest-card-accent" style="background:{color}"></div>
              <div class="prest-card-body">
                <div class="prest-card-top">
                  <div class="prest-card-pills">{type_pills}</div>
                  {stars_html(p["rating"])}
                </div>
                <div class="prest-card-name">{p["nom"]}</div>
                {f'<div class="prest-contacts">{contacts_html}</div>' if contacts_html else ''}
                {f'<div class="prest-marques">{marque_pills}</div>' if marque_pills else ''}
                {notes_html}
              </div>
            </div>"""

        groups_html += f"""<div class="prest-group" data-group-type="{gtype}">
          <div class="prest-group-header" style="border-left:3px solid {color}">
            <span class="prest-group-name" style="color:{color}">{gtype}</span>
            <span class="prest-group-count">{len(items)}</span>
          </div>
          <div class="prest-cards-grid">{cards_html}</div>
        </div>"""

    # Injecter les données marques pour les filtres JS (sera lues au démarrage)
    marques_json_global = _json.dumps(all_marques)
    return f"""<div id="prest-groups">{groups_html}</div>
<script>var PREST_MARQUES = {marques_json_global}; initPrestFilters();</script>"""


# ─── JavaScript ───────────────────────────────────────────────────────────────

def _js():
    return r"""
// ── Collapse sections ────────────────────────────────────────────────
// ── Recherche par voiture dans chaque module ────────────────────────
var searchQueries = { frais: '', ct: '', reservees: '' };

function filterBySearch(section, query) {
  searchQueries[section] = query.trim().toLowerCase();
  var clearBtn = document.querySelector('#search-' + section + ' ~ .search-clear-btn, #body-' + section + ' .search-clear-btn');
  if (clearBtn) clearBtn.classList.toggle('visible', query.length > 0);
  applySearchFilter(section);
}

function clearSearch(section) {
  var input = document.getElementById('search-' + section);
  if (input) { input.value = ''; input.focus(); }
  searchQueries[section] = '';
  var clearBtn = document.querySelector('#body-' + section + ' .search-clear-btn');
  if (clearBtn) clearBtn.classList.remove('visible');
  applySearchFilter(section);
}

function applySearchFilter(section) {
  var q = searchQueries[section];
  if (section === 'frais') {
    document.querySelectorAll('.car-frais-block').forEach(function(block) {
      var name = (block.querySelector('.car-frais-name-text') || block.querySelector('.car-name') || {textContent:''}).textContent.toLowerCase();
      block.style.display = (!q || name.includes(q)) ? '' : 'none';
    });
  } else if (section === 'ct') {
    applyCTFilter(); // CT uses its own filter — we override post-hoc
    if (q) {
      document.querySelectorAll('#ct-table-body .ct-row').forEach(function(row) {
        if (row.style.display !== 'none') {
          var name = (row.querySelector('.car-name') || {textContent:''}).textContent.toLowerCase();
          if (!name.includes(q)) row.style.display = 'none';
        }
      });
    }
  } else if (section === 'reservees') {
    document.querySelectorAll('.res-block').forEach(function(block) {
      var name = (block.querySelector('.car-name') || {textContent:''}).textContent.toLowerCase();
      block.style.display = (!q || name.includes(q)) ? '' : 'none';
    });
  }
}

function toggleSection(id) {
  var body = document.getElementById('body-' + id);
  var btn = document.getElementById('collapse-' + id);
  if (!body) return;
  var isOpen = body.classList.contains('open');
  if (isOpen) {
    // Fermeture : figer la hauteur actuelle puis animer vers 0
    body.style.height = body.scrollHeight + 'px';
    body.style.transition = 'none';
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        body.style.transition = 'height 0.38s cubic-bezier(0.4,0,0.2,1), opacity 0.28s ease';
        body.style.height = '0';
        body.style.opacity = '0';
        body.classList.remove('open');
        if (btn) btn.classList.remove('rotated');
      });
    });
  } else {
    // Ouverture : mesurer la vraie hauteur et animer vers elle
    body.style.height = '0';
    body.style.opacity = '0';
    body.style.transition = 'none';
    body.classList.add('open');
    var target = body.scrollHeight;
    requestAnimationFrame(function() {
      requestAnimationFrame(function() {
        body.style.transition = 'height 0.42s cubic-bezier(0.4,0,0.2,1), opacity 0.35s ease 0.04s';
        body.style.height = target + 'px';
        body.style.opacity = '1';
        if (btn) btn.classList.add('rotated');
        // Une fois l'animation terminée, libérer la hauteur (pour le contenu dynamique)
        body.addEventListener('transitionend', function handler(e) {
          if (e.propertyName === 'height') {
            body.style.height = 'auto';
            body.style.transition = '';
            body.removeEventListener('transitionend', handler);
          }
        });
      });
    });
  }
}

// ── Tri voitures réservées ───────────────────────────────────────────
var reserveesSortDesc = true; // plus récent en premier par défaut
function toggleSortReservees(btn) {
  reserveesSortDesc = !reserveesSortDesc;
  btn.textContent = reserveesSortDesc ? '↓ Plus récent' : '↑ Plus ancien';
  var grid = document.querySelector('.reservations-grid');
  if (!grid) return;
  var cards = Array.from(grid.querySelectorAll('.reservation-card'));
  cards.sort(function(a, b) {
    var ta = parseInt(a.getAttribute('data-ts') || '0', 10);
    var tb = parseInt(b.getAttribute('data-ts') || '0', 10);
    return reserveesSortDesc ? tb - ta : ta - tb;
  });
  cards.forEach(function(c) { grid.appendChild(c); });
}


// ── État des filtres ────────────────────────────────────────────────
var ctState = { group: 'tous', statuses: new Set() };

// ── Filtre Frais (date + statut) ─────────────────────────────────────
var fraisState = { days: 0, statut: 'tous' };

function applyFraisFilter() {
  var now = Math.floor(Date.now() / 1000);
  var cutoff = fraisState.days > 0 ? now - fraisState.days * 86400 : 0;
  var visible = 0;
  document.querySelectorAll('.car-frais-block').forEach(function(block) {
    var statut = (block.getAttribute('data-statut') || '').toLowerCase();
    var okStatut = fraisState.statut === 'tous' || statut.indexOf('acompte') !== -1;
    if (!okStatut) {
      block.style.display = 'none';
      return;
    }
    var anyVisible = false;
    block.querySelectorAll('[data-section="frais"]').forEach(function(row) {
      var ts = parseInt(row.getAttribute('data-ts') || '0', 10);
      var show = (fraisState.days === 0) || (ts > 0 && ts >= cutoff);
      row.style.display = show ? '' : 'none';
      if (show) { anyVisible = true; visible++; }
    });
    block.style.display = anyVisible ? '' : 'none';
  });
  var el = document.getElementById('frais-count');
  if (el) el.textContent = visible;
}

document.querySelectorAll('.filter-bar[data-target="frais"] .filter-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.filter-bar[data-target="frais"] .filter-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    fraisState.days = parseInt(btn.getAttribute('data-days'), 10);
    applyFraisFilter();
  });
});

document.querySelectorAll('.frais-statut-filter .filter-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.frais-statut-filter .filter-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    fraisState.statut = btn.getAttribute('data-frais-statut');
    applyFraisFilter();
  });
});

// ── Filtres CT ───────────────────────────────────────────────────────
function applyCTFilter() {
  var rows = document.querySelectorAll('#ct-table-body .ct-row');
  var visible = 0;
  rows.forEach(function(row) {
    var type = row.getAttribute('data-ct-type');
    var crit = row.getAttribute('data-ct-crit');
    var okGroup, okStatus;
    if (ctState.group === 'tous') {
      okGroup = type !== 'acompte-ok';
    } else {
      okGroup = (type === 'acompte' || type === 'acompte-ok');
    }
    okStatus = ctState.statuses.size === 0 || ctState.statuses.has(crit);
    var show = okGroup && okStatus;
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  var el = document.getElementById('ct-count');
  if (el) el.textContent = visible;
}

document.querySelectorAll('.ct-filter .filter-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.ct-filter .filter-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    ctState.group = btn.getAttribute('data-ct');
    applyCTFilter();
  });
});

document.querySelectorAll('.ct-status-filter .filter-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var val = btn.getAttribute('data-ct-status');
    if (val === 'tous') {
      ctState.statuses.clear();
      document.querySelectorAll('.ct-status-filter .filter-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
    } else {
      document.querySelector('.ct-status-filter .filter-btn[data-ct-status="tous"]').classList.remove('active');
      if (btn.classList.contains('active')) {
        btn.classList.remove('active');
        ctState.statuses.delete(val);
        if (ctState.statuses.size === 0) {
          document.querySelector('.ct-status-filter .filter-btn[data-ct-status="tous"]').classList.add('active');
        }
      } else {
        btn.classList.add('active');
        ctState.statuses.add(val);
      }
    }
    applyCTFilter();
  });
});

// Init CT (cache acompte-ok par défaut)
applyCTFilter();

// KPI Marge dynamique (voitures réservées Airtable)
function computeMarge(days) {
  var now = Math.floor(Date.now() / 1000);
  var cutoff = days > 0 ? now - days * 86400 : 0;
  var total = 0;
  MARGES_DATA.forEach(function(r) {
    if (days === 0 || r.ts === 0 || r.ts >= cutoff) {
      total += r.marge || 0;
    }
  });
  if (total === 0) return '—';
  return total.toLocaleString('fr-FR', {maximumFractionDigits: 0}) + '\u202f€';
}

function updateMargeKPI(days) {
  var el = document.getElementById('marge-value');
  if (el) el.textContent = computeMarge(days);
}

document.querySelectorAll('.marge-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.marge-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    updateMargeKPI(parseInt(btn.getAttribute('data-days'), 10));
  });
});

// Init marge KPI (3 mois par défaut)
updateMargeKPI(90);

// ── Modal voiture réservée ──────────────────────────────────────────────
function openResModal(card) {
  var voiture = card.getAttribute('data-voiture') || '—';
  var fck = card.getAttribute('data-fck') || '';
  var bc = card.getAttribute('data-bc') || '';
  var prix = card.getAttribute('data-prix') || '—';
  var marge = card.getAttribute('data-marge') || '—';
  var fiche = card.getAttribute('data-fiche') || '#';
  var travaux = card.getAttribute('data-travaux') || fiche;
  var photo = card.getAttribute('data-photo') || '';
  var commerciaux = JSON.parse(card.getAttribute('data-commerciaux') || '[]');
  var ctLabel = card.getAttribute('data-ct') || '';
  var ctCls = card.getAttribute('data-ct-cls') || '';

  var m = document.getElementById('res-modal');
  var img = document.getElementById('res-modal-photo');
  if (photo) { img.src = photo; img.style.display = 'block'; }
  else { img.style.display = 'none'; }

  document.getElementById('res-modal-name').innerHTML = voiture + (fck ? ' <span class="fck-badge">' + fck + '</span>' : '');
  var bcEl = document.getElementById('res-modal-bc');
  bcEl.textContent = bc; bcEl.style.display = bc ? 'inline-block' : 'none';
  document.getElementById('res-modal-prix').textContent = prix;
  document.getElementById('res-modal-marge').textContent = marge;
  document.getElementById('res-modal-fiche').href = fiche;
  document.getElementById('res-modal-travaux').href = travaux;

  var ctEl = document.getElementById('res-modal-ct');
  ctEl.className = 'ct-res-badge ' + (ctCls || '');
  ctEl.textContent = ctLabel;
  ctEl.style.display = ctLabel ? 'inline-flex' : 'none';

  var comDiv = document.getElementById('res-modal-commerciaux');
  comDiv.innerHTML = commerciaux.map(function(c) { return '<span class="commercial-badge">' + c + '</span>'; }).join('');

  m.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeResModal(e) {
  if (e && e.target !== document.getElementById('res-modal') && !e.target.classList.contains('res-modal-close')) return;
  document.getElementById('res-modal').classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.getElementById('res-modal').classList.remove('open');
    document.body.style.overflow = '';
    closePrestAddModal();
  }
});

// ── KPI CT cliquable ─────────────────────────────────────────────────────────
function jumpToCT() {
  // 1. Ouvrir la section CT si fermée
  var body = document.getElementById('body-ct');
  if (body && !body.classList.contains('open')) {
    toggleSection('ct');
  }
  // 2. Activer filtres Expiré(0) + Manquant(1) + Bientôt(2), désactiver OK et Tous
  ctState.statuses = new Set(['0', '1', '2']);
  document.querySelectorAll('.ct-status-filter .filter-btn').forEach(function(btn) {
    var v = btn.getAttribute('data-ct-status');
    btn.classList.toggle('active', v === '0' || v === '1' || v === '2');
  });
  applyCTFilter();
  // 3. Scroll fluide vers la section CT (délai pour laisser l'animation démarrer)
  var section = document.getElementById('section-ct');
  if (section) {
    setTimeout(function() {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  }
}

// ── Prestataires ─────────────────────────────────────────────────────────────
var prestState = { type: 'tous', marque: 'tous', search: '' };

function initPrestFilters() {
  // Injecter les boutons de type depuis les groupes présents
  var typeBar = document.getElementById('prest-type-filters');
  if (!typeBar) return;
  var groups = document.querySelectorAll('.prest-group[data-group-type]');
  groups.forEach(function(g) {
    var t = g.getAttribute('data-group-type');
    var btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.setAttribute('data-prest-type', t);
    btn.textContent = t;
    btn.onclick = function() { setPrestTypeFilter(btn); };
    typeBar.appendChild(btn);
  });
  // Injecter les boutons de marque
  var marqueBar = document.getElementById('prest-marque-filters');
  if (marqueBar && typeof PREST_MARQUES !== 'undefined') {
    PREST_MARQUES.forEach(function(m) {
      var btn = document.createElement('button');
      btn.className = 'filter-btn';
      btn.setAttribute('data-prest-marque', m);
      btn.textContent = m;
      btn.onclick = function() { setPrestMarqueFilter(btn); };
      marqueBar.appendChild(btn);
    });
  }
}

function setPrestTypeFilter(btn) {
  document.querySelectorAll('#prest-type-filters .filter-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  prestState.type = btn.getAttribute('data-prest-type');
  applyPrestFilters();
}

function setPrestMarqueFilter(btn) {
  document.querySelectorAll('#prest-marque-filters .filter-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  prestState.marque = btn.getAttribute('data-prest-marque');
  applyPrestFilters();
}

function clearPrestSearch() {
  var inp = document.getElementById('search-prest');
  if (inp) { inp.value = ''; inp.focus(); }
  prestState.search = '';
  var cb = document.querySelector('.prest-search-wrap .search-clear-btn');
  if (cb) cb.classList.remove('visible');
  applyPrestFilters();
}

function applyPrestFilters() {
  var inp = document.getElementById('search-prest');
  if (inp) {
    prestState.search = inp.value.trim().toLowerCase();
    var cb = document.querySelector('.prest-search-wrap .search-clear-btn');
    if (cb) cb.classList.toggle('visible', prestState.search.length > 0);
  }
  var total = 0;
  document.querySelectorAll('.prest-group').forEach(function(group) {
    var gtype = group.getAttribute('data-group-type');
    var okType = prestState.type === 'tous' || gtype === prestState.type;
    var groupVisible = 0;
    group.querySelectorAll('.prest-card').forEach(function(card) {
      var types = JSON.parse(card.getAttribute('data-types') || '[]');
      var marques = JSON.parse(card.getAttribute('data-marques') || '[]');
      var txt = card.getAttribute('data-searchtext') || '';
      var okT = prestState.type === 'tous' || types.indexOf(prestState.type) !== -1;
      var okM = prestState.marque === 'tous' || marques.indexOf(prestState.marque) !== -1;
      var okS = !prestState.search || txt.indexOf(prestState.search) !== -1;
      var show = okType && okT && okM && okS;
      card.style.display = show ? '' : 'none';
      if (show) { groupVisible++; total++; }
    });
    group.style.display = (okType && groupVisible > 0) ? '' : 'none';
  });
  var countEl = document.getElementById('prest-count');
  if (countEl) countEl.textContent = total;
}

// ── Modal ajout prestataire ───────────────────────────────────────────────────
function openPrestAddModal() {
  document.getElementById('prest-add-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
  // Reset form
  document.getElementById('prest-add-form').reset();
  setPfRating(0);
  document.getElementById('pf-submit-btn').disabled = false;
  document.getElementById('pf-submit-btn').textContent = 'Ajouter le prestataire';
  document.getElementById('pf-submit-btn').style.background = '';
}

function closePrestAddModal(e) {
  if (e && e.target !== document.getElementById('prest-add-modal') &&
      !e.target.classList.contains('prest-modal-close')) return;
  document.getElementById('prest-add-modal').classList.remove('open');
  document.body.style.overflow = '';
}

// Star rating dans le formulaire
var pfRating = 0;
function setPfRating(v) {
  pfRating = v;
  document.getElementById('pf-rating').value = v;
  document.querySelectorAll('.pf-star').forEach(function(s) {
    s.classList.toggle('pf-star-on', parseInt(s.getAttribute('data-v')) <= v);
  });
}
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.pf-star').forEach(function(s) {
    s.addEventListener('click', function() { setPfRating(parseInt(s.getAttribute('data-v'))); });
    s.addEventListener('mouseenter', function() {
      var v = parseInt(s.getAttribute('data-v'));
      document.querySelectorAll('.pf-star').forEach(function(ss) {
        ss.classList.toggle('pf-star-hover', parseInt(ss.getAttribute('data-v')) <= v);
      });
    });
    s.addEventListener('mouseleave', function() {
      document.querySelectorAll('.pf-star').forEach(function(ss) { ss.classList.remove('pf-star-hover'); });
    });
  });
});

function submitNewPrestataire(e) {
  e.preventDefault();
  var btn = document.getElementById('pf-submit-btn');
  btn.disabled = true;
  btn.textContent = 'Envoi en cours…';

  var nom     = document.getElementById('pf-nom').value.trim();
  var typeVal = document.getElementById('pf-type').value;
  var marques = Array.from(document.querySelectorAll('#pf-marques input:checked')).map(function(cb) { return cb.value; });
  var rating  = parseInt(document.getElementById('pf-rating').value || '0', 10);
  var tel     = document.getElementById('pf-tel').value.trim();
  var email   = document.getElementById('pf-email').value.trim();
  var adresse = document.getElementById('pf-adresse').value.trim();
  var contact = document.getElementById('pf-contact').value.trim();
  var ville   = document.getElementById('pf-ville').value.trim();
  var site    = document.getElementById('pf-site').value.trim();
  var notes   = document.getElementById('pf-notes').value.trim();

  var fields = {};
  if (nom)     fields['Nom du garage'] = nom;
  if (typeVal) fields['Type'] = { name: typeVal };
  if (marques.length) fields['Marque'] = marques.map(function(m) { return { name: m }; });
  if (rating > 0) fields['Rating'] = rating;
  if (tel)     fields['Téléphone'] = tel;
  if (email)   fields['Email']     = email;
  if (adresse) fields['Adresse']   = adresse;
  if (contact) fields['Contact']   = contact;
  if (ville)   fields['Ville']     = ville;
  if (site)    fields['Site web']  = site;
  if (notes)   fields['Notes']     = notes;

  if (!PREST_TOKEN || PREST_TOKEN === 'None') {
    btn.disabled = false;
    btn.textContent = 'Ajouter le prestataire';
    alert('Token Prestataires non configuré — configure PRESTATAIRES_TOKEN dans config.py');
    return;
  }

  fetch(PREST_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + PREST_TOKEN,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fields: fields })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.id) {
      btn.textContent = '✓ Prestataire ajouté !';
      btn.style.background = '#22c55e';
      setTimeout(function() {
        closePrestAddModal();
        document.body.style.overflow = '';
      }, 1800);
    } else {
      btn.disabled = false;
      btn.textContent = 'Ajouter le prestataire';
      var msg = (data.error && data.error.message) ? data.error.message : JSON.stringify(data);
      alert('Erreur Airtable : ' + msg);
    }
  })
  .catch(function(err) {
    btn.disabled = false;
    btn.textContent = 'Ajouter le prestataire';
    alert('Erreur réseau : ' + err.message);
  });
}
"""


# ─── CSS ──────────────────────────────────────────────────────────────────────

def _css():
    return """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
      background: #eef1f6;
      color: #0a0f1e;
      min-height: 100vh;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    .glass-card {
      background: #ffffff;
      border: 1px solid rgba(0,0,0,0.06);
      border-radius: 18px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.05);
      transition: box-shadow 0.25s ease, transform 0.25s ease;
    }

    .app { max-width: 1440px; margin: 0 auto; padding: 28px; }

    /* Header */
    .header { padding: 26px 36px; margin-bottom: 20px; position: relative; overflow: hidden; }
    .header-car-bg {
      position: absolute;
      height: 430%; width: auto;
      top: 50%; left: 50%;
      transform: translate(-54%, -56%);
      opacity: 0.38;
      -webkit-mask-image: linear-gradient(to right, transparent 0%, black 8%, black 88%, transparent 100%);
      mask-image: linear-gradient(to right, transparent 0%, black 8%, black 88%, transparent 100%);
      pointer-events: none; user-select: none; z-index: 0;
    }
    .header-content { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
    .mecanicus-logo { height: 72px; width: auto; filter: brightness(0); }
    .header-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
    .time-badge { font-size: 44px; font-weight: 200; letter-spacing: -2.5px; color: #0a0f1e; font-variant-numeric: tabular-nums; line-height: 1; }
    .refresh-btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 9px 20px; background: #2FAEE0; border: none; border-radius: 980px;
      color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 600;
      transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }
    .refresh-btn:hover { background: #003f7a; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,87,168,0.35); }
    .refresh-note { font-size: 10px; color: #adb5c2; text-align: right; }

    /* KPI */
    .kpi-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-bottom: 20px; }
    .kpi { display: flex; align-items: center; gap: 18px; padding: 26px 28px; }
    .kpi:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.09); }
    .kpi-clickable { cursor: pointer; }
    .kpi-clickable:hover { box-shadow: 0 6px 28px rgba(234,88,12,0.18); border-color: rgba(234,88,12,0.25); }
    .kpi-arrow { font-size: 16px; color: #d1d5db; margin-left: auto; transition: transform 0.2s ease, color 0.2s ease; align-self: center; }
    .kpi-clickable:hover .kpi-arrow { transform: translateX(4px); color: #ea580c; }
    .kpi-icon-wrap { width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }

    /* Animation cloche — pivot depuis le haut */
    @keyframes ring {
      0%   { transform: rotate(0deg); }
      8%   { transform: rotate(18deg); }
      20%  { transform: rotate(-16deg); }
      32%  { transform: rotate(13deg); }
      44%  { transform: rotate(-10deg); }
      56%  { transform: rotate(7deg); }
      68%  { transform: rotate(-4deg); }
      80%  { transform: rotate(2deg); }
      100% { transform: rotate(0deg); }
    }
    /* Animation alerte — tremblement latéral */
    @keyframes shake {
      0%,100% { transform: translateX(0); }
      12%  { transform: translateX(-4px) rotate(-2deg); }
      25%  { transform: translateX(4px) rotate(2deg); }
      37%  { transform: translateX(-4px) rotate(-1deg); }
      50%  { transform: translateX(4px) rotate(1deg); }
      62%  { transform: translateX(-2px); }
      75%  { transform: translateX(2px); }
      87%  { transform: translateX(-1px); }
    }
    .kpi:hover .kpi-red   svg { transform-origin: 50% 0%; animation: ring  0.7s cubic-bezier(0.36,0.07,0.19,0.97) both; }
    .kpi:hover .kpi-orange svg { animation: shake 0.6s cubic-bezier(0.36,0.07,0.19,0.97) both; }
    .kpi-green  { background: #d1fae5; }
    .kpi-blue   { background: #dbeafe; }
    .kpi-orange { background: #ffedd5; }
    .kpi-red    { background: #fee2e2; }
    .kpi-body { display: flex; flex-direction: column; min-width: 0; }
    .kpi-value { font-size: 40px; font-weight: 700; color: #0a0f1e; letter-spacing: -2px; line-height: 1; font-variant-numeric: tabular-nums; }
    .kpi-label { font-size: 10px; color: #8a94a6; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600; }

    .module-sub-filters { display: flex; gap: 20px; flex-wrap: wrap; padding: 0 0 14px 0; border-bottom: 1px solid #f0f2f5; margin-bottom: 6px; }
    .collapsible-header { cursor: pointer; border-radius: 12px; padding: 4px 6px; margin: -4px -6px; transition: background 0.15s; }
    .collapsible-header:hover { background: rgba(0,87,168,0.04); }
    .collapsible-header:hover .collapse-btn { border-color: #2FAEE0; color: #2FAEE0; }
    .header-filters { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 0; }
    .collapse-btn { background: none; border: 1px solid #dde1e8; border-radius: 8px; color: #adb5c2; padding: 5px 8px; cursor: pointer; transition: all 0.2s ease; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
    .collapse-btn svg { transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1); }
    .collapse-btn.rotated svg { transform: rotate(180deg); }
    /* Section body — géré en JS (hauteur exacte) */
    .section-body { overflow: hidden; opacity: 0; height: 0; }

    /* Grid */
    .grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 18px; }
    .col-span-2 { grid-column: span 2; }
    .col-span-3 { grid-column: span 3; }

    /* Section */
    .section { padding: 22px 26px; }
    .section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; min-height: 40px; }
    .section-search-wrap { display: flex; align-items: center; gap: 8px; background: #f5f7fa; border: 1.5px solid #2FAEE0; border-radius: 10px; padding: 7px 12px; margin-bottom: 14px; transition: background 0.15s; }
    .section-search-wrap:focus-within { background: #fff; }
    .section-search { flex: 1; border: none; background: transparent; font-size: 13px; color: #0a0f1e; outline: none; }
    .section-search::placeholder { color: #c0c6d4; }
    .search-clear-btn { background: none; border: none; cursor: pointer; color: #c0c6d4; font-size: 12px; padding: 0 0 0 4px; line-height: 1; display: none; transition: color 0.15s; }
    .search-clear-btn:hover { color: #6b7280; }
    .search-clear-btn.visible { display: block; }
    .section-icon { flex-shrink: 0; display: flex; align-items: center; opacity: 0.7; }
    h2 { font-size: 16px; font-weight: 600; color: #0a0f1e; white-space: nowrap; letter-spacing: -0.2px; }
    .count-badge { background: #eff4ff; border: 1px solid #c3d3f7; color: #2FAEE0; font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 980px; }

    /* Filtres pill Apple */
    .filter-bar { display: flex; gap: 4px; flex-wrap: wrap; }
    .filter-btn { padding: 5px 13px; border-radius: 980px; border: 1px solid #dde1e8; background: #ffffff; color: #374151; font-size: 11px; font-weight: 500; cursor: pointer; transition: all 0.15s ease; white-space: nowrap; }
    .filter-btn:hover { background: #f5f7fa; border-color: #c5cad3; }
    .filter-btn.active { background: #2FAEE0; border-color: #2FAEE0; color: #ffffff; box-shadow: 0 1px 4px rgba(0,87,168,0.3); }
    .sort-toggle-btn { padding: 5px 13px; border-radius: 980px; border: 1px solid #dde1e8; background: #ffffff; color: #374151; font-size: 11px; font-weight: 500; cursor: pointer; transition: all 0.15s ease; white-space: nowrap; }
    .sort-toggle-btn:hover { background: #f5f7fa; border-color: #2FAEE0; color: #2FAEE0; }


    /* Réservées */
    .reservations-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; padding: 6px; }
    .reservation-card { display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; background: #f7f9fc; border: 1px solid #edf0f5; transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.25s ease; }
    .reservation-card:hover { transform: translateY(-6px) scale(1.04); box-shadow: 0 20px 45px rgba(0,0,0,0.13); }
    .res-photo { width: 100%; height: 140px; object-fit: cover; display: block; }
    .res-photo-placeholder { width: 100%; height: 80px; background: #e5e9f0; }
    .res-info { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 14px; }
    .res-header-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
    .res-header .car-name { font-size: 13px; line-height: 1.4; flex: 1; }
    .bc-badge { flex-shrink: 0; font-size: 10px; font-weight: 600; color: #9ca3af; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px; padding: 2px 7px; letter-spacing: 0.4px; font-family: 'SF Mono', ui-monospace, monospace; white-space: nowrap; margin-top: 1px; }
    .res-footer { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 2px; }
    .commercial-badge { display: inline-block; padding: 3px 11px; border-radius: 980px; background: #eff4ff; border: 1px solid #c3d3f7; color: #2FAEE0; font-size: 11px; font-weight: 600; }
    .fck-badge { font-size: 26px; opacity: 1; margin-left: 6px; display: inline-block; vertical-align: middle; }
    .res-amounts { display: flex; gap: 14px; flex-wrap: wrap; }
    .res-prix { font-size: 12px; color: #6b7280; }
    .res-marge { font-size: 12px; color: #2FAEE0; font-weight: 700; }
    .fiche-btn { display: inline-flex; align-items: center; padding: 7px 14px; background: #2FAEE0; border: none; color: #ffffff; border-radius: 980px; text-decoration: none; font-size: 11px; font-weight: 600; transition: background 0.2s ease, transform 0.2s ease; }
    .fiche-btn:hover { background: #003f7a; transform: translateY(-1px); }

    /* CT */
    .ct-table-header { display: grid; grid-template-columns: 2fr 1.5fr 1.5fr 1fr 1fr 1fr 90px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.09em; color: #adb5c2; padding: 0 14px 10px; font-weight: 600; }
    .ct-row { display: grid; grid-template-columns: 2fr 1.5fr 1.5fr 1fr 1fr 1fr 90px; padding: 11px 14px; border-radius: 10px; margin-bottom: 4px; border-left: 3px solid transparent; background: #f7f9fc; border-top: 1px solid #edf0f5; border-right: 1px solid #edf0f5; border-bottom: 1px solid #edf0f5; align-items: center; transition: background 0.15s; }
    .ct-row:hover { background: #eff4ff; }
    .ct-expire   { border-left-color: #ef4444; }
    .ct-manquant { border-left-color: #f97316; }
    .ct-bientot  { border-left-color: #eab308; }
    .ct-ok       { border-left-color: #22c55e; }
    .ct-date { font-size: 12px; color: #6b7280; }
    .statut-pill { font-size: 10px; padding: 3px 9px; border-radius: 980px; background: #eff4ff; color: #2FAEE0; font-weight: 500; white-space: nowrap; }
    .ct-status-badge { font-size: 11px; padding: 3px 9px; border-radius: 980px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }
    .ct-expire-badge   { background: #fee2e2; color: #dc2626; }
    .ct-manquant-badge { background: #ffedd5; color: #ea580c; }
    .ct-bientot-badge  { background: #fef9c3; color: #a16207; }
    .ct-ok-badge       { background: #d1fae5; color: #059669; }
    .jul { font-size: 13px; line-height: 1; display: inline-block; vertical-align: middle; }
    .jours-expire  { color: #dc2626; font-weight: 700; font-size: 12px; }
    .jours-bientot { color: #a16207; font-weight: 700; font-size: 12px; }
    .jours-ok      { color: #059669; font-weight: 700; font-size: 12px; }
    .jours-manquant{ color: #adb5c2; font-size: 12px; }
    .fiche-btn-sm { padding: 5px 11px; border-radius: 980px; background: #eff4ff; border: 1px solid #c3d3f7; color: #2FAEE0; text-decoration: none; font-size: 11px; font-weight: 600; transition: all 0.15s; white-space: nowrap; display: inline-block; }
    .fiche-btn-sm:hover { background: #dbeafe; }

    /* Frais */
    .frais-container { display: flex; flex-direction: column; gap: 12px; }
    .car-frais-block { border-radius: 12px; overflow: hidden; border: 1px solid #edf0f5; }
    .car-frais-header { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #f7f9fc; border-bottom: 1px solid #edf0f5; }
    .car-thumb { width: 56px; height: 42px; object-fit: cover; border-radius: 8px; flex-shrink: 0; }
    .car-thumb-placeholder { width: 56px; height: 42px; border-radius: 8px; background: #e5e9f0; flex-shrink: 0; }
    .car-frais-name { font-weight: 600; color: #0a0f1e; font-size: 13px; flex: 1; }
    .car-frais-name-text { font-weight: 600; color: #0a0f1e; font-size: 13px; }
    .car-frais-total { font-size: 13px; color: #dc2626; font-weight: 700; white-space: nowrap; }
    .frais-list { padding: 4px; background: #ffffff; }
    .frais-row { display: grid; grid-template-columns: 90px 1fr auto; padding: 7px 10px; border-radius: 8px; gap: 10px; font-size: 12px; color: #6b7280; }
    .frais-row:hover { background: #f7f9fc; }
    .frais-date { color: #adb5c2; }
    .frais-montant { color: #dc2626; font-weight: 700; white-space: nowrap; }
    .airtable-link { color: #dc2626; text-decoration: none; }
    .airtable-link:hover { text-decoration: underline; }

    /* Divers */
    .empty-state { text-align: center; padding: 40px 0; color: #adb5c2; font-size: 13px; }
    .footer { text-align: center; padding: 28px; color: #c5cad3; font-size: 11px; letter-spacing: 0.04em; margin-top: 16px; }

    @media (max-width: 1100px) {
      .ct-table-header, .ct-row { grid-template-columns: 2fr 1.2fr 1.2fr 0.8fr 0.8fr 0.8fr 80px; }
    }
    @media (max-width: 1024px) {
      .grid { grid-template-columns: 1fr 1fr; }
      .col-span-2 { grid-column: span 2; }
      .col-span-3 { grid-column: span 2; }
      .kpi-row { grid-template-columns: repeat(2,1fr); }
    }
    @media (max-width: 640px) {
      .grid, .kpi-row { grid-template-columns: 1fr; }
      .col-span-2, .col-span-3 { grid-column: span 1; }
    }

    /* ── Modal voiture réservée ─────────────────────────────────────── */
    .res-modal-overlay {
      display: none; position: fixed; inset: 0; z-index: 1000;
      background: rgba(10,14,26,0.72); backdrop-filter: blur(6px);
      align-items: center; justify-content: center;
    }
    .res-modal-overlay.open { display: flex; animation: modalFadeIn 0.2s ease; }
    @keyframes modalFadeIn { from { opacity: 0; } to { opacity: 1; } }
    .res-modal-card {
      position: relative; background: #fff; border-radius: 22px;
      overflow: hidden; width: min(560px, 92vw);
      box-shadow: 0 40px 100px rgba(0,0,0,0.35);
      animation: modalSlideUp 0.25s cubic-bezier(0.34,1.4,0.64,1);
    }
    @keyframes modalSlideUp { from { transform: scale(0.88) translateY(24px); opacity: 0; } to { transform: scale(1) translateY(0); opacity: 1; } }
    .res-modal-close {
      position: absolute; top: 14px; right: 14px; z-index: 10;
      width: 32px; height: 32px; border-radius: 50%; border: none;
      background: rgba(0,0,0,0.45); color: #fff; font-size: 14px;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }
    .res-modal-close:hover { background: rgba(0,0,0,0.65); }
    .res-modal-photo { width: 100%; height: 300px; object-fit: cover; display: block; }
    .res-modal-body { padding: 22px 24px 26px; display: flex; flex-direction: column; gap: 16px; }
    .res-modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
    .res-modal-name { font-size: 18px; font-weight: 700; color: #111827; line-height: 1.35; flex: 1; }
    .res-modal-bc { font-size: 11px; margin-top: 3px; }
    .res-modal-amounts { display: flex; gap: 20px; }
    .res-modal-amount-block { display: flex; flex-direction: column; gap: 2px; }
    .res-modal-label { font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .res-modal-value-prix { font-size: 20px; font-weight: 700; color: #111827; }
    .res-modal-value-marge { font-size: 20px; font-weight: 700; color: #2FAEE0; }
    .res-modal-commerciaux { display: flex; gap: 8px; flex-wrap: wrap; }
    .res-modal-actions { display: flex; gap: 10px; flex-wrap: wrap; }
    .res-modal-fiche-btn { align-self: flex-start; }
    .reservation-card { cursor: pointer; }
    /* Badge CT sur cartes réservées */
    .ct-res-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 980px; font-size: 11px; font-weight: 600; margin-top: 5px; }
    /* Bouton Travaux */
    .fiche-btn-travaux { background: #f3f4f6 !important; color: #374151 !important; border: 1px solid #d1d5db; }
    .fiche-btn-travaux:hover { background: #e5e7eb !important; color: #111827 !important; transform: translateY(-1px); }

    /* ── Prestataires ──────────────────────────────────────────────────── */
    .prest-section { padding: 22px 26px; }
    .prest-add-btn {
      display: inline-flex; align-items: center; gap: 5px;
      padding: 6px 16px; background: #2FAEE0; border: none; border-radius: 980px;
      color: #fff; font-size: 12px; font-weight: 600; cursor: pointer;
      transition: background 0.2s ease, transform 0.15s ease;
    }
    .prest-add-btn:hover { background: #003f7a; transform: translateY(-1px); }

    .prest-controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
    .prest-search-wrap { flex: 1; max-width: 480px; }
    .prest-filter-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }

    /* Groupes */
    .prest-group { margin-bottom: 24px; }
    .prest-group:last-child { margin-bottom: 0; }
    .prest-group-header {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 14px; margin-bottom: 12px;
      background: #f7f9fc; border-radius: 10px;
      border: 1px solid #edf0f5;
    }
    .prest-group-name { font-size: 13px; font-weight: 700; letter-spacing: -0.1px; }
    .prest-group-count {
      font-size: 11px; font-weight: 600; padding: 1px 8px;
      border-radius: 980px; background: rgba(0,0,0,0.06); color: #6b7280;
    }

    /* Cards */
    .prest-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
    }
    .prest-card {
      position: relative; border-radius: 12px; overflow: hidden;
      background: #fff; border: 1px solid #edf0f5;
      transition: transform 0.2s cubic-bezier(0.34,1.4,0.64,1), box-shadow 0.2s ease;
    }
    .prest-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.1); }
    .prest-card-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
    .prest-card-body { padding: 14px 14px 12px; display: flex; flex-direction: column; gap: 8px; }
    .prest-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 6px; }
    .prest-card-pills { display: flex; flex-wrap: wrap; gap: 4px; flex: 1; }
    .prest-type-pill {
      font-size: 10px; font-weight: 600; padding: 2px 8px;
      border-radius: 980px; border: 1px solid transparent; white-space: nowrap;
    }
    .prest-marque-pill {
      font-size: 10px; padding: 2px 8px; border-radius: 980px;
      background: #f3f4f6; color: #6b7280; border: 1px solid #e5e7eb; white-space: nowrap;
    }
    .prest-card-name { font-size: 14px; font-weight: 700; color: #111827; line-height: 1.3; }
    .prest-stars { display: inline-flex; gap: 1px; font-size: 13px; flex-shrink: 0; }
    .star-on  { color: #f59e0b; }
    .star-off { color: #e5e7eb; }
    .prest-contacts { display: flex; flex-direction: column; gap: 4px; }
    .prest-contact-item { display: flex; align-items: flex-start; gap: 6px; font-size: 11px; line-height: 1.4; }
    .pci-icon { flex-shrink: 0; font-size: 11px; opacity: 0.7; }
    .pci-link { color: #2FAEE0; text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px; }
    .pci-link:hover { text-decoration: underline; }
    .pci-text { color: #6b7280; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px; }
    .prest-marques { display: flex; flex-wrap: wrap; gap: 4px; }
    .prest-notes {
      font-size: 11px; color: #9ca3af; line-height: 1.4;
      overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }
    .prest-empty { padding: 48px 24px; color: #ea580c; font-size: 13px; font-weight: 500; }

    /* ── Modal ajout prestataire ────────────────────────────────────────── */
    .prest-modal-overlay {
      display: none; position: fixed; inset: 0; z-index: 1001;
      background: rgba(10,14,26,0.72); backdrop-filter: blur(6px);
      align-items: center; justify-content: center; overflow-y: auto; padding: 24px;
    }
    .prest-modal-overlay.open { display: flex; animation: modalFadeIn 0.2s ease; }
    .prest-modal-card {
      position: relative; background: #fff; border-radius: 20px;
      width: min(640px, 94vw); max-height: calc(100vh - 48px); overflow-y: auto;
      box-shadow: 0 40px 100px rgba(0,0,0,0.35);
      animation: modalSlideUp 0.25s cubic-bezier(0.34,1.4,0.64,1);
    }
    .prest-modal-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 22px 24px 0; position: sticky; top: 0; background: #fff;
      z-index: 2; border-radius: 20px 20px 0 0;
    }
    .prest-modal-header h3 { font-size: 17px; font-weight: 700; color: #111827; }
    .prest-modal-close {
      width: 30px; height: 30px; border-radius: 50%; border: none;
      background: #f3f4f6; color: #6b7280; font-size: 13px;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }
    .prest-modal-close:hover { background: #e5e7eb; color: #111827; }
    #prest-add-form { padding: 20px 24px 24px; display: flex; flex-direction: column; gap: 14px; }
    .pf-row { display: flex; flex-direction: column; gap: 5px; }
    .pf-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .pf-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
    .pf-input {
      padding: 9px 12px; border: 1.5px solid #e5e7eb; border-radius: 10px;
      font-size: 13px; color: #111827; outline: none; background: #f9fafb;
      transition: border-color 0.15s, background 0.15s;
    }
    .pf-input:focus { border-color: #2FAEE0; background: #fff; }
    .pf-textarea { resize: vertical; min-height: 72px; font-family: inherit; }
    .pf-marques-wrap {
      display: flex; flex-wrap: wrap; gap: 6px;
      padding: 10px; background: #f9fafb; border: 1.5px solid #e5e7eb;
      border-radius: 10px; max-height: 120px; overflow-y: auto;
    }
    .pf-marque-check { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #374151; cursor: pointer; white-space: nowrap; }
    .pf-marque-check input { cursor: pointer; accent-color: #2FAEE0; }
    /* Stars input form */
    .pf-stars-input { display: flex; gap: 4px; }
    .pf-star { font-size: 22px; color: #e5e7eb; cursor: pointer; transition: color 0.1s, transform 0.1s; line-height: 1; }
    .pf-star:hover, .pf-star-hover { color: #f59e0b; transform: scale(1.15); }
    .pf-star-on { color: #f59e0b; }
    .pf-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; padding-top: 14px; border-top: 1px solid #f0f2f5; }
    .pf-cancel-btn {
      padding: 10px 20px; border-radius: 980px; border: 1.5px solid #e5e7eb;
      background: #fff; color: #374151; font-size: 13px; font-weight: 600; cursor: pointer;
      transition: all 0.15s;
    }
    .pf-cancel-btn:hover { background: #f3f4f6; }
    .pf-submit-btn {
      padding: 10px 24px; border-radius: 980px; border: none;
      background: #2FAEE0; color: #fff; font-size: 13px; font-weight: 700; cursor: pointer;
      transition: background 0.2s ease, transform 0.15s ease;
    }
    .pf-submit-btn:hover:not(:disabled) { background: #003f7a; transform: translateY(-1px); }
    .pf-submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
    """
