/** @type {import('next').NextConfig} */
const BACKEND = process.env.API_PROXY_TARGET || 'http://localhost:8001';

const nextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true,
  },
  rewrites: async () => [
    { source: '/auth/:path*', destination: `${BACKEND}/auth/:path*` },
    { source: '/query/:path*', destination: `${BACKEND}/query/:path*` },
    { source: '/chat/:path*', destination: `${BACKEND}/chat/:path*` },
    { source: '/chat-history', destination: `${BACKEND}/chat-history` },
    { source: '/chat-images', destination: `${BACKEND}/chat-images` },
    { source: '/chat-images/:path*', destination: `${BACKEND}/chat-images/:path*` },
    { source: '/query-stream', destination: `${BACKEND}/query-stream` },
    { source: '/courses/:path*', destination: `${BACKEND}/courses/:path*` },
    { source: '/curriculum/:path*', destination: `${BACKEND}/curriculum/:path*` },
    { source: '/flashcards', destination: `${BACKEND}/flashcards` },
    { source: '/flashcards/:path*', destination: `${BACKEND}/flashcards/:path*` },
    { source: '/quiz', destination: `${BACKEND}/quiz` },
    { source: '/quiz/:path*', destination: `${BACKEND}/quiz/:path*` },
    { source: '/analytics/:path*', destination: `${BACKEND}/analytics/:path*` },
    { source: '/admin/:path*', destination: `${BACKEND}/admin/:path*` },
    { source: '/users/:path*', destination: `${BACKEND}/users/:path*` },
    { source: '/scheduler/:path*', destination: `${BACKEND}/scheduler/:path*` },
    { source: '/tasks/:path*', destination: `${BACKEND}/tasks/:path*` },
    { source: '/materials/:path*', destination: `${BACKEND}/materials/:path*` },
    { source: '/api/:path*', destination: `${BACKEND}/api/:path*` },
    { source: '/ingest', destination: `${BACKEND}/ingest` },
    { source: '/chunks', destination: `${BACKEND}/chunks` },
    { source: '/health', destination: `${BACKEND}/health` },
    { source: '/generate-paper', destination: `${BACKEND}/generate-paper` },
    { source: '/questions', destination: `${BACKEND}/questions` },
    { source: '/stats', destination: `${BACKEND}/stats` },
  ],
};

export default nextConfig;
