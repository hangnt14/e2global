/**
 * server.js
 * Express test server for integration tests.
 * Serves 4 HTML pages + 1 API endpoint + robots.txt.
 * Starts on a random available port.
 */

import express from 'express';
import { createServer } from 'http';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function createTestServer() {
  const app = express();

  // Serve static HTML pages
  app.get('/', (req, res) => res.sendFile(join(__dirname, 'index.html')));
  app.get('/about', (req, res) => res.sendFile(join(__dirname, 'about.html')));
  app.get('/login', (req, res) => res.sendFile(join(__dirname, 'login.html')));
  app.get('/dashboard', (req, res) => res.sendFile(join(__dirname, 'dashboard.html')));

  // API endpoint
  app.get('/api/status', (req, res) => {
    res.json({ status: 'ok', version: '1.0' });
  });

  // robots.txt — disallow /admin
  app.get('/robots.txt', (req, res) => {
    res.type('text/plain').send('User-agent: *\nDisallow: /admin\n');
  });

  // 404 for everything else
  app.use((req, res) => res.status(404).send('Not found'));

  return new Promise((resolve) => {
    const server = createServer(app);
    // Port 0 = OS assigns random available port
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({
        url: `http://127.0.0.1:${port}`,
        port,
        close: () => new Promise((r) => server.close(r)),
      });
    });
  });
}
