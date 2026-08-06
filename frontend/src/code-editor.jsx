// Shared Monaco Python editor + playground helpers (CDN, no bundler)

const MONACO_VERSION = '0.52.2';
const MONACO_CDN_BASES = [
  `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VERSION}/min`,
  `https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/${MONACO_VERSION}/min`,
  `https://unpkg.com/monaco-editor@${MONACO_VERSION}/min`,
];
const MONACO_LOAD_TIMEOUT_MS = 15000;
const PLAYGROUND_CODE_KEY = 'ba_playground_code';
const PLAYGROUND_STDIN_KEY = 'ba_playground_stdin';

function loadScriptOnce(src, timeoutMs) {
  return new Promise((resolve, reject) => {
    const existing = Array.from(document.querySelectorAll('script[data-ba-src]'))
      .find((node) => node.dataset.baSrc === src);
    if (existing) {
      if (existing.dataset.baLoaded === '1') {
        resolve();
        return;
      }
      if (existing.dataset.baFailed === '1') {
        reject(new Error(`Не удалось загрузить ${src}`));
        return;
      }
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error(`Не удалось загрузить ${src}`)), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.dataset.baSrc = src;
    const timer = setTimeout(() => {
      script.dataset.baFailed = '1';
      reject(new Error(`Таймаут загрузки редактора (${timeoutMs}мс)`));
    }, timeoutMs);
    script.onload = () => {
      clearTimeout(timer);
      script.dataset.baLoaded = '1';
      resolve();
    };
    script.onerror = () => {
      clearTimeout(timer);
      script.dataset.baFailed = '1';
      reject(new Error(`Не удалось загрузить Monaco (${src})`));
    };
    document.head.appendChild(script);
  });
}

function configureMonacoEnvironment(base) {
  window.MonacoEnvironment = {
    getWorkerUrl() {
      const body = `
        self.MonacoEnvironment = { baseUrl: '${base}/' };
        importScripts('${base}/vs/base/worker/workerMain.js');
      `;
      return URL.createObjectURL(new Blob([body], { type: 'text/javascript' }));
    },
  };
}

function applyBaTheme(monaco) {
  if (monaco.editor.__baTheme) return;
  monaco.editor.defineTheme('ba-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '8B949E', fontStyle: 'italic' },
      { token: 'string', foreground: 'A5D6FF' },
      { token: 'keyword', foreground: 'FF7B72' },
      { token: 'number', foreground: '79C0FF' },
      { token: 'type', foreground: 'FFA657' },
      { token: 'delimiter', foreground: 'C9D1D9' },
    ],
    colors: {
      'editor.background': '#0d1117',
      'editor.foreground': '#e6edf3',
      'editorLineNumber.foreground': '#6e7681',
      'editorLineNumber.activeForeground': '#e6edf3',
      'editor.selectionBackground': '#388bfd66',
      'editor.inactiveSelectionBackground': '#388bfd44',
      'editor.selectionHighlightBackground': '#388bfd33',
      'editorCursor.foreground': '#06B6D4',
      'editor.lineHighlightBackground': '#161b22',
      'editorIndentGuide.background': '#21262d',
      'editorIndentGuide.activeBackground': '#30363d',
      'scrollbarSlider.background': '#ffffff22',
      'scrollbarSlider.hoverBackground': '#ffffff33',
    },
  });
  monaco.editor.__baTheme = true;
}

function loadMonacoFromBase(base) {
  configureMonacoEnvironment(base);
  return loadScriptOnce(`${base}/vs/loader.js`, MONACO_LOAD_TIMEOUT_MS).then(
    () => new Promise((resolve, reject) => {
      const amdRequire = window.require;
      if (typeof amdRequire !== 'function' || typeof amdRequire.config !== 'function') {
        reject(new Error('AMD loader Monaco не инициализировался'));
        return;
      }

      const configured = amdRequire.config({
        context: 'ba-monaco',
        paths: { vs: `${base}/vs` },
        'vs/nls': { availableLanguages: { '*': '' } },
      });
      // Monaco loader often returns undefined from config(); fall back to global require.
      const req = typeof configured === 'function' ? configured : amdRequire;

      const timer = setTimeout(() => {
        reject(new Error('Таймаут инициализации Monaco Editor'));
      }, MONACO_LOAD_TIMEOUT_MS);

      req(
        ['vs/editor/editor.main'],
        () => {
          clearTimeout(timer);
          const monaco = window.monaco;
          if (!monaco?.editor) {
            reject(new Error('Monaco failed to load'));
            return;
          }
          applyBaTheme(monaco);
          window.__monacoLoaderReady = true;
          window.__monacoBase = base;
          resolve(monaco);
        },
        (err) => {
          clearTimeout(timer);
          reject(err || new Error('Не удалось загрузить editor.main'));
        },
      );
    }),
  );
}

function ensureMonaco(onStatus) {
  if (window.monaco?.editor) return Promise.resolve(window.monaco);
  if (window.__monacoLoading) return window.__monacoLoading;

  window.__monacoLoading = (async () => {
    let lastErr = null;
    for (let i = 0; i < MONACO_CDN_BASES.length; i += 1) {
      const base = MONACO_CDN_BASES[i];
      onStatus?.(`Загрузка редактора (${i + 1}/${MONACO_CDN_BASES.length})…`);
      try {
        return await loadMonacoFromBase(base);
      } catch (err) {
        lastErr = err;
      }
    }
    throw lastErr || new Error('Не удалось загрузить Monaco Editor');
  })().catch((err) => {
    window.__monacoLoading = null;
    throw err;
  });

  return window.__monacoLoading;
}

function stashPlaygroundCode(code, stdin) {
  try {
    sessionStorage.setItem(PLAYGROUND_CODE_KEY, code || '');
    sessionStorage.setItem(PLAYGROUND_STDIN_KEY, stdin || '');
  } catch (_) { /* private mode / quota */ }
}

function takePlaygroundStash() {
  let code = '';
  let stdin = '';
  try {
    code = sessionStorage.getItem(PLAYGROUND_CODE_KEY) || '';
    stdin = sessionStorage.getItem(PLAYGROUND_STDIN_KEY) || '';
    sessionStorage.removeItem(PLAYGROUND_CODE_KEY);
    sessionStorage.removeItem(PLAYGROUND_STDIN_KEY);
  } catch (_) { /* ignore */ }
  return { code, stdin };
}

function openPlaygroundWithCode(navigate, code, stdin) {
  stashPlaygroundCode(code, stdin);
  if (typeof navigate === 'function') {
    navigate(window.Routes.PLAYGROUND);
    return;
  }
  const url = '/playground';
  history.pushState(null, '', url);
  window.dispatchEvent(new PopStateEvent('popstate'));
}

function PythonCodeEditor({
  value,
  onChange,
  readOnly = false,
  height = 320,
  filename = 'solution.py',
  className = '',
  showHeader = true,
}) {
  const hostRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const onChangeRef = React.useRef(onChange);
  const valueRef = React.useRef(value);
  const [monacoApi, setMonacoApi] = React.useState(null);
  const [loadError, setLoadError] = React.useState('');
  const [ready, setReady] = React.useState(false);
  const [statusHint, setStatusHint] = React.useState('загрузка…');

  onChangeRef.current = onChange;
  valueRef.current = value;

  React.useEffect(() => {
    let disposed = false;
    ensureMonaco(setStatusHint)
      .then((monaco) => {
        if (disposed) return;
        setMonacoApi(monaco);
        setStatusHint('');
      })
      .catch((err) => {
        if (disposed) return;
        setLoadError(err.message || 'Ошибка загрузки редактора');
        setStatusHint('');
      });
    return () => { disposed = true; };
  }, []);

  React.useEffect(() => {
    if (!monacoApi || loadError) return undefined;
    let disposed = false;
    let resizeObs = null;
    let raf = 0;
    let tries = 0;

    const mount = () => {
      if (disposed) return;
      if (!hostRef.current) {
        if (tries++ < 90) {
          raf = requestAnimationFrame(mount);
        } else {
          setLoadError('Контейнер редактора не готов');
        }
        return;
      }
      if (editorRef.current) return;
      const editor = monacoApi.editor.create(hostRef.current, {
        value: valueRef.current || '',
        language: 'python',
        theme: 'ba-dark',
        readOnly: !!readOnly,
        automaticLayout: true,
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 13,
        lineHeight: 20,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        smoothScrolling: true,
        cursorBlinking: 'smooth',
        cursorSmoothCaretAnimation: 'on',
        renderLineHighlight: 'line',
        padding: { top: 12, bottom: 12 },
        tabSize: 4,
        insertSpaces: true,
        wordWrap: 'on',
        bracketPairColorization: { enabled: true },
        guides: { indentation: true, bracketPairs: true },
        scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
        overviewRulerLanes: 0,
        hideCursorInOverviewRuler: true,
        fixedOverflowWidgets: true,
      });
      editorRef.current = editor;
      editor.onDidChangeModelContent(() => {
        const next = editor.getValue();
        if (onChangeRef.current) onChangeRef.current(next);
      });
      if (typeof ResizeObserver !== 'undefined') {
        resizeObs = new ResizeObserver(() => editor.layout());
        resizeObs.observe(hostRef.current);
      }
      setReady(true);
    };

    raf = requestAnimationFrame(mount);
    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      resizeObs?.disconnect();
      editorRef.current?.dispose();
      editorRef.current = null;
      setReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monacoApi, loadError]);

  React.useEffect(() => {
    const ed = editorRef.current;
    if (!ed) return;
    const current = ed.getValue();
    if ((value || '') !== current) {
      const pos = ed.getPosition();
      ed.setValue(value || '');
      if (pos) ed.setPosition(pos);
    }
  }, [value]);

  React.useEffect(() => {
    const ed = editorRef.current;
    if (!ed) return;
    ed.updateOptions({ readOnly: !!readOnly });
  }, [readOnly]);

  const useMonaco = !!monacoApi && !loadError;
  const showTextarea = !ready;

  return (
    <div className={`rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-[#0d1117] code-bg ${className}`}>
      {showHeader && (
        <div className="px-4 py-2.5 border-b border-white/10 flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 font-semibold">Python</span>
          <span className="ml-auto font-mono text-[11px] text-slate-500">{filename}</span>
          {!ready && !loadError && (
            <span className="text-[10px] text-slate-500">{statusHint || 'загрузка…'}</span>
          )}
          {loadError && (
            <span className="text-[10px] text-amber-300/90" title={loadError}>простой режим</span>
          )}
        </div>
      )}
      {showTextarea && (
        <textarea
          value={value || ''}
          onChange={(e) => onChange?.(e.target.value)}
          spellCheck="false"
          disabled={readOnly}
          aria-label={filename}
          className="w-full bg-transparent text-slate-100 font-mono text-xs leading-[1.55] p-4 resize-y focus:outline-none disabled:opacity-60"
          style={{ minHeight: height, caretColor: '#06B6D4' }}
        />
      )}
      {useMonaco && (
        <div
          ref={hostRef}
          style={{ height: ready ? height : 0, overflow: 'hidden' }}
          className="w-full"
          aria-hidden={!ready}
        />
      )}
    </div>
  );
}

Object.assign(window, {
  ensureMonaco,
  PythonCodeEditor,
  openPlaygroundWithCode,
  stashPlaygroundCode,
  takePlaygroundStash,
  PLAYGROUND_CODE_KEY,
  PLAYGROUND_STDIN_KEY,
});
