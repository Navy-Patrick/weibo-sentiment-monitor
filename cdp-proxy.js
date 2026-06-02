#!/usr/bin/env node
/**
 * CDP HTTP Proxy for weibo-sentiment-monitor.
 *
 * This proxy adapts the backend crawler's simple HTTP interface to Chrome's
 * native DevTools Protocol websocket API.
 *
 * Required backend endpoints:
 *   GET  /new?url=https://...
 *   POST /eval?target=<targetId>       body: JavaScript source
 *   GET  /scroll?target=<targetId>&y=3000
 *   GET  /close?target=<targetId>
 *   GET  /health
 *
 * Usage on macOS local development:
 *   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
 *     --remote-debugging-port=9222 \
 *     --user-data-dir=/tmp/weibo-cdp-profile
 *   node cdp-proxy.js
 *
 * Usage in Docker:
 *   - Run Chrome with remote debugging on the host or in another container.
 *   - Set CHROME_CDP_URL to that Chrome endpoint, for example:
 *       CHROME_CDP_URL=http://host.docker.internal:9222 node cdp-proxy.js
 *
 * Environment variables:
 *   CDP_PROXY_PORT       HTTP proxy listen port. Default: 3456
 *   CDP_PROXY_HOST       HTTP proxy listen host. Default: 0.0.0.0
 *   CHROME_CDP_URL       Native Chrome DevTools HTTP URL. Default: http://127.0.0.1:9222
 *   CDP_NAV_TIMEOUT_MS   Page navigation wait timeout. Default: 15000
 */

const http = require('http');
const net = require('net');
const crypto = require('crypto');
const { URL } = require('url');

const PROXY_PORT = Number(process.env.CDP_PROXY_PORT || 3456);
const PROXY_HOST = process.env.CDP_PROXY_HOST || '0.0.0.0';
const CHROME_CDP_URL = (process.env.CHROME_CDP_URL || 'http://127.0.0.1:9222').replace(/\/$/, '');
const NAV_TIMEOUT_MS = Number(process.env.CDP_NAV_TIMEOUT_MS || 15000);

const pages = new Map();
let commandId = 1;

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function chromeFetch(path, options = {}) {
  const targetUrl = new URL(path, CHROME_CDP_URL);
  const body = options.body || null;

  return new Promise((resolve, reject) => {
    const req = http.request(
      targetUrl,
      {
        method: options.method || 'GET',
        headers: body
          ? {
              'Content-Type': 'application/json',
              'Content-Length': Buffer.byteLength(body),
            }
          : undefined,
      },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(`Chrome CDP HTTP ${res.statusCode}: ${text}`));
            return;
          }
          try {
            resolve(text ? JSON.parse(text) : {});
          } catch (_) {
            resolve(text);
          }
        });
      }
    );
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function encodeWebSocketFrame(payload) {
  const data = Buffer.from(payload);
  const length = data.length;
  let header;

  if (length < 126) {
    header = Buffer.alloc(2);
    header[1] = 0x80 | length;
  } else if (length < 65536) {
    header = Buffer.alloc(4);
    header[1] = 0x80 | 126;
    header.writeUInt16BE(length, 2);
  } else {
    header = Buffer.alloc(10);
    header[1] = 0x80 | 127;
    header.writeBigUInt64BE(BigInt(length), 2);
  }

  header[0] = 0x81;
  const mask = crypto.randomBytes(4);
  const masked = Buffer.alloc(data.length);
  for (let i = 0; i < data.length; i += 1) {
    masked[i] = data[i] ^ mask[i % 4];
  }
  return Buffer.concat([header, mask, masked]);
}

function decodeWebSocketFrames(buffer) {
  const messages = [];
  let offset = 0;

  while (buffer.length - offset >= 2) {
    const first = buffer[offset];
    const second = buffer[offset + 1];
    const opcode = first & 0x0f;
    const masked = Boolean(second & 0x80);
    let length = second & 0x7f;
    let headerLength = 2;

    if (length === 126) {
      if (buffer.length - offset < 4) break;
      length = buffer.readUInt16BE(offset + 2);
      headerLength = 4;
    } else if (length === 127) {
      if (buffer.length - offset < 10) break;
      length = Number(buffer.readBigUInt64BE(offset + 2));
      headerLength = 10;
    }

    const maskLength = masked ? 4 : 0;
    const frameLength = headerLength + maskLength + length;
    if (buffer.length - offset < frameLength) break;

    let payload = buffer.slice(offset + headerLength + maskLength, offset + frameLength);
    if (masked) {
      const mask = buffer.slice(offset + headerLength, offset + headerLength + 4);
      const unmasked = Buffer.alloc(payload.length);
      for (let i = 0; i < payload.length; i += 1) {
        unmasked[i] = payload[i] ^ mask[i % 4];
      }
      payload = unmasked;
    }

    if (opcode === 0x1) {
      messages.push(payload.toString('utf8'));
    }

    offset += frameLength;
  }

  return { messages, remaining: buffer.slice(offset) };
}

class CdpSocket {
  constructor(webSocketDebuggerUrl) {
    this.url = new URL(webSocketDebuggerUrl);
    this.socket = null;
    this.buffer = Buffer.alloc(0);
    this.pending = new Map();
  }

  connect() {
    return new Promise((resolve, reject) => {
      const key = crypto.randomBytes(16).toString('base64');
      const port = Number(this.url.port || 80);
      const socket = net.createConnection({ host: this.url.hostname, port }, () => {
        socket.write(
          `GET ${this.url.pathname}${this.url.search} HTTP/1.1\r\n` +
            `Host: ${this.url.host}\r\n` +
            'Upgrade: websocket\r\n' +
            'Connection: Upgrade\r\n' +
            `Sec-WebSocket-Key: ${key}\r\n` +
            'Sec-WebSocket-Version: 13\r\n\r\n'
        );
      });

      let handshake = Buffer.alloc(0);
      let connected = false;

      socket.on('data', (chunk) => {
        if (!connected) {
          handshake = Buffer.concat([handshake, chunk]);
          const marker = handshake.indexOf('\r\n\r\n');
          if (marker === -1) return;

          const header = handshake.slice(0, marker).toString('utf8');
          if (!header.includes(' 101 ')) {
            reject(new Error(`WebSocket handshake failed: ${header}`));
            socket.destroy();
            return;
          }

          connected = true;
          this.socket = socket;
          const rest = handshake.slice(marker + 4);
          if (rest.length) this.handleData(rest);
          resolve();
          return;
        }
        this.handleData(chunk);
      });

      socket.on('error', (error) => {
        if (!connected) reject(error);
        for (const pending of this.pending.values()) pending.reject(error);
        this.pending.clear();
      });

      socket.on('close', () => {
        const error = new Error('CDP websocket closed');
        for (const pending of this.pending.values()) pending.reject(error);
        this.pending.clear();
      });
    });
  }

  handleData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    const decoded = decodeWebSocketFrames(this.buffer);
    this.buffer = decoded.remaining;

    for (const messageText of decoded.messages) {
      let message;
      try {
        message = JSON.parse(messageText);
      } catch (_) {
        continue;
      }

      if (message.id && this.pending.has(message.id)) {
        const pending = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
        else pending.resolve(message.result || {});
      }
    }
  }

  send(method, params = {}) {
    if (!this.socket) throw new Error('CDP websocket is not connected');

    const id = commandId++;
    const payload = JSON.stringify({ id, method, params });
    this.socket.write(encodeWebSocketFrame(payload));

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP command timeout: ${method}`));
      }, NAV_TIMEOUT_MS);

      this.pending.set(id, {
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });
    });
  }

  close() {
    if (this.socket) this.socket.destroy();
    this.socket = null;
  }
}

async function getPage(targetId) {
  const page = pages.get(targetId);
  if (!page) throw new Error(`Unknown target: ${targetId}`);
  return page;
}

async function newPage(targetUrl) {
  if (!targetUrl) throw new Error('Missing url parameter');

  const pageInfo = await chromeFetch(`/json/new?${encodeURIComponent(targetUrl)}`);
  const targetId = pageInfo.id || pageInfo.targetId;
  const webSocketDebuggerUrl = pageInfo.webSocketDebuggerUrl;

  if (!targetId || !webSocketDebuggerUrl) {
    throw new Error(`Invalid Chrome target response: ${JSON.stringify(pageInfo)}`);
  }

  const cdp = new CdpSocket(webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');

  pages.set(targetId, { targetId, cdp, pageInfo });

  await new Promise((resolve) => setTimeout(resolve, 500));
  return { targetId };
}

async function evalJs(targetId, expression) {
  const page = await getPage(targetId);
  const result = await page.cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });

  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || 'Runtime.evaluate failed');
  }

  const remoteObject = result.result || {};
  if ('value' in remoteObject) return { value: remoteObject.value };
  if ('description' in remoteObject) return { value: remoteObject.description };
  return { value: '' };
}

async function scrollPage(targetId, y) {
  const amount = Number(y || 3000);
  await evalJs(targetId, `window.scrollBy(0, ${JSON.stringify(amount)}); 'ok';`);
  return { success: true, y: amount };
}

async function closePage(targetId) {
  const page = await getPage(targetId);
  page.cdp.close();
  pages.delete(targetId);
  try {
    await chromeFetch(`/json/close/${encodeURIComponent(targetId)}`);
  } catch (_) {
    // The websocket close above is enough for crawler cleanup; Chrome may have
    // already closed the target by the time /json/close is called.
  }
  return { success: true };
}

async function route(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = requestUrl.pathname.replace(/^\//, '');

  try {
    if (pathname === 'health') {
      const version = await chromeFetch('/json/version');
      sendJson(res, 200, {
        status: 'ok',
        chrome: version.Browser || version.browser || 'unknown',
        chrome_cdp_url: CHROME_CDP_URL,
        open_pages: pages.size,
      });
      return;
    }

    if (pathname === 'new' && req.method === 'GET') {
      sendJson(res, 200, await newPage(requestUrl.searchParams.get('url')));
      return;
    }

    if (pathname === 'eval' && req.method === 'POST') {
      const body = await readBody(req);
      sendJson(res, 200, await evalJs(requestUrl.searchParams.get('target'), body));
      return;
    }

    if (pathname === 'scroll' && req.method === 'GET') {
      sendJson(res, 200, await scrollPage(requestUrl.searchParams.get('target'), requestUrl.searchParams.get('y')));
      return;
    }

    if (pathname === 'close' && req.method === 'GET') {
      sendJson(res, 200, await closePage(requestUrl.searchParams.get('target')));
      return;
    }

    sendJson(res, 404, { error: `Unknown endpoint: ${req.method} /${pathname}` });
  } catch (error) {
    sendJson(res, 500, { error: error.message });
  }
}

const server = http.createServer(route);

server.listen(PROXY_PORT, PROXY_HOST, () => {
  console.log(`CDP proxy listening on http://${PROXY_HOST}:${PROXY_PORT}`);
  console.log(`Chrome DevTools endpoint: ${CHROME_CDP_URL}`);
});

process.on('SIGINT', () => {
  for (const page of pages.values()) page.cdp.close();
  process.exit(0);
});

process.on('SIGTERM', () => {
  for (const page of pages.values()) page.cdp.close();
  process.exit(0);
});
