import React from 'react';
import { createRoot } from 'react-dom/client';
import { getAssetUrls } from '@tldraw/assets/selfHosted';
import { useSync } from '@tldraw/sync';
import {
  AssetRecordType,
  createTLStore,
  getHashForString,
  getSnapshot,
  loadSnapshot,
  Tldraw,
  uniqueId,
} from 'tldraw';
import 'tldraw/tldraw.css';

const mounts = new Map();

function appBasePath() {
  const meta = document.querySelector('meta[name="app-base"]');
  return (meta?.getAttribute('content') || '').replace(/\/$/, '');
}

function sameOriginSyncUrls() {
  const appBase = appBasePath();
  const httpProto = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const wsProto = httpProto === 'https:' ? 'wss:' : 'ws:';
  const origin = `${window.location.host}${appBase}`;
  return {
    wsBase: `${wsProto}//${origin}/whiteboard-sync`,
    httpBase: `${httpProto}//${origin}/whiteboard-sync`,
  };
}

function isSameSiteBase(value) {
  try {
    const url = new URL(value, window.location.href);
    return url.host === window.location.host;
  } catch (_) {
    return false;
  }
}

function resolveSyncUrls(syncBaseUrl) {
  const trimmed = String(syncBaseUrl || '').replace(/\/$/, '');
  // Чужой хост или голый порт VPN режет, даже если сам сайт открыт.
  if (trimmed && /^(https?|wss?):\/\//i.test(trimmed) && isSameSiteBase(trimmed)) {
    if (trimmed.startsWith('ws')) {
      return {
        wsBase: trimmed,
        httpBase: trimmed.replace(/^ws/i, 'http'),
      };
    }
    return {
      wsBase: trimmed.replace(/^http/i, 'ws'),
      httpBase: trimmed.replace(/^ws/i, 'http'),
    };
  }

  const devPort = window.location.port;
  if (!trimmed && (devPort === '3000' || devPort === '4173')) {
    return {
      wsBase: 'ws://127.0.0.1:5858',
      httpBase: 'http://127.0.0.1:5858',
    };
  }

  return sameOriginSyncUrls();
}

function boardAssetUrls() {
  return getAssetUrls({ baseUrl: `${appBasePath()}/tldraw-assets` });
}

function buildConnectUri(wsBase, roomId, syncToken) {
  const params = new URLSearchParams();
  if (syncToken) {
    params.set('token', syncToken);
  }
  const qs = params.toString();
  return `${wsBase}/connect/${encodeURIComponent(roomId)}${qs ? `?${qs}` : ''}`;
}

const SYNC_ASSET_MAX_BYTES = 2 * 1024 * 1024;

async function uploadViaAcademyStorage(file) {
  if (typeof window.uploadBoardAsset === 'function') {
    const data = await window.uploadBoardAsset(file);
    if (!data?.url) throw new Error('Board asset upload failed');
    return { src: data.url };
  }
  if (typeof window.fetchApiForm === 'function') {
    const form = new FormData();
    form.append('file', file);
    const data = await window.fetchApiForm(
      '/api/communication/board-assets/',
      form,
      { method: 'POST', auth: true },
    );
    if (!data?.url) throw new Error('Board asset upload failed');
    return { src: data.url };
  }
  throw new Error('Нет API для загрузки файла на доску');
}

function createAssetStore(httpBase) {
  return {
    async upload(_asset, file) {
      const isImage = String(file?.type || '').startsWith('image/');
      const tooLarge = Number(file?.size || 0) > SYNC_ASSET_MAX_BYTES;
      // Крупные и не-картинки — в хранилище академии (на доске только URL).
      if (!isImage || tooLarge) {
        return uploadViaAcademyStorage(file);
      }
      const id = uniqueId();
      const objectName = `${id}-${file.name}`;
      const uploadUrl = `${httpBase}/uploads/${encodeURIComponent(objectName)}`;
      const response = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: file.type ? { 'Content-Type': file.type } : undefined,
      });
      if (response.status === 413 || response.status === 415) {
        return uploadViaAcademyStorage(file);
      }
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      return {
        src: `${document.querySelector('meta[name="app-base"]')?.getAttribute('content')?.replace(/\/$/, '') || ''}/whiteboard-sync/uploads/${encodeURIComponent(objectName)}`,
      };
    },
    resolve(asset) {
      const src = asset?.props?.src;
      if (!src) return '';
      if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('ws://') || src.startsWith('wss://')) {
        try {
          const parsed = new URL(src);
          return parsed.pathname + parsed.search;
        } catch (_) {
          return src;
        }
      }
      return src;
    },
  };
}

async function unfurlBookmarkUrl(httpBase, { url }) {
  const asset = {
    id: AssetRecordType.createId(getHashForString(url)),
    typeName: 'asset',
    type: 'bookmark',
    meta: {},
    props: {
      src: url,
      description: '',
      image: '',
      favicon: '',
      title: '',
    },
  };

  try {
    const response = await fetch(`${httpBase}/unfurl?url=${encodeURIComponent(url)}`);
    if (response.ok) {
      const data = await response.json();
      asset.props.description = data?.description ?? '';
      asset.props.image = data?.image ?? '';
      asset.props.favicon = data?.favicon ?? '';
      asset.props.title = data?.title ?? '';
    }
  } catch (_) {
    /* ignore unfurl errors */
  }

  return asset;
}

function WhiteboardStatus({ children, loadingText, errorText }) {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f8fafc',
        color: '#0B1226',
        font: '14px/1.45 system-ui, sans-serif',
        textAlign: 'center',
        padding: '16px',
        pointerEvents: 'none',
      }}
    >
      {children || loadingText || errorText}
    </div>
  );
}

class BoardGuard extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <WhiteboardStatus>
          <div style={{ pointerEvents: 'auto' }}>
            <div style={{ fontWeight: 650 }}>Доска остановилась</div>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                marginTop: 12,
                height: 36,
                padding: '0 14px',
                borderRadius: 10,
                border: 0,
                background: '#2563EB',
                color: '#fff',
                font: '600 13px/1 system-ui, sans-serif',
                cursor: 'pointer',
              }}
            >
              Обновить
            </button>
          </div>
        </WhiteboardStatus>
      );
    }
    return this.props.children;
  }
}

function bindViewportBounds(editor, rootEl) {
  const container = editor.getContainer();
  const syncBounds = () => {
    const target = rootEl || container;
    if (!target || typeof target.getBoundingClientRect !== 'function') return;
    const rect = target.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      editor.updateViewportScreenBounds(target);
    }
  };

  syncBounds();
  requestAnimationFrame(syncBounds);

  const observer = new ResizeObserver(() => syncBounds());
  if (rootEl) observer.observe(rootEl);
  observer.observe(container);

  const onWindowChange = () => syncBounds();
  window.addEventListener('resize', onWindowChange);
  window.addEventListener('scroll', onWindowChange, true);

  return () => {
    observer.disconnect();
    window.removeEventListener('resize', onWindowChange);
    window.removeEventListener('scroll', onWindowChange, true);
  };
}

function pageIsEmpty(editor) {
  try {
    const ids = editor.getCurrentPageShapeIds();
    if (!ids || typeof ids.size !== 'number') return false;
    return ids.size === 0;
  } catch (_) {
    return false;
  }
}

function restoreSnapshotIfEmpty(editor, snapshot) {
  if (!editor || !snapshot || !pageIsEmpty(editor)) return;
  try {
    loadSnapshot(editor.store, snapshot);
  } catch (_) {
    /* битый снимок не затирает живую доску */
  }
}

function WhiteboardEditor({ container, roomId, syncBaseUrl, syncToken, licenseKey, initialSnapshot }) {
  const rootRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const cleanupRef = React.useRef(null);
  const { wsBase, httpBase } = React.useMemo(
    () => resolveSyncUrls(syncBaseUrl),
    [syncBaseUrl],
  );
  const assets = React.useMemo(() => createAssetStore(httpBase), [httpBase]);
  const assetUrls = React.useMemo(() => boardAssetUrls(), []);
  const connectUri = React.useMemo(
    () => buildConnectUri(wsBase, roomId, syncToken),
    [wsBase, roomId, syncToken],
  );
  const store = useSync({
    uri: connectUri,
    assets,
  });
  // useSync drops the store object when the socket later reports an error.
  // Unmounting Tldraw at that moment leaves a white panel. Keep the last
  // live store so the board stays on screen.
  const keptStoreRef = React.useRef(null);
  if (store.store) keptStoreRef.current = store.store;
  const liveStore = keptStoreRef.current;

  React.useEffect(() => {
    const editor = editorRef.current;
    if (editor) {
      editor.updateInstanceState({ isReadonly: false });
      cleanupRef.current?.();
      cleanupRef.current = bindViewportBounds(editor, rootRef.current);
    }
  }, [store.status]);

  React.useEffect(() => () => {
    cleanupRef.current?.();
    cleanupRef.current = null;
  }, []);

  if (!liveStore && store.status === 'error') {
    return (
      <WhiteboardStatus>
        <div>
          <div style={{ fontWeight: 650 }}>Не удалось подключить доску</div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#64748b' }}>
            {store.error?.message || 'Нет связи с доской'}
          </div>
        </div>
      </WhiteboardStatus>
    );
  }

  if (!liveStore) {
    return <WhiteboardStatus loadingText="Подключение к доске…" />;
  }

  return (
    <div ref={rootRef} className="whiteboard-root absolute inset-0 z-[2] pointer-events-auto">
      <Tldraw
        store={liveStore}
        inferDarkMode={false}
        autoFocus
        licenseKey={licenseKey || undefined}
        assetUrls={assetUrls}
        options={{ maxPages: 1 }}
        onMount={(editor) => {
          editorRef.current = editor;
          const entry = mounts.get(container);
          if (entry) entry.editor = editor;
          editor.updateInstanceState({ isReadonly: false });
          editor.registerExternalAssetHandler('url', (payload) => unfurlBookmarkUrl(httpBase, payload));
          cleanupRef.current?.();
          cleanupRef.current = bindViewportBounds(editor, rootRef.current);
          requestAnimationFrame(() => restoreSnapshotIfEmpty(editor, initialSnapshot));
        }}
      />
    </div>
  );
}

function WhiteboardApp({ container, roomId, syncBaseUrl, syncToken, licenseKey, initialSnapshot }) {
  if (!syncToken) {
    return <WhiteboardStatus loadingText="Получение доступа к доске…" />;
  }

  return (
    <BoardGuard>
      <WhiteboardEditor
        container={container}
        roomId={roomId}
        syncBaseUrl={syncBaseUrl}
        syncToken={syncToken}
        licenseKey={licenseKey}
        initialSnapshot={initialSnapshot}
      />
    </BoardGuard>
  );
}

function waitForEditor(timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const tick = () => {
      for (const entry of mounts.values()) {
        if (entry?.editor) {
          resolve(entry.editor);
          return;
        }
      }
      if (Date.now() - started > timeoutMs) {
        reject(new Error('Доска ещё не готова. Подождите секунду и откройте снова.'));
        return;
      }
      requestAnimationFrame(tick);
    };
    tick();
  });
}

function guessImageMime(src) {
  const name = String(src || '').toLowerCase();
  if (name.endsWith('.svg')) return 'image/svg+xml';
  if (name.endsWith('.png')) return 'image/png';
  if (name.endsWith('.gif')) return 'image/gif';
  if (name.endsWith('.webp')) return 'image/webp';
  if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg';
  return 'image/png';
}

function loadImageSize(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      resolve({
        w: img.naturalWidth || 800,
        h: img.naturalHeight || 600,
      });
    };
    img.onerror = () => resolve({ w: 800, h: 600 });
    img.src = src;
  });
}

async function createImagesFromUrls(urls = []) {
  const list = (urls || []).map(String).filter(Boolean);
  if (!list.length) return;
  const editor = await waitForEditor();
  const existing = new Set();
  try {
    for (const asset of editor.getAssets()) {
      const key = asset?.meta?.importSrc || asset?.props?.src;
      if (key) existing.add(String(key));
    }
  } catch (_) { /* older store */ }

  let x = 0;
  let placed = 0;
  for (const src of list) {
    if (existing.has(src)) continue;
    const { w, h } = await loadImageSize(src);
    const maxW = 1100;
    const scale = w > maxW ? maxW / w : 1;
    const dw = Math.max(120, Math.round(w * scale));
    const dh = Math.max(80, Math.round(h * scale));
    const assetId = AssetRecordType.createId();
    editor.createAssets([{
      id: assetId,
      typeName: 'asset',
      type: 'image',
      meta: { importSrc: src },
      props: {
        name: decodeURIComponent(String(src).split('/').pop() || 'image'),
        src,
        w,
        h,
        mimeType: guessImageMime(src),
        isAnimated: false,
      },
    }]);
    editor.createShape({
      type: 'image',
      x,
      y: 0,
      props: {
        w: dw,
        h: dh,
        assetId,
        playing: true,
        url: '',
        crop: null,
      },
    });
    existing.add(src);
    x += dw + 48;
    placed += 1;
  }
  if (placed > 0 && typeof editor.zoomToFit === 'function') {
    try {
      editor.zoomToFit({ animation: { duration: 200 } });
    } catch (_) {
      editor.zoomToFit();
    }
  }
}

function mount(container, options = {}) {
  if (!container) return;
  const roomId = options.roomId;
  if (!roomId) return;

  unmount(container);

  const root = createRoot(container);
  root.render(
    <WhiteboardApp
      container={container}
      roomId={roomId}
      syncBaseUrl={options.syncBaseUrl}
      syncToken={options.syncToken}
      licenseKey={options.licenseKey}
      initialSnapshot={options.initialSnapshot || null}
    />,
  );
  mounts.set(container, { root, roomId: String(roomId), editor: null });
}

function unmount(container) {
  const entry = mounts.get(container);
  if (!entry) return;
  entry.root.unmount();
  mounts.delete(container);
}

async function exportPngBlob() {
  let editor = null;
  for (const entry of mounts.values()) {
    if (entry.editor) {
      editor = entry.editor;
      break;
    }
  }
  if (!editor) {
    throw new Error('Доска не активна');
  }

  const shapeIds = [...editor.getCurrentPageShapeIds()];
  if (!shapeIds.length) {
    throw new Error('Доска пуста');
  }

  const result = await editor.toImage(shapeIds, {
    format: 'png',
    background: true,
    scale: 2,
  });
  return result.blob;
}

function exportSnapshotJson() {
  let editor = null;
  for (const entry of mounts.values()) {
    if (entry.editor) {
      editor = entry.editor;
      break;
    }
  }
  if (!editor) {
    throw new Error('Доска не активна');
  }
  return getSnapshot(editor.store);
}

function WhiteboardReadOnly({ container, snapshot, licenseKey }) {
  const rootRef = React.useRef(null);
  const store = React.useMemo(() => {
    const next = createTLStore();
    if (snapshot) {
      loadSnapshot(next, snapshot);
    }
    return next;
  }, [snapshot]);
  const assetUrls = React.useMemo(() => boardAssetUrls(), []);

  return (
    <div ref={rootRef} className="whiteboard-root absolute inset-0 z-[2]">
      <Tldraw
        store={store}
        inferDarkMode={false}
        licenseKey={licenseKey || undefined}
        assetUrls={assetUrls}
        options={{ maxPages: 1 }}
        onMount={(editor) => {
          editor.updateInstanceState({ isReadonly: true });
          bindViewportBounds(editor, rootRef.current);
        }}
      />
    </div>
  );
}

function mountReadOnly(container, options = {}) {
  if (!container || !options.snapshot) return;
  unmount(container);
  const root = createRoot(container);
  root.render(
    <WhiteboardReadOnly
      container={container}
      snapshot={options.snapshot}
      licenseKey={options.licenseKey}
    />,
  );
  mounts.set(container, { root, roomId: 'readonly', editor: null });
}

window.BervinovWhiteboard = {
  mount,
  unmount,
  exportPngBlob,
  exportSnapshotJson,
  mountReadOnly,
  createImagesFromUrls,
};
