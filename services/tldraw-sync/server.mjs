import cors from '@fastify/cors';
import websocketPlugin from '@fastify/websocket';
import fastify from 'fastify';
import { verifyWhiteboardToken } from './auth.mjs';
import { AssetTooLargeError, loadAsset, storeAsset } from './assets.mjs';
import { makeOrLoadRoom } from './rooms.mjs';
import { unfurl } from 'unfurl.js';

const PORT = Number(process.env.PORT || 5858);
const ALLOWED_UPLOAD_TYPES = new Set([
  'image/png',
  'image/jpeg',
  'image/jpg',
  'image/gif',
  'image/webp',
  'image/svg+xml',
]);

const app = fastify({ logger: true });
app.register(websocketPlugin);
app.register(cors, { origin: true });

app.get('/health', async () => ({ ok: true }));

app.register(async (scopedApp) => {
  scopedApp.get('/connect/:roomId', { websocket: true }, async (socket, req) => {
    const roomId = req.params.roomId;
    const sessionId = req.query?.sessionId;
    const token = req.query?.token;

    if (!roomId || !sessionId || !verifyWhiteboardToken(token, roomId)) {
      socket.close();
      return;
    }

    const caughtMessages = [];
    const collectMessagesListener = (message) => {
      caughtMessages.push(message);
    };

    socket.on('message', collectMessagesListener);

    const room = makeOrLoadRoom(roomId);
    room.handleSocketConnect({ sessionId, socket });

    socket.off('message', collectMessagesListener);

    for (const message of caughtMessages) {
      socket.emit('message', message);
    }
  });

  scopedApp.addContentTypeParser('*', (_, __, done) => done(null));

  scopedApp.put('/uploads/:id', async (req, res) => {
    const id = req.params.id;
    const ctype = String(req.headers['content-type'] || '')
      .split(';')[0]
      .trim()
      .toLowerCase();
    if (ctype && !ALLOWED_UPLOAD_TYPES.has(ctype)) {
      res.code(415).send({
        detail: 'Only image uploads are allowed on the board sync.',
      });
      return;
    }
    try {
      await storeAsset(id, req.raw);
      res.send({ ok: true });
    } catch (error) {
      if (error instanceof AssetTooLargeError) {
        res.code(413).send({
          detail: 'Asset too large (max 2MB). Use board-assets API.',
        });
        return;
      }
      throw error;
    }
  });

  scopedApp.get('/uploads/:id', async (req, res) => {
    const id = req.params.id;
    const data = await loadAsset(id);
    res.header('Content-Security-Policy', "default-src 'none'");
    res.header('X-Content-Type-Options', 'nosniff');
    res.send(data);
  });

  scopedApp.get('/unfurl', async (req, res) => {
    const url = req.query?.url;
    if (!url) {
      res.code(400).send({ detail: 'url is required' });
      return;
    }
    try {
      res.send(await unfurl(url));
    } catch (error) {
      res.code(502).send({ detail: String(error?.message || error) });
    }
  });
});

app.listen({ port: PORT, host: '0.0.0.0' }, (err) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }
  console.log(`tldraw sync listening on ${PORT}`);
});
