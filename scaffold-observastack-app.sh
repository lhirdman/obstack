#!/usr/bin/env bash
set -euo pipefail
ROOT="observastack-app"
mkdir -p "$ROOT" && cd "$ROOT"

cat > README.md <<'MD'
# observastack-app (monorepo)

App monorepo for ObservaStack: **frontend** (React/TypeScript) + **bff** (FastAPI) + **contracts** + **e2e**.

## Quickstart (dev)
```bash
# Frontend
yarn --version >/dev/null 2>&1 || npm i -g yarn >/dev/null || true
cd frontend && npm i && npm run dev

# BFF
cd ../bff && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload
```
MD

cat > .gitignore <<'GI'
node_modules/
dist/
.build/
.cache/
.vscode/
.idea/
.DS_Store
.env*
**/__pycache__/
**/.pytest_cache/
**/.venv/
**/*.pyc
coverage/
e2e/.cache/
GI

mkdir -p contracts e2e
cat > contracts/openapi.yaml <<'YAML'
openapi: 3.0.3
info:
  title: ObservaStack BFF API
  version: 0.1.0
paths:
  /api/meta/flags:
    get:
      summary: Edition flags
      responses:
        '200': { description: OK }
  /api/auth/login:
    post:
      summary: Local login (Community)
      responses:
        '200': { description: Tokens }
  /api/auth/refresh:
    post:
      summary: Refresh access token
      responses:
        '200': { description: Tokens }
  /api/auth/jwks:
    get:
      summary: JWKS (Community mode)
      responses:
        '200': { description: JWKS }
  /api/search:
    post:
      summary: Unified search
      responses:
        '200': { description: Search results }
  /api/search/stream:
    get:
      summary: Stream log results (SSE)
      responses:
        '200': { description: Stream }
  /api/alerts:
    get:
      summary: List alerts
      responses:
        '200': { description: Alerts }
  /api/alerts/inbox:
    post:
      summary: Webhook ingest (Alertmanager/Loki)
      responses:
        '202': { description: Accepted }
  /api/alerts/{id}/ack:
    post:
      summary: Acknowledge alert
      responses:
        '200': { description: OK }
  /api/alerts/{id}/assign:
    post:
      summary: Assign alert
      responses:
        '200': { description: OK }
  /api/alerts/{id}/resolve:
    post:
      summary: Resolve alert
      responses:
        '200': { description: OK }
components: {}
YAML

# --- frontend (React + Vite + TS)
mkdir -p frontend/src/{shell,views}
cat > frontend/package.json <<'JSON'
{
  "name": "observastack-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.4",
    "vite": "^5.4.2"
  }
}
JSON

cat > frontend/index.html <<'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ObservaStack</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTML

cat > frontend/tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "strict": true,
    "skipLibCheck": true
  }
}
JSON

cat > frontend/vite.config.ts <<'TS'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: { '/api': 'http://localhost:8000', '/grafana': 'http://localhost:3001' } }
})
TS

cat > frontend/src/main.tsx <<'TSX'
import React from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import App from './shell/App'
import Search from './views/Search'
import Alerts from './views/Alerts'
import Insights from './views/Insights'
import Admin from './views/Admin'

const router = createBrowserRouter([
  { path: '/', element: <App />, children: [
    { path: '/', element: <Search /> },
    { path: '/search', element: <Search /> },
    { path: '/alerts', element: <Alerts /> },
    { path: '/insights', element: <Insights /> },
    { path: '/admin', element: <Admin /> }
  ]}
])

const root = createRoot(document.getElementById('root')!)
root.render(<RouterProvider router={router} />)
TSX

cat > frontend/src/shell/App.tsx <<'TSX'
import React from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
export default function App() {
  const loc = useLocation()
  return (
    <div style={{display:'grid', gridTemplateColumns:'240px 1fr', height:'100vh'}}>
      <aside style={{borderRight:'1px solid #eee', padding:'12px'}}>
        <div style={{fontWeight:700, marginBottom:12}}>ObservaStack</div>
        <nav style={{display:'grid', gap:8}}>
          <Link to="/search">Search</Link>
          <Link to="/alerts">Alerts</Link>
          <Link to="/insights">Insights</Link>
          <Link to="/admin">Admin</Link>
        </nav>
        <div style={{marginTop:16, fontSize:12, color:'#666'}}>Route: {loc.pathname}</div>
      </aside>
      <main style={{padding:'16px'}}>
        <Outlet />
      </main>
    </div>
  )
}
TSX

cat > frontend/src/views/Search.tsx <<'TSX'
import React, { useState } from 'react'
export default function Search() {
  const [q, setQ] = useState('')
  const [type, setType] = useState<'logs'|'metrics'|'traces'>('logs')
  const [results, setResults] = useState<any[]>([])
  const onSearch = async () => {
    const res = await fetch('/api/search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ freeText: q, type }) })
    const data = await res.json()
    setResults(data.items || [])
  }
  return (
    <div>
      <h1>Unified Search</h1>
      <div style={{display:'flex', gap:8}}>
        <input placeholder="free text" value={q} onChange={e=>setQ(e.target.value)} />
        <select value={type} onChange={e=>setType(e.target.value as any)}>
          <option value="logs">logs</option>
          <option value="metrics">metrics</option>
          <option value="traces">traces</option>
        </select>
        <button onClick={onSearch}>Search</button>
      </div>
      <ul>
        {results.map((r, i) => <li key={i}><code>{JSON.stringify(r)}</code></li>)}
      </ul>
    </div>
  )
}
TSX

cat > frontend/src/views/Alerts.tsx <<'TSX'
import React, { useEffect, useState } from 'react'
export default function Alerts() {
  const [items, setItems] = useState<any[]>([])
  useEffect(()=>{ fetch('/api/alerts').then(r=>r.json()).then(d=>setItems(d.items || [])) },[])
  return (
    <div>
      <h1>Alert Center</h1>
      <ul>
        {items.map((r, i) => <li key={i}><strong>{r.severity}</strong> {r.title}</li>)}
      </ul>
    </div>
  )
}
TSX

cat > frontend/src/views/Insights.tsx <<'TSX'
import React from 'react'
export default function Insights() {
  return (
    <div>
      <h1>Insights</h1>
      <p>Tiles coming soon (error rate, latency p95, noisy services).</p>
    </div>
  )
}
TSX

cat > frontend/src/views/Admin.tsx <<'TSX'
import React from 'react'
export default function Admin() {
  return (
    <div>
      <h1>Admin</h1>
      <p>Settings depend on edition & flags.</p>
    </div>
  )
}
TSX

cat > frontend/Dockerfile <<'DOCKER'
# Build
FROM node:20-bullseye as build
WORKDIR /app
COPY package.json .
RUN npm i --silent
COPY . .
RUN npm run build

# Serve
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
DOCKER

# --- bff (FastAPI)
mkdir -p bff/app
cat > bff/requirements.txt <<'REQ'
fastapi==0.111.1
uvicorn[standard]==0.30.5
python-jose[cryptography]==3.3.0
pydantic==2.8.2
httpx==0.27.0
REQ

cat > bff/app/main.py <<'PY'
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json, asyncio

app = FastAPI(title="ObservaStack BFF", version="0.1.0")

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/meta/flags")
def flags():
    return {"edition":"community","features":{"sso":False,"opensearch":False,"cost_insights":False}}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    return {"accessToken":"demo-token","refreshToken":"demo-refresh"}

@app.post("/api/auth/refresh")
def refresh():
    return {"accessToken":"demo-token-refreshed","refreshToken":"demo-refresh"}

@app.get("/api/auth/jwks")
def jwks():
    return {"keys":[{"kty":"oct","kid":"demo","k":"not-a-real-key"}]}

@app.post("/api/search")
def search():
    items = [{"message":"hello log line","service":"api"},{"message":"another line","service":"web"}]
    return {"items": items, "stats": {"matched": len(items), "scanned": 100, "latencyMs": 42}}

@app.get("/api/search/stream")
def search_stream():
    async def gen():
        for i in range(5):
            yield json.dumps({"line": f"chunk {i}"}) + "\n"
            await asyncio.sleep(0.3)
    return StreamingResponse(gen(), media_type="application/json")

@app.get("/api/alerts")
def alerts():
    items = [
        {"id":"a1","severity":"high","title":"CPU saturation"},
        {"id":"a2","severity":"medium","title":"Error rate spike"}
    ]
    return {"items": items}
PY

cat > bff/Dockerfile <<'DOCKER'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER

# --- CI (placeholder)
cat > .gitlab-ci.yml <<'CI'
stages: [test, build]

test:bff:
  image: python:3.12-slim
  stage: test
  script:
    - pip install -r bff/requirements.txt
    - python - <<'PY'
import importlib; importlib.import_module('fastapi'); print('fastapi ok')
PY

test:frontend:
  image: node:20-bullseye
  stage: test
  script:
    - cd frontend && npm i --silent && npm run build
CI

# --- bootstrap convenience
cat > bootstrap.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
REPO_URL="${1:-}"
if [[ -z "$REPO_URL" ]]; then
  echo "Usage: ./bootstrap.sh <git-remote-url>"; exit 1; fi
git init -b master
git add .
git commit -m "chore: initial scaffold (observastack-app)"
git remote add origin "$REPO_URL"
git push -u origin master
SH
chmod +x bootstrap.sh

echo "✓ observastack-app scaffolded."
