// PROBLEM solving page — 3 resizable panels: task / editor / mentor chat

function ProblemPage() {
  const [tab, setTab] = React.useState('condition');
  const [lang, setLang] = React.useState('Python');
  const [code, setCode] = React.useState(DEFAULT_CODE.Python);
  const [running, setRunning] = React.useState(false);
  const [results, setResults] = React.useState(null);
  const [leftW, setLeftW] = React.useState(40);
  const [rightW, setRightW] = React.useState(22);

  React.useEffect(() => { setCode(DEFAULT_CODE[lang] || ''); }, [lang]);

  const handleRun = (submit) => {
    setRunning(true); setResults(null);
    setTimeout(() => {
      setRunning(false);
      const tests = [
        { id: 1, name: 'Простой пример', input: '5', expected: '15', got: '15', pass: true, time: '24ms' },
        { id: 2, name: 'Нули и единицы', input: '1', expected: '1', got: '1', pass: true, time: '12ms' },
        { id: 3, name: 'Большое число', input: '1000', expected: '500500', got: submit ? '500500' : '500500', pass: true, time: '48ms' },
        { id: 4, name: 'Отрицательное число', input: '-3', expected: '-6', got: submit ? '-6' : '0', pass: !!submit, time: '18ms' },
      ];
      setResults({ tests, submit });
    }, 900);
  };

  return (
    <div data-screen-label="03 Problem" className="min-h-[calc(100vh-64px)] bg-paper">
      <div className="border-b border-black/5 bg-white">
        <div className="max-w-[1600px] mx-auto px-5 sm:px-8 h-14 flex items-center gap-3 text-sm">
          <span className="text-ink/50">Python с нуля до Junior</span>
          <I.ChevronRight className="w-3.5 h-3.5 text-ink/30"/>
          <span className="text-ink/50">Модуль 4 · Циклы и рекурсия</span>
          <I.ChevronRight className="w-3.5 h-3.5 text-ink/30"/>
          <span className="font-semibold">Задача 12: Сумма арифметической прогрессии</span>
          <div className="flex-1"/>
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-violet-500/10 text-violet-600 font-medium">
            <I.Bolt className="w-3 h-3"/> Сложность · средняя
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-flame-500/10 text-flame-500 font-medium">
            +20 XP
          </span>
        </div>
      </div>

      <ResizableThree
        leftW={leftW} setLeftW={setLeftW} rightW={rightW} setRightW={setRightW}
        left={<TaskPanel tab={tab} setTab={setTab} />}
        center={
          <EditorPanel
            lang={lang} setLang={setLang} code={code} setCode={setCode}
            running={running} results={results}
            onRun={() => handleRun(false)} onSubmit={() => handleRun(true)}
          />
        }
        right={<MentorChatPanel />}
      />
    </div>
  );
}

const DEFAULT_CODE = {
  Python: `def sum_progression(n: int) -> int:
    """Сумма чисел от 1 до n включительно."""
    if n <= 0:
        return 0
    return n * (n + 1) // 2


# вход
n = int(input())
print(sum_progression(n))`,
  JavaScript: `function sumProgression(n) {
  if (n <= 0) return 0;
  return (n * (n + 1)) / 2;
}

const n = Number(require('fs').readFileSync(0, 'utf8'));
console.log(sumProgression(n));`,
  'C++': `#include <iostream>
using namespace std;

long long sum_progression(int n) {
    if (n <= 0) return 0;
    return (long long)n * (n + 1) / 2;
}

int main() {
    int n; cin >> n;
    cout << sum_progression(n) << endl;
}`
};

function ResizableThree({ leftW, setLeftW, rightW, setRightW, left, center, right }) {
  const startResize = (which) => (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startLeft = leftW; const startRight = rightW;
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
    const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up); };
    window.addEventListener('mousemove', move); window.addEventListener('mouseup', up);
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

function TaskPanel({ tab, setTab }) {
  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-5 pt-5 pb-3 border-b border-black/5">
        <div className="text-[11px] uppercase tracking-widest text-ink/50">Задача 12 · Циклы и рекурсия</div>
        <h1 className="text-2xl font-bold mt-1.5 leading-tight">Сумма арифметической прогрессии</h1>
        <div className="flex items-center gap-2 mt-4">
          {[
            { id: 'condition', label: 'Условие' },
            { id: 'hints', label: 'Подсказки' },
            { id: 'discuss', label: 'Обсуждение' },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
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
        {tab === 'condition' && <ConditionContent/>}
        {tab === 'hints' && <HintsContent/>}
        {tab === 'discuss' && <DiscussContent/>}
      </div>
    </div>
  );
}

function ConditionContent() {
  return (
    <div className="space-y-5">
      <p>Дано натуральное число <span className="font-mono bg-violet-500/10 text-violet-600 px-1.5 rounded">n</span>. Найди сумму всех чисел от <span className="font-mono bg-violet-500/10 text-violet-600 px-1.5 rounded">1</span> до <span className="font-mono bg-violet-500/10 text-violet-600 px-1.5 rounded">n</span> включительно.</p>
      <p>Кажется простым? Так и есть. Но обрати внимание на крайние случаи: что если <span className="font-mono">n = 0</span>? Или отрицательное? А если <span className="font-mono">n = 10^9</span> — успеет ли наивный цикл?</p>

      <div className="rounded-xl p-4 grad-bg-soft text-sm text-ink/80 border border-violet-500/15">
        <span className="font-semibold">Цель:</span> разобраться, когда цикл — лучший друг, а когда — враг производительности.
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-2">Формат ввода</div>
        <div className="text-sm text-ink/70">Одно целое число <span className="font-mono">n</span> (−10⁹ ≤ n ≤ 10⁹).</div>
      </div>
      <div>
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-2">Формат вывода</div>
        <div className="text-sm text-ink/70">Одно целое число — искомая сумма.</div>
      </div>

      <CodeExample input="5" output="15" note="1 + 2 + 3 + 4 + 5"/>
      <CodeExample input="1000" output="500500" note="формула Гаусса"/>
      <CodeExample input="-3" output="-6" note="−1 + (−2) + (−3)"/>

      <div className="pt-2">
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-2">Ограничения</div>
        <ul className="space-y-1.5 text-sm text-ink/70">
          <li className="flex items-center gap-2"><I.Clock className="w-3.5 h-3.5 text-violet-600"/> Время: 1 секунда</li>
          <li className="flex items-center gap-2"><I.Layers className="w-3.5 h-3.5 text-violet-600"/> Память: 64 МБ</li>
        </ul>
      </div>
    </div>
  );
}

function CodeExample({ input, output, note }) {
  return (
    <div className="rounded-xl bg-black/[0.025] ring-1 ring-black/[0.04] overflow-hidden">
      <div className="grid grid-cols-2 divide-x divide-black/[0.05]">
        <div className="p-3">
          <div className="text-[10px] uppercase tracking-widest text-ink/40 font-semibold mb-1.5">Ввод</div>
          <div className="font-mono text-sm">{input}</div>
        </div>
        <div className="p-3">
          <div className="text-[10px] uppercase tracking-widest text-ink/40 font-semibold mb-1.5">Вывод</div>
          <div className="font-mono text-sm">{output}</div>
        </div>
      </div>
      {note && <div className="px-3 py-1.5 bg-black/[0.025] text-[11px] text-ink/55 border-t border-black/[0.04]">// {note}</div>}
    </div>
  );
}

function HintsContent() {
  const [open, setOpen] = React.useState(null);
  const hints = [
    { t: 'Подсказка 1 · Подумай о крайних случаях', b: 'Что вернёт твоя функция при n = 0? А при отрицательном n? Опиши на бумаге 3 крайних случая прежде чем писать код.' },
    { t: 'Подсказка 2 · Цикл vs. формула', b: 'Если n = 10⁹, цикл успеет? Вспомни: операция занимает ~1нс, значит 10⁹ операций — ~1 секунда. Это ровно граница TL.' },
    { t: 'Подсказка 3 · Формула Гаусса', b: 'Гаусс в школе вывел: S = n·(n+1)/2. Это O(1) — независимо от размера n.' },
  ];
  return (
    <div className="space-y-3">
      {hints.map((h, i) => (
        <div key={i} className="rounded-xl ring-1 ring-black/[0.06] overflow-hidden">
          <button onClick={() => setOpen(open === i ? null : i)} className="w-full px-4 py-3 flex items-center justify-between text-left">
            <span className="text-sm font-medium">{h.t}</span>
            <I.ChevronDown className={`w-4 h-4 transition-transform ${open === i ? 'rotate-180' : ''}`}/>
          </button>
          <FM.AnimatePresence initial={false}>
            {open === i && (
              <FM.motion.div key="body" initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                className="overflow-hidden">
                <div className="px-4 pb-4 text-sm text-ink/65">{h.b}</div>
              </FM.motion.div>
            )}
          </FM.AnimatePresence>
        </div>
      ))}
    </div>
  );
}

function DiscussContent() {
  const msgs = [
    { user: 'Аня К.', avatar: 'АК', tint: '#7C3AED', text: 'А зачем формула, если цикл и так успевает?', when: '2 ч назад', likes: 12 },
    { user: 'Мирон', avatar: 'МБ', mentor: true, text: 'Аня, успевает при n до 10⁸. При 10⁹ — уже TL. Тренируй привычку оценивать сложность сразу.', when: '1 ч назад', likes: 24 },
    { user: 'Дима П.', avatar: 'ДП', tint: '#06B6D4', text: 'Зашло объяснение про Гаусса! Никогда так не думал об этом.', when: '40 мин назад', likes: 8 },
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
            <div className="flex items-center gap-3 mt-1.5 text-xs text-ink/50">
              <button className="inline-flex items-center gap-1 hover:text-violet-600"><I.Heart className="w-3.5 h-3.5"/>{m.likes}</button>
              <button className="hover:text-violet-600">Ответить</button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EditorPanel({ lang, setLang, code, setCode, running, results, onRun, onSubmit }) {
  const lines = code.split('\n');
  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-3 border-b border-black/5 flex items-center gap-3 flex-wrap">
        <div className="inline-flex items-center bg-black/[0.04] rounded-lg p-0.5">
          {['Python', 'JavaScript', 'C++'].map((l) => (
            <button key={l} onClick={() => setLang(l)}
              className={`px-3 h-8 text-xs font-medium rounded-md transition-colors ${
                lang === l ? 'bg-white shadow-sm text-ink' : 'text-ink/55 hover:text-ink/80'
              }`}>{l}</button>
          ))}
        </div>
        <div className="flex-1"/>
        <div className="text-[11px] text-ink/45 uppercase tracking-widest hidden sm:block">solution.{lang === 'Python' ? 'py' : lang === 'C++' ? 'cpp' : 'js'}</div>
        <button onClick={onRun} disabled={running}
          className="h-9 px-3.5 rounded-lg text-sm font-semibold bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 inline-flex items-center gap-1.5 transition-all disabled:opacity-50">
          <I.Play className="w-3.5 h-3.5 text-violet-600"/> Запустить
        </button>
        <button onClick={onSubmit} disabled={running}
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
          style={{ caretColor: '#F97316' }}
        />
      </div>

      <ConsoleOutput running={running} results={results}/>
    </div>
  );
}

function ConsoleOutput({ running, results }) {
  return (
    <div className="border-t border-black/5 bg-paper">
      <div className="px-4 py-2.5 flex items-center gap-3 border-b border-black/5">
        <div className="text-[11px] uppercase tracking-widest text-ink/55 font-semibold">Тесты</div>
        {results && (
          <>
            <div className="text-xs text-ink/55">
              {results.tests.filter(t => t.pass).length} из {results.tests.length} прошло
            </div>
            <div className="flex-1"/>
            {results.submit && results.tests.every(t => t.pass) && (
              <FM.motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }}
                className="text-xs font-semibold text-emerald-600 inline-flex items-center gap-1">
                <I.Sparkle className="w-3 h-3"/> Принято · +20 XP
              </FM.motion.div>
            )}
          </>
        )}
      </div>
      <div className="max-h-44 overflow-auto scrollbar-thin p-3 space-y-1.5">
        {running && (
          <div className="flex items-center gap-2 text-sm text-ink/60">
            <span className="w-3 h-3 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
            Компилируем и запускаем тесты…
          </div>
        )}
        {!running && !results && (
          <div className="text-sm text-ink/40 font-mono">{`> готов к запуску. нажми "Запустить" или ⌘+Enter`}</div>
        )}
        {!running && results && results.tests.map((t, i) => (
          <FM.motion.div key={t.id}
            initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
              t.pass ? 'bg-emerald-500/[0.08]' : 'bg-rose-500/[0.08]'
            }`}>
            <div className={t.pass ? 'check-dot' : 'cross-dot'}/>
            <div className="flex-1">
              <div className="font-medium">Тест {t.id}: {t.name}</div>
              {!t.pass && (
                <div className="text-xs text-ink/60 font-mono mt-0.5">
                  ожидали <span className="text-emerald-600">{t.expected}</span>, получили <span className="text-rose-600">{t.got}</span>
                </div>
              )}
            </div>
            <div className="text-[10px] font-mono text-ink/40 uppercase tracking-widest">{t.time}</div>
          </FM.motion.div>
        ))}
      </div>
    </div>
  );
}

function MentorChatPanel() {
  const messages = [
    { from: 'mentor', text: 'Привет! Видел твоё решение по предыдущей задаче — рекурсия там лишняя. Глянь как через `dict` собрать.', when: '10:24' },
    { from: 'me', text: 'Спасибо! Сейчас гляну. А по текущей — формула Гаусса подойдёт?', when: '10:32' },
    { from: 'mentor', text: 'Да, но не забудь про отрицательные n — там знак сменится. И int64, иначе переполнение.', when: '10:33' },
    { from: 'me', text: 'Понял, попробую 👍', when: '10:35' },
  ];
  const [draft, setDraft] = React.useState('');
  return (
    <div className="h-full flex flex-col bg-white relative">
      <div className="px-4 py-3 border-b border-black/5 flex items-center gap-3">
        <div className="avatar-ring"><div className="w-9 h-9 rounded-full bg-white flex items-center justify-center text-xs font-bold grad-text">МБ</div></div>
        <div className="flex-1">
          <div className="text-sm font-semibold">Мирон Бервинов</div>
          <div className="text-[11px] text-ink/55 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulseDot"/> Ментор онлайн
          </div>
        </div>
        <button className="text-ink/40 hover:text-ink"><I.Bell className="w-4 h-4"/></button>
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
        <div className="flex justify-start">
          <div className="bg-black/[0.04] rounded-2xl rounded-bl-md px-3.5 py-3 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulseDot"/>
            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulseDot" style={{ animationDelay: '0.2s' }}/>
            <span className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-pulseDot" style={{ animationDelay: '0.4s' }}/>
          </div>
        </div>
      </div>

      <div className="border-t border-black/5 p-3">
        <div className="ring-grad flex items-end gap-2 px-3 py-2 rounded-xl border border-black/[0.08] bg-white transition-all">
          <textarea
            value={draft} onChange={(e) => setDraft(e.target.value)} rows={1}
            placeholder="Спроси у Мирона…"
            className="flex-1 bg-transparent text-sm resize-none placeholder:text-ink/40 max-h-24"/>
          <button className="w-9 h-9 rounded-lg grad-bg text-white flex items-center justify-center shadow-soft hover:scale-105 transition-transform">
            <I.Send className="w-4 h-4"/>
          </button>
        </div>
        <div className="mt-1.5 text-[10px] text-ink/40 px-1">Среднее время ответа: 27 минут</div>
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
          <button className="mt-4 h-10 px-4 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold inline-flex items-center gap-1.5">
            <I.Bell className="w-3.5 h-3.5"/> Уведомить о запуске
          </button>
        </div>
      </div>
    </div>
  );
}

window.ProblemPage = ProblemPage;
