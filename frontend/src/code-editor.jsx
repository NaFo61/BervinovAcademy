// Shared Monaco Python editor + playground helpers (CDN, no bundler)

const MONACO_VERSION = '0.52.2';
const MONACO_BASE = `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VERSION}/min`;
const PLAYGROUND_CODE_KEY = 'ba_playground_code';
const PLAYGROUND_STDIN_KEY = 'ba_playground_stdin';

function ensureMonaco() {
  if (window.monaco?.editor) return Promise.resolve(window.monaco);
  if (window.__monacoLoading) return window.__monacoLoading;

  window.__monacoLoading = new Promise((resolve, reject) => {
    const finish = () => {
      try {
        const monaco = window.monaco;
        if (!monaco?.editor) throw new Error('Monaco failed to load');
        if (!monaco.editor.__baTheme) {
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
        resolve(monaco);
      } catch (err) {
        reject(err);
      }
    };

    if (window.require && window.__monacoLoaderReady) {
      window.require(['vs/editor/editor.main'], finish);
      return;
    }

    const script = document.createElement('script');
    script.src = `${MONACO_BASE}/vs/loader.js`;
    script.async = true;
    script.onload = () => {
      window.require.config({
        paths: { vs: `${MONACO_BASE}/vs` },
        'vs/nls': { availableLanguages: { '*': '' } },
      });
      window.__monacoLoaderReady = true;
      window.require(['vs/editor/editor.main'], finish);
    };
    script.onerror = () => reject(new Error('Не удалось загрузить Monaco Editor'));
    document.head.appendChild(script);
  }).catch((err) => {
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
  const [loadError, setLoadError] = React.useState('');
  const [ready, setReady] = React.useState(false);

  onChangeRef.current = onChange;

  React.useEffect(() => {
    let disposed = false;
    let resizeObs = null;

    ensureMonaco()
      .then((monaco) => {
        if (disposed || !hostRef.current) return;
        const editor = monaco.editor.create(hostRef.current, {
          value: value || '',
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
      })
      .catch((err) => setLoadError(err.message || 'Ошибка загрузки редактора'));

    return () => {
      disposed = true;
      resizeObs?.disconnect();
      editorRef.current?.dispose();
      editorRef.current = null;
    };
    // mount once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  return (
    <div className={`rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-[#0d1117] code-bg ${className}`}>
      {showHeader && (
        <div className="px-4 py-2.5 border-b border-white/10 flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 font-semibold">Python</span>
          <span className="ml-auto font-mono text-[11px] text-slate-500">{filename}</span>
          {!ready && !loadError && <span className="text-[10px] text-slate-500">загрузка…</span>}
        </div>
      )}
      {loadError ? (
        <textarea
          value={value || ''}
          onChange={(e) => onChange?.(e.target.value)}
          spellCheck="false"
          disabled={readOnly}
          className="w-full bg-transparent text-slate-100 font-mono text-xs leading-[1.55] p-4 resize-y focus:outline-none disabled:opacity-60"
          style={{ minHeight: height, caretColor: '#06B6D4' }}
        />
      ) : (
        <div ref={hostRef} style={{ height }} className="w-full" />
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
