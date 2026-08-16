// Browser Python interpreter (Pyodide) — code / stdin / stdout, no tests

const PYODIDE_VERSION = '0.27.5';
const PYODIDE_INDEXES = [
  `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
  `https://cdn.jsdelivr.net/npm/pyodide@${PYODIDE_VERSION}/`,
];
const PYODIDE_LOAD_TIMEOUT_MS = 45000;
const DEFAULT_PLAYGROUND_CODE = `# Пиши код и жми «Запустить»
name = input("Как тебя зовут? ")
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

function ensurePyodide(onStatus) {
  if (window.__pyodideInstance) return Promise.resolve(window.__pyodideInstance);
  if (window.__pyodideLoading) return window.__pyodideLoading;

  window.__pyodideLoading = (async () => {
    let lastErr = null;
    for (let i = 0; i < PYODIDE_INDEXES.length; i += 1) {
      const indexURL = PYODIDE_INDEXES[i];
      try {
        onStatus?.(`Загрузка Python в браузере (${i + 1}/${PYODIDE_INDEXES.length})…`);
        if (!window.loadPyodide) {
          await loadScriptWithTimeout(`${indexURL}pyodide.js`, PYODIDE_LOAD_TIMEOUT_MS);
        }
        onStatus?.('Инициализация интерпретатора…');
        const pyodide = await Promise.race([
          window.loadPyodide({ indexURL }),
          new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Таймаут инициализации Pyodide')), PYODIDE_LOAD_TIMEOUT_MS);
          }),
        ]);
        window.__pyodideInstance = pyodide;
        onStatus?.('Готово');
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

async function runPythonInBrowser(code, stdinText) {
  const pyodide = await ensurePyodide();
  const stdin = String(stdinText ?? '');
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

function PlaygroundPage({ navigate }) {
  const stash = React.useMemo(() => window.takePlaygroundStash?.() || { code: '', stdin: '' }, []);
  const [code, setCode] = React.useState(stash.code || DEFAULT_PLAYGROUND_CODE);
  const [stdin, setStdin] = React.useState(stash.stdin || '');
  const [stdout, setStdout] = React.useState('');
  const [stderr, setStderr] = React.useState('');
  const [runError, setRunError] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [running, setRunning] = React.useState(false);
  const [readyHint, setReadyHint] = React.useState('Первый запуск подгрузит Python (~10–20 МБ).');
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
    ensurePyodide(setReadyHint).catch(() => setReadyHint('Не удалось подготовить интерпретатор'));
  }, []);

  const run = async () => {
    if (running) return;
    setRunning(true);
    setStdout('');
    setStderr('');
    setRunError('');
    setStatus('Выполнение…');
    try {
      const result = await runPythonInBrowser(code, stdin);
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
    <div className="min-h-[calc(100vh-4rem)] bg-[#070b14]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-[0.18em] text-cyan-400/80 mb-2">Песочница</div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Python<span className="text-cyan-400">‑интерпретатор</span>
            </h1>
            <p className="mt-2 text-sm text-white/50 max-w-xl">
              Код выполняется в браузере (Pyodide). Без тестов и очереди — просто вход, код и вывод.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate(window.Routes.MESSAGES)}
              className="h-11 px-4 rounded-xl text-sm font-semibold text-white/70 ring-1 ring-white/10 hover:bg-white/5 transition-colors"
            >
              К сообщениям
            </button>
            <button
              type="button"
              onClick={run}
              disabled={running}
              className="h-11 px-6 rounded-xl text-sm font-bold text-[#041018] bg-gradient-to-r from-cyan-400 to-sky-400 hover:brightness-110 disabled:opacity-50 inline-flex items-center gap-2 shadow-[0_0_24px_rgba(34,211,238,0.25)]"
            >
              {running
                ? <span className="w-4 h-4 border-2 border-[#041018]/35 border-t-[#041018] rounded-full animate-spin" />
                : <window.I.Play className="w-4 h-4" />}
              {running ? 'Бежит…' : 'Запустить'}
              <kbd className="hidden sm:inline ml-1 text-[10px] font-mono opacity-70">Ctrl+Enter</kbd>
            </button>
          </div>
        </div>

        <p className="mb-4 text-xs text-white/40">{readyHint}{status ? ` · ${status}` : ''}</p>

        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-4">
          <window.PythonCodeEditor
            value={code}
            onChange={setCode}
            height={editorH}
            filename="main.py"
            readOnly={running}
          />

          <div className="flex flex-col gap-4 min-h-0">
            <div className="rounded-2xl overflow-hidden ring-1 ring-white/10 bg-[#0d1117] flex flex-col min-h-[160px]">
              <div className="px-4 py-2.5 border-b border-white/10 flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-widest text-amber-300/90">Входные данные</span>
                <span className="text-[10px] text-white/35 font-mono">stdin · для input()</span>
              </div>
              <textarea
                value={stdin}
                onChange={(e) => setStdin(e.target.value)}
                spellCheck="false"
                placeholder={'строка 1\nстрока 2'}
                className="flex-1 min-h-[120px] w-full bg-transparent text-slate-100 font-mono text-xs leading-[1.55] p-4 resize-y focus:outline-none placeholder:text-white/25"
                style={{ caretColor: '#FBBF24' }}
              />
            </div>

            <div className="rounded-2xl overflow-hidden ring-1 ring-white/10 bg-[#0d1117] flex flex-col flex-1 min-h-[220px]">
              <div className="px-4 py-2.5 border-b border-white/10 flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-widest text-emerald-300/90">Вывод</span>
                <button
                  type="button"
                  onClick={() => { setStdout(''); setStderr(''); setRunError(''); }}
                  className="text-[10px] font-semibold text-white/40 hover:text-white/70"
                >
                  Очистить
                </button>
              </div>
              <pre className="flex-1 overflow-auto p-4 text-xs font-mono leading-[1.55] min-h-[180px] whitespace-pre-wrap break-words">
                {!stdout && !stderr && !runError ? (
                  <span className="text-white/25">Здесь появится print() и ошибки…</span>
                ) : (
                  <>
                    {stdout ? <span className="text-emerald-100/90">{stdout}</span> : null}
                    {stderr ? <span className="block text-red-400">{stderr}</span> : null}
                    {runError ? <span className="block text-red-400">{runError}</span> : null}
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
