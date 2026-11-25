// Общая доска школы. Страница не монтирует tldraw: без лицензии он гасит холст.

const Routes = window.Routes;

const WORLD_MIN = -1000000;
const WORLD_MAX = 1000000;
const MIN_SCALE = 0.2;
const MAX_SCALE = 4;
const DOT = 32;
const PEN_COLORS = [
  { value: '#0B1226', label: 'Чёрный' },
  { value: '#64748B', label: 'Серый' },
  { value: '#2563EB', label: 'Синий' },
  { value: '#0EA5E9', label: 'Голубой' },
  { value: '#059669', label: 'Зелёный' },
  { value: '#65A30D', label: 'Салатовый' },
  { value: '#EAB308', label: 'Жёлтый' },
  { value: '#F97316', label: 'Оранжевый' },
  { value: '#E11D48', label: 'Красный' },
  { value: '#DB2777', label: 'Розовый' },
  { value: '#7C3AED', label: 'Фиолетовый' },
  { value: '#92400E', label: 'Коричневый' },
];
const FONTS = [
  { value: 'sans', label: 'Обычный', css: 'system-ui, "Segoe UI", sans-serif' },
  { value: 'serif', label: 'С засечками', css: 'Georgia, "Times New Roman", serif' },
  { value: 'hand', label: 'Рукописный', css: '"Comic Sans MS", "Segoe Script", cursive' },
  { value: 'mono', label: 'Машинный', css: 'ui-monospace, Consolas, monospace' },
];
const TEXT_SIZE = 28;
const TEXT_WRAP = 320;
const layoutCache = new Map();

function fontCss(key) {
  const found = FONTS.find((row) => row.value === key);
  return found ? found.css : FONTS[0].css;
}

function wrapText(ctx, text, maxWidth) {
  const paragraphs = String(text || '').split('\n');
  const lines = [];
  paragraphs.forEach((paragraph) => {
    const words = paragraph.split(/(\s+)/);
    let line = '';
    words.forEach((word) => {
      const trial = line + word;
      if (line && ctx.measureText(trial).width > maxWidth) {
        lines.push(line.replace(/\s+$/, ''));
        line = word.trimStart();
      } else line = trial;
    });
    lines.push(line);
  });
  return lines.length ? lines : [''];
}

function layoutText(item, maxWidth) {
  const size = Number(item.size) || TEXT_SIZE;
  const wrap = Math.max(32, Number(maxWidth) || Number(item.w) || TEXT_WRAP);
  const key = `${item.font}|${size}|${Math.round(wrap)}|${item.text}`;
  const cached = layoutCache.get(key);
  if (cached) return cached;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.font = `${size}px ${fontCss(item.font)}`;
  const lines = wrapText(ctx, item.text || '', wrap);
  const lineH = size * 1.35;
  let width = 8;
  lines.forEach((line) => {
    width = Math.max(width, ctx.measureText(line || ' ').width);
  });
  const result = {
    lines,
    lineH,
    w: Math.min(4000, wrap),
    contentW: Math.min(4000, Math.max(32, Math.round(width + 8))),
    h: Math.min(4000, Math.max(8, Math.round(lines.length * lineH + 4))),
  };
  layoutCache.set(key, result);
  if (layoutCache.size > 200) layoutCache.delete(layoutCache.keys().next().value);
  return result;
}

function toolCursor(name) {
  if (name === 'hand') return 'grab';
  if (name === 'text') return 'text';
  if (name === 'pen') return 'crosshair';
  return 'default';
}

function Icon({ children }) {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {children}
    </svg>
  );
}

function copyItem(item) {
  if (!item) return item;
  if (item.type === 'stroke') {
    return { ...item, points: (item.points || []).map((pt) => [pt[0], pt[1]]) };
  }
  return { ...item };
}

function whiteboardFeatureEnabled() {
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  if (!meta) return true;
  return meta.getAttribute('content') !== 'false';
}

function emptyBoard() {
  return { kind: 'academy-board', version: 1, revision: 0, items: [] };
}

function boardSavePayload(doc, removedIds) {
  return {
    snapshot: {
      kind: 'academy-board',
      version: 1,
      revision: doc.revision || 0,
      items: doc.items || [],
    },
    base_revision: doc.revision || 0,
    removed_ids: removedIds || [],
  };
}

function readBoard(snapshot) {
  if (!snapshot || typeof snapshot !== 'object') return emptyBoard();
  const raw = snapshot.kind === 'academy-board' ? snapshot : snapshot.academy_board;
  if (!raw || raw.kind !== 'academy-board') return emptyBoard();
  const items = Array.isArray(raw.items) ? raw.items : [];
  return {
    kind: 'academy-board',
    version: 1,
    revision: Number(raw.revision) || 0,
    items,
  };
}

function newId() {
  const head = Math.random().toString(36).slice(2, 10);
  const tail = Date.now().toString(36);
  return (`s${head}${tail}`).replace(/[^a-z0-9]/gi, '').slice(0, 32);
}

function distToSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const len = dx * dx + dy * dy;
  if (len <= 0.0001) {
    const ox = px - ax;
    const oy = py - ay;
    return Math.sqrt(ox * ox + oy * oy);
  }
  let t = ((px - ax) * dx + (py - ay) * dy) / len;
  t = Math.max(0, Math.min(1, t));
  const ox = px - (ax + t * dx);
  const oy = py - (ay + t * dy);
  return Math.sqrt(ox * ox + oy * oy);
}

function hitsItem(item, x, y, pad = 0) {
  if (!item) return false;
  if (item.type === 'image' || item.type === 'text') {
    const box = itemBounds(item);
    return !!box && x >= box.minX - pad && y >= box.minY - pad
      && x <= box.maxX + pad && y <= box.maxY + pad;
  }
  const pts = item.points || [];
  const radius = pad + (Number(item.size) || 4) / 2;
  if (!pts.length) return false;
  if (pts.length === 1) {
    const dx = pts[0][0] - x;
    const dy = pts[0][1] - y;
    return dx * dx + dy * dy <= radius * radius;
  }
  for (let i = 1; i < pts.length; i += 1) {
    const prev = pts[i - 1];
    const next = pts[i];
    if (distToSegment(x, y, prev[0], prev[1], next[0], next[1]) <= radius) return true;
  }
  return false;
}

function round1(value) {
  return Math.round(value * 10) / 10;
}

function clampWorld(value) {
  return Math.min(WORLD_MAX, Math.max(WORLD_MIN, round1(value)));
}

function viewOf(canvas) {
  return {
    rect: canvas.getBoundingClientRect(),
    dpr: Math.min(window.devicePixelRatio || 1, 2),
  };
}

function worldFromEvent(event, view, camera) {
  if (!view || !camera || !view.rect) return null;
  const sx = event.clientX - view.rect.left;
  const sy = event.clientY - view.rect.top;
  return [
    clampWorld((sx - view.rect.width / 2) / camera.scale + camera.x),
    clampWorld((sy - view.rect.height / 2) / camera.scale + camera.y),
  ];
}

function contentBox(items) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  let any = false;
  (items || []).forEach((item) => {
    if (!item) return;
    if (item.type === 'image' || item.type === 'text') {
      const box = itemBounds(item);
      if (!box) return;
      any = true;
      minX = Math.min(minX, box.minX);
      minY = Math.min(minY, box.minY);
      maxX = Math.max(maxX, box.maxX);
      maxY = Math.max(maxY, box.maxY);
      return;
    }
    (item.points || []).forEach((pt) => {
      any = true;
      minX = Math.min(minX, pt[0]);
      minY = Math.min(minY, pt[1]);
      maxX = Math.max(maxX, pt[0]);
      maxY = Math.max(maxY, pt[1]);
    });
  });
  if (!any) return null;
  return { minX, minY, maxX, maxY };
}

function fitCamera(items, width, height) {
  const box = contentBox(items);
  if (!box || width < 8 || height < 8) return { x: 0, y: 0, scale: 1 };
  const bw = Math.max(box.maxX - box.minX, 48);
  const bh = Math.max(box.maxY - box.minY, 48);
  const raw = Math.min((width - 96) / bw, (height - 96) / bh);
  const scale = Math.min(1.25, Math.max(MIN_SCALE, raw));
  return {
    x: (box.minX + box.maxX) / 2,
    y: (box.minY + box.maxY) / 2,
    scale: Number.isFinite(scale) ? scale : 1,
  };
}

function fittedSize(size) {
  const w0 = size && size.w ? size.w : 320;
  const h0 = size && size.h ? size.h : 240;
  const fit = w0 > 480 ? 480 / w0 : 1;
  let w = Math.max(32, Math.round(w0 * fit));
  let h = Math.max(32, Math.round(h0 * fit));
  if (h > 2000) {
    w = Math.max(32, Math.round(w * (2000 / h)));
    h = 2000;
  }
  return { w, h };
}

function topItem(items, x, y, pad) {
  for (let i = (items || []).length - 1; i >= 0; i -= 1) {
    if (hitsItem(items[i], x, y, pad)) return items[i];
  }
  return null;
}

function itemBounds(item) {
  if (!item) return null;
  if (item.type === 'image' || item.type === 'text') {
    const w = Number(item.w) || 32;
    const h = Number(item.h) || 32;
    return { minX: item.x, minY: item.y, maxX: item.x + w, maxY: item.y + h };
  }
  return contentBox([item]);
}

function boundsOverlap(a, b) {
  if (!a || !b) return false;
  return a.minX <= b.maxX && a.maxX >= b.minX && a.minY <= b.maxY && a.maxY >= b.minY;
}

function unionBounds(items) {
  let box = null;
  (items || []).forEach((item) => {
    const next = itemBounds(item);
    if (!next) return;
    if (!box) {
      box = { ...next };
      return;
    }
    box.minX = Math.min(box.minX, next.minX);
    box.minY = Math.min(box.minY, next.minY);
    box.maxX = Math.max(box.maxX, next.maxX);
    box.maxY = Math.max(box.maxY, next.maxY);
  });
  return box;
}

function boxFromCorners(x0, y0, x1, y1) {
  return {
    minX: Math.min(x0, x1),
    minY: Math.min(y0, y1),
    maxX: Math.max(x0, x1),
    maxY: Math.max(y0, y1),
  };
}

function movedItem(origin, dx, dy) {
  if (origin.type === 'image' || origin.type === 'text') {
    return { ...origin, x: clampWorld(origin.x + dx), y: clampWorld(origin.y + dy) };
  }
  return {
    ...origin,
    points: (origin.points || []).map((pt) => [clampWorld(pt[0] + dx), clampWorld(pt[1] + dy)]),
  };
}

function paddedBox(box, scale) {
  const gap = 8 / (scale || 1);
  return {
    minX: box.minX - gap,
    minY: box.minY - gap,
    maxX: box.maxX + gap,
    maxY: box.maxY + gap,
  };
}

function handlePoints(box) {
  const midX = (box.minX + box.maxX) / 2;
  const midY = (box.minY + box.maxY) / 2;
  return {
    nw: [box.minX, box.minY],
    n: [midX, box.minY],
    ne: [box.maxX, box.minY],
    e: [box.maxX, midY],
    se: [box.maxX, box.maxY],
    s: [midX, box.maxY],
    sw: [box.minX, box.maxY],
    w: [box.minX, midY],
  };
}

const HANDLE_CURSOR = {
  nw: 'nwse-resize',
  se: 'nwse-resize',
  ne: 'nesw-resize',
  sw: 'nesw-resize',
  n: 'ns-resize',
  s: 'ns-resize',
  e: 'ew-resize',
  w: 'ew-resize',
};

function hitHandle(point, box, scale) {
  if (!point || !box) return null;
  const reach = 14 / (scale || 1);
  const points = handlePoints(box);
  let best = null;
  let bestD = reach * reach;
  Object.keys(points).forEach((name) => {
    const pt = points[name];
    const dx = point[0] - pt[0];
    const dy = point[1] - pt[1];
    const dist = dx * dx + dy * dy;
    if (dist <= bestD) {
      best = name;
      bestD = dist;
    }
  });
  return best;
}

function pointInBox(point, box) {
  if (!point || !box) return false;
  return point[0] >= box.minX && point[0] <= box.maxX
    && point[1] >= box.minY && point[1] <= box.maxY;
}

function scaleFactor(origin, anchor, next) {
  const span = origin - anchor;
  if (Math.abs(span) < 1) return 1;
  let factor = (next - anchor) / span;
  if (factor < 0.15) factor = 0.15;
  if (factor > 8) factor = 8;
  return factor;
}

function scaleItem(origin, ax, ay, sx, sy, movingX, movingY) {
  const useSx = movingX ? sx : 1;
  const useSy = movingY ? sy : 1;
  if (origin.type === 'image') {
    const x = movingX ? ax + (origin.x - ax) * useSx : origin.x;
    const y = movingY ? ay + (origin.y - ay) * useSy : origin.y;
    return {
      ...origin,
      x: clampWorld(x),
      y: clampWorld(y),
      w: round1(Math.max(8, Math.min(2000, origin.w * useSx))),
      h: round1(Math.max(8, Math.min(2000, origin.h * useSy))),
    };
  }
  if (origin.type === 'text') {
    const x = movingX ? ax + (origin.x - ax) * useSx : origin.x;
    const y = movingY ? ay + (origin.y - ay) * useSy : origin.y;
    const w = round1(Math.max(32, Math.min(4000, (origin.w || 80) * useSx)));
    const size = movingY
      ? round1(Math.max(16, Math.min(72, (origin.size || TEXT_SIZE) * useSy)))
      : (origin.size || TEXT_SIZE);
    const next = { ...origin, x: clampWorld(x), y: clampWorld(y), w, size };
    next.h = layoutText(next, w).h;
    return next;
  }
  const size = round1(Math.max(2, Math.min(24, (origin.size || 5) * ((useSx + useSy) / 2))));
  return {
    ...origin,
    size,
    points: (origin.points || []).map((pt) => [
      clampWorld(movingX ? ax + (pt[0] - ax) * useSx : pt[0]),
      clampWorld(movingY ? ay + (pt[1] - ay) * useSy : pt[1]),
    ]),
  };
}

function resizedItems(origins, bounds, handle, pointer) {
  const movingX = handle === 'e' || handle === 'w' || handle.length === 2;
  const movingY = handle === 'n' || handle === 's' || handle.length === 2;
  let sx = 1;
  let sy = 1;
  if (movingX) {
    const originX = handle.includes('w') ? bounds.minX : bounds.maxX;
    const anchorX = handle.includes('w') ? bounds.maxX : bounds.minX;
    sx = scaleFactor(originX, anchorX, pointer[0]);
  }
  if (movingY) {
    const originY = handle.includes('n') ? bounds.minY : bounds.maxY;
    const anchorY = handle.includes('n') ? bounds.maxY : bounds.minY;
    sy = scaleFactor(originY, anchorY, pointer[1]);
  }
  const list = Object.values(origins);
  const only = list.length === 1 ? list[0] : null;
  if (only && movingX && movingY && (only.type === 'image' || only.type === 'text')) {
    const uniform = Math.max(sx, sy);
    sx = uniform;
    sy = uniform;
  }
  const ax = movingX ? (handle.includes('w') ? bounds.maxX : bounds.minX) : bounds.minX;
  const ay = movingY ? (handle.includes('n') ? bounds.maxY : bounds.minY) : bounds.minY;
  return list.map((origin) => scaleItem(origin, ax, ay, sx, sy, movingX, movingY));
}

function loadImageSize(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve({
      w: img.naturalWidth || 320,
      h: img.naturalHeight || 240,
    });
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

function WhiteboardPage({ navigate, hashParams, embedded = false, ownerPublicId = '' }) {
  const token = window.getAccessToken();
  const ownerFromQuery = ownerPublicId || hashParams?.get('user') || '';
  const canvasRef = React.useRef(null);
  const metricsRef = React.useRef(null);
  const docRef = React.useRef(emptyBoard());
  const wsRef = React.useRef(null);
  const clientIdRef = React.useRef(newId());
  const pendingRef = React.useRef({ upserts: new Map(), removes: new Set() });
  const remoteLiveRef = React.useRef({});
  const localStrokeRef = React.useRef(null);
  const toolRef = React.useRef('select');
  const colorRef = React.useRef(PEN_COLORS[0].value);
  const fontRef = React.useRef(FONTS[0].value);
  const selectionRef = React.useRef(new Set());
  const marqueeRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const editorNodeRef = React.useRef(null);
  const ignoreEditorBlurRef = React.useRef(false);
  const historyRef = React.useRef({ undo: [], redo: [] });
  const recordingRef = React.useRef(true);
  const resizeRef = React.useRef(null);
  const [historyTick, setHistoryTick] = React.useState(0);
  const imagesRef = React.useRef(new Map());
  const genRef = React.useRef(0);
  const saveTimerRef = React.useRef(0);
  const liveTimerRef = React.useRef(0);
  const retryTimerRef = React.useRef(0);
  const stoppedRef = React.useRef(false);
  const ownerIdRef = React.useRef('');
  const snapUrlRef = React.useRef('');
  const paintRef = React.useRef(() => {});
  const fileRef = React.useRef(null);
  const cameraRef = React.useRef({ x: 0, y: 0, scale: 1 });
  const panRef = React.useRef(null);
  const dragRef = React.useRef(null);
  const spaceRef = React.useRef(false);
  const fittedRef = React.useRef(false);
  const liveItemRef = React.useRef(null);

  const [viewScale, setViewScale] = React.useState(1);

  const [error, setError] = React.useState('');
  const [ready, setReady] = React.useState(false);
  const [tool, setTool] = React.useState('select');
  const [color, setColor] = React.useState(PEN_COLORS[0].value);
  const [font, setFont] = React.useState(FONTS[0].value);
  const [selectionIds, setSelectionIds] = React.useState([]);
  const [editor, setEditor] = React.useState(null);
  const [status, setStatus] = React.useState('Подключение…');
  const [notice, setNotice] = React.useState('');
  const [isOwn, setIsOwn] = React.useState(!ownerFromQuery);
  const [ownerName, setOwnerName] = React.useState('');
  const [backNav, setBackNav] = React.useState(null);
  const [sideImages, setSideImages] = React.useState([]);
  const [docVersion, setDocVersion] = React.useState(0);

  const scheduleDraw = React.useCallback(() => {
    paintRef.current();
  }, []);

  const setBoard = React.useCallback((next) => {
    docRef.current = next;
    setDocVersion((value) => value + 1);
  }, []);

  const socketOpen = React.useCallback(() => {
    const ws = wsRef.current;
    return !!ws && ws.readyState === WebSocket.OPEN;
  }, []);

  const sendJson = React.useCallback((body) => {
    if (!socketOpen()) return false;
    try {
      wsRef.current.send(JSON.stringify(body));
      return true;
    } catch (_) {
      return false;
    }
  }, [socketOpen]);

  const flushPending = React.useCallback(() => {
    if (!socketOpen()) return;
    pendingRef.current.upserts.forEach((item) => {
      sendJson({ event: 'commit', payload: { client: clientIdRef.current, item } });
    });
    if (pendingRef.current.removes.size) {
      sendJson({
        event: 'remove',
        payload: { client: clientIdRef.current, ids: [...pendingRef.current.removes] },
      });
    }
  }, [sendJson, socketOpen]);

  const persistSoon = React.useCallback(() => {
    if (socketOpen()) return;
    window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(async () => {
      if (stoppedRef.current || socketOpen() || !snapUrlRef.current) return;
      const seen = genRef.current;
      const doc = docRef.current;
      try {
        const saved = await window.apiJson(snapUrlRef.current, {
          method: 'PUT',
          auth: true,
          body: boardSavePayload(doc, [...pendingRef.current.removes]),
        });
        if (stoppedRef.current || genRef.current !== seen) return;
        pendingRef.current.upserts.clear();
        pendingRef.current.removes.clear();
        setBoard({
          ...docRef.current,
          revision: Math.max(docRef.current.revision, Number(saved?.revision) || 0),
        });
        setStatus('Сохранено');
      } catch (_) {
        if (!stoppedRef.current) setStatus('Не удалось сохранить');
      }
    }, 400);
  }, [setBoard, socketOpen]);

  const markDirty = React.useCallback(() => {
    genRef.current += 1;
  }, []);

  const applyRemoteHello = React.useCallback((snapshot) => {
    const remote = readBoard(snapshot);
    const local = docRef.current;
    const pending = pendingRef.current;
    remoteLiveRef.current = {};
    const gone = new Set(Array.isArray(snapshot?.removed) ? snapshot.removed : []);
    gone.forEach((id) => {
      pending.upserts.delete(id);
      pending.removes.delete(id);
    });
    if ((remote.revision || 0) < (local.revision || 0)) {
      const byId = new Map((remote.items || []).map((item) => [item.id, item]));
      local.items.forEach((item) => {
        if (!gone.has(item.id)) byId.set(item.id, item);
      });
      pending.removes.forEach((id) => byId.delete(id));
      gone.forEach((id) => byId.delete(id));
      setBoard({ ...local, items: [...byId.values()] });
    } else {
      let items = (remote.items || []).filter(
        (item) => !pending.removes.has(item.id) && !gone.has(item.id),
      );
      pending.upserts.forEach((item) => {
        items = items.filter((row) => row.id !== item.id).concat(item);
      });
      setBoard({ ...remote, items });
    }
    flushPending();
  }, [flushPending, setBoard]);

  const upsertFromServer = React.useCallback((item, revision, fromMe) => {
    delete remoteLiveRef.current[item.id];
    if (fromMe) pendingRef.current.upserts.delete(item.id);
    else pendingRef.current.removes.delete(item.id);
    const doc = docRef.current;
    const items = doc.items.filter((row) => row.id !== item.id).concat(item);
    setBoard({
      ...doc,
      items,
      revision: Math.max(doc.revision || 0, Number(revision) || 0),
    });
    if (fromMe) setStatus('Сохранено');
  }, [setBoard]);

  const removeFromServer = React.useCallback((ids, revision, fromMe) => {
    const drop = new Set(ids || []);
    drop.forEach((id) => {
      delete remoteLiveRef.current[id];
      if (fromMe) pendingRef.current.removes.delete(id);
      else pendingRef.current.upserts.delete(id);
    });
    const doc = docRef.current;
    setBoard({
      ...doc,
      items: doc.items.filter((item) => !drop.has(item.id)),
      revision: Math.max(doc.revision || 0, Number(revision) || 0),
    });
  }, [setBoard]);

  React.useEffect(() => {
    if (!embedded) return undefined;
    const exportPng = () => new Promise((resolve, reject) => {
      const canvas = canvasRef.current;
      if (!canvas || canvas.width < 2) {
        reject(new Error('Доска ещё не загружена'));
        return;
      }
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('Не удалось сделать снимок'));
      }, 'image/png');
    });
    const exportDoc = () => docRef.current;
    window.exportAcademyBoardPng = exportPng;
    window.exportAcademyBoardSnapshot = exportDoc;
    return () => {
      if (window.exportAcademyBoardPng === exportPng) delete window.exportAcademyBoardPng;
      if (window.exportAcademyBoardSnapshot === exportDoc) delete window.exportAcademyBoardSnapshot;
    };
  }, [embedded]);

  React.useEffect(() => {
    toolRef.current = tool;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cursor = toolCursor(tool);
    canvas.style.cursor = cursor;
    canvas.dataset.cursor = cursor;
  }, [tool, ready]);

  React.useEffect(() => {
    colorRef.current = color;
  }, [color]);

  React.useEffect(() => {
    fontRef.current = font;
  }, [font]);

  const setSelection = React.useCallback((ids) => {
    const next = [...new Set(ids || [])];
    selectionRef.current = new Set(next);
    setSelectionIds(next);
  }, []);

  React.useEffect(() => {
    paintRef.current = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const view = viewOf(canvas);
      metricsRef.current = view;
      const camera = cameraRef.current;
      canvas.dataset.zoom = String(camera.scale);
      canvas.dataset.camX = String(Math.round(camera.x));
      canvas.dataset.camY = String(Math.round(camera.y));
      if (view.rect.width < 2 || view.rect.height < 2) return;
      const pxW = Math.round(view.rect.width * view.dpr);
      const pxH = Math.round(view.rect.height * view.dpr);
      if (canvas.width !== pxW || canvas.height !== pxH) {
        canvas.width = pxW;
        canvas.height = pxH;
      }
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
      ctx.clearRect(0, 0, view.rect.width, view.rect.height);
      ctx.fillStyle = '#F6F8FC';
      ctx.fillRect(0, 0, view.rect.width, view.rect.height);
      ctx.save();
      ctx.translate(view.rect.width / 2, view.rect.height / 2);
      ctx.scale(camera.scale, camera.scale);
      ctx.translate(-camera.x, -camera.y);
      const margin = 64;
      const left = camera.x - view.rect.width / (2 * camera.scale) - margin;
      const top = camera.y - view.rect.height / (2 * camera.scale) - margin;
      const worldW = view.rect.width / camera.scale + margin * 2;
      const worldH = view.rect.height / camera.scale + margin * 2;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(left, top, worldW, worldH);
      ctx.fillStyle = 'rgba(11, 18, 38, 0.16)';
      const dot = 1.6 / camera.scale;
      const xStart = Math.floor(left / DOT) * DOT;
      const yStart = Math.floor(top / DOT) * DOT;
      for (let x = xStart; x <= left + worldW; x += DOT) {
        for (let y = yStart; y <= top + worldH; y += DOT) ctx.fillRect(x, y, dot, dot);
      }
      const drawItem = (item) => {
        if (!item) return;
        if (editorRef.current && item.id === editorRef.current.id) return;
        if (item.type === 'image') {
          let img = imagesRef.current.get(item.src);
          if (!img) {
            img = new Image();
            img.onload = () => paintRef.current();
            img.src = item.src;
            imagesRef.current.set(item.src, img);
          }
          if (img.complete && img.naturalWidth) ctx.drawImage(img, item.x, item.y, item.w, item.h);
          else {
            ctx.fillStyle = 'rgba(11, 18, 38, 0.06)';
            ctx.fillRect(item.x, item.y, item.w, item.h);
          }
          return;
        }
        if (item.type === 'text') {
          const layout = layoutText(item);
          const size = Number(item.size) || TEXT_SIZE;
          ctx.save();
          ctx.font = `${size}px ${fontCss(item.font)}`;
          ctx.fillStyle = item.color || '#0B1226';
          ctx.textBaseline = 'top';
          layout.lines.forEach((line, index) => {
            ctx.fillText(line, item.x, item.y + index * layout.lineH);
          });
          ctx.restore();
          return;
        }
        const pts = item.points || [];
        if (!pts.length) return;
        ctx.beginPath();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = item.color || '#0B1226';
        ctx.lineWidth = item.size || 5;
        ctx.moveTo(pts[0][0], pts[0][1]);
        if (pts.length === 1) ctx.lineTo(pts[0][0] + 0.2, pts[0][1]);
        else pts.slice(1).forEach((pt) => ctx.lineTo(pt[0], pt[1]));
        ctx.stroke();
      };
      const drawFrame = (box, fill) => {
        if (!box) return;
        ctx.save();
        ctx.strokeStyle = '#2563EB';
        ctx.lineWidth = (fill ? 1.5 : 1.75) / camera.scale;
        if (fill) {
          ctx.fillStyle = 'rgba(37, 99, 235, 0.16)';
          ctx.fillRect(box.minX, box.minY, box.maxX - box.minX, box.maxY - box.minY);
        }
        ctx.strokeRect(box.minX, box.minY, box.maxX - box.minX, box.maxY - box.minY);
        ctx.restore();
      };
      const drawSelection = (box) => {
        if (!box) return;
        const frame = paddedBox(box, camera.scale);
        drawFrame(frame, false);
        const size = 8 / camera.scale;
        ctx.save();
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#2563EB';
        ctx.lineWidth = 1.6 / camera.scale;
        Object.values(handlePoints(frame)).forEach(([x, y]) => {
          ctx.beginPath();
          ctx.rect(x - size / 2, y - size / 2, size, size);
          ctx.fill();
          ctx.stroke();
        });
        ctx.restore();
      };
      const live = remoteLiveRef.current;
      (docRef.current.items || []).forEach((item) => {
        if (!live[item.id]) drawItem(item);
      });
      Object.values(live).forEach(drawItem);
      if (localStrokeRef.current) drawItem(localStrokeRef.current);
      const itemsNow = docRef.current.items || [];
      let selected = itemsNow.filter((item) => selectionRef.current.has(item.id));
      if (marqueeRef.current) {
        const area = boxFromCorners(
          marqueeRef.current.x0,
          marqueeRef.current.y0,
          marqueeRef.current.x1,
          marqueeRef.current.y1,
        );
        drawFrame(area, true);
        selected = itemsNow.filter((item) => boundsOverlap(itemBounds(item), area));
      }
      const chosen = unionBounds(selected);
      drawSelection(chosen);
      canvas.dataset.handles = chosen && !marqueeRef.current ? '1' : '0';
      const editing = editorRef.current;
      const node = editorNodeRef.current;
      if (editing && node) {
        node.style.left = `${(editing.x - camera.x) * camera.scale + view.rect.width / 2}px`;
        node.style.top = `${(editing.y - camera.y) * camera.scale + view.rect.height / 2}px`;
        node.style.width = `${TEXT_WRAP * camera.scale}px`;
        node.style.fontSize = `${(editing.size || TEXT_SIZE) * camera.scale}px`;
      }
      ctx.restore();
    };
    paintRef.current();
  }, [docVersion, tool]);

  React.useEffect(() => {
    if (editor) paintRef.current();
  }, [editor]);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const observer = new ResizeObserver(() => paintRef.current());
    observer.observe(canvas);
    window.addEventListener('resize', paintRef.current);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', paintRef.current);
    };
  }, [ready]);

  const flushSnapshot = React.useCallback((doc) => {
    const access = window.getAccessToken();
    const path = snapUrlRef.current;
    if (!access || !path || !doc) return;
    const url = `${window.getApiBase()}${path}`;
    const body = JSON.stringify(
      boardSavePayload(doc, [...pendingRef.current.removes]),
    );
    fetch(url, {
      method: 'PUT',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access}`,
      },
      body,
    }).catch(() => {});
  }, []);

  const commitItem = React.useCallback((item, options) => {
    markDirty();
    pendingRef.current.removes.delete(item.id);
    pendingRef.current.upserts.set(item.id, item);
    const doc = docRef.current;
    const next = {
      ...doc,
      items: doc.items.filter((row) => row.id !== item.id).concat(item),
    };
    setBoard(next);
    const sent = sendJson({
      event: 'commit',
      payload: {
        client: clientIdRef.current,
        item,
        restore: !!(options && options.restore),
      },
    });
    if (!sent) {
      flushSnapshot(next);
      setStatus('Нет связи — сохраняем на сервере');
      persistSoon();
    }
  }, [flushSnapshot, markDirty, persistSoon, sendJson, setBoard]);

  const commitRemove = React.useCallback((ids) => {
    if (!ids.length) return;
    markDirty();
    const drop = new Set(ids);
    ids.forEach((id) => {
      pendingRef.current.upserts.delete(id);
      pendingRef.current.removes.add(id);
      delete remoteLiveRef.current[id];
    });
    const doc = docRef.current;
    const next = { ...doc, items: doc.items.filter((item) => !drop.has(item.id)) };
    setBoard(next);
    const sent = sendJson({
      event: 'remove',
      payload: { client: clientIdRef.current, ids },
    });
    if (!sent) {
      flushSnapshot(next);
      persistSoon();
    }
  }, [flushSnapshot, markDirty, persistSoon, sendJson, setBoard]);

  const remember = React.useCallback((before, after) => {
    if (!recordingRef.current) return;
    const prior = (before || []).filter(Boolean).map(copyItem);
    const next = (after || []).filter(Boolean).map(copyItem);
    if (JSON.stringify(prior) === JSON.stringify(next)) return;
    const history = historyRef.current;
    history.undo.push({ before: prior, after: next });
    if (history.undo.length > 50) history.undo.shift();
    history.redo = [];
    setHistoryTick((value) => value + 1);
  }, []);

  const applyHistory = React.useCallback((before, after) => {
    recordingRef.current = false;
    try {
      const keep = new Set(before.map((item) => item.id));
      const drop = after.map((item) => item.id).filter((id) => !keep.has(id));
      if (drop.length) commitRemove(drop);
      before.forEach((item) => commitItem(copyItem(item), { restore: true }));
    } finally {
      recordingRef.current = true;
    }
  }, [commitItem, commitRemove]);

  const undo = React.useCallback(() => {
    const entry = historyRef.current.undo.pop();
    if (!entry) return;
    historyRef.current.redo.push(entry);
    setHistoryTick((value) => value + 1);
    applyHistory(entry.before, entry.after);
    setSelection(entry.before.map((item) => item.id));
  }, [applyHistory, setSelection]);

  const redo = React.useCallback(() => {
    const entry = historyRef.current.redo.pop();
    if (!entry) return;
    historyRef.current.undo.push(entry);
    setHistoryTick((value) => value + 1);
    applyHistory(entry.after, entry.before);
    setSelection(entry.after.map((item) => item.id));
  }, [applyHistory, setSelection]);

  const commitEditor = React.useCallback(() => {
    const current = editorRef.current;
    if (!current) return;
    editorRef.current = null;
    setEditor(null);
    const text = String(current.text || '').replace(/\u0000/g, '').trim();
    if (!text) {
      if (!current.isNew && current.previous) {
        remember([current.previous], []);
        commitRemove([current.id]);
      }
      setSelection(selectionRef.current.has(current.id)
        ? [...selectionRef.current].filter((id) => id !== current.id)
        : [...selectionRef.current]);
      scheduleDraw();
      return;
    }
    const wrap = current.previous && current.previous.w ? current.previous.w : TEXT_WRAP;
    const item = {
      id: current.id,
      type: 'text',
      text: text.slice(0, 500),
      x: current.x,
      y: current.y,
      color: current.color || colorRef.current,
      font: current.font || fontRef.current,
      size: current.size || TEXT_SIZE,
    };
    const box = layoutText(item, wrap);
    const saved = {
      ...item,
      w: current.previous && current.previous.w ? current.previous.w : box.contentW,
      h: box.h,
    };
    if (current.isNew) remember([], [saved]);
    else remember([current.previous], [saved]);
    commitItem(saved);
    setSelection([saved.id]);
    scheduleDraw();
  }, [commitItem, commitRemove, remember, scheduleDraw, setSelection]);

  const openEditor = React.useCallback((item, isNew) => {
    const next = {
      id: item.id,
      x: item.x,
      y: item.y,
      text: item.text || '',
      color: item.color || colorRef.current,
      font: item.font || fontRef.current,
      size: item.size || TEXT_SIZE,
      w: item.w,
      isNew: !!isNew,
      previous: isNew ? null : copyItem(item),
    };
    ignoreEditorBlurRef.current = true;
    editorRef.current = next;
    colorRef.current = next.color;
    fontRef.current = next.font;
    setColor(next.color);
    setFont(next.font);
    setEditor(next);
    setSelection([item.id]);
    scheduleDraw();
    window.setTimeout(() => {
      ignoreEditorBlurRef.current = false;
      editorNodeRef.current?.focus();
    }, 0);
  }, [scheduleDraw, setSelection]);

  const applyStyle = React.useCallback((patch) => {
    if (patch.color) {
      colorRef.current = patch.color;
      setColor(patch.color);
    }
    if (patch.font) {
      fontRef.current = patch.font;
      setFont(patch.font);
    }
    if (editorRef.current) {
      const next = { ...editorRef.current, ...patch };
      editorRef.current = next;
      setEditor(next);
    }
    const ids = selectionRef.current;
    if (!ids.size || editorRef.current) return;
    const before = [];
    const after = [];
    (docRef.current.items || []).forEach((item) => {
      if (!ids.has(item.id)) return;
      if (patch.color && (item.type === 'stroke' || item.type === 'text')) {
        const updated = { ...copyItem(item), color: patch.color };
        if (updated.type === 'text') updated.h = layoutText(updated).h;
        before.push(copyItem(item));
        after.push(updated);
      } else if (patch.font && item.type === 'text') {
        const updated = { ...copyItem(item), font: patch.font };
        updated.h = layoutText(updated).h;
        before.push(copyItem(item));
        after.push(updated);
      }
    });
    if (!after.length) return;
    remember(before, after);
    after.forEach((item) => commitItem(item));
  }, [commitItem, remember]);

  const removeSelection = React.useCallback(() => {
    const ids = [...selectionRef.current];
    if (!ids.length) return;
    const before = ids
      .map((id) => (docRef.current.items || []).find((item) => item.id === id))
      .filter(Boolean)
      .map(copyItem);
    setSelection([]);
    remember(before, []);
    commitRemove(ids);
  }, [commitRemove, remember, setSelection]);

  const placeImage = React.useCallback(async (src, x, y, center = false) => {
    const size = await loadImageSize(src);
    if (!size) return false;
    const fitted = fittedSize(size);
    const item = {
      id: newId(),
      type: 'image',
      src,
      x: clampWorld(center ? x - fitted.w / 2 : x),
      y: clampWorld(center ? y - fitted.h / 2 : y),
      w: fitted.w,
      h: fitted.h,
    };
    remember([], [item]);
    commitItem(item);
    return true;
  }, [commitItem, remember]);

  const addImageFile = React.useCallback(async (file) => {
    if (!file || !String(file.type || '').startsWith('image/')) {
      setNotice('Нужна картинка: png, jpg или webp.');
      return;
    }
    try {
      setStatus('Загружаем картинку…');
      const data = await window.uploadBoardAsset(file);
      if (!data?.url) throw new Error('Не удалось загрузить картинку');
      const cam = cameraRef.current;
      const ok = await placeImage(data.url, cam.x, cam.y, true);
      if (!ok) throw new Error('Картинка не открылась');
      setStatus(socketOpen() ? 'На связи' : 'Сохранено');
    } catch (err) {
      setNotice(err?.message || 'Не удалось поставить картинку');
      setStatus(socketOpen() ? 'На связи' : 'Нет связи');
    }
  }, [placeImage, socketOpen]);

  React.useEffect(() => {
    if (!token) return undefined;
    if (!whiteboardFeatureEnabled()) {
      setError('Доска отключена на сервере.');
      return undefined;
    }
    stoppedRef.current = false;
    let cancelled = false;
    const pendingImport = !ownerFromQuery && window.consumeLessonBoardImport
      ? window.consumeLessonBoardImport()
      : null;
    if (pendingImport?.backRoute) {
      setBackNav({ route: pendingImport.backRoute, query: pendingImport.backQuery || {} });
    }
    const tokenPath = ownerFromQuery
      ? `/api/communication/whiteboard/users/${encodeURIComponent(ownerFromQuery)}/token/`
      : '/api/communication/whiteboard/studio/token/';

    const connect = () => {
      if (cancelled || stoppedRef.current || !ownerIdRef.current) return;
      const access = window.getAccessToken();
      if (!access) return;
      const url = `${window.getWsBase()}/ws/whiteboard/${encodeURIComponent(ownerIdRef.current)}/?token=${encodeURIComponent(access)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => {
        if (!cancelled) setStatus('На связи');
      };
      ws.onmessage = (event) => {
        let message;
        try { message = JSON.parse(event.data); } catch (_) { return; }
        const payload = message.payload || {};
        const fromMe = payload.client === clientIdRef.current;
        if (message.event === 'hello') applyRemoteHello(payload.document);
        else if (message.event === 'live' && payload.item && !fromMe) {
          remoteLiveRef.current[payload.item.id] = payload.item;
          scheduleDraw();
        } else if (message.event === 'commit' && payload.item) {
          upsertFromServer(payload.item, payload.revision, fromMe);
        } else if (message.event === 'remove') {
          removeFromServer(payload.ids || [], payload.revision, fromMe);
        } else if (message.event === 'error' && payload.detail) {
          setNotice(payload.detail);
        }
      };
      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null;
        if (cancelled || stoppedRef.current) return;
        setStatus('Нет связи — рисунок сохранится');
        retryTimerRef.current = window.setTimeout(connect, 1500);
      };
    };

    (async () => {
      setError('');
      try {
        const data = await window.apiJson(tokenPath, { method: 'POST', auth: true, body: {} });
        if (cancelled) return;
        const ownerId = data.owner_public_id || ownerFromQuery;
        ownerIdRef.current = ownerId;
        snapUrlRef.current = `/api/communication/whiteboard/users/${encodeURIComponent(ownerId)}/snapshot/`;
        setOwnerName(data.owner_name || '');
        setIsOwn(typeof data.is_own === 'boolean' ? data.is_own : !ownerFromQuery);
        setBoard(readBoard(data.snapshot));
        setReady(true);
        const fitNow = () => {
          if (cancelled || fittedRef.current) return;
          const canvas = canvasRef.current;
          if (!canvas) return;
          const view = viewOf(canvas);
          if (view.rect.width < 8 || view.rect.height < 8) return;
          cameraRef.current = fitCamera(
            docRef.current.items,
            view.rect.width,
            view.rect.height,
          );
          setViewScale(cameraRef.current.scale);
          fittedRef.current = true;
          paintRef.current();
        };
        window.requestAnimationFrame(() => {
          fitNow();
          if (!fittedRef.current) window.requestAnimationFrame(fitNow);
        });
        connect();
        if (pendingImport?.urls?.length) {
          const title = pendingImport.title
            ? `Картинка с задания «${pendingImport.title}».`
            : 'Картинка задания на доске.';
          let x = 24;
          let placed = 0;
          const failed = [];
          for (const src of pendingImport.urls) {
            const ok = await placeImage(src, x, 24);
            if (ok) {
              placed += 1;
              x += 520;
            } else failed.push(src);
          }
          if (!cancelled && placed) setNotice(`${title} Рисуйте поверх.`);
          if (!cancelled && failed.length) setSideImages(failed);
        }
      } catch (err) {
        if (!cancelled) setError(err?.message || 'Не удалось открыть доску.');
      }
    })();

    const saveOnLeave = () => flushSnapshot(docRef.current);
    window.addEventListener('pagehide', saveOnLeave);

    return () => {
      saveOnLeave();
      window.removeEventListener('pagehide', saveOnLeave);
      cancelled = true;
      stoppedRef.current = true;
      window.clearTimeout(saveTimerRef.current);
      window.clearTimeout(retryTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [
    token,
    ownerFromQuery,
    applyRemoteHello,
    flushSnapshot,
    placeImage,
    removeFromServer,
    scheduleDraw,
    setBoard,
    upsertFromServer,
  ]);

  React.useEffect(() => {
    const typing = (event) => {
      const tag = event.target && event.target.tagName;
      return tag === 'INPUT' || tag === 'TEXTAREA' || event.target?.isContentEditable;
    };
    const down = (event) => {
      if ((event.ctrlKey || event.metaKey) && !typing(event) && (event.code === 'KeyZ' || event.code === 'KeyY')) {
        event.preventDefault();
        if (event.code === 'KeyY' || event.shiftKey) redo();
        else undo();
        return;
      }
      if (typing(event)) return;
      if (event.code === 'Space') {
        spaceRef.current = true;
        event.preventDefault();
        return;
      }
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        removeSelection();
      }
    };
    const up = (event) => {
      if (event.code === 'Space') spaceRef.current = false;
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, [redo, removeSelection, undo]);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !ready) return undefined;
    const onWheel = (event) => {
      event.preventDefault();
      const view = metricsRef.current || viewOf(canvas);
      const cam = cameraRef.current;
      if (event.ctrlKey || event.metaKey) {
        const factor = event.deltaY < 0 ? 1.08 : 1 / 1.08;
        const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, cam.scale * factor));
        const sx = event.clientX - view.rect.left;
        const sy = event.clientY - view.rect.top;
        const wx = (sx - view.rect.width / 2) / cam.scale + cam.x;
        const wy = (sy - view.rect.height / 2) / cam.scale + cam.y;
        cam.scale = scale;
        cam.x = wx - (sx - view.rect.width / 2) / scale;
        cam.y = wy - (sy - view.rect.height / 2) / scale;
        setViewScale(scale);
      } else {
        cam.x += event.deltaX / cam.scale;
        cam.y += event.deltaY / cam.scale;
      }
      scheduleDraw();
    };
    canvas.addEventListener('wheel', onWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', onWheel);
  }, [ready, scheduleDraw]);

  React.useEffect(() => {
    if (!ready) return undefined;
    const onPaste = (event) => {
      const tag = event.target && event.target.tagName;
      if (tag === 'TEXTAREA' || tag === 'INPUT') return;
      const list = event.clipboardData && event.clipboardData.items;
      if (!list) return;
      let file = null;
      for (let i = 0; i < list.length; i += 1) {
        if (String(list[i].type || '').startsWith('image/')) {
          file = list[i].getAsFile();
          break;
        }
      }
      if (!file) return;
      event.preventDefault();
      const type = file.type || 'image/png';
      const named = /\.(png|jpe?g|gif|webp)$/i.test(file.name || '');
      const ext = type.includes('jpeg') ? 'jpg' : (type.split('/')[1] || 'png');
      const readyFile = named ? file : new File([file], `paste.${ext}`, { type });
      addImageFile(readyFile);
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [ready, addImageFile]);

  const queueLiveItems = (items) => {
    const list = (items || []).filter(Boolean);
    if (!list.length) return;
    liveItemRef.current = list[list.length - 1];
    if (liveTimerRef.current) return;
    list.forEach((item) => {
      sendJson({
        event: 'live',
        payload: { client: clientIdRef.current, item: copyItem(item) },
      });
    });
    liveTimerRef.current = window.setTimeout(() => {
      liveTimerRef.current = 0;
    }, 40);
  };

  const finishStroke = React.useCallback(() => {
    if (liveTimerRef.current) {
      window.clearTimeout(liveTimerRef.current);
      liveTimerRef.current = 0;
    }
    const stroke = localStrokeRef.current;
    localStrokeRef.current = null;
    if (!stroke || !(stroke.points || []).length) {
      scheduleDraw();
      return;
    }
    remember([], [stroke]);
    commitItem(stroke);
  }, [commitItem, remember, scheduleDraw]);

  const finishDrag = () => {
    if (liveTimerRef.current) {
      window.clearTimeout(liveTimerRef.current);
      liveTimerRef.current = 0;
    }
    const drag = dragRef.current;
    dragRef.current = null;
    liveItemRef.current = null;
    if (!drag || !drag.moved) {
      if (drag && drag.hitId && (drag.ids || []).length > 1) setSelection([drag.hitId]);
      scheduleDraw();
      return;
    }
    const ids = drag.ids || (drag.id ? [drag.id] : []);
    const before = ids.map((id) => drag.origins[id]).filter(Boolean);
    const moved = ids
      .map((id) => (docRef.current.items || []).find((row) => row.id === id))
      .filter(Boolean);
    if (moved.length) {
      remember(before, moved);
      moved.forEach((item) => commitItem(item));
    } else scheduleDraw();
  };

  const finishResize = () => {
    if (liveTimerRef.current) {
      window.clearTimeout(liveTimerRef.current);
      liveTimerRef.current = 0;
    }
    const resize = resizeRef.current;
    resizeRef.current = null;
    if (!resize || !resize.moved) {
      scheduleDraw();
      return;
    }
    const ids = Object.keys(resize.origins);
    const before = ids.map((id) => resize.origins[id]).filter(Boolean);
    const after = ids
      .map((id) => (docRef.current.items || []).find((row) => row.id === id))
      .filter(Boolean);
    if (after.length) {
      remember(before, after);
      after.forEach((item) => commitItem(item));
    } else scheduleDraw();
  };

  const zoomBy = (factor) => {
    const cam = cameraRef.current;
    const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, cam.scale * factor));
    cameraRef.current = { ...cam, scale };
    setViewScale(scale);
    scheduleDraw();
  };

  const showAll = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const view = viewOf(canvas);
    const next = fitCamera(docRef.current.items, view.rect.width, view.rect.height);
    cameraRef.current = next;
    setViewScale(next.scale);
    scheduleDraw();
  };

  const onPointerDown = (event) => {
    if (!ready) return;
    const button = event.button;
    if (button != null && button !== 0 && button !== 1) return;
    const wantsPan = button === 1 || spaceRef.current || toolRef.current === 'hand';
    if (wantsPan) {
      if (button === 1) event.preventDefault();
      panRef.current = { x: event.clientX, y: event.clientY };
      event.currentTarget.style.cursor = 'grabbing';
      event.currentTarget.dataset.cursor = 'grabbing';
      event.currentTarget.setPointerCapture?.(event.pointerId);
      return;
    }
    const point = worldFromEvent(
      event,
      metricsRef.current || viewOf(event.currentTarget),
      cameraRef.current,
    );
    if (!point) return;
    if (editorRef.current) commitEditor();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    const pad = 10 / (cameraRef.current.scale || 1);
    const hit = topItem(docRef.current.items, point[0], point[1], pad);
    if (toolRef.current === 'text') {
      event.currentTarget.releasePointerCapture?.(event.pointerId);
      if (hit && hit.type === 'text') openEditor(hit, false);
      else {
        openEditor({
          id: newId(),
          x: point[0],
          y: point[1],
          text: '',
          color: colorRef.current,
          font: fontRef.current,
          size: TEXT_SIZE,
        }, true);
      }
      return;
    }
    if (toolRef.current === 'select') {
      const selectedNow = (docRef.current.items || []).filter((item) => selectionRef.current.has(item.id));
      const rawFrame = unionBounds(selectedNow);
      const frame = rawFrame ? paddedBox(rawFrame, cameraRef.current.scale || 1) : null;
      const hasSelection = !!frame;
      const handle = hasSelection ? hitHandle(point, frame, cameraRef.current.scale || 1) : null;
      if (handle) {
        const origins = {};
        selectedNow.forEach((item) => { origins[item.id] = copyItem(item); });
        resizeRef.current = { handle, origins, bounds: frame, start: point, moved: false };
        scheduleDraw();
        return;
      }
      const inside = hasSelection && pointInBox(point, frame);
      if (hit || inside) {
        const ids = hit && !selectionRef.current.has(hit.id) ? [hit.id] : [...selectionRef.current];
        setSelection(ids);
        const picked = hit && ids.length === 1 ? hit : null;
        if (picked && picked.color) {
          colorRef.current = picked.color;
          setColor(picked.color);
        }
        if (picked && picked.type === 'text' && picked.font) {
          fontRef.current = picked.font;
          setFont(picked.font);
        }
        const origins = {};
        ids.forEach((id) => {
          const row = (docRef.current.items || []).find((item) => item.id === id);
          if (row) origins[id] = copyItem(row);
        });
        dragRef.current = { ids, start: point, origins, moved: false, hitId: hit ? hit.id : null };
      } else {
        setSelection([]);
        marqueeRef.current = { x0: point[0], y0: point[1], x1: point[0], y1: point[1] };
      }
      scheduleDraw();
      return;
    }
    if (toolRef.current !== 'pen') return;
    localStrokeRef.current = {
      id: newId(),
      type: 'stroke',
      color: colorRef.current,
      size: 5,
      points: [point],
    };
    scheduleDraw();
  };

  const onPointerMove = (event) => {
    if (panRef.current) {
      const pan = panRef.current;
      const cam = cameraRef.current;
      cam.x -= (event.clientX - pan.x) / cam.scale;
      cam.y -= (event.clientY - pan.y) / cam.scale;
      pan.x = event.clientX;
      pan.y = event.clientY;
      scheduleDraw();
      return;
    }
    const point = worldFromEvent(
      event,
      metricsRef.current || viewOf(event.currentTarget),
      cameraRef.current,
    );
    if (resizeRef.current && point) {
      const resize = resizeRef.current;
      const dx = point[0] - resize.start[0];
      const dy = point[1] - resize.start[1];
      const scale = cameraRef.current.scale || 1;
      if (!resize.moved && (dx * dx + dy * dy) * scale * scale < 9) return;
      resize.moved = true;
      const moved = resizedItems(resize.origins, resize.bounds, resize.handle, point);
      const byId = new Map(moved.map((item) => [item.id, item]));
      const doc = docRef.current;
      docRef.current = {
        ...doc,
        items: doc.items.map((row) => byId.get(row.id) || row),
      };
      queueLiveItems(moved);
      scheduleDraw();
      return;
    }
    if (marqueeRef.current && point) {
      marqueeRef.current.x1 = point[0];
      marqueeRef.current.y1 = point[1];
      scheduleDraw();
      return;
    }
    if (dragRef.current) {
      if (!point) return;
      const drag = dragRef.current;
      const dx = point[0] - drag.start[0];
      const dy = point[1] - drag.start[1];
      const scale = cameraRef.current.scale || 1;
      if (!drag.moved && (dx * dx + dy * dy) * scale * scale < 9) return;
      drag.moved = true;
      const moved = [];
      const doc = docRef.current;
      const items = doc.items.map((row) => {
        const origin = drag.origins[row.id];
        if (!origin) return row;
        const next = movedItem(origin, dx, dy);
        moved.push(next);
        return next;
      });
      docRef.current = { ...doc, items };
      queueLiveItems(moved);
      scheduleDraw();
      return;
    }
    if (point && !localStrokeRef.current && toolRef.current === 'select') {
      const selectedNow = (docRef.current.items || []).filter((item) => selectionRef.current.has(item.id));
      const raw = unionBounds(selectedNow);
      const frame = raw ? paddedBox(raw, cameraRef.current.scale || 1) : null;
      const handle = hitHandle(point, frame, cameraRef.current.scale || 1);
      const cursor = handle ? HANDLE_CURSOR[handle] : 'default';
      event.currentTarget.style.cursor = cursor;
      event.currentTarget.dataset.cursor = cursor;
    }
    const stroke = localStrokeRef.current;
    if (!stroke || !point) return;
    const last = stroke.points[stroke.points.length - 1];
    const dx = point[0] - last[0];
    const dy = point[1] - last[1];
    const min = 2 / (cameraRef.current.scale || 1);
    if (dx * dx + dy * dy < min * min) return;
    stroke.points.push(point);
    if (stroke.points.length >= 2500) {
      finishStroke();
      localStrokeRef.current = {
        id: newId(),
        type: 'stroke',
        color: colorRef.current,
        size: 5,
        points: [point],
      };
    } else {
      queueLiveItems([stroke]);
    }
    scheduleDraw();
  };

  const onPointerUp = (event) => {
    const canvas = event.currentTarget;
    if (canvas && canvas.dataset) {
      const cursor = toolCursor(toolRef.current);
      canvas.style.cursor = cursor;
      canvas.dataset.cursor = cursor;
    }
    if (panRef.current) {
      panRef.current = null;
      scheduleDraw();
      return;
    }
    if (resizeRef.current) {
      finishResize();
      return;
    }
    if (marqueeRef.current) {
      const area = boxFromCorners(
        marqueeRef.current.x0,
        marqueeRef.current.y0,
        marqueeRef.current.x1,
        marqueeRef.current.y1,
      );
      const wide = (area.maxX - area.minX) > 4 || (area.maxY - area.minY) > 4;
      if (wide) {
        const ids = (docRef.current.items || [])
          .filter((item) => boundsOverlap(itemBounds(item), area))
          .map((item) => item.id);
        setSelection(ids);
      }
      marqueeRef.current = null;
      scheduleDraw();
      return;
    }
    if (dragRef.current) {
      finishDrag();
      return;
    }
    if (toolRef.current === 'pen') finishStroke();
    scheduleDraw();
  };

  const onDoubleClick = (event) => {
    if (!ready || toolRef.current !== 'select') return;
    const point = worldFromEvent(
      event,
      metricsRef.current || viewOf(event.currentTarget),
      cameraRef.current,
    );
    if (!point) return;
    const pad = 10 / (cameraRef.current.scale || 1);
    const hit = topItem(docRef.current.items, point[0], point[1], pad);
    if (hit && hit.type === 'text') openEditor(hit, false);
  };

  const onPickImage = (event) => {
    const file = event.target.files && event.target.files[0];
    event.target.value = '';
    if (file) addImageFile(file);
  };

  if (!token) {
    return (
      <div className="mx-auto max-w-md px-5 py-20 text-center">
        <div className="text-2xl font-bold text-ink">Нужен вход</div>
        <p className="mt-2 text-sm text-ink/60">Доска доступна после авторизации.</p>
        <button
          type="button"
          onClick={() => navigate(Routes.AUTH)}
          className="btn-grad mt-6 h-11 rounded-xl px-6 text-sm font-semibold text-white"
        >
          Войти
        </button>
      </div>
    );
  }

  const canUndo = historyTick >= 0 && historyRef.current.undo.length > 0;
  const canRedo = historyRef.current.redo.length > 0;
  const showFont = tool === 'text' || !!editor || (docRef.current.items || []).some(
    (item) => item.type === 'text' && selectionIds.includes(item.id),
  );
  const iconBtn = (active) => `h-9 w-9 rounded-xl inline-flex items-center justify-center ${active ? 'bg-sky-50 text-sky-800' : 'text-ink/70 hover:bg-black/[0.04]'} disabled:opacity-30`;
  const hint = tool === 'select'
    ? (selectionIds.length
      ? 'Перетащите синюю рамку — сдвинется всё внутри. Уголки меняют размер.'
      : 'Потяните по пустому месту: появится рамка вокруг объектов.')
    : 'Ctrl+Z отменяет действие. Ctrl+V вставляет картинку.';

  return (
    <div className={`${embedded ? 'absolute inset-0' : 'h-full'} min-h-0 bg-[#F6F8FC] flex flex-col`} data-board-embed={embedded ? '1' : '0'}>
      {!embedded && <div className="shrink-0 h-14 px-3 sm:px-5 flex items-center gap-3 border-b border-black/[0.08] bg-white">
        <button
          type="button"
          onClick={() => {
            if (backNav?.route) navigate(backNav.route, backNav.query);
            else if (!isOwn) navigate(Routes.MENTOR);
            else navigate(Routes.PROFILE);
          }}
          className="h-9 px-3 rounded-lg text-sm font-medium text-ink/70 hover:bg-black/[0.04] shrink-0"
        >
          ← {backNav?.route ? 'К заданию' : (!isOwn ? 'К ученикам' : 'Назад')}
        </button>
        <div className="min-w-0 flex-1">
          <div className="text-base font-semibold text-ink truncate">
            {isOwn ? 'Моя доска' : `Доска: ${ownerName || 'ученик'}`}
          </div>
          <div className="text-xs text-ink/50 truncate">
            {isOwn
              ? 'Ctrl+Z отменяет. Ctrl+V — картинка. Колёсико двигает лист.'
              : 'Можно рисовать вместе. Ctrl+Z отменяет. Ctrl+V — картинка.'}
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate(Routes.CONFERENCES)}
          className="h-9 px-3 rounded-lg text-sm font-semibold text-sky-700 hover:bg-sky-50 shrink-0"
        >
          Созвоны
        </button>
      </div>}
      <div className="relative flex-1 min-h-0 overflow-hidden flex flex-col lg:flex-row">
        {sideImages.length > 0 && (
          <div className="shrink-0 lg:w-[42%] max-h-[38vh] lg:max-h-none lg:h-full overflow-auto bg-white border-b lg:border-b-0 lg:border-r border-black/[0.08] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-2">
              Схема задания
            </div>
            {sideImages.map((src) => (
              <img
                key={src}
                src={src}
                alt="Схема задания"
                className="w-full h-auto rounded-lg ring-1 ring-black/[0.06] bg-[#fafafa] mb-3"
              />
            ))}
          </div>
        )}
        <div className="relative flex-1 min-h-0 overflow-hidden">
          {error && (
            <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-3 px-6 text-center bg-[#F6F8FC]">
              <div className="text-sm text-rose-600">{error}</div>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold"
              >
                Обновить
              </button>
            </div>
          )}
          <canvas
            ref={canvasRef}
            data-board="academy"
            data-ready={ready ? '1' : '0'}
            data-zoom={viewScale}
            data-tool={tool}
            data-color={color}
            data-font={font}
            data-selection={selectionIds.join(',')}
            className="absolute inset-0 h-full w-full touch-none"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            onDoubleClick={onDoubleClick}
            onAuxClick={(event) => event.preventDefault()}
          />
          {editor && (
            <textarea
              key={editor.id}
              ref={editorNodeRef}
              autoFocus
              data-board-text="1"
              aria-label="Текст на доске"
              value={editor.text}
              rows={Math.min(8, Math.max(2, editor.text.split('\n').length))}
              onChange={(event) => {
                const text = event.target.value.slice(0, 500);
                const next = { ...(editorRef.current || editor), text };
                editorRef.current = next;
                setEditor(next);
              }}
              onBlur={() => {
                if (ignoreEditorBlurRef.current) return;
                if (!editorRef.current || editorRef.current.id !== editor.id) return;
                commitEditor();
              }}
              onPointerDown={(event) => event.stopPropagation()}
              onKeyDown={(event) => {
                event.stopPropagation();
                if (event.key === 'Escape') {
                  event.preventDefault();
                  event.currentTarget.blur();
                }
              }}
              className="absolute z-30 resize-none rounded-md bg-white/95 px-1 py-0.5 shadow-soft ring-1 ring-sky-300 outline-none"
              style={{
                left: canvasRef.current
                  ? (editor.x - cameraRef.current.x) * cameraRef.current.scale
                    + canvasRef.current.getBoundingClientRect().width / 2
                  : 0,
                top: canvasRef.current
                  ? (editor.y - cameraRef.current.y) * cameraRef.current.scale
                    + canvasRef.current.getBoundingClientRect().height / 2
                  : 0,
                width: (editor.w || TEXT_WRAP) * (cameraRef.current.scale || 1),
                fontSize: (editor.size || TEXT_SIZE) * (cameraRef.current.scale || 1),
                fontFamily: fontCss(editor.font),
                color: editor.color,
                lineHeight: 1.35,
              }}
            />
          )}
          <div className="absolute top-3 left-3 right-3 z-20 flex flex-wrap items-center gap-2 pointer-events-none">
            <div className="pointer-events-auto flex flex-wrap items-center gap-1 rounded-2xl bg-white/95 p-1 shadow-soft ring-1 ring-black/[0.06]">
              <button type="button" title="Отменить (Ctrl+Z)" aria-label="Отменить" disabled={!canUndo} onClick={undo} className={iconBtn(false)}>
                <Icon><path d="M8 8H4v4" /><path d="M4 11a8 8 0 1 0 2.5-5.5L4 8" /></Icon>
              </button>
              <button type="button" title="Повторить (Ctrl+Y)" aria-label="Повторить" disabled={!canRedo} onClick={redo} className={iconBtn(false)}>
                <Icon><path d="M16 8h4v4" /><path d="M20 11a8 8 0 1 1-2.5-5.5L20 8" /></Icon>
              </button>
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              <button type="button" title="Выбор" aria-label="Выбор" aria-pressed={tool === 'select'} onClick={() => setTool('select')} className={iconBtn(tool === 'select')}>
                <Icon><path d="M5 4l7 16 1.8-6.2L20 12z" /></Icon>
              </button>
              <button type="button" title="Ручка" aria-label="Ручка" aria-pressed={tool === 'pen'} onClick={() => setTool('pen')} className={iconBtn(tool === 'pen')}>
                <Icon><path d="M4 20l4.2-.8L19 8.4 15.6 5 4.8 15.8z" /><path d="M13.5 7l3.5 3.5" /></Icon>
              </button>
              <button type="button" title="Текст" aria-label="Текст" aria-pressed={tool === 'text'} onClick={() => setTool('text')} className={iconBtn(tool === 'text')}>
                <Icon><path d="M5 6h14" /><path d="M12 6v12" /><path d="M8 18h8" /></Icon>
              </button>
              <button type="button" title="Рука — сдвинуть лист" aria-label="Рука" aria-pressed={tool === 'hand'} onClick={() => setTool('hand')} className={iconBtn(tool === 'hand')}>
                <Icon><path d="M8 11V6.5a1.5 1.5 0 0 1 3 0V11" /><path d="M11 10V5.5a1.5 1.5 0 0 1 3 0V11" /><path d="M14 11V7.5a1.5 1.5 0 0 1 3 0V14a5 5 0 0 1-5 5h-1.5A5.5 5.5 0 0 1 5 13.5V11a1.5 1.5 0 0 1 3 0" /></Icon>
              </button>
              <button type="button" title="Картинка. Ещё можно Ctrl+V" aria-label="Картинка" onClick={() => fileRef.current?.click()} className={iconBtn(false)}>
                <Icon><rect x="4" y="5" width="16" height="14" rx="2" /><circle cx="9" cy="10" r="1.3" /><path d="M4 16l4.2-3.6 2.8 2.4L15 11l5 5" /></Icon>
              </button>
              <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={onPickImage} />
              {selectionIds.length > 0 && (
                <button type="button" title="Удалить выделенное" aria-label="Удалить" onClick={removeSelection} className={`${iconBtn(false)} text-rose-700`}>
                  <Icon><path d="M5 7h14" /><path d="M9 7V5h6v2" /><path d="M8 7l1 12h6l1-12" /></Icon>
                </button>
              )}
              {showFont && (
                <select
                  aria-label="Шрифт"
                  title="Шрифт"
                  value={font}
                  onChange={(event) => applyStyle({ font: event.target.value })}
                  className="h-9 max-w-[9.5rem] rounded-xl bg-transparent px-2 text-sm font-semibold text-ink/80"
                  style={{ fontFamily: fontCss(font) }}
                >
                  {FONTS.map((row) => (
                    <option key={row.value} value={row.value}>{row.label}</option>
                  ))}
                </select>
              )}
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              {PEN_COLORS.map((swatch) => (
                <button
                  key={swatch.value}
                  type="button"
                  data-swatch={swatch.value}
                  aria-label={swatch.label}
                  title={swatch.label}
                  onClick={() => applyStyle({ color: swatch.value })}
                  className={`h-6 w-6 rounded-full ring-2 ring-offset-1 ${color === swatch.value ? 'ring-sky-500' : 'ring-transparent'}`}
                  style={{ background: swatch.value }}
                />
              ))}
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              <button type="button" title="Отдалить" aria-label="Отдалить" onClick={() => zoomBy(1 / 1.2)} className={iconBtn(false)}>
                <Icon><path d="M6 12h12" /></Icon>
              </button>
              <span className="min-w-[3rem] text-center text-xs font-semibold text-ink/60">{Math.round(viewScale * 100)}%</span>
              <button type="button" title="Приблизить" aria-label="Приблизить" onClick={() => zoomBy(1.2)} className={iconBtn(false)}>
                <Icon><path d="M12 6v12" /><path d="M6 12h12" /></Icon>
              </button>
              <button type="button" title="Показать всё" aria-label="Показать всё" onClick={showAll} className={iconBtn(false)}>
                <Icon><path d="M9 4H4v5" /><path d="M15 4h5v5" /><path d="M9 20H4v-5" /><path d="M15 20h5v-5" /></Icon>
              </button>
            </div>
          </div>
          <div data-board-hint className="pointer-events-none absolute bottom-3 left-3 z-20 max-w-[22rem] rounded-full bg-white/95 px-3 py-1.5 text-[12px] text-ink/70 ring-1 ring-black/[0.06]">
            {hint}
          </div>
          <div
            data-board-status={status}
            className="absolute bottom-3 right-3 z-20 rounded-full bg-white/95 px-3 py-1 text-[12px] text-ink/60 ring-1 ring-black/[0.06]"
          >
            {status}
          </div>
          {notice && !error && (
            <div className="absolute left-3 right-3 sm:left-auto sm:right-4 bottom-12 z-20 max-w-md rounded-xl bg-white/95 ring-1 ring-violet-200 shadow-soft px-4 py-3 text-sm text-ink/80">
              {notice}
              <button
                type="button"
                onClick={() => setNotice('')}
                className="mt-2 block text-[12px] font-semibold text-violet-700"
              >
                Скрыть
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { WhiteboardPage });
