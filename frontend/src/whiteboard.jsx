// Общая доска школы. Страница не монтирует tldraw: без лицензии он гасит холст.

const Routes = window.Routes;

const WORLD_MIN = -1000000;
const WORLD_MAX = 1000000;
const MIN_SCALE = 0.2;
const MAX_SCALE = 4;
const DOT = 32;
const PEN_COLORS = [
  { value: '#0B1226', label: 'Чёрный' },
  { value: '#2563EB', label: 'Синий' },
  { value: '#E11D48', label: 'Красный' },
  { value: '#059669', label: 'Зелёный' },
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

function layoutText(item) {
  const size = Number(item.size) || TEXT_SIZE;
  const key = `${item.font}|${size}|${item.text}`;
  const cached = layoutCache.get(key);
  if (cached) return cached;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.font = `${size}px ${fontCss(item.font)}`;
  const lines = wrapText(ctx, item.text || '', TEXT_WRAP);
  const lineH = size * 1.35;
  let width = 8;
  lines.forEach((line) => {
    width = Math.max(width, ctx.measureText(line || ' ').width);
  });
  const result = {
    lines,
    lineH,
    w: Math.min(4000, Math.max(8, Math.round(width + 8))),
    h: Math.min(4000, Math.max(8, Math.round(lines.length * lineH + 4))),
  };
  layoutCache.set(key, result);
  if (layoutCache.size > 200) layoutCache.delete(layoutCache.keys().next().value);
  return result;
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

function WhiteboardPage({ navigate, hashParams }) {
  const token = window.getAccessToken();
  const ownerFromQuery = hashParams?.get('user') || '';
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
    toolRef.current = tool;
  }, [tool]);

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
        const gap = 6 / camera.scale;
        ctx.save();
        ctx.strokeStyle = 'rgba(37, 99, 235, 0.95)';
        ctx.lineWidth = 1.5 / camera.scale;
        ctx.setLineDash([7 / camera.scale, 5 / camera.scale]);
        if (fill) {
          ctx.fillStyle = 'rgba(37, 99, 235, 0.08)';
          ctx.fillRect(box.minX, box.minY, box.maxX - box.minX, box.maxY - box.minY);
        }
        ctx.strokeRect(
          box.minX - (fill ? 0 : gap),
          box.minY - (fill ? 0 : gap),
          box.maxX - box.minX + (fill ? 0 : gap * 2),
          box.maxY - box.minY + (fill ? 0 : gap * 2),
        );
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
      drawFrame(unionBounds(selected), false);
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

  const commitItem = React.useCallback((item) => {
    markDirty();
    pendingRef.current.removes.delete(item.id);
    pendingRef.current.upserts.set(item.id, item);
    const doc = docRef.current;
    const next = {
      ...doc,
      items: doc.items.filter((row) => row.id !== item.id).concat(item),
    };
    setBoard(next);
    flushSnapshot(next);
    const sent = sendJson({
      event: 'commit',
      payload: { client: clientIdRef.current, item },
    });
    if (!sent) {
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
    flushSnapshot(next);
    const sent = sendJson({
      event: 'remove',
      payload: { client: clientIdRef.current, ids },
    });
    if (!sent) persistSoon();
  }, [flushSnapshot, markDirty, persistSoon, sendJson, setBoard]);

  const commitEditor = React.useCallback(() => {
    const current = editorRef.current;
    if (!current) return;
    editorRef.current = null;
    setEditor(null);
    const text = String(current.text || '').replace(/\u0000/g, '').trim();
    if (!text) {
      if (!current.isNew) commitRemove([current.id]);
      setSelection(selectionRef.current.has(current.id)
        ? [...selectionRef.current].filter((id) => id !== current.id)
        : [...selectionRef.current]);
      scheduleDraw();
      return;
    }
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
    const box = layoutText(item);
    commitItem({ ...item, w: box.w, h: box.h });
    setSelection([item.id]);
    scheduleDraw();
  }, [commitItem, commitRemove, scheduleDraw, setSelection]);

  const openEditor = React.useCallback((item, isNew) => {
    const next = {
      id: item.id,
      x: item.x,
      y: item.y,
      text: item.text || '',
      color: item.color || colorRef.current,
      font: item.font || fontRef.current,
      size: item.size || TEXT_SIZE,
      isNew: !!isNew,
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
    (docRef.current.items || []).forEach((item) => {
      if (!ids.has(item.id)) return;
      if (patch.color && (item.type === 'stroke' || item.type === 'text')) {
        const updated = { ...copyItem(item), color: patch.color };
        if (updated.type === 'text') {
          const box = layoutText(updated);
          updated.w = box.w;
          updated.h = box.h;
        }
        commitItem(updated);
      } else if (patch.font && item.type === 'text') {
        const updated = { ...item, font: patch.font };
        const box = layoutText(updated);
        commitItem({ ...updated, w: box.w, h: box.h });
      }
    });
  }, [commitItem]);

  const removeSelection = React.useCallback(() => {
    const ids = [...selectionRef.current];
    if (!ids.length) return;
    setSelection([]);
    commitRemove(ids);
  }, [commitRemove, setSelection]);

  const placeImage = React.useCallback(async (src, x, y, center = false) => {
    const size = await loadImageSize(src);
    if (!size) return false;
    const fitted = fittedSize(size);
    commitItem({
      id: newId(),
      type: 'image',
      src,
      x: clampWorld(center ? x - fitted.w / 2 : x),
      y: clampWorld(center ? y - fitted.h / 2 : y),
      w: fitted.w,
      h: fitted.h,
    });
    return true;
  }, [commitItem]);

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
  }, [removeSelection]);

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
    commitItem(stroke);
  }, [commitItem, scheduleDraw]);

  const finishDrag = () => {
    if (liveTimerRef.current) {
      window.clearTimeout(liveTimerRef.current);
      liveTimerRef.current = 0;
    }
    const drag = dragRef.current;
    dragRef.current = null;
    liveItemRef.current = null;
    if (!drag || !drag.moved) {
      scheduleDraw();
      return;
    }
    const ids = drag.ids || (drag.id ? [drag.id] : []);
    const moved = ids
      .map((id) => (docRef.current.items || []).find((row) => row.id === id))
      .filter(Boolean);
    if (moved.length) moved.forEach((item) => commitItem(item));
    else scheduleDraw();
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
      if (hit) {
        const ids = selectionRef.current.has(hit.id)
          ? [...selectionRef.current]
          : [hit.id];
        setSelection(ids);
        if (ids.length === 1 && hit.color) {
          colorRef.current = hit.color;
          setColor(hit.color);
        }
        if (ids.length === 1 && hit.type === 'text' && hit.font) {
          fontRef.current = hit.font;
          setFont(hit.font);
        }
        const origins = {};
        ids.forEach((id) => {
          const row = (docRef.current.items || []).find((item) => item.id === id);
          if (row) origins[id] = copyItem(row);
        });
        dragRef.current = { ids, start: point, origins, moved: false };
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

  const onPointerUp = () => {
    if (panRef.current) {
      panRef.current = null;
      scheduleDraw();
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

  return (
    <div className="h-full min-h-0 bg-[#F6F8FC] flex flex-col">
      <div className="shrink-0 h-14 px-3 sm:px-5 flex items-center gap-3 border-b border-black/[0.08] bg-white">
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
              ? 'Выбор, ручка и текст. Рамкой можно сдвинуть сразу несколько. Ctrl+V — картинка.'
              : 'Можно рисовать вместе. Рамкой можно сдвинуть сразу несколько. Ctrl+V — картинка.'}
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate(Routes.CONFERENCES)}
          className="h-9 px-3 rounded-lg text-sm font-semibold text-sky-700 hover:bg-sky-50 shrink-0"
        >
          Созвоны
        </button>
      </div>
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
            className={`absolute inset-0 h-full w-full touch-none ${tool === 'hand' ? 'cursor-grab' : tool === 'text' ? 'cursor-text' : tool === 'pen' ? 'cursor-crosshair' : 'cursor-default'}`}
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
                width: TEXT_WRAP * (cameraRef.current.scale || 1),
                fontSize: (editor.size || TEXT_SIZE) * (cameraRef.current.scale || 1),
                fontFamily: fontCss(editor.font),
                color: editor.color,
                lineHeight: 1.35,
              }}
            />
          )}
          <div className="absolute top-3 left-3 right-3 z-20 flex flex-wrap items-center gap-2 pointer-events-none">
            <div className="pointer-events-auto flex flex-wrap items-center gap-1 rounded-2xl bg-white/95 p-1 shadow-soft ring-1 ring-black/[0.06]">
              <button
                type="button"
                aria-pressed={tool === 'select'}
                onClick={() => setTool('select')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'select' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Выбор
              </button>
              <button
                type="button"
                aria-pressed={tool === 'pen'}
                onClick={() => setTool('pen')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'pen' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Ручка
              </button>
              <button
                type="button"
                aria-pressed={tool === 'text'}
                onClick={() => setTool('text')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'text' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Текст
              </button>
              <button
                type="button"
                aria-pressed={tool === 'hand'}
                title="Сдвинуть лист"
                onClick={() => setTool('hand')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'hand' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Рука
              </button>
              <button
                type="button"
                title="Поставить картинку. Ещё можно Ctrl+V"
                onClick={() => fileRef.current?.click()}
                className="h-9 px-3 rounded-xl text-sm font-semibold text-ink/75 hover:bg-black/[0.04]"
              >
                Картинка
              </button>
              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                className="hidden"
                onChange={onPickImage}
              />
              {selectionIds.length > 0 && (
                <button
                  type="button"
                  onClick={removeSelection}
                  className="h-9 px-3 rounded-xl text-sm font-semibold text-rose-700 hover:bg-rose-50"
                >
                  Удалить
                </button>
              )}
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              <select
                aria-label="Шрифт"
                value={font}
                onChange={(event) => applyStyle({ font: event.target.value })}
                className="h-9 max-w-[9.5rem] rounded-xl bg-transparent px-2 text-sm font-semibold text-ink/80"
                style={{ fontFamily: fontCss(font) }}
              >
                {FONTS.map((row) => (
                  <option key={row.value} value={row.value}>{row.label}</option>
                ))}
              </select>
              {PEN_COLORS.map((swatch) => (
                <button
                  key={swatch.value}
                  type="button"
                  aria-label={swatch.label}
                  title={`${swatch.label}. Цвет линии и текста`}
                  onClick={() => applyStyle({ color: swatch.value })}
                  className={`h-7 w-7 rounded-full ring-2 ring-offset-2 ${color === swatch.value ? 'ring-sky-500' : 'ring-transparent'}`}
                  style={{ background: swatch.value }}
                />
              ))}
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              <button
                type="button"
                title="Отдалить"
                aria-label="Отдалить"
                onClick={() => zoomBy(1 / 1.2)}
                className="h-9 w-9 rounded-xl text-sm font-semibold text-ink/75 hover:bg-black/[0.04]"
              >
                −
              </button>
              <span className="min-w-[3rem] text-center text-xs font-semibold text-ink/60">
                {Math.round(viewScale * 100)}%
              </span>
              <button
                type="button"
                title="Приблизить"
                aria-label="Приблизить"
                onClick={() => zoomBy(1.2)}
                className="h-9 w-9 rounded-xl text-sm font-semibold text-ink/75 hover:bg-black/[0.04]"
              >
                +
              </button>
              <button
                type="button"
                title="Показать весь рисунок"
                onClick={showAll}
                className="h-9 px-3 rounded-xl text-sm font-semibold text-ink/75 hover:bg-black/[0.04]"
              >
                Всё
              </button>
            </div>
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
