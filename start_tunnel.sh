#!/bin/bash
# Démarre server.py + tunnel Cloudflare, puis met à jour Netlify avec la nouvelle URL

export PATH="/Users/nico/.npm-global/bin:$PATH"
DIR="$(dirname "$0")"
LOG="$DIR/logs/tunnel.log"
mkdir -p "$DIR/logs"

# Tuer les anciens processus
pkill -f "server.py" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 2

# Démarrer le serveur Python
/usr/local/bin/python3 "$DIR/server.py" >> "$LOG" 2>&1 &
echo "$(date) — serveur.py démarré" >> "$LOG"

# Démarrer le tunnel Cloudflare
rm -f /tmp/cf_tunnel.log
/Users/nico/.npm-global/bin/cloudflared tunnel --url http://localhost:8080 \
  --logfile /tmp/cf_tunnel.log >> "$LOG" 2>&1 &

# Attendre que l'URL apparaisse (max 30s)
echo "$(date) — attente URL tunnel..." >> "$LOG"
for i in $(seq 1 30); do
    TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_tunnel.log 2>/dev/null | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo "$(date) — URL tunnel : $TUNNEL_URL" >> "$LOG"
        break
    fi
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    echo "$(date) — ERREUR: URL tunnel non trouvée" >> "$LOG"
    exit 1
fi

# Mettre à jour Netlify avec une page de redirection
mkdir -p "$DIR/public"
cat > "$DIR/public/index.html" << EOF
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=$TUNNEL_URL">
  <title>Tracking Logistique — Mecanicus</title>
  <style>
    body { font-family: -apple-system, sans-serif; display: flex; align-items: center;
           justify-content: center; height: 100vh; margin: 0; background: #eef1f6; }
    .card { background: white; border-radius: 18px; padding: 40px; text-align: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
    .logo { font-size: 22px; font-weight: 700; color: #0a0f1e; margin-bottom: 16px; }
    p { color: #6b7280; font-size: 14px; }
    a { color: #2FAEE0; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">MECANICUS</div>
    <p>Redirection vers le tableau de bord…</p>
    <p><a href="$TUNNEL_URL">Cliquer ici si la redirection ne fonctionne pas</a></p>
  </div>
  <script>window.location.href = "$TUNNEL_URL";</script>
</body>
</html>
EOF

# Déployer sur Netlify
netlify deploy --prod --dir="$DIR/public" --site=6f7a10e7-97c7-4d54-b3b2-e2caf7f28c43 >> "$LOG" 2>&1 && \
    echo "$(date) — ✅ Netlify mis à jour → https://mecanicus-bilan.netlify.app" >> "$LOG" || \
    echo "$(date) — ❌ Erreur Netlify" >> "$LOG"
