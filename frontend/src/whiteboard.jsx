// Общая доска школы. Страница не монтирует tldraw: без лицензии он гасит холст.

const Routes = window.Routes;

const BOARD_W = 1600;
const BOARD_H = 1000;
const PEN_COLORS = [
  { value: '#0B1226', label: 'Чёрный' },
  { value: '#2563EB', label: 'Синий' },
  { value: '#E11D48', label: 'Красный' },
  { value: '#059669', label: 'Зелёный' },
];

function whiteboardFeatureEnabled() {
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  if (!meta) return true;
  return meta.getAttribute('content') !== 'false';
}

function emptyBoard() {
  return { kind: 'academy-board', version: 1, revision: 0, items: [] };
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

function hitsItem(item, x, y) {
  if (!item) return false;
  if (item.type === 'image') {
    return x >= item.x && y >= item.y && x <= item.x + item.w && y <= item.y + item.h;
  }
  const pts = item.points || [];
  const radius = 16 + (Number(item.size) || 4) / 2;
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

function measureCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const scale = Math.min(rect.width / BOARD_W, rect.height / BOARD_H) || 1;
  return {
    rect,
    scale,
    ox: (rect.width - BOARD_W * scale) / 2,
    oy: (rect.height - BOARD_H * scale) / 2,
    dpr: Math.min(window.devicePixelRatio || 1, 2),
  };
}

function pointOnBoard(event, metrics) {
  if (!metrics) return null;
  const x = (event.clientX - metrics.rect.left - metrics.ox) / metrics.scale;
  const y = (event.clientY - metrics.rect.top - metrics.oy) / metrics.scale;
  if (x < 0 || y < 0 || x > BOARD_W || y > BOARD_H) return null;
  return [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
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
  const toolRef = React.useRef('pen');
  const colorRef = React.useRef(PEN_COLORS[0].value);
  const eraserCursorRef = React.useRef(null);
  const imagesRef = React.useRef(new Map());
  const genRef = React.useRef(0);
  const saveTimerRef = React.useRef(0);
  const retryTimerRef = React.useRef(0);
  const stoppedRef = React.useRef(false);
  const ownerIdRef = React.useRef('');
  const snapUrlRef = React.useRef('');
  const paintRef = React.useRef(() => {});
  const fileRef = React.useRef(null);

  const [error, setError] = React.useState('');
  const [ready, setReady] = React.useState(false);
  const [tool, setTool] = React.useState('pen');
  const [color, setColor] = React.useState(PEN_COLORS[0].value);
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
          body: {
            snapshot: {
              kind: 'academy-board',
              version: 1,
              revision: doc.revision,
              items: doc.items,
            },
            base_revision: doc.revision,
          },
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
    if ((remote.revision || 0) < (local.revision || 0)) {
      const byId = new Map((remote.items || []).map((item) => [item.id, item]));
      local.items.forEach((item) => byId.set(item.id, item));
      pending.removes.forEach((id) => byId.delete(id));
      setBoard({ ...local, items: [...byId.values()] });
    } else {
      let items = (remote.items || []).filter((item) => !pending.removes.has(item.id));
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
    paintRef.current = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const metrics = measureCanvas(canvas);
      metricsRef.current = metrics;
      if (metrics.rect.width < 2 || metrics.rect.height < 2) return;
      const pxW = Math.round(metrics.rect.width * metrics.dpr);
      const pxH = Math.round(metrics.rect.height * metrics.dpr);
      if (canvas.width !== pxW || canvas.height !== pxH) {
        canvas.width = pxW;
        canvas.height = pxH;
      }
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
      ctx.clearRect(0, 0, metrics.rect.width, metrics.rect.height);
      ctx.fillStyle = '#F6F8FC';
      ctx.fillRect(0, 0, metrics.rect.width, metrics.rect.height);
      ctx.save();
      ctx.translate(metrics.ox, metrics.oy);
      ctx.scale(metrics.scale, metrics.scale);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, BOARD_W, BOARD_H);
      ctx.strokeStyle = 'rgba(11, 18, 38, 0.08)';
      ctx.lineWidth = 2;
      ctx.strokeRect(0, 0, BOARD_W, BOARD_H);
      ctx.fillStyle = 'rgba(11, 18, 38, 0.16)';
      for (let x = 32; x < BOARD_W; x += 32) {
        for (let y = 32; y < BOARD_H; y += 32) ctx.fillRect(x, y, 1.5, 1.5);
      }
      const drawItem = (item) => {
        if (!item) return;
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
      (docRef.current.items || []).forEach(drawItem);
      Object.values(remoteLiveRef.current).forEach(drawItem);
      if (localStrokeRef.current) drawItem(localStrokeRef.current);
      if (toolRef.current === 'eraser' && eraserCursorRef.current) {
        const [x, y] = eraserCursorRef.current;
        ctx.beginPath();
        ctx.arc(x, y, 16, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(11, 18, 38, 0.45)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      ctx.restore();
    };
    paintRef.current();
  }, [docVersion, tool]);

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

  const commitItem = React.useCallback((item) => {
    markDirty();
    pendingRef.current.removes.delete(item.id);
    pendingRef.current.upserts.set(item.id, item);
    const doc = docRef.current;
    setBoard({
      ...doc,
      items: doc.items.filter((row) => row.id !== item.id).concat(item),
    });
    const sent = sendJson({
      event: 'commit',
      payload: { client: clientIdRef.current, item },
    });
    if (!sent) {
      setStatus('Нет связи — сохраняем на сервере');
      persistSoon();
    }
  }, [markDirty, persistSoon, sendJson, setBoard]);

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
    setBoard({ ...doc, items: doc.items.filter((item) => !drop.has(item.id)) });
    const sent = sendJson({
      event: 'remove',
      payload: { client: clientIdRef.current, ids },
    });
    if (!sent) persistSoon();
  }, [markDirty, persistSoon, sendJson, setBoard]);

  const placeImage = React.useCallback(async (src, x, y) => {
    const size = await loadImageSize(src);
    if (!size) return false;
    const maxW = 480;
    const scale = size.w > maxW ? maxW / size.w : 1;
    const w = Math.max(32, Math.round(size.w * scale));
    const h = Math.max(32, Math.round(size.h * scale));
    commitItem({
      id: newId(),
      type: 'image',
      src,
      x: Math.max(0, Math.round(x)),
      y: Math.max(0, Math.round(y)),
      w,
      h,
    });
    return true;
  }, [commitItem]);

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

    return () => {
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
    placeImage,
    removeFromServer,
    scheduleDraw,
    setBoard,
    upsertFromServer,
  ]);

  const finishStroke = React.useCallback(() => {
    const stroke = localStrokeRef.current;
    localStrokeRef.current = null;
    if (!stroke || !(stroke.points || []).length) {
      scheduleDraw();
      return;
    }
    commitItem(stroke);
  }, [commitItem, scheduleDraw]);

  const onPointerDown = (event) => {
    if (!ready || event.button != null && event.button !== 0) return;
    const point = pointOnBoard(event, metricsRef.current || measureCanvas(event.currentTarget));
    if (!point) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    if (toolRef.current === 'eraser') {
      eraserCursorRef.current = point;
      const hits = docRef.current.items
        .filter((item) => hitsItem(item, point[0], point[1]))
        .map((item) => item.id);
      commitRemove(hits);
      scheduleDraw();
      return;
    }
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
    const point = pointOnBoard(event, metricsRef.current || measureCanvas(event.currentTarget));
    if (toolRef.current === 'eraser') {
      eraserCursorRef.current = point;
      if (point && (event.buttons & 1)) {
        const hits = docRef.current.items
          .filter((item) => hitsItem(item, point[0], point[1]))
          .map((item) => item.id);
        commitRemove(hits);
      }
      scheduleDraw();
      return;
    }
    const stroke = localStrokeRef.current;
    if (!stroke || !point) return;
    const last = stroke.points[stroke.points.length - 1];
    const dx = point[0] - last[0];
    const dy = point[1] - last[1];
    if (dx * dx + dy * dy < 2) return;
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
      sendJson({
        event: 'live',
        payload: { client: clientIdRef.current, item: stroke },
      });
    }
    scheduleDraw();
  };

  const onPointerUp = () => {
    if (toolRef.current === 'pen') finishStroke();
    eraserCursorRef.current = null;
    scheduleDraw();
  };

  const onPickImage = async (event) => {
    const file = event.target.files && event.target.files[0];
    event.target.value = '';
    if (!file) return;
    if (!String(file.type || '').startsWith('image/')) {
      setNotice('Нужна картинка: png, jpg или webp.');
      return;
    }
    try {
      setStatus('Загружаем картинку…');
      const data = await window.uploadBoardAsset(file);
      if (!data?.url) throw new Error('Не удалось загрузить картинку');
      const size = await loadImageSize(data.url);
      const w = size ? Math.min(480, size.w) : 320;
      const h = size ? Math.round((size.h || 240) * (w / (size.w || w))) : 240;
      const ok = await placeImage(data.url, (BOARD_W - w) / 2, (BOARD_H - h) / 2);
      if (!ok) throw new Error('Картинка не открылась');
      setStatus(socketOpen() ? 'На связи' : 'Сохранено');
    } catch (err) {
      setNotice(err?.message || 'Не удалось поставить картинку');
      setStatus(socketOpen() ? 'На связи' : 'Нет связи');
    }
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
              ? 'Одна доска. Двое рисуют сразу, рисунок сохраняется.'
              : 'Можно рисовать вместе. Рисунок не пропадает.'}
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
            className="absolute inset-0 h-full w-full touch-none"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
          />
          <div className="absolute top-3 left-3 right-3 z-20 flex flex-wrap items-center gap-2 pointer-events-none">
            <div className="pointer-events-auto flex flex-wrap items-center gap-1 rounded-2xl bg-white/95 p-1 shadow-soft ring-1 ring-black/[0.06]">
              <button
                type="button"
                aria-pressed={tool === 'pen'}
                onClick={() => setTool('pen')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'pen' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Карандаш
              </button>
              <button
                type="button"
                aria-pressed={tool === 'eraser'}
                onClick={() => setTool('eraser')}
                className={`h-9 px-3 rounded-xl text-sm font-semibold ${tool === 'eraser' ? 'bg-sky-50 text-sky-800' : 'text-ink/75 hover:bg-black/[0.04]'}`}
              >
                Ластик
              </button>
              <button
                type="button"
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
              <span className="mx-1 h-6 w-px bg-black/[0.08]" />
              {PEN_COLORS.map((swatch) => (
                <button
                  key={swatch.value}
                  type="button"
                  aria-label={swatch.label}
                  title={swatch.label}
                  onClick={() => { setColor(swatch.value); setTool('pen'); }}
                  className={`h-7 w-7 rounded-full ring-2 ring-offset-2 ${color === swatch.value && tool === 'pen' ? 'ring-sky-500' : 'ring-transparent'}`}
                  style={{ background: swatch.value }}
                />
              ))}
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
