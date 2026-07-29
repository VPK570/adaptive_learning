const { createServer } = require('http');
const { createProxyServer } = require('http-proxy');
const { spawn } = require('child_process');
const path = require('path');

const BACKEND = process.env.API_PROXY_TARGET || 'http://localhost:8001';
const NEXT_PORT = parseInt(process.env.NEXT_INTERNAL_PORT || '3001', 10);
const PROXY_PORT = parseInt(process.env.PORT || '3000', 10);

const proxy = createProxyServer({ proxyTimeout: 120000, timeout: 120000 });

const API_PREFIXES = [
  '/auth/', '/query/', '/chat/', '/chat-images', '/courses/', '/curriculum/',
  '/flashcards', '/quiz', '/paper', '/analytics/', '/admin/', '/users/',
  '/scheduler/', '/tasks/', '/materials/', '/api/', '/ingest', '/chunks',
  '/health', '/generate-paper', '/questions', '/stats', '/chat-history',
  '/query-stream', '/chat/feedback',
];

function isApi(pathname) {
  return API_PREFIXES.some(p => pathname === p || pathname.startsWith(p));
}

const nextServer = spawn('node', [path.join(__dirname, 'standalone/server.js')], {
  env: { ...process.env, PORT: String(NEXT_PORT), HOSTNAME: '0.0.0.0' },
  stdio: 'inherit',
});

process.on('exit', () => nextServer.kill());
process.on('SIGTERM', () => nextServer.kill());
process.on('SIGINT', () => nextServer.kill());

proxy.on('error', (err, req, res) => {
  if (res.writeHead) {
    try { res.writeHead(502, { 'Content-Type': 'text/plain' }); } catch (_) {}
    res.end('Bad Gateway');
  }
});

createServer((req, res) => {
  const parsedUrl = new URL(req.url, 'http://localhost');
  if (isApi(parsedUrl.pathname)) {
    proxy.web(req, res, { target: BACKEND });
  } else {
    proxy.web(req, res, { target: `http://localhost:${NEXT_PORT}` });
  }
}).on('upgrade', (req, socket, head) => {
  proxy.ws(req, socket, head, { target: BACKEND });
}).listen(PROXY_PORT, () => {
  console.log(`> Proxy ready on http://localhost:${PROXY_PORT} (Next.js: ${NEXT_PORT}, backend: ${BACKEND})`);
});
