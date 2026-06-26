import React from 'react';
import { createRoot } from 'react-dom/client';
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

function resolveSyncUrls(syncBaseUrl) {
  const trimmed = String(syncBaseUrl || '').replace(/\/$/, '');
  if (trimmed) {
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
  if (devPort === '3000' || devPort === '4173') {
    return {
      wsBase: 'ws://127.0.0.1:5858',
      httpBase: 'http://127.0.0.1:5858',
    };
  }

  const meta = document.querySelector('meta[name="app-base"]');
  const appBase = (meta?.getAttribute('content') || '').replace(/\/$/, '');

  return {
    wsBase: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${appBase}/whiteboard-sync`,
    httpBase: `${window.location.protocol}//${window.location.host}${appBase}/whiteboard-sync`,
  };
}

function buildConnectUri(wsBase, roomId, syncToken) {
  const params = new URLSearchParams();
  if (syncToken) {
    params.set('token', syncToken);
  }
  const qs = params.toString();
  return `${wsBase}/connect/${encodeURIComponent(roomId)}${qs ? `?${qs}` : ''}`;
}

function createAssetStore(httpBase) {
  return {
    async upload(_asset, file) {
      const id = uniqueId();
      const objectName = `${id}-${file.name}`;
      const uploadUrl = `${httpBase}/uploads/${encodeURIComponent(objectName)}`;
      const response = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
      });
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
    <div className="absolute inset-0 flex items-center justify-center bg-white text-slate-600 text-sm px-4 text-center pointer-events-none">
      {children || loadingText || errorText}
    </div>
  );
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

function WhiteboardEditor({ container, roomId, syncBaseUrl, syncToken, licenseKey }) {
  const rootRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const cleanupRef = React.useRef(null);
  const { wsBase, httpBase } = React.useMemo(
    () => resolveSyncUrls(syncBaseUrl),
    [syncBaseUrl],
  );
  const assets = React.useMemo(() => createAssetStore(httpBase), [httpBase]);
  const connectUri = React.useMemo(
    () => buildConnectUri(wsBase, roomId, syncToken),
    [wsBase, roomId, syncToken],
  );
  const store = useSync({
    uri: connectUri,
    assets,
  });

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

  if (store.status === 'loading') {
    return <WhiteboardStatus loadingText="Подключение к доске…" />;
  }

  if (store.status === 'error') {
    return (
      <WhiteboardStatus
        errorText={(
          <>
            <div className="font-semibold text-slate-700">Не удалось подключить доску</div>
            <div className="text-xs text-slate-500 mt-2">{store.error?.message || 'Ошибка sync-сервера'}</div>
          </>
        )}
      />
    );
  }

  return (
    <div ref={rootRef} className="whiteboard-root absolute inset-0 z-[2] pointer-events-auto">
      <Tldraw
        store={store.store}
        inferDarkMode={false}
        autoFocus
        licenseKey={licenseKey || undefined}
        options={{ maxPages: 1 }}
        onMount={(editor) => {
          editorRef.current = editor;
          const entry = mounts.get(container);
          if (entry) entry.editor = editor;
          editor.updateInstanceState({ isReadonly: false });
          editor.registerExternalAssetHandler('url', (payload) => unfurlBookmarkUrl(httpBase, payload));
          cleanupRef.current?.();
          cleanupRef.current = bindViewportBounds(editor, rootRef.current);
        }}
      />
    </div>
  );
}

function WhiteboardApp({ container, roomId, syncBaseUrl, syncToken, licenseKey }) {
  if (!syncToken) {
    return <WhiteboardStatus loadingText="Получение доступа к доске…" />;
  }

  return (
    <WhiteboardEditor
      container={container}
      roomId={roomId}
      syncBaseUrl={syncBaseUrl}
      syncToken={syncToken}
      licenseKey={licenseKey}
    />
  );
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

  return (
    <div ref={rootRef} className="whiteboard-root absolute inset-0 z-[2]">
      <Tldraw
        store={store}
        inferDarkMode={false}
        licenseKey={licenseKey || undefined}
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

window.BervinovWhiteboard = { mount, unmount, exportPngBlob, exportSnapshotJson, mountReadOnly };
