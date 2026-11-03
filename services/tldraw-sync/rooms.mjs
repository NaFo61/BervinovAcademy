import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { NodeSqliteWrapper, SQLiteSyncStorage, TLSocketRoom } from '@tldraw/sync-core';

const DATA_DIR = process.env.DATA_DIR || './data/rooms';
const IDLE_CLOSE_MS = Number(process.env.ROOM_IDLE_CLOSE_MS || 60_000);

mkdirSync(DATA_DIR, { recursive: true });

function sanitizeRoomId(roomId) {
  return String(roomId).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128);
}

/** Комната живёт в файле. Выход людей файл не удаляет. */
const rooms = new Map();

function openDatabase(dbPath) {
  const db = new DatabaseSync(dbPath);
  db.exec('PRAGMA journal_mode = WAL;');
  db.exec('PRAGMA synchronous = NORMAL;');
  db.exec('PRAGMA busy_timeout = 5000;');
  return db;
}

function rememberRoom(entry) {
  entry.room = new TLSocketRoom({
    storage: entry.storage,
    onSessionRemoved(_roomInstance, args) {
      if (args.numSessionsRemaining !== 0) return;
      if (entry.idleTimer) clearTimeout(entry.idleTimer);
      entry.idleTimer = setTimeout(() => {
        entry.idleTimer = null;
        const room = entry.room;
        if (!room || room.isClosed()) return;
        try {
          room.close();
        } catch (_) {
          /* комната уже закрыта */
        }
        try {
          entry.db.exec('PRAGMA wal_checkpoint(PASSIVE);');
        } catch (_) {
          /* файл всё равно остаётся */
        }
      }, IDLE_CLOSE_MS);
    },
  });
  return entry.room;
}

export function makeOrLoadRoom(roomId) {
  const safeId = sanitizeRoomId(roomId);
  const existing = rooms.get(safeId);
  if (existing) {
    if (existing.idleTimer) {
      clearTimeout(existing.idleTimer);
      existing.idleTimer = null;
    }
    if (existing.room && !existing.room.isClosed()) {
      return existing.room;
    }
    return rememberRoom(existing);
  }

  const dbPath = join(DATA_DIR, `${safeId}.db`);
  const db = openDatabase(dbPath);
  const sql = new NodeSqliteWrapper(db);
  const storage = new SQLiteSyncStorage({ sql });
  const entry = {
    db,
    storage,
    room: null,
    idleTimer: null,
  };
  rooms.set(safeId, entry);
  return rememberRoom(entry);
}

export function checkpointRooms() {
  for (const entry of rooms.values()) {
    try {
      entry.db.exec('PRAGMA wal_checkpoint(TRUNCATE);');
    } catch (_) {
      /* процесс всё равно завершается */
    }
  }
}
