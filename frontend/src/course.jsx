// COURSE page — course detail with modules and challenges

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;
const CourseCover = window.CourseCover;
const COURSES = window.COURSES;

// ── Module data per static course ──────────────────────────────────────────
const COURSE_MODULES = {
  'python-junior': [
    {
      id: 'm1', title: 'Основы Python', icon: '🐍', lessons: 8, hours: 14, tasks: 6,
      items: [
        { id: 'l1',  type: 'lesson', title: 'Переменные, типы данных, ввод-вывод', dur: '25 мин' },
        { id: 'l2',  type: 'task',   title: 'Задача: Калькулятор на Python', dur: '20 мин' },
        { id: 'l3',  type: 'lesson', title: 'Условия и циклы', dur: '30 мин' },
        { id: 'l4',  type: 'task',   title: 'Задача: FizzBuzz + расширения', dur: '15 мин' },
        { id: 'l5',  type: 'lesson', title: 'Функции и область видимости', dur: '35 мин' },
        { id: 'l6',  type: 'task',   title: 'Задача: Рекурсия на списках', dur: '25 мин' },
        { id: 'l7',  type: 'lesson', title: 'Списки, кортежи, словари, множества', dur: '40 мин' },
        { id: 'l8',  type: 'quiz',   title: 'Тест по основам', dur: '10 мин' },
      ],
    },
    {
      id: 'm2', title: 'ООП в Python', icon: '🔧', lessons: 7, hours: 16, tasks: 5,
      items: [
        { id: 'l9',  type: 'lesson', title: 'Классы, объекты, __init__', dur: '35 мин' },
        { id: 'l10', type: 'task',   title: 'Задача: Класс банковского счёта', dur: '30 мин' },
        { id: 'l11', type: 'lesson', title: 'Наследование и полиморфизм', dur: '40 мин' },
        { id: 'l12', type: 'lesson', title: 'Магические методы (__str__, __len__, …)', dur: '30 мин' },
        { id: 'l13', type: 'task',   title: 'Задача: Стек и очередь через ООП', dur: '25 мин' },
        { id: 'l14', type: 'lesson', title: 'Декораторы: как работают на самом деле', dur: '45 мин' },
        { id: 'l15', type: 'task',   title: 'Задача: Кэширующий декоратор', dur: '35 мин' },
      ],
    },
    {
      id: 'm3', title: 'Асинхронность', icon: '⚡', lessons: 6, hours: 12, tasks: 4,
      items: [
        { id: 'l16', type: 'lesson', title: 'asyncio: event loop и корутины', dur: '40 мин' },
        { id: 'l17', type: 'lesson', title: 'async/await на практике', dur: '35 мин' },
        { id: 'l18', type: 'task',   title: 'Задача: Асинхронный парсер страниц', dur: '50 мин' },
        { id: 'l19', type: 'lesson', title: 'aiohttp vs httpx — когда что выбирать', dur: '25 мин' },
        { id: 'l20', type: 'task',   title: 'Задача: 50 конкурентных запросов', dur: '40 мин' },
        { id: 'l21', type: 'quiz',   title: 'Тест: асинхронное программирование', dur: '10 мин' },
      ],
    },
    {
      id: 'm4', title: 'Тестирование', icon: '✅', lessons: 5, hours: 10, tasks: 4,
      items: [
        { id: 'l22', type: 'lesson', title: 'pytest: основы и фикстуры', dur: '30 мин' },
        { id: 'l23', type: 'lesson', title: 'Моки и патчи (unittest.mock)', dur: '35 мин' },
        { id: 'l24', type: 'task',   title: 'Задача: Покрыть код тестами на 80%', dur: '45 мин' },
        { id: 'l25', type: 'lesson', title: 'TDD на практике', dur: '40 мин' },
        { id: 'l26', type: 'task',   title: 'Задача: TDD — игра «Жизнь»', dur: '60 мин' },
      ],
    },
    {
      id: 'm5', title: 'Финальный проект: Telegram-бот', icon: '🚀', lessons: 6, hours: 28, tasks: 8,
      items: [
        { id: 'l27', type: 'lesson', title: 'Архитектура Telegram-бота на aiogram', dur: '30 мин' },
        { id: 'l28', type: 'task',   title: 'Задача: Инлайн-клавиатуры и FSM', dur: '60 мин' },
        { id: 'l29', type: 'task',   title: 'Задача: Интеграция с PostgreSQL (asyncpg)', dur: '90 мин' },
        { id: 'l30', type: 'task',   title: 'Задача: Деплой на VPS через Docker Compose', dur: '60 мин' },
        { id: 'l31', type: 'lesson', title: 'Код-ревью с ментором', dur: '45 мин' },
        { id: 'l32', type: 'lesson', title: 'Финальная защита проекта', dur: '30 мин' },
      ],
    },
  ],

  'algo': [
    {
      id: 'am1', title: 'Сложность и базовые структуры', icon: '📊', lessons: 7, hours: 12, tasks: 8,
      items: [
        { id: 'al1', type: 'lesson', title: 'Big-O: O(n), O(log n), O(n²) — и почему это важно', dur: '35 мин' },
        { id: 'al2', type: 'lesson', title: 'Массивы, стеки, очереди, связные списки', dur: '40 мин' },
        { id: 'al3', type: 'task',   title: 'Задача: Балансировка скобок', dur: '20 мин' },
        { id: 'al4', type: 'task',   title: 'Задача: LRU-кэш через OrderedDict', dur: '30 мин' },
        { id: 'al5', type: 'lesson', title: 'Хэш-таблицы: коллизии и нагрузка', dur: '35 мин' },
        { id: 'al6', type: 'task',   title: 'Задача: Два числа (Two Sum)', dur: '20 мин' },
        { id: 'al7', type: 'quiz',   title: 'Тест: структуры данных', dur: '10 мин' },
      ],
    },
    {
      id: 'am2', title: 'Рекурсия и сортировки', icon: '🔄', lessons: 6, hours: 14, tasks: 6,
      items: [
        { id: 'al8',  type: 'lesson', title: 'Рекурсия: стек вызовов, хвостовая рекурсия', dur: '30 мин' },
        { id: 'al9',  type: 'task',   title: 'Задача: Перестановки и подмножества', dur: '35 мин' },
        { id: 'al10', type: 'lesson', title: 'MergeSort, QuickSort — разбор по шагам', dur: '45 мин' },
        { id: 'al11', type: 'task',   title: 'Задача: K-й наибольший элемент (QuickSelect)', dur: '30 мин' },
        { id: 'al12', type: 'lesson', title: 'Бинарный поиск и его вариации', dur: '40 мин' },
        { id: 'al13', type: 'task',   title: 'Задача: Поиск в повёрнутом массиве', dur: '25 мин' },
      ],
    },
    {
      id: 'am3', title: 'Графы', icon: '🌐', lessons: 8, hours: 18, tasks: 8,
      items: [
        { id: 'al14', type: 'lesson', title: 'BFS и DFS: когда что выбирать', dur: '40 мин' },
        { id: 'al15', type: 'task',   title: 'Задача: Число островов', dur: '25 мин' },
        { id: 'al16', type: 'task',   title: 'Задача: Кратчайший путь (BFS)', dur: '30 мин' },
        { id: 'al17', type: 'lesson', title: 'Алгоритм Дейкстры — пошагово', dur: '50 мин' },
        { id: 'al18', type: 'task',   title: 'Задача: Сеть компьютеров (Dijkstra)', dur: '40 мин' },
        { id: 'al19', type: 'lesson', title: 'Топологическая сортировка', dur: '35 мин' },
        { id: 'al20', type: 'task',   title: 'Задача: Порядок учебных курсов', dur: '30 мин' },
        { id: 'al21', type: 'quiz',   title: 'Тест: алгоритмы на графах', dur: '10 мин' },
      ],
    },
    {
      id: 'am4', title: 'Динамическое программирование', icon: '🧩', lessons: 7, hours: 20, tasks: 9,
      items: [
        { id: 'al22', type: 'lesson', title: 'Что такое ДП и как не путаться с рекурсией', dur: '40 мин' },
        { id: 'al23', type: 'task',   title: 'Задача: Лестница (Climbing Stairs)', dur: '15 мин' },
        { id: 'al24', type: 'task',   title: 'Задача: Наибольшая общая подпоследовательность (LCS)', dur: '35 мин' },
        { id: 'al25', type: 'lesson', title: 'Задача о рюкзаке — три подхода', dur: '45 мин' },
        { id: 'al26', type: 'task',   title: 'Задача: Разбиение суммы (Partition Equal Subset Sum)', dur: '40 мин' },
        { id: 'al27', type: 'lesson', title: 'Сегментные деревья: обновление и запросы', dur: '60 мин' },
        { id: 'al28', type: 'task',   title: 'Задача: Сумма на отрезке с обновлениями', dur: '50 мин' },
      ],
    },
  ],

  'web-react-fastapi': [
    {
      id: 'wm1', title: 'React 18 — современный подход', icon: '⚛️', lessons: 9, hours: 18, tasks: 7,
      items: [
        { id: 'wl1',  type: 'lesson', title: 'JSX, компоненты, props, state', dur: '30 мин' },
        { id: 'wl2',  type: 'lesson', title: 'Хуки: useState, useEffect, useRef', dur: '40 мин' },
        { id: 'wl3',  type: 'task',   title: 'Задача: Компонент формы с валидацией', dur: '35 мин' },
        { id: 'wl4',  type: 'lesson', title: 'useReducer и useContext', dur: '35 мин' },
        { id: 'wl5',  type: 'task',   title: 'Задача: Корзина покупок через useReducer', dur: '40 мин' },
        { id: 'wl6',  type: 'lesson', title: 'TanStack Query: кэш, инвалидация, мутации', dur: '50 мин' },
        { id: 'wl7',  type: 'task',   title: 'Задача: Бесконечный скролл списка', dur: '45 мин' },
        { id: 'wl8',  type: 'lesson', title: 'React Router 6: вложенные маршруты, лейауты', dur: '35 мин' },
        { id: 'wl9',  type: 'quiz',   title: 'Тест: React 18', dur: '10 мин' },
      ],
    },
    {
      id: 'wm2', title: 'FastAPI — бэкенд на Python', icon: '🚀', lessons: 8, hours: 16, tasks: 7,
      items: [
        { id: 'wl10', type: 'lesson', title: 'Маршруты, зависимости, Pydantic-схемы', dur: '35 мин' },
        { id: 'wl11', type: 'task',   title: 'Задача: CRUD-сервис через FastAPI', dur: '45 мин' },
        { id: 'wl12', type: 'lesson', title: 'SQLAlchemy 2.0 — async ORM', dur: '50 мин' },
        { id: 'wl13', type: 'task',   title: 'Задача: Модели и Alembic-миграции', dur: '40 мин' },
        { id: 'wl14', type: 'lesson', title: 'JWT-авторизация и OAuth2', dur: '45 мин' },
        { id: 'wl15', type: 'task',   title: 'Задача: Регистрация + защищённые эндпоинты', dur: '50 мин' },
        { id: 'wl16', type: 'lesson', title: 'WebSocket в FastAPI', dur: '30 мин' },
        { id: 'wl17', type: 'quiz',   title: 'Тест: FastAPI и REST', dur: '10 мин' },
      ],
    },
    {
      id: 'wm3', title: 'PostgreSQL и деплой', icon: '🐘', lessons: 6, hours: 12, tasks: 5,
      items: [
        { id: 'wl18', type: 'lesson', title: 'Индексы, EXPLAIN ANALYZE, оконные функции', dur: '40 мин' },
        { id: 'wl19', type: 'task',   title: 'Задача: Оптимизация медленного JOIN', dur: '35 мин' },
        { id: 'wl20', type: 'lesson', title: 'Docker Compose: фронт + бэк + БД', dur: '45 мин' },
        { id: 'wl21', type: 'task',   title: 'Задача: Собрать стек локально за 10 мин', dur: '30 мин' },
        { id: 'wl22', type: 'lesson', title: 'Деплой на VPS: nginx, SSL, CI/CD', dur: '50 мин' },
        { id: 'wl23', type: 'task',   title: 'Задача: Полный деплой проекта', dur: '90 мин' },
      ],
    },
    {
      id: 'wm4', title: 'Финальный проект', icon: '🏆', lessons: 5, hours: 20, tasks: 6,
      items: [
        { id: 'wl24', type: 'lesson', title: 'Архитектура и дизайн системы', dur: '45 мин' },
        { id: 'wl25', type: 'task',   title: 'Задача: Реализация основных функций', dur: '120 мин' },
        { id: 'wl26', type: 'task',   title: 'Задача: Тесты (pytest + Playwright)', dur: '60 мин' },
        { id: 'wl27', type: 'task',   title: 'Задача: Деплой финального проекта', dur: '60 мин' },
        { id: 'wl28', type: 'lesson', title: 'Код-ревью и итоговый разбор', dur: '45 мин' },
      ],
    },
  ],
};

const GENERIC_MODULES = (course) => [
  {
    id: 'gm1', title: 'Введение и основы', icon: '📖', lessons: 6, hours: 10, tasks: 5,
    items: [
      { id: 'gi1', type: 'lesson', title: `Введение в ${course.title}`, dur: '20 мин' },
      { id: 'gi2', type: 'lesson', title: 'Основные концепции и терминология', dur: '35 мин' },
      { id: 'gi3', type: 'task',   title: 'Задача: Первые шаги', dur: '25 мин' },
      { id: 'gi4', type: 'lesson', title: 'Практические примеры из реальных проектов', dur: '40 мин' },
      { id: 'gi5', type: 'task',   title: 'Задача: Практическое применение', dur: '30 мин' },
      { id: 'gi6', type: 'quiz',   title: 'Тест по основам', dur: '10 мин' },
    ],
  },
  {
    id: 'gm2', title: 'Основные темы', icon: '🎯', lessons: 8, hours: 16, tasks: 6,
    items: [
      { id: 'gi7',  type: 'lesson', title: 'Углублённый разбор ключевых тем', dur: '40 мин' },
      { id: 'gi8',  type: 'task',   title: 'Задача: Применение на практике', dur: '35 мин' },
      { id: 'gi9',  type: 'lesson', title: 'Типичные паттерны и антипаттерны', dur: '35 мин' },
      { id: 'gi10', type: 'task',   title: 'Задача: Код-рефакторинг', dur: '30 мин' },
      { id: 'gi11', type: 'lesson', title: 'Отладка и решение проблем', dur: '30 мин' },
      { id: 'gi12', type: 'task',   title: 'Задача: Найди баг', dur: '25 мин' },
      { id: 'gi13', type: 'lesson', title: 'Интеграция с другими инструментами', dur: '35 мин' },
      { id: 'gi14', type: 'quiz',   title: 'Тест по пройденным темам', dur: '10 мин' },
    ],
  },
  {
    id: 'gm3', title: 'Продвинутый уровень', icon: '🔥', lessons: 7, hours: 14, tasks: 5,
    items: [
      { id: 'gi15', type: 'lesson', title: 'Оптимизация и производительность', dur: '45 мин' },
      { id: 'gi16', type: 'task',   title: 'Задача: Ускорить в 10 раз', dur: '50 мин' },
      { id: 'gi17', type: 'lesson', title: 'Архитектурные решения', dur: '40 мин' },
      { id: 'gi18', type: 'task',   title: 'Задача: Спроектируй систему', dur: '60 мин' },
      { id: 'gi19', type: 'lesson', title: 'Тестирование и CI/CD', dur: '35 мин' },
      { id: 'gi20', type: 'task',   title: 'Задача: Полное тестовое покрытие', dur: '45 мин' },
      { id: 'gi21', type: 'quiz',   title: 'Финальный тест', dur: '15 мин' },
    ],
  },
  {
    id: 'gm4', title: 'Финальный проект', icon: '🚀', lessons: 4, hours: 14, tasks: 4,
    items: [
      { id: 'gi22', type: 'lesson', title: 'Архитектура и планирование проекта', dur: '30 мин' },
      { id: 'gi23', type: 'task',   title: 'Задача: Реализация проекта', dur: '120 мин' },
      { id: 'gi24', type: 'lesson', title: 'Код-ревью с ментором', dur: '45 мин' },
      { id: 'gi25', type: 'lesson', title: 'Защита и обратная связь', dur: '30 мин' },
    ],
  },
];

const MODULE_ICONS = ['📚', '🔧', '⚡', '✅', '🚀', '🌐', '🧩', '📊'];

function mapApiModules(modules) {
  return (modules || []).map((mod, i) => ({
    id: mod.public_id,
    title: mod.title,
    icon: MODULE_ICONS[i % MODULE_ICONS.length],
    lessons: 0,
    hours: 0,
    tasks: 0,
    items: [],
    description: mod.description || '',
  }));
}

function getCourseModules(courseId, course) {
  return COURSE_MODULES[courseId] || GENERIC_MODULES(course || { title: 'курс' });
}

// ── Item type config ────────────────────────────────────────────────────────
const ITEM_TYPE = {
  lesson: { label: 'Урок',  color: '#2563EB', bg: 'rgba(37,99,235,0.10)',  icon: '📖' },
  task:   { label: 'Задача', color: '#06B6D4', bg: 'rgba(6,182,212,0.10)', icon: '💻' },
  quiz:   { label: 'Тест',  color: '#7C3AED', bg: 'rgba(124,58,237,0.10)', icon: '🎯' },
};

// ── Helpers ─────────────────────────────────────────────────────────────────
function findCourse(courseId) {
  if (!courseId) return null;
  return COURSES.find((c) => c.id === courseId || c.slug === courseId) || null;
}

// ── CoursePage ──────────────────────────────────────────────────────────────
function CoursePage({ navigate, hashParams }) {
  const courseId = hashParams && hashParams.get ? hashParams.get('id') : null;
  const [apiRow, setApiRow] = React.useState(null);
  const [staticId, setStaticId] = React.useState(null);
  const [loadState, setLoadState] = React.useState(() => (courseId ? 'loading' : 'idle'));

  React.useEffect(() => {
    if (!courseId) {
      setApiRow(null);
      setStaticId(null);
      setLoadState('idle');
      return;
    }
    let cancelled = false;
    setLoadState('loading');
    setApiRow(null);
    setStaticId(null);
    (async () => {
      try {
        const data = await window.apiJson(`/api/content/courses/${encodeURIComponent(courseId)}/`);
        if (!cancelled) {
          setApiRow(data);
          setLoadState('ok');
        }
      } catch (e) {
        if (!cancelled) {
          const demo = findCourse(courseId);
          if (demo) {
            setStaticId(courseId);
            setLoadState('ok');
          } else {
            setLoadState('err');
          }
        }
      }
    })();
    return () => { cancelled = true; };
  }, [courseId]);

  const course = apiRow
    ? mapApiCourseToCourse(apiRow)
    : (staticId ? findCourse(staticId) : null);

  if (loadState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 text-ink/60 bg-paper">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем курс…</div>
      </div>
    );
  }

  if (!course || loadState === 'err' || (loadState === 'idle' && !courseId)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-paper text-center px-6">
        <div className="text-5xl">🔍</div>
        <div className="text-xl font-bold text-ink/80">Курс не найден</div>
        <p className="text-sm text-ink/55 max-w-sm">Возможно, курс был перемещён или ещё не добавлен в каталог.</p>
        <button onClick={() => navigate(Routes.CATALOG)}
          className="btn-grad btn-shimmer mt-2 h-11 px-6 rounded-xl text-white font-semibold">
          Открыть каталог
        </button>
      </div>
    );
  }

  const modules = apiRow
    ? mapApiModules(apiRow.modules)
    : getCourseModules(course.id || courseId, course);
  const totalLessons = modules.reduce((s, m) => s + (m.items || []).filter(i => i.type === 'lesson').length, 0);
  const totalTasks   = modules.reduce((s, m) => s + (m.items || []).filter(i => i.type === 'task').length, 0);
  const totalHours   = modules.reduce((s, m) => s + m.hours, 0);

  return (
    <div data-screen-label="Course" className="min-h-screen bg-paper">
      <CourseHero course={course} navigate={navigate} modules={modules}
        totalLessons={totalLessons} totalTasks={totalTasks} totalHours={totalHours}/>
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-14 grid lg:grid-cols-[1fr_340px] gap-10">
        <div className="space-y-10">
          <CourseHighlights course={course}/>
          <CourseModulesSection modules={modules} navigate={navigate} course={course}/>
        </div>
        <div>
          <CourseSidebar course={course} navigate={navigate}
            totalLessons={totalLessons} totalTasks={totalTasks} totalHours={totalHours}/>
        </div>
      </div>
    </div>
  );
}

// ── Hero ─────────────────────────────────────────────────────────────────────
function CourseHero({ course, navigate, modules, totalLessons, totalTasks, totalHours }) {
  const M = FM.motion;
  return (
    <section className="relative overflow-hidden"
      style={{ background: `linear-gradient(135deg, ${course.gradFrom} 0%, ${course.gradTo} 100%)` }}>
      {/* decorative overlay */}
      <div className="absolute inset-0 opacity-20"
        style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.1) 0 2px, transparent 2px 48px)' }}/>
      <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-white/20 blur-3xl"/>
      <div className="absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-white/10 blur-3xl"/>

      <div className="relative max-w-7xl mx-auto px-5 sm:px-8 py-14 pb-16">
        {/* breadcrumb */}
        <M.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          className="flex items-center gap-2 text-white/70 text-sm mb-8">
          <button onClick={() => navigate(Routes.LANDING)} className="hover:text-white transition-colors">Главная</button>
          <I.ChevronRight className="w-3.5 h-3.5"/>
          <button onClick={() => navigate(Routes.CATALOG)} className="hover:text-white transition-colors">Каталог</button>
          <I.ChevronRight className="w-3.5 h-3.5"/>
          <span className="text-white/90 truncate max-w-[200px]">{course.title}</span>
        </M.div>

        <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-start">
          <div>
            {/* tags */}
            <M.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.05 }}
              className="flex flex-wrap gap-2 mb-5">
              {(course.tags || []).slice(0, 4).map((t) => (
                <span key={t} className="px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white backdrop-blur border border-white/30 uppercase tracking-wide">
                  {t}
                </span>
              ))}
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/15 text-white/80 backdrop-blur border border-white/20">
                {course.level}
              </span>
            </M.div>

            {/* title */}
            <M.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
              className="text-3xl sm:text-5xl font-extrabold text-white leading-tight mb-4 max-w-2xl">
              {course.title}
            </M.h1>

            {/* desc */}
            <M.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.18 }}
              className="text-white/80 text-lg max-w-xl leading-relaxed mb-8">
              {course.desc}
            </M.p>

            {/* stats row */}
            <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.26 }}
              className="flex flex-wrap items-center gap-5 text-white/90 text-sm mb-8">
              {course.rating && course.rating !== '—' && (
                <span className="flex items-center gap-1.5 font-semibold">
                  <I.Star className="w-4 h-4 text-amber-300"/>
                  {course.rating} рейтинг
                </span>
              )}
              {course.students > 0 && (
                <span className="flex items-center gap-1.5">
                  <I.Users className="w-4 h-4"/>
                  {course.students.toLocaleString('ru-RU')} учеников
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <I.Book className="w-4 h-4"/>
                {totalLessons} уроков
              </span>
              <span className="flex items-center gap-1.5">
                <I.Code className="w-4 h-4"/>
                {totalTasks} задач
              </span>
              <span className="flex items-center gap-1.5">
                <I.Clock className="w-4 h-4"/>
                {totalHours} часов
              </span>
              <span className="flex items-center gap-1.5">
                <I.Layers className="w-4 h-4"/>
                {modules.length} модулей
              </span>
            </M.div>

            {/* CTAs */}
            <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.32 }}
              className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate(Routes.PROBLEM)}
                className="h-14 px-7 rounded-2xl bg-white text-ink font-bold text-[15px] inline-flex items-center gap-2.5 hover:scale-[1.02] transition-transform shadow-glow">
                <I.Play className="w-5 h-5 text-violet-600"/> Начать бесплатно
              </button>
              <button
                onClick={() => navigate(Routes.AUTH)}
                className="h-14 px-6 rounded-2xl bg-white/15 backdrop-blur border border-white/30 text-white font-semibold inline-flex items-center gap-2 hover:bg-white/25 transition-colors">
                Записаться на курс <I.ChevronRight className="w-4 h-4"/>
              </button>
            </M.div>
          </div>

          {/* floating card — course preview */}
          <M.div initial={{ opacity: 0, x: 30, scale: 0.95 }} animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="hidden lg:block w-72 bg-white rounded-3xl shadow-glow ring-1 ring-white/20 overflow-hidden">
            <CourseCover course={course} big/>
            <div className="p-5 space-y-3">
              {[
                { icon: '✅', text: `${totalLessons} уроков с разбором` },
                { icon: '💻', text: `${totalTasks} задач с проверкой` },
                { icon: '🏆', text: 'Сертификат по итогам' },
                { icon: '💬', text: 'Личный ментор' },
              ].map((it, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-ink/80">
                  <span className="text-base">{it.icon}</span>
                  {it.text}
                </div>
              ))}
            </div>
          </M.div>
        </div>
      </div>
    </section>
  );
}

// ── Highlights ────────────────────────────────────────────────────────────────
function CourseHighlights({ course }) {
  const M = FM.motion;
  const items = [
    { icon: I.Code,    tint: '#2563EB', title: 'Практика с первого дня',    desc: 'Каждый модуль заканчивается реальной задачей. Не «а вот пример», а «напиши сам».' },
    { icon: I.Chat,    tint: '#06B6D4', title: 'Живое code review',         desc: 'Ментор открывает твоё решение, прогоняет его и оставляет комментарии прямо в строках.' },
    { icon: I.Sparkle, tint: '#0EA5E9', title: 'Без воды',                  desc: 'Никаких 3-часовых лекций. Каждый урок — одна тема, один навык, одна задача.' },
    { icon: I.Trophy,  tint: '#7C3AED', title: 'Сертификат по итогам',      desc: 'После защиты финального проекта получишь именной сертификат.' },
  ];
  return (
    <div>
      <h2 className="text-2xl font-extrabold mb-6 tracking-tight">Чему ты научишься</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        {items.map((it, i) => (
          <M.div key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.45, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
            className="flex gap-4 p-5 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft hover:shadow-glow transition-shadow">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: `${it.tint}18`, color: it.tint }}>
              <it.icon className="w-5 h-5"/>
            </div>
            <div>
              <div className="font-semibold text-[15px] leading-tight mb-1">{it.title}</div>
              <div className="text-sm text-ink/60 leading-relaxed">{it.desc}</div>
            </div>
          </M.div>
        ))}
      </div>
    </div>
  );
}

// ── Modules accordion ─────────────────────────────────────────────────────────
function CourseModulesSection({ modules, navigate, course }) {
  const M = FM.motion;
  const [open, setOpen] = React.useState(new Set([modules[0]?.id]));

  const toggle = (id) => {
    setOpen((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalItems = modules.reduce((s, m) => s + (m.items || []).length, 0);

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <h2 className="text-2xl font-extrabold tracking-tight">Программа курса</h2>
        <div className="text-sm text-ink/50">
          {modules.length} модулей{totalItems > 0 ? ` · ${totalItems} занятий` : ''}
        </div>
      </div>

      <div className="space-y-3">
        {modules.map((mod, mi) => {
          const isOpen = open.has(mod.id);
          const taskCount = (mod.items || []).filter(i => i.type === 'task').length;
          return (
            <M.div key={mod.id}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: mi * 0.06, ease: [0.16, 1, 0.3, 1] }}
              className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft overflow-hidden">

              {/* module header */}
              <button type="button" onClick={() => toggle(mod.id)}
                className="w-full text-left px-6 py-5 flex items-center gap-4 hover:bg-black/[0.015] transition-colors group">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-paper shrink-0 ring-1 ring-black/[0.06]">
                  {mod.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">Модуль {mi + 1}</span>
                    {taskCount > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-700 font-semibold">
                        {taskCount} задач
                      </span>
                    )}
                  </div>
                  <div className="font-bold text-[16px] leading-snug truncate">{mod.title}</div>
                  {(mod.lessons > 0 || mod.hours > 0) ? (
                    <div className="text-xs text-ink/50 mt-1 flex items-center gap-3">
                      <span>{mod.lessons} уроков</span>
                      <span>·</span>
                      <span>{mod.hours} ч</span>
                    </div>
                  ) : mod.description ? (
                    <p className="text-xs text-ink/50 mt-1 line-clamp-2">{mod.description}</p>
                  ) : null}
                </div>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all shrink-0
                  ${isOpen ? 'grad-bg text-white' : 'bg-black/[0.04] text-ink/50 group-hover:bg-black/[0.07]'}`}>
                  <I.ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}/>
                </div>
              </button>

              {/* module items */}
              <FM.AnimatePresence initial={false}>
                {isOpen && (
                  <M.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
                    <div className="border-t border-black/[0.05]">
                      {(mod.items || []).length > 0 ? (
                        <div className="divide-y divide-black/[0.04]">
                          {(mod.items || []).map((item, ii) => (
                            <LessonRow key={item.id} item={item} index={ii} navigate={navigate}/>
                          ))}
                        </div>
                      ) : (
                        <p className="px-6 py-4 text-sm text-ink/65 leading-relaxed">
                          {mod.description || 'Содержимое модуля скоро появится.'}
                        </p>
                      )}
                    </div>
                  </M.div>
                )}
              </FM.AnimatePresence>
            </M.div>
          );
        })}
      </div>
    </div>
  );
}

// ── LessonRow ─────────────────────────────────────────────────────────────────
function LessonRow({ item, index, navigate }) {
  const M = FM.motion;
  const cfg = ITEM_TYPE[item.type] || ITEM_TYPE.lesson;
  const isTask = item.type === 'task';

  return (
    <M.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}
      className={`flex items-center gap-4 px-6 py-3.5 ${isTask ? 'hover:bg-cyan-500/[0.04] cursor-pointer group/row' : 'hover:bg-black/[0.02]'} transition-colors`}
      onClick={isTask ? () => navigate(Routes.PROBLEM) : undefined}>

      {/* index number */}
      <div className="w-6 text-[11px] font-mono text-ink/30 text-right shrink-0">{index + 1}</div>

      {/* type icon */}
      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base shrink-0"
        style={{ background: cfg.bg }}>
        {cfg.icon}
      </div>

      {/* title */}
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium leading-snug ${isTask ? 'group-hover/row:text-cyan-700 transition-colors' : 'text-ink/85'}`}>
          {item.title}
        </div>
      </div>

      {/* type badge */}
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md shrink-0"
        style={{ color: cfg.color, background: cfg.bg }}>
        {cfg.label}
      </span>

      {/* duration */}
      <span className="text-[11px] text-ink/40 font-mono shrink-0 hidden sm:block">{item.dur}</span>

      {/* arrow for tasks */}
      {isTask && (
        <I.ChevronRight className="w-4 h-4 text-cyan-600 opacity-0 group-hover/row:opacity-100 transition-opacity shrink-0"/>
      )}
    </M.div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function CourseSidebar({ course, navigate, totalLessons, totalTasks, totalHours }) {
  const M = FM.motion;
  const [sticky, setSticky] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setSticky(window.scrollY > 280);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const includes = [
    { icon: '📖', text: `${totalLessons} структурированных уроков` },
    { icon: '💻', text: `${totalTasks} задач с авто-проверкой` },
    { icon: '💬', text: 'Личный ментор в чате' },
    { icon: '⏱️', text: `${totalHours} часов контента` },
    { icon: '🏆', text: 'Именной сертификат' },
    { icon: '🔄', text: 'Пожизненный доступ к материалам' },
  ];

  return (
    <div className={`lg:sticky lg:top-20 space-y-5 transition-all`}>
      {/* price card */}
      <M.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="bg-white rounded-3xl ring-1 ring-black/[0.06] shadow-glow overflow-hidden">
        <CourseCover course={course}/>
        <div className="p-6">
          {course.price > 0 && (
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-extrabold">{course.price.toLocaleString('ru-RU')} ₽</span>
              <span className="text-sm text-ink/40 line-through">{Math.round(course.price * 1.43).toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          {course.price > 0 && (
            <div className="text-xs font-semibold text-emerald-600 mb-4 flex items-center gap-1">
              <I.Bolt className="w-3 h-3"/> Скидка 30% — до 30 мая
            </div>
          )}
          <button onClick={() => navigate(Routes.AUTH)}
            className="btn-grad btn-shimmer w-full h-13 py-3.5 rounded-2xl text-white font-bold text-[15px] inline-flex items-center justify-center gap-2 shadow-glow mb-3">
            {course.price > 0 ? 'Записаться на курс' : 'Начать бесплатно'}
            <I.ChevronRight className="w-4 h-4"/>
          </button>
          <button onClick={() => navigate(Routes.PROBLEM)}
            className="w-full h-11 rounded-xl border border-black/[0.08] text-sm font-semibold text-ink/70 hover:border-violet-300 hover:text-violet-600 transition-colors inline-flex items-center justify-center gap-2">
            <I.Play className="w-3.5 h-3.5"/> Попробовать бесплатно
          </button>

          <div className="mt-5 pt-5 border-t border-black/[0.05] space-y-2.5">
            <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-3">Курс включает</div>
            {includes.map((it, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-ink/75">
                <span className="text-base">{it.icon}</span>
                {it.text}
              </div>
            ))}
          </div>
        </div>
      </M.div>

      {/* mentor card */}
      <M.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
        className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-5">
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-4">Ведущий ментор</div>
        <div className="flex items-center gap-3 mb-4">
          <div className="avatar-ring">
            <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-sm font-bold grad-text">КБ</div>
          </div>
          <div>
            <div className="font-bold">Кирилл Бервинов</div>
            <div className="text-xs text-ink/55 flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulseDot"/>
              Онлайн · отвечает за 1 час
            </div>
          </div>
        </div>
        <p className="text-sm text-ink/65 leading-relaxed">
          8 лет опыта в Python и системном дизайне. Через меня прошло 5 600+ учеников. Отвечаю лично, без шаблонов.
        </p>
        <div className="mt-4 flex items-center gap-4 text-xs text-ink/55">
          <span className="flex items-center gap-1"><I.Star className="w-3.5 h-3.5 text-amber-400"/> 4.9</span>
          <span className="flex items-center gap-1"><I.Users className="w-3.5 h-3.5"/> 5 600+ учеников</span>
          <span className="flex items-center gap-1"><I.Book className="w-3.5 h-3.5"/> 6 курсов</span>
        </div>
      </M.div>
    </div>
  );
}

function mapApiCourseToCourse(row) {
  const tags = (row.technology || []).map((t) => t.name || '').filter(Boolean);
  const palette = [['#2563EB', '#06B6D4'], ['#7C3AED', '#F97316'], ['#1D4ED8', '#0EA5E9']];
  const h = String(row.public_id || '').split('').reduce((s, c) => s + c.charCodeAt(0), 0);
  const [gradFrom, gradTo] = palette[Math.abs(h) % palette.length];
  const moduleCount = (row.modules || []).length;
  const description = (row.description || '').trim();
  return {
    id: row.public_id, slug: row.slug, title: row.title || 'Курс',
    desc: description || (tags.length ? `Технологии: ${tags.join(', ')}.` : 'Курс Академии Бервинова.'),
    tags: tags.length ? tags : ['Курс'], cat: tags[0] || 'Курс',
    level: 'Курс', rating: '—', students: 0, lessons: moduleCount, hours: moduleCount, price: 0,
    gradFrom, gradTo,
    accentEmoji: tags[0] ? tags[0].slice(0, 2) : (row.title || '').slice(0, 2),
    imageUrl: row.image ? window.mediaUrl(row.image) : '',
    popularity: 75, fromApi: true,
  };
}

window.CoursePage = CoursePage;
