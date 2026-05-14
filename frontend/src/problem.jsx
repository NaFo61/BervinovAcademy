// PROBLEM page — coding challenge from API + demo local "tests"

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;

const DEFAULT_PYTHON_CODE = `def solve():
    pass

print(solve())`;

function ProblemPage({ hashParams, navigate }) {
  const challengeParam = hashParams && hashParams.get ? hashParams.get('challenge') : null;

  const [challenges, setChallenges] = React.useState([]);
  const [listState, setListState] = React.useState('loading');
  const [listError, setListError] = React.useState('');
  const [detail, setDetail] = React.useState(null);
  const [detailState, setDetailState] = React.useState('idle');
  const [detailError, setDetailError] = React.useState('');

  const [tab, setTab] = React.useState('condition');
  const [code, setCode] = React.useState(DEFAULT_PYTHON_CODE);
  const [running, setRunning] = React.useState(false);
  const [results, setResults] = React.useState(null);
  const [leftW, setLeftW] = React.useState(40);
  const [rightW, setRightW] = React.useState(22);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      setListState('loading');
      setListError('');
      try {
        const data = await window.apiJson('/api/content/challenges/');
        const list = Array.isArray(data) ? data : (data.results || []);
        if (!cancelled) {
          setChallenges(list);
          setListState('ok');
        }
      } catch (e) {
        if (!cancelled) {
          setChallenges([]);
          setListError(e.message || 'Не удалось загрузить задачи');
          setListState('err');
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const selectedId = React.useMemo(() => {
    if (!challenges.length) return null;
    if (challengeParam && challenges.some((c) => String(c.public_id) === String(challengeParam))) {
      return challengeParam;
    }
    return challenges[0].public_id;
  }, [challenges, challengeParam]);

  React.useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      setDetailState('idle');
      return;
    }
    let cancelled = false;
    (async () => {
      setDetailState('loading');
      setDetailError('');
      try {
        const d = await window.apiJson(`/api/content/challenges/${selectedId}/`);
        if (!cancelled) {
          setDetail(d);
          setCode((d && d.initial_code) ? d.initial_code : DEFAULT_PYTHON_CODE);
          setDetailState('ok');
        }
      } catch (e) {
        if (!cancelled) {
          setDetail(null);
          setDetailError(e.message || 'Не удалось загрузить задачу');
          setDetailState('err');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [selectedId]);

  const handleRun = (submit) => {
    setRunning(true);
    setResults(null);
    window.setTimeout(() => {
      setRunning(false);
      const rawCases = (detail && detail.test_cases) ? detail.test_cases : [];
      const cases = rawCases.filter((tc) => !tc.is_hidden && tc.input_data !== '[Скрытый тест]');
      let tests;
      if (cases.length) {
        tests = cases.map((tc, i) => ({
          id: tc.public_id || i + 1,
          name: `Публичный тест ${i + 1}`,
          input: tc.input_data,
          expected: String(tc.expected_output == null ? '' : tc.expected_output).trim(),
          got: String(tc.expected_output == null ? '' : tc.expected_output).trim(),
          pass: true,
          time: 'демо',
        }));
      } else {
        tests = [
          { id: 1, name: 'Пример', input: '—', expected: '—', got: '—', pass: true, time: 'демо' },
        ];
      }
      setResults({ tests, submit, demo: true });
    }, submit ? 700 : 500);
  };

  const onPickChallenge = (id) => {
    navigate(`${Routes.PROBLEM}?challenge=${encodeURIComponent(id)}`);
  };

  if (listState === 'loading') {
    return (
      <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 text-ink/60 bg-paper">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем задачи…</div>
      </div>
    );
  }

  if (listState === 'err' || !challenges.length) {
    return (
      <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 px-6 text-center bg-paper">
        <div className="text-lg font-bold text-ink/80">Задачи недоступны</div>
        <p className="text-sm text-ink/55 max-w-md">{listError || 'Список задач пуст. Добавь задачи в админке Django.'}</p>
      </div>
    );
  }

  if (detailState === 'err') {
    return (
      <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 px-6 text-center bg-paper">
        <div className="text-lg font-bold text-ink/80">Не удалось открыть задачу</div>
        <p className="text-sm text-ink/55">{detailError}</p>
      </div>
    );
  }

  if (selectedId && !detail) {
    return (
      <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 text-ink/60 bg-paper">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем условие…</div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 text-ink/60 bg-paper">
        <div className="text-sm">Нет выбранной задачи</div>
      </div>
    );
  }

  return (
    <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] bg-paper">
      <div className="border-b border-black/5 bg-white">
        <div className="max-w-[1600px] mx-auto px-5 sm:px-8 min-h-14 py-2 flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2 text-ink/50">
            <span className="hidden sm:inline">Задача</span>
            <select
              value={String(selectedId)}
              onChange={(e) => onPickChallenge(e.target.value)}
              className="max-w-[min(100vw-4rem,520px)] text-sm font-medium text-ink bg-black/[0.04] border border-black/[0.06] rounded-lg px-2 py-1.5">
              {challenges.map((c) => (
                <option key={c.public_id} value={String(c.public_id)}>{c.title}</option>
              ))}
            </select>
          </label>
          <I.ChevronRight className="w-3.5 h-3.5 text-ink/30 hidden sm:block"/>
          <span className="font-semibold line-clamp-2">{detail.title}</span>
          <div className="flex-1"/>
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-violet-500/10 text-violet-600 font-medium">
            <I.Bolt className="w-3 h-3"/> {detail.difficulty_display || detail.difficulty || '—'}
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-flame-500/10 text-flame-500 font-medium">
            +{detail.points != null ? detail.points : 0} XP
          </span>
        </div>
      </div>

      <ResizableThree
        leftW={leftW} setLeftW={setLeftW} rightW={rightW} setRightW={setRightW}
        left={<TaskPanel tab={tab} setTab={setTab} detail={detail} />}
        center={
          <EditorPanel
            code={code} setCode={setCode}
            running={running} results={results}
            onRun={() => handleRun(false)} onSubmit={() => handleRun(true)}
          />
        }
        right={<MentorChatPanel />}
      />
    </div>
  );
}

function ResizableThree({ leftW, setLeftW, rightW, setRightW, left, center, right }) {
  const startResize = (which) => (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startLeft = leftW;
    const startRight = rightW;
    const container = e.currentTarget.parentElement.getBoundingClientRect();
    const move = (ev) => {
      const dxPct = ((ev.clientX - startX) / container.width) * 100;
      if (which === 'L') {
        const nl = Math.min(Math.max(25, startLeft + dxPct), 60);
        setLeftW(nl);
      } else {
        const nr = Math.min(Math.max(15, startRight - dxPct), 40);
        setRightW(nr);
      }
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };

  const center_w = Math.max(20, 100 - leftW - rightW);

  return (
    <div className="max-w-[1600px] mx-auto px-3 sm:px-5 py-5">
      <div className="flex gap-0 h-[calc(100vh-64px-56px-40px)] min-h-[700px] rounded-2xl overflow-hidden ring-1 ring-black/5 bg-white shadow-soft">
        <div style={{ width: `${leftW}%` }} className="overflow-hidden">{left}</div>
        <div onMouseDown={startResize('L')} className="w-1.5 cursor-col-resize bg-black/[0.04] hover:bg-violet-500/30 transition-colors"/>
        <div style={{ width: `${center_w}%` }} className="overflow-hidden">{center}</div>
        <div onMouseDown={startResize('R')} className="w-1.5 cursor-col-resize bg-black/[0.04] hover:bg-violet-500/30 transition-colors"/>
        <div style={{ width: `${rightW}%` }} className="overflow-hidden">{right}</div>
      </div>
    </div>
  );
}

function TaskPanel({ tab, setTab, detail }) {
  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-5 pt-5 pb-3 border-b border-black/5">
        <div className="text-[11px] uppercase tracking-widest text-ink/50">Условие</div>
        <h1 className="text-2xl font-bold mt-1.5 leading-tight">{detail.title}</h1>
        <div className="flex items-center gap-2 mt-4">
          {[
            { id: 'condition', label: 'Условие' },
            { id: 'hints', label: 'Подсказки' },
            { id: 'discuss', label: 'Обсуждение' },
          ].map((t) => (
            <button key={t.id} type="button" onClick={() => setTab(t.id)}
              className={`relative px-3 py-2 text-sm font-medium transition-colors ${tab === t.id ? 'text-ink' : 'text-ink/50 hover:text-ink/80'}`}>
              {t.label}
              {tab === t.id && (
                <FM.motion.span layoutId="tab-underline"
                  className="absolute inset-x-2 -bottom-px h-0.5 grad-bg rounded-full"/>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin px-5 py-5 text-[14.5px] leading-relaxed text-ink/80">
        {tab === 'condition' && <ConditionContent detail={detail} />}
        {tab === 'hints' && <HintsContent detail={detail} />}
        {tab === 'discuss' && <DiscussContent/>}
      </div>
    </div>
  );
}

function ConditionContent({ detail }) {
  const desc = detail.description || '';
  const instr = detail.instructions || '';
  return (
    <div className="space-y-5">
      {desc && (
        <div className="whitespace-pre-wrap">{desc}</div>
      )}
      {instr && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-2">Инструкции</div>
          <div className="whitespace-pre-wrap rounded-xl bg-black/[0.025] ring-1 ring-black/[0.04] p-4 font-mono text-[13px]">{instr}</div>
        </div>
      )}
      {!desc && !instr && (
        <p className="text-ink/55">Описание задачи пока не заполнено.</p>
      )}

      <Callout tint="#2563EB">
        <span className="font-semibold">Ограничения:</span>{' '}
        время {detail.time_limit_ms != null ? `${detail.time_limit_ms} мс` : '—'},
        память {detail.memory_limit_mb != null ? `${detail.memory_limit_mb} МБ` : '—'}.
      </Callout>
    </div>
  );
}

function Callout({ children }) {
  return (
    <div className="rounded-xl p-4 grad-bg-soft text-sm text-ink/80 border border-violet-500/15">
      {children}
    </div>
  );
}

function HintsContent({ detail }) {
  const instr = detail.instructions || '';
  if (!instr) {
    return <p className="text-ink/55">Подсказок пока нет. Загляни в инструкции на вкладке «Условие».</p>;
  }
  return (
    <div className="space-y-3 text-sm text-ink/70">
      <p>Кратко: начни с чтения инструкций и публичных тестов в панели «Тесты» после запуска.</p>
      <div className="rounded-xl ring-1 ring-black/[0.06] p-4 whitespace-pre-wrap font-mono text-[12px] bg-black/[0.02]">{instr}</div>
    </div>
  );
}

function DiscussContent() {
  const msgs = [
    { user: 'Аня К.', avatar: 'АК', tint: '#2563EB', text: 'А зачем формула, если цикл и так успевает?', when: '2 ч назад', likes: 12 },
    { user: 'Куратор', avatar: 'КР', mentor: true, text: 'Аня, успевает при n до 10⁸. При 10⁹ — уже TL. Тренируй привычку оценивать сложность сразу.', when: '1 ч назад', likes: 24 },
  ];
  return (
    <div className="space-y-4">
      {msgs.map((m, i) => (
        <div key={i} className="flex gap-3">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0
            ${m.mentor ? 'grad-bg' : ''}`}
            style={!m.mentor ? { background: `linear-gradient(135deg, ${m.tint}, ${m.tint}99)` } : {}}>
            {m.avatar}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{m.user}</span>
              {m.mentor && <span className="text-[10px] grad-bg text-white px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">Ментор</span>}
              <span className="text-xs text-ink/40">· {m.when}</span>
            </div>
            <div className="text-sm text-ink/75 mt-1 leading-relaxed">{m.text}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EditorPanel({ code, setCode, running, results, onRun, onSubmit }) {
  const lines = code.split('\n');
  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-3 border-b border-black/5 flex items-center gap-3 flex-wrap">
        <div className="text-xs font-semibold text-ink/70 px-2 py-1 rounded-md bg-black/[0.04]">Python</div>
        <div className="flex-1"/>
        <div className="text-[11px] text-ink/45 uppercase tracking-widest hidden sm:block">solution.py</div>
        <button type="button" onClick={onRun} disabled={running}
          className="h-9 px-3.5 rounded-lg text-sm font-semibold bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 inline-flex items-center gap-1.5 transition-all disabled:opacity-50">
          <I.Play className="w-3.5 h-3.5 text-violet-600"/> Запустить
        </button>
        <button type="button" onClick={onSubmit} disabled={running}
          className="btn-grad btn-shimmer h-9 px-4 rounded-lg text-sm font-semibold text-white shadow-soft inline-flex items-center gap-1.5 disabled:opacity-50">
          <I.Send className="w-3.5 h-3.5"/> Отправить решение
        </button>
      </div>

      <div className="flex-1 code-bg overflow-hidden flex">
        <div className="px-3 py-3 font-mono text-xs text-slate-500 select-none text-right">
          {lines.map((_, i) => <div key={i} className="leading-[1.55]">{i + 1}</div>)}
        </div>
        <textarea
          value={code} onChange={(e) => setCode(e.target.value)}
          spellCheck="false"
          className="flex-1 bg-transparent text-slate-100 font-mono text-xs leading-[1.55] py-3 pr-4 resize-none scrollbar-thin focus:outline-none"
          style={{ caretColor: '#06B6D4' }}
        />
      </div>

      <ConsoleOutput running={running} results={results}/>
    </div>
  );
}

function ConsoleOutput({ running, results }) {
  return (
    <div className="border-t border-black/5 bg-paper">
      <div className="px-4 py-2.5 flex items-center gap-3 border-b border-black/5 flex-wrap">
        <div className="text-[11px] uppercase tracking-widest text-ink/55 font-semibold">Тесты</div>
        {results && results.demo && (
          <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
            демо (без сервера)
          </span>
        )}
        {results && (
          <>
            <div className="text-xs text-ink/55">
              {results.tests.filter((t) => t.pass).length} из {results.tests.length} (показ)
            </div>
            <div className="flex-1"/>
            {results.submit && results.tests.every((t) => t.pass) && (
              <FM.motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }}
                className="text-xs font-semibold text-emerald-600 inline-flex items-center gap-1">
                <I.Sparkle className="w-3 h-3"/> Демо принято
              </FM.motion.div>
            )}
          </>
        )}
      </div>
      <div className="max-h-44 overflow-auto scrollbar-thin p-3 space-y-1.5">
        {running && (
          <div className="flex items-center gap-2 text-sm text-ink/60">
            <span className="w-3 h-3 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
            Готовим отчёт по тестам…
          </div>
        )}
        {!running && !results && (
          <div className="text-sm text-ink/40 font-mono">{`> нажми «Запустить» — демо по публичным тестам из API`}</div>
        )}
        {!running && results && results.tests.map((t, i) => (
          <FM.motion.div key={t.id || i}
            initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
              t.pass ? 'bg-emerald-500/[0.08]' : 'bg-rose-500/[0.08]'
            }`}>
            <div className={t.pass ? 'check-dot' : 'cross-dot'}/>
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{t.name}</div>
              {!t.pass && (
                <div className="text-xs text-ink/60 font-mono mt-0.5 truncate">
                  ожидали <span className="text-emerald-600">{t.expected}</span>, получили <span className="text-rose-600">{t.got}</span>
                </div>
              )}
            </div>
            <div className="text-[10px] font-mono text-ink/40 uppercase tracking-widest shrink-0">{t.time}</div>
          </FM.motion.div>
        ))}
      </div>
    </div>
  );
}

function MentorChatPanel() {
  const messages = [
    { from: 'mentor', text: 'Привет! Когда подключим проверку на сервере, здесь появится разбор твоего решения.', when: '10:24' },
  ];
  const [draft, setDraft] = React.useState('');
  return (
    <div className="h-full flex flex-col bg-white relative">
      <div className="px-4 py-3 border-b border-black/5 flex items-center gap-3">
        <div className="avatar-ring"><div className="w-9 h-9 rounded-full bg-white flex items-center justify-center text-xs font-bold grad-text">КР</div></div>
        <div className="flex-1">
          <div className="text-sm font-semibold">Куратор курса</div>
          <div className="text-[11px] text-ink/55 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulseDot"/> Ментор онлайн
          </div>
        </div>
        <button type="button" className="text-ink/40 hover:text-ink"><I.Bell className="w-4 h-4"/></button>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin px-4 py-4 space-y-3">
        <div className="text-center text-[10px] text-ink/40 uppercase tracking-widest">Сегодня</div>
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.from === 'me' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-3.5 py-2.5 text-sm leading-relaxed ${
              m.from === 'me'
                ? 'grad-bg text-white rounded-2xl rounded-br-md'
                : 'bg-black/[0.04] text-ink rounded-2xl rounded-bl-md'
            }`}>
              <div>{m.text}</div>
              <div className={`text-[10px] mt-1 ${m.from === 'me' ? 'text-white/70' : 'text-ink/40'}`}>{m.when}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-black/5 p-3">
        <div className="ring-grad flex items-end gap-2 px-3 py-2 rounded-xl border border-black/[0.08] bg-white transition-all">
          <textarea
            value={draft} onChange={(e) => setDraft(e.target.value)} rows={1}
            placeholder="Напиши ментору…"
            className="flex-1 bg-transparent text-sm resize-none placeholder:text-ink/40 max-h-24"/>
          <button type="button" className="w-9 h-9 rounded-lg grad-bg text-white flex items-center justify-center shadow-soft hover:scale-105 transition-transform">
            <I.Send className="w-4 h-4"/>
          </button>
        </div>
      </div>

      <div className="absolute inset-0 flex items-center justify-center px-4"
        style={{ background: 'rgba(255,255,255,0.55)', backdropFilter: 'blur(6px)' }}>
        <div className="bg-white rounded-2xl shadow-glow ring-1 ring-violet-500/15 p-6 text-center max-w-[280px]">
          <div className="w-14 h-14 mx-auto rounded-2xl grad-bg flex items-center justify-center text-white mb-4">
            <I.Sparkle className="w-7 h-7"/>
          </div>
          <div className="text-base font-bold leading-tight">Чат с ментором — скоро</div>
          <p className="text-sm text-ink/60 mt-2 leading-relaxed">
            Готовим живые сессии: ментор будет видеть твой код в реальном времени и отвечать прямо здесь.
          </p>
        </div>
      </div>
    </div>
  );
}

window.ProblemPage = ProblemPage;
