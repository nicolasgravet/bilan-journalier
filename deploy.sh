#!/bin/bash
# Génère le rapport et le publie sur Netlify
cd "$(dirname "$0")"

export PATH="/Users/nico/.npm-global/bin:$PATH"
export REPORT_PATH="./public/index.html"

mkdir -p public

echo "$(date) — Génération du rapport..."
/usr/local/bin/python3 generate_report.py

echo "$(date) — Déploiement sur Netlify..."
netlify deploy --prod --dir=public --json > /dev/null 2>&1 && \
  echo "$(date) — ✅ En ligne : https://mecanicus-bilan.netlify.app" || \
  echo "$(date) — ❌ Erreur lors du déploiement"
