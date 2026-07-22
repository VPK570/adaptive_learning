#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR/new_frontend"
CADDYFILE="/tmp/prod-Caddyfile"
COMPOSE_OVERRIDE="/tmp/dc-prod.yml"
CLOUDFLARED_LOG="/tmp/prod-cloudflared.log"
FRONTEND_PID=""
CADDY_PID=""
CLOUDFLARED_PID=""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[prod]${NC} $1"; }
warn()  { echo -e "${YELLOW}[prod]${NC} $1"; }
err()   { echo -e "${RED}[prod]${NC} $1"; }

install_cloudflared() {
    info "Installing cloudflared..."
    curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    info "cloudflared installed"
}

install_caddy() {
    info "Installing Caddy..."
    curl -sL "https://github.com/caddyserver/caddy/releases/latest/download/caddy_linux_amd64.tar.gz" -o /tmp/caddy.tar.gz
    tar -xzf /tmp/caddy.tar.gz -C /tmp caddy
    sudo mv /tmp/caddy /usr/local/bin/caddy
    info "Caddy installed"
}

wait_for_port() {
    local port=$1 name=$2 max=$3
    for i in $(seq 1 "$max"); do
        if curl -sf "http://localhost:$port" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

cleanup() {
    echo ""
    info "Shutting down..."
    [ -n "$CLOUDFLARED_PID" ] && kill "$CLOUDFLARED_PID" 2>/dev/null && info "Tunnel stopped"
    [ -n "$CADDY_PID" ]       && kill "$CADDY_PID" 2>/dev/null       && info "Caddy stopped"
    [ -n "$FRONTEND_PID" ]    && kill "$FRONTEND_PID" 2>/dev/null   && info "Frontend stopped"
    wait 2>/dev/null
    rm -f "$CADDYFILE" "$COMPOSE_OVERRIDE" "$CLOUDFLARED_LOG"
    info "Stopped. Docker services still running."
}
trap cleanup EXIT INT TERM

# ──────────────────────────────────────────────
# 1. Prereq check + auto-install
# ──────────────────────────────────────────────
info "Checking dependencies..."
command -v docker       >/dev/null 2>&1 || { err "docker is required"; exit 1; }
command -v node         >/dev/null 2>&1 || { err "node is required";  exit 1; }
command -v npm          >/dev/null 2>&1 || { err "npm is required";   exit 1; }
command -v cloudflared  >/dev/null 2>&1 || install_cloudflared
command -v caddy        >/dev/null 2>&1 || install_caddy

# ──────────────────────────────────────────────
# 2. Frontend deps
# ──────────────────────────────────────────────
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    info "Installing frontend dependencies..."
    cd "$FRONTEND_DIR" && npm ci
fi

# ──────────────────────────────────────────────
# 3. Caddyfile
# ──────────────────────────────────────────────
info "Creating reverse proxy config..."
cat > "$CADDYFILE" << 'CADDY'
:8080 {
    @backend {
        path /auth/* /health /query* /courses/* /curriculum* /chat-history* /ingest* /materials/* /flashcards* /quiz* /generate-paper* /chat-images* /analytics* /questions* /users/* /admin/* /api/* /tasks/* /scheduler/* /stats /chunks /docs* /openapi.json /redoc*
    }
    handle @backend {
        reverse_proxy localhost:8001
    }
    handle {
        reverse_proxy localhost:3000
    }
}
CADDY

# ──────────────────────────────────────────────
# 4. Docker-compose override for CORS
# ──────────────────────────────────────────────
cat > "$COMPOSE_OVERRIDE" << 'YAML'
services:
  backend:
    environment:
      - CORS_ORIGINS=*
YAML

# ──────────────────────────────────────────────
# 5. Start backend stack
# ──────────────────────────────────────────────
info "Starting backend services (SurrealDB, Redis, Backend, Worker)..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" -f "$COMPOSE_OVERRIDE" up -d surrealdb redis backend worker

# ──────────────────────────────────────────────
# 6. Free port 3000
# ──────────────────────────────────────────────
docker compose -f "$PROJECT_DIR/docker-compose.yml" stop frontend 2>/dev/null || true

# ──────────────────────────────────────────────
# 7. Build frontend (with empty API base = relative URLs)
# ──────────────────────────────────────────────
info "Building frontend (NEXT_PUBLIC_API_URL='')..."
cd "$FRONTEND_DIR"
NEXT_PUBLIC_API_URL='' npm run build

# ──────────────────────────────────────────────
# 8. Start frontend server
# ──────────────────────────────────────────────
info "Starting frontend server..."
NEXT_PUBLIC_API_URL='' npm start &
FRONTEND_PID=$!

if wait_for_port 3000 "Frontend" 30; then
    info "Frontend ready on http://localhost:3000"
else
    err "Frontend failed to start on port 3000"
    exit 1
fi

# ──────────────────────────────────────────────
# 9. Start Caddy
# ──────────────────────────────────────────────
info "Starting Caddy reverse proxy..."
caddy run --config "$CADDYFILE" &
CADDY_PID=$!

if wait_for_port 8080 "Caddy" 10; then
    info "Caddy ready on http://localhost:8080"
else
    err "Caddy failed to start on port 8080"
    exit 1
fi

# ──────────────────────────────────────────────
# 10. Start tunnel (background) + capture URL
# ──────────────────────────────────────────────
info "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8080 > "$CLOUDFLARED_LOG" 2>&1 &
CLOUDFLARED_PID=$!

URL=""
for i in $(seq 1 20); do
    URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "$CLOUDFLARED_LOG" 2>/dev/null || true)
    [ -n "$URL" ] && break
    sleep 1
done

if [ -n "$URL" ]; then
    echo ""
    echo -e "${CYAN}  ┌──────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}  │  ${GREEN}✨ Share this URL with anyone!${NC}              │${NC}"
    echo -e "${CYAN}  │                                          │${NC}"
    echo -e "${CYAN}  │  ${NC}$URL${NC}  │"
    echo -e "${CYAN}  │                                          │${NC}"
    echo -e "${CYAN}  │  Your laptop must stay on.               │${NC}"
    echo -e "${CYAN}  │  Press ${RED}Ctrl+C${NC} to stop.                        │${NC}"
    echo -e "${CYAN}  └──────────────────────────────────────────┘${NC}"
    echo ""
else
    warn "Could not detect tunnel URL. Check: tail -f $CLOUDFLARED_LOG"
    echo ""
fi

# ──────────────────────────────────────────────
# 11. Wait for tunnel process
# ──────────────────────────────────────────────
wait "$CLOUDFLARED_PID"
