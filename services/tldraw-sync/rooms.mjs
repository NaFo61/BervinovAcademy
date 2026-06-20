import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { NodeSqliteWrapper, SQLiteSyncStorage, TLSocketRoom } from '@tldraw/sync-core';

const DATA_DIR = process.env.DATA_DIR || './data/rooms';

mkdirSync(DATA_DIR, { recursive: true });

function sanitizeRoomId(roomId) {
  return String(roomId).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
}

const rooms = new Map();

export function makeOrLoadRoom(roomId) {
  const safeId = sanitizeRoomId(roomId);
  const existing = rooms.get(safeId);
  if (existing && !existing.isClosed()) {
    return existing;
  }

  const dbPath = join(DATA_DIR, `${safeId}.db`);
  const db = new DatabaseSync(dbPath);
  const sql = new NodeSqliteWrapper(db);
  const storage = new SQLiteSyncStorage({ sql });

  const room = new TLSocketRoom({
    storage,
    onSessionRemoved(roomInstance, args) {
      if (args.numSessionsRemaining === 0) {
        roomInstance.close();
        db.close();
        rooms.delete(safeId);
      }
    },
  });

  rooms.set(safeId, room);
  return room;
}
