from datetime import datetime

JOURS_FR = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
MOIS_FR  = ["janvier","février","mars","avril","mai","juin",
             "juillet","août","septembre","octobre","novembre","décembre"]

def generate_html(offres, reservees, frais_by_car, ct_data=None, car_photos=None, francois_cars=None):
    now = datetime.utcnow()
    gen_ts = int(now.timestamp())  # timestamp UTC → JS le convertit en heure locale
    date_str = f"{JOURS_FR[now.weekday()]} {now.day} {MOIS_FR[now.month-1]} {now.year}"
    time_str = now.strftime("%H:%M")
    ct_data = ct_data or []
    car_photos = car_photos or {}
    francois_cars = francois_cars or set()

    import json as _json
    # CT global = toutes les voitures non-réservées (visibles dans "Tous")
    ct_alert_count = sum(1 for c in ct_data if c.get("ct_filter_type") not in ("acompte", "acompte-ok"))
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
    <div class="glass-card kpi">
      <div class="kpi-icon-wrap kpi-orange">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="kpi-body">
        <div class="kpi-value">{ct_alert_count}</div>
        <div class="kpi-label">Alertes CT — Global</div>
      </div>
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
            <button class="filter-btn" data-days="7">7j</button>
            <button class="filter-btn" data-days="3">3j</button>
            <button class="filter-btn" data-days="1">1j</button>
          </div>
          <div class="filter-bar frais-statut-filter">
            <button class="filter-btn active" data-frais-statut="tous">Tous</button>
            <button class="filter-btn" data-frais-statut="reservees">Réservées</button>
          </div>
        </div>
        <button class="collapse-btn" id="collapse-frais">▼</button>
      </div>
      <div class="section-body" id="body-frais" style="display:none">
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
        <button class="collapse-btn" id="collapse-ct">▼</button>
      </div>
      <div class="section-body" id="body-ct" style="display:none">
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
        <div class="header-filters"></div>
        <button class="collapse-btn" id="collapse-reservees">▼</button>
      </div>
      <div class="section-body" id="body-reservees" style="display:none">
        <div class="section-search-wrap" onclick="event.stopPropagation()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#adb5c2" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" class="section-search" id="search-reservees" placeholder="Rechercher une voiture…" oninput="filterBySearch('reservees', this.value)" autocomplete="off">
          <button class="search-clear-btn" onclick="clearSearch('reservees')">✕</button>
        </div>
        {_render_reservees(reservees, francois_cars)}
      </div>
    </section>

  </div>

  <footer class="footer">
    Généré le {date_str} à {time_str} · Données Slack & Airtable · Rafraîchissement quotidien à 19h
  </footer>
</div>
<script>var MARGES_DATA = {marges_data};</script>
<script>{_js()}</script>
</body>
</html>"""


# ─── Renderers ────────────────────────────────────────────────────────────────

def _render_reservees(reservees, francois_cars=None):
    francois_cars = francois_cars or set()
    if not reservees:
        return '<div class="empty-state">Aucune voiture réservée</div>'
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
        items += f"""<div class="reservation-card">
          {photo_html}
          <div class="res-info">
            <div class="res-header">
              <span class="car-name">{voiture}{fck}</span>
            </div>
            <div class="res-amounts">
              <span class="res-prix">Prix : <strong>{r.get('prix_fmt','—')}</strong></span>
              <span class="res-marge">Marge : <strong>{r.get('marge_fmt','—')}</strong></span>
            </div>
            <div class="res-footer">
              <a class="fiche-btn" href="{r.get('fiche_url','#')}" target="_blank">Accéder à la fiche →</a>
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
  var collapsed = body.style.display === 'none';
  body.style.display = collapsed ? '' : 'none';
  if (btn) btn.textContent = collapsed ? '▲' : '▼';
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
    .kpi-icon-wrap { width: 52px; height: 52px; border-radius: 14px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
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
    .collapse-btn { background: none; border: 1px solid #dde1e8; border-radius: 8px; color: #adb5c2; font-size: 11px; padding: 4px 10px; cursor: pointer; transition: all 0.15s ease; flex-shrink: 0; }

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


    /* Réservées */
    .reservations-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
    .reservation-card { display: flex; flex-direction: column; border-radius: 14px; overflow: hidden; background: #f7f9fc; border: 1px solid #edf0f5; transition: transform 0.22s ease, box-shadow 0.22s ease; }
    .reservation-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(0,0,0,0.1); }
    .res-photo { width: 100%; height: 140px; object-fit: cover; display: block; }
    .res-photo-placeholder { width: 100%; height: 80px; background: #e5e9f0; }
    .res-info { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 14px; }
    .res-header .car-name { font-size: 13px; line-height: 1.4; }
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
    """
