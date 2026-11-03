// LANDING — платформа для занятий с учениками

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;
const CourseCard = window.CourseCard;
const mapApiCourseToCard = window.mapApiCourseToCard;

const TRACKS = [
  {
    kicker: 'ЕГЭ',
    title: 'Информатика',
    desc: 'Задания экзамена по темам: графы, кодирование, таблицы, программы. Сначала короткое объяснение, затем задача — в том числе с кодом на Python.',
    points: ['Теория по номеру задания', 'Практика в формате экзамена', 'Разбор ошибки с преподавателем'],
    Icon: I.Code,
  },
  {
    kicker: 'ЕГЭ',
    title: 'Другие предметы',
    desc: 'Тот же формат для других предметов: урок по теме и задания, близкие к экзамену. Курс ведёт преподаватель, ученик идёт в своём темпе.',
    points: ['Курс по предмету', 'Задания после объяснения', 'Вопросы — в чат или на созвоне'],
    Icon: I.Book,
  },
  {
    kicker: 'С нуля',
    title: 'IT',
    desc: 'Если экзамен ещё не цель. Основы программирования: как написать программу, прочитать ошибку и довести задачу до результата.',
    points: ['Первые программы на Python', 'Код запускается в браузере', 'Можно начать без опыта'],
    Icon: I.Layers,
  },
];

const STEPS = [
  {
    title: 'Маршрут по курсу',
    desc: 'Курс разбит на уроки. Можно идти по порядку или открыть нужную тему.',
    Icon: I.Book,
  },
  {
    title: 'Задание после теории',
    desc: 'После короткого объяснения ученик решает задачу сам: тест, ответ или программа.',
    Icon: I.Layers,
  },
  {
    title: 'Код в браузере',
    desc: 'Python запускается на платформе. Сразу видно, что вывела программа и где ошибка.',
    Icon: I.Code,
  },
  {
    title: 'Преподаватель на связи',
    desc: 'Вопрос по заданию — в чат. Нужен разбор голосом — созвон и общая доска.',
    Icon: I.Chat,
  },
];

function LandingPage({ navigate }) {
  return (
    <div data-screen-label="01 Landing" className="min-h-screen">
      <Hero navigate={navigate} />
      <Tracks />
      <HowItWorks />
      <TopCourses navigate={navigate} />
      <CTABand navigate={navigate} />
    </div>
  );
}

function Hero({ navigate }) {
  const M = FM.motion;
  return (
    <section className="relative mesh-bg pt-12 sm:pt-20 pb-16 sm:pb-24 overflow-hidden">
      <div className="relative max-w-7xl mx-auto px-5 sm:px-8 grid lg:grid-cols-[1.1fr,1fr] gap-12 lg:gap-8 items-center">
        <div>
          <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/80 backdrop-blur border border-black/[0.06] text-xs font-semibold text-ink/70 mb-6">
            Платформа для занятий с учениками
          </M.div>
          <M.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.04 }}
            className="text-[40px] sm:text-[56px] lg:text-[64px] font-extrabold leading-[1.02] tracking-tight">
            Курсы и живые занятия<br />
            <span className="grad-text">в одном месте</span>
          </M.h1>
          <M.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.12 }}
            className="text-lg text-ink/65 mt-6 max-w-xl leading-relaxed">
            Bervinov Academy — место, где ученик проходит курс, а преподаватель ведёт его: объясняет, проверяет и разбирает ошибки. Готовим к ЕГЭ по информатике и другим предметам. Учим IT с нуля.
          </M.p>
          <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.2 }}
            className="mt-8 flex flex-col sm:flex-row sm:items-center gap-3">
            <button type="button" onClick={() => navigate(Routes.CATALOG)}
              className="btn-grad btn-shimmer h-14 px-7 rounded-2xl text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2">
              Смотреть курсы <I.ChevronRight className="w-5 h-5" />
            </button>
            <button type="button" onClick={() => navigate(Routes.AUTH)}
              className="h-14 px-6 rounded-2xl bg-white/80 backdrop-blur border border-black/[0.06] hover:border-violet-300 font-semibold inline-flex items-center justify-center gap-2 transition-colors">
              Создать аккаунт
            </button>
          </M.div>
          <M.ul initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35, duration: 0.5 }}
            className="mt-10 grid sm:grid-cols-3 gap-4 max-w-xl text-sm text-ink/70">
            {[
              'Урок, затем задание',
              'Python прямо в браузере',
              'Чат и созвон с преподавателем',
            ].map((line) => (
              <li key={line} className="flex items-start gap-2">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-sky-600 shrink-0" />
                <span>{line}</span>
              </li>
            ))}
          </M.ul>
        </div>
        <HeroBoard />
      </div>
    </section>
  );
}

function HeroBoard() {
  const M = FM.motion;
  return (
    <M.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
      className="relative">
      <div className="absolute -inset-6 -z-10 rounded-3xl grad-bg-soft blur-2xl opacity-90" />
      <div className="bg-white rounded-3xl shadow-glow ring-1 ring-black/[0.06] p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3 mb-5">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">Занятие</div>
            <div className="mt-1 text-xl font-bold tracking-tight">Как идёт работа с учеником</div>
          </div>
          <div className="shrink-0 inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            На связи
          </div>
        </div>

        <div className="space-y-2">
          {TRACKS.map((track, i) => (
            <div key={track.title}
              className={`rounded-2xl px-4 py-3 flex items-center gap-3 ${i === 0 ? 'bg-sky-50 ring-1 ring-sky-200' : 'bg-paper ring-1 ring-black/[0.04]'}`}>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${i === 0 ? 'bg-white text-sky-700' : 'bg-white text-ink/50'}`}>
                <track.Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">{track.kicker}</div>
                <div className="font-semibold leading-tight">{track.title}</div>
              </div>
              {i === 0 ? (
                <span className="text-[11px] font-semibold text-sky-800">Сейчас</span>
              ) : null}
            </div>
          ))}
        </div>

        <ol className="mt-5 grid grid-cols-3 gap-2 text-center">
          {['Объяснить', 'Решить', 'Разобрать'].map((step, i) => (
            <li key={step} className="rounded-xl bg-paper px-2 py-3 ring-1 ring-black/[0.04]">
              <div className="text-[11px] font-semibold text-ink/35">{i + 1}</div>
              <div className="text-sm font-semibold mt-0.5">{step}</div>
            </li>
          ))}
        </ol>
      </div>
    </M.div>
  );
}

function Tracks() {
  const M = FM.motion;
  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <div className="max-w-2xl mb-12">
          <div className="text-xs font-semibold uppercase tracking-widest text-sky-700 mb-3">Направления</div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            Три курса. Один способ заниматься
          </h2>
          <p className="mt-4 text-ink/60 leading-relaxed">
            Цель разная — экзамен или первые шаги в программировании. Ход занятия один: короткое объяснение, своя попытка, разбор с преподавателем.
          </p>
        </div>
        <div className="grid lg:grid-cols-3 gap-5">
          {TRACKS.map((track, i) => (
            <M.article key={track.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.45, delay: i * 0.06 }}
              className="rounded-3xl bg-paper p-6 sm:p-8 ring-1 ring-black/[0.04]">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-11 h-11 rounded-2xl bg-white text-sky-700 ring-1 ring-black/[0.04] flex items-center justify-center">
                  <track.Icon className="w-5 h-5" />
                </div>
                <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">{track.kicker}</div>
              </div>
              <h3 className="text-2xl font-bold tracking-tight">{track.title}</h3>
              <p className="mt-3 text-sm text-ink/65 leading-relaxed">{track.desc}</p>
              <ul className="mt-5 space-y-2">
                {track.points.map((point) => (
                  <li key={point} className="flex items-start gap-2 text-sm text-ink/75">
                    <I.Check className="w-4 h-4 mt-0.5 text-sky-700 shrink-0" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </M.article>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const M = FM.motion;
  return (
    <section className="bg-paper">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <div className="max-w-2xl mb-12">
          <div className="text-xs font-semibold uppercase tracking-widest text-sky-700 mb-3">На занятии</div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            Ученик делает сам. Преподаватель рядом
          </h2>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {STEPS.map((step, i) => (
            <M.div key={step.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
              className="rounded-2xl bg-white p-6 ring-1 ring-black/[0.05]">
              <div className="w-11 h-11 rounded-2xl bg-sky-50 text-sky-700 flex items-center justify-center mb-4">
                <step.Icon className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg leading-tight">{step.title}</h3>
              <p className="mt-2 text-sm text-ink/60 leading-relaxed">{step.desc}</p>
            </M.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TopCourses({ navigate }) {
  const [courses, setCourses] = React.useState([]);
  const [state, setState] = React.useState('loading');

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await window.fetchCoursesList();
        if (!cancelled) {
          setCourses(list.slice(0, 3).map(mapApiCourseToCard));
          setState('ok');
        }
      } catch (_) {
        if (!cancelled) {
          setCourses([]);
          setState('err');
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <div className="flex items-end justify-between flex-wrap gap-6 mb-12">
          <div className="max-w-2xl">
            <div className="text-xs font-semibold uppercase tracking-widest text-sky-700 mb-3">Каталог</div>
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">Открытые курсы</h2>
            <p className="mt-3 text-ink/60">Выберите курс и начните с любого урока. Полный список — в каталоге.</p>
          </div>
          <button type="button" onClick={() => navigate(Routes.CATALOG)}
            className="inline-flex items-center gap-2 text-sm font-semibold text-ink hover:text-violet-600 transition-colors">
            Все курсы <I.ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {state === 'loading' ? (
            <div className="col-span-full flex justify-center py-16 text-ink/55 text-sm gap-2">
              <span className="w-6 h-6 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
              Загружаем курсы…
            </div>
          ) : state === 'err' ? (
            <p className="col-span-full text-sm text-ink/55 text-center py-12">
              Курсы сейчас не загрузились.{' '}
              <button type="button" onClick={() => navigate(Routes.CATALOG)} className="text-sky-700 font-semibold hover:underline">
                Открыть каталог
              </button>
            </p>
          ) : courses.length === 0 ? (
            <p className="col-span-full text-sm text-ink/55 text-center py-12">
              Курсов пока нет.{' '}
              <button type="button" onClick={() => navigate(Routes.CATALOG)} className="text-sky-700 font-semibold hover:underline">
                Открыть каталог
              </button>
            </p>
          ) : (
            courses.map((c, i) => (
              <CourseCard
                key={c.id}
                course={c}
                delay={i * 0.08}
                onOpen={() => navigate(window.Routes.COURSE, { id: c.id })}
              />
            ))
          )}
        </div>
      </div>
    </section>
  );
}

function CTABand({ navigate }) {
  return (
    <section className="bg-paper">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-14 sm:py-24">
        <div className="rounded-3xl bg-ink text-white px-6 py-10 sm:px-14 sm:py-14">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
            <div className="max-w-2xl">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
                Выберите курс и начните занятие
              </h2>
              <p className="mt-4 text-white/70 leading-relaxed">
                Регистрация занимает минуту. Дальше — каталог, урок и преподаватель, если задание не идёт.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 shrink-0">
              <button type="button" onClick={() => navigate(Routes.CATALOG)}
                className="h-14 px-7 rounded-2xl bg-white text-ink font-semibold inline-flex items-center justify-center gap-2">
                Открыть каталог <I.ChevronRight className="w-5 h-5" />
              </button>
              <button type="button" onClick={() => navigate(Routes.AUTH)}
                className="h-14 px-6 rounded-2xl bg-white/10 border border-white/30 text-white font-semibold inline-flex items-center justify-center hover:bg-white/25 transition-colors">
                Создать аккаунт
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

window.LandingPage = LandingPage;
