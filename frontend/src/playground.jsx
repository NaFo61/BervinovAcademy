// Browser Python interpreter (Pyodide) — code / stdin / stdout, no tests

const PYODIDE_VERSION = '0.27.5';
const PYODIDE_INDEXES = [
  `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
  `https://cdn.jsdelivr.net/npm/pyodide@${PYODIDE_VERSION}/`,
];
const PYODIDE_LOAD_TIMEOUT_MS = 45000;
const DEFAULT_PLAYGROUND_CODE = `name = input("Как тебя зовут? ")
print(f"Привет, {name}!")
`;

function loadScriptWithTimeout(src, timeoutMs) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    const timer = setTimeout(() => reject(new Error(`Таймаут загрузки ${src}`)), timeoutMs);
    s.onload = () => { clearTimeout(timer); resolve(); };
    s.onerror = () => { clearTimeout(timer); reject(new Error(`Не удалось загрузить ${src}`)); };
    document.head.appendChild(s);
  });
}

function ensurePyodide() {
  if (window.__pyodideInstance) return Promise.resolve(window.__pyodideInstance);
  if (window.__pyodideLoading) return window.__pyodideLoading;

  window.__pyodideLoading = (async () => {
    let lastErr = null;
    for (let i = 0; i < PYODIDE_INDEXES.length; i += 1) {
      const indexURL = PYODIDE_INDEXES[i];
      try {
        if (!window.loadPyodide) {
          await loadScriptWithTimeout(`${indexURL}pyodide.js`, PYODIDE_LOAD_TIMEOUT_MS);
        }
        const pyodide = await Promise.race([
          window.loadPyodide({ indexURL }),
          new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Таймаут инициализации Pyodide')), PYODIDE_LOAD_TIMEOUT_MS);
          }),
        ]);
        window.__pyodideInstance = pyodide;
        return pyodide;
      } catch (err) {
        lastErr = err;
        window.loadPyodide = undefined;
      }
    }
    throw lastErr || new Error('Не удалось загрузить Pyodide');
  })().catch((err) => {
    window.__pyodideLoading = null;
    throw err;
  });

  return window.__pyodideLoading;
}

function playgroundFileName(name) {
  const base = String(name || 'data.txt').split(/[/\\]/).pop() || 'data.txt';
  return base.replace(/[^\w.\- ()а-яА-ЯёЁ]/g, '_') || 'data.txt';
}

async function runPythonInBrowser(code, stdinText, files) {
  const pyodide = await ensurePyodide();
  const stdin = String(stdinText ?? '');
  const attached = Array.isArray(files) ? files : [];
  for (const file of attached) {
    if (!file?.name) continue;
    pyodide.FS.writeFile(playgroundFileName(file.name), String(file.text || ''));
  }
  const stdoutChunks = [];
  const stderrChunks = [];
  const decoder = new TextDecoder('utf-8');
  const pushDecoded = (target, s) => {
    if (s == null || s === '') return;
    if (typeof s === 'string') {
      target.push(s);
      return;
    }
    try {
      target.push(decoder.decode(s));
    } catch (_) {
      target.push(String(s));
    }
  };

  const attach = (setter, target) => {
    try {
      setter({
        write(buf) {
          pushDecoded(target, buf);
          return buf?.length ?? buf?.byteLength ?? 0;
        },
        isatty: false,
      });
    } catch (_) {
      setter({
        batched: (s) => {
          const text = String(s ?? '');
          target.push(text.endsWith('\n') ? text : `${text}\n`);
        },
      });
    }
  };

  attach((opts) => pyodide.setStdout(opts), stdoutChunks);
  attach((opts) => pyodide.setStderr(opts), stderrChunks);

  await pyodide.runPythonAsync(`
import sys
from io import StringIO
sys.stdin = StringIO(${JSON.stringify(stdin)})
`);

  try {
    await pyodide.runPythonAsync(code || '');
  } catch (err) {
    const msg = err?.message || String(err);
    return {
      ok: false,
      stdout: stdoutChunks.join(''),
      stderr: stderrChunks.join(''),
      error: msg,
    };
  }
  return {
    ok: true,
    stdout: stdoutChunks.join(''),
    stderr: stderrChunks.join(''),
    error: '',
  };
}

function PlaygroundPage() {
  const stash = React.useMemo(() => window.takePlaygroundStash?.() || { code: '', stdin: '', file: null }, []);
  const [code, setCode] = React.useState(stash.code || DEFAULT_PLAYGROUND_CODE);
  const [stdin, setStdin] = React.useState(stash.stdin || '');
  const [files, setFiles] = React.useState(stash.file?.name ? [stash.file] : []);
  const fileInputRef = React.useRef(null);
  const [stdout, setStdout] = React.useState('');
  const [stderr, setStderr] = React.useState('');
  const [runError, setRunError] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [running, setRunning] = React.useState(false);
  const [editorH, setEditorH] = React.useState(320);

  React.useEffect(() => {
    const mq = window.matchMedia('(min-width: 1024px)');
    const apply = () => setEditorH(mq.matches ? 420 : 260);
    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, []);

  React.useEffect(() => {
    // warm load in background
    ensurePyodide().catch(() => {});
  }, []);

  const run = async () => {
    if (running) return;
    setRunning(true);
    setStdout('');
    setStderr('');
    setRunError('');
    setStatus('Выполнение…');
    try {
      const result = await runPythonInBrowser(code, stdin, files);
      setStdout(result.stdout || '');
      setStderr(result.stderr || '');
      setRunError(result.error || '');
      if (!result.stdout && !result.stderr && !result.error && result.ok) {
        setStdout('(нет вывода)');
      }
      setStatus(result.ok ? 'Готово' : 'Ошибка выполнения');
    } catch (e) {
      setRunError(e.message || String(e));
      setStatus('Ошибка');
    } finally {
      setRunning(false);
    }
  };

  const runRef = React.useRef(run);
  runRef.current = run;

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runRef.current();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className="min-h-[calc(100vh-4rem)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-700 mb-2">Песочница</div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-ink">
              Python<span className="grad-text">‑интерпретатор</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={run}
              disabled={running}
              className="btn-grad h-11 px-6 rounded-xl text-sm font-bold text-white disabled:opacity-50 inline-flex items-center gap-2"
            >
              {running
                ? <span className="w-4 h-4 border-2 border-white/35 border-t-white rounded-full animate-spin" />
                : <window.I.Play className="w-4 h-4" />}
              {running ? 'Запуск…' : 'Запустить'}
            </button>
          </div>
        </div>

        {status ? <p className="mb-4 text-xs text-ink/45">{status}</p> : null}

        <div className="mb-4 rounded-2xl ring-1 ring-black/[0.06] bg-white px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest text-sky-800">Файлы</div>
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="h-9 px-3 rounded-lg text-[12px] font-semibold text-sky-800 bg-sky-50 ring-1 ring-sky-200 hover:bg-sky-100"
            >
              Добавить txt
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.csv,.md,text/plain"
              className="hidden"
              onChange={async (event) => {
                const picked = event.target.files?.[0];
                event.target.value = '';
                if (!picked) return;
                const text = await picked.text();
                const name = playgroundFileName(picked.name);
                setFiles((prev) => [...prev.filter((row) => row.name !== name), { name, text }]);
              }}
            />
          </div>
          {files.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {files.map((file) => (
                <li key={file.name} className="flex items-center justify-between gap-3 rounded-lg bg-black/[0.03] px-3 py-2">
                  <span className="min-w-0 truncate font-mono text-[12px] text-ink/80">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => setFiles((prev) => prev.filter((row) => row.name !== file.name))}
                    className="shrink-0 text-[11px] font-semibold text-ink/45 hover:text-ink"
                  >
                    Убрать
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-4">
          <window.PythonCodeEditor
            value={code}
            onChange={setCode}
            height={editorH}
            filename="main.py"
            readOnly={running}
          />

          <div className="flex flex-col gap-4 min-h-0">
            <div className="rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-white flex flex-col min-h-[160px]">
              <div className="px-4 py-2.5 border-b border-black/[0.06] flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-widest text-amber-700">Входные данные</span>
              </div>
              <textarea
                value={stdin}
                onChange={(e) => setStdin(e.target.value)}
                spellCheck="false"
                placeholder={'строка 1\nстрока 2'}
                className="flex-1 min-h-[120px] w-full bg-white text-ink font-mono text-xs leading-[1.55] p-4 resize-y focus:outline-none placeholder:text-ink/30"
                style={{ caretColor: '#D97706' }}
              />
            </div>

            <div className="rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-white flex flex-col flex-1 min-h-[220px]">
              <div className="px-4 py-2.5 border-b border-black/[0.06] flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-widest text-emerald-700">Вывод</span>
                <button
                  type="button"
                  onClick={() => { setStdout(''); setStderr(''); setRunError(''); }}
                  className="text-[10px] font-semibold text-ink/45 hover:text-ink"
                >
                  Очистить
                </button>
              </div>
              <pre className="flex-1 overflow-auto p-4 text-xs font-mono leading-[1.55] min-h-[180px] whitespace-pre-wrap break-words">
                {!stdout && !stderr && !runError ? (
                  <span className="text-ink/35">Пока пусто</span>
                ) : (
                  <>
                    {stdout ? <span className="text-ink">{stdout}</span> : null}
                    {stderr ? <span className="block text-rose-600">{stderr}</span> : null}
                    {runError ? <span className="block text-rose-600">{runError}</span> : null}
                  </>
                )}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

window.PlaygroundPage = PlaygroundPage;
