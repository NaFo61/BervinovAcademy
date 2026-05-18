// CATALOG page — API courses + search / sort

function mapApiCourseToCard(row) {
  const tags = (row.technology || []).map((t) => t.name || '').filter(Boolean);
  const cat = tags[0] || 'Курс';
  const palette = [
    ['#2563EB', '#06B6D4'],
    ['#7C3AED', '#F97316'],
    ['#1D4ED8', '#0EA5E9'],
    ['#0EA5E9', '#22C55E'],
  ];
  const h = String(row.public_id || '').split('').reduce((s, c) => s + c.charCodeAt(0), 0);
  const [gradFrom, gradTo] = palette[Math.abs(h) % palette.length];
  const img = row.image ? window.mediaUrl(row.image) : '';
  const title = (row.title || 'Курс').trim();
  const emoji = tags[0] ? tags[0].slice(0, 2) : title.slice(0, 2);
  return {
    id: row.public_id,
    publicId: row.public_id,
    slug: row.slug,
    title: row.title,
    desc: tags.length ? `Технологии: ${tags.join(', ')}.` : 'Курс Академии Бервинова.',
    tags: tags.length ? tags : ['Курс'],
    cat,
    level: 'Курс',
    rating: '—',
    students: 0,
    lessons: 0,
    hours: 0,
    price: 0,
    lang: 'RU',
    popularity: Math.min(95, 40 + (Math.abs(h) % 56)),
    gradFrom,
    gradTo,
    accentEmoji: emoji,
    imageUrl: img,
    fromApi: true,
    createdAt: row.created_at || '',
  };
}

function CatalogPage({ navigate, hashParams }) {
  const FM = window.FM;
  const M = FM.motion;
  const I = window.I;
  const CourseCard = window.CourseCard;
  const [rows, setRows] = React.useState([]);
  const [loadState, setLoadState] = React.useState('loading');
  const [loadError, setLoadError] = React.useState('');
  const [cat, setCat] = React.useState('Все');
  const [query, setQuery] = React.useState(() => (hashParams && hashParams.get('q')) || '');
  const [sort, setSort] = React.useState('Новизна');

  React.useEffect(() => {
    const q = (hashParams && hashParams.get('q')) || '';
    setQuery(q);
  }, [hashParams]);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoadState('loading');
      setLoadError('');
      try {
        const data = await window.apiJson('/api/content/courses/');
        const list = Array.isArray(data) ? data : (data.results || []);
        if (!cancelled) {
          setRows(list);
          setLoadState('ok');
        }
      } catch (e) {
        if (!cancelled) {
          setRows([]);
          setLoadError(e.message || 'Не удалось загрузить курсы');
          setLoadState('err');
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const courses = React.useMemo(() => rows.map(mapApiCourseToCard), [rows]);

  const categories = React.useMemo(() => {
    const set = new Set();
    courses.forEach((c) => {
      c.tags.forEach((t) => set.add(t));
    });
    return ['Все', ...Array.from(set).sort()];
  }, [courses]);

  const filtered = React.useMemo(() => {
    let out = courses.filter((c) => {
      if (cat !== 'Все' && !c.tags.includes(cat) && c.cat !== cat) return false;
      if (query) {
        const hay = `${c.title} ${c.desc} ${c.tags.join(' ')}`.toLowerCase();
        if (!hay.includes(query.toLowerCase())) return false;
      }
      return true;
    });
    if (sort === 'Новизна') {
      out = [...out].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
    }
    if (sort === 'Название') {
      out = [...out].sort((a, b) => a.title.localeCompare(b.title, 'ru'));
    }
    if (sort === 'Популярность') {
      out = [...out].sort((a, b) => b.popularity - a.popularity);
    }
    return out;
  }, [courses, cat, query, sort]);

  return (
    <div data-screen-label="02 Catalog" className="min-h-screen mesh-bg-dim pb-16">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 pt-12 pb-8">
        <div className="text-xs font-semibold uppercase tracking-widest text-violet-600 mb-3">Каталог</div>
        <div className="flex items-end justify-between flex-wrap gap-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Найди свой <span className="grad-text">курс</span>
          </h1>
          <div className="text-sm text-ink/55">
            Показано <span className="font-semibold text-ink">{filtered.length}</span>
            {loadState === 'ok' ? <span> из <span className="font-semibold text-ink">{courses.length}</span></span> : null}
          </div>
        </div>

        {loadState === 'err' && (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-sm px-4 py-3">
            {loadError}
          </div>
        )}

        <div className="mt-8 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-4 flex flex-col gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pr-2">
              {categories.map((c) => (
                <button key={c} onClick={() => setCat(c)}
                  className={`px-3.5 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                    cat === c ? 'grad-bg text-white shadow-soft' : 'bg-black/[0.04] text-ink/70 hover:bg-black/[0.07]'
                  }`}>
                  {c}
                </button>
              ))}
            </div>
            <div className="flex-1 min-w-[200px]"/>
            <div className="ring-grad flex items-center gap-2 px-3 h-11 rounded-xl border border-black/[0.06] bg-white w-full sm:w-72 transition-all">
              <I.Search className="w-4 h-4 text-ink/50"/>
              <input value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder="Название, технология…"
                className="bg-transparent text-sm flex-1 placeholder:text-ink/40"/>
              {query && (
                <button type="button" onClick={() => setQuery('')} className="text-ink/40 hover:text-ink">
                  <I.X className="w-3.5 h-3.5"/>
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-6 flex-wrap pt-1">
            <div className="flex items-center gap-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-ink/50">Сортировка</div>
              {['Новизна', 'Название', 'Популярность'].map((s) => (
                <button key={s} type="button" onClick={() => setSort(s)}
                  className={`px-3 h-9 rounded-lg text-xs font-medium transition-all ${
                    sort === s ? 'bg-violet-500/10 text-violet-600 ring-1 ring-violet-500/20' : 'text-ink/60 hover:bg-black/[0.04]'
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {loadState === 'loading' && (
          <div className="flex flex-col items-center justify-center py-24 text-ink/55 gap-3">
            <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
            <div className="text-sm">Загружаем курсы…</div>
          </div>
        )}

        {loadState !== 'loading' && (
          <FM.LayoutGroup>
            <M.div layout className="grid sm:grid-cols-2 xl:grid-cols-3 gap-6">
              <FM.AnimatePresence mode="popLayout">
                {filtered.map((c, i) => (
                  <M.div layout key={c.id}
                    initial={{ opacity: 0, y: 14, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.94 }}
                    transition={{ duration: 0.35, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}>
                    <CourseCard
                      course={c}
                      onOpen={() => navigate(window.Routes.COURSE, { id: c.id })}
                      delay={0}
                    />
                  </M.div>
                ))}
              </FM.AnimatePresence>
            </M.div>
          </FM.LayoutGroup>
        )}

        {loadState !== 'loading' && filtered.length === 0 && (
          <div className="text-center py-20 text-ink/50">
            <div className="text-5xl mb-3">🔍</div>
            <div className="text-lg font-semibold text-ink/70">Ничего не нашлось</div>
            <div className="text-sm mt-1">Попробуй изменить поиск или категорию</div>
          </div>
        )}
      </div>
    </div>
  );
}

window.CatalogPage = CatalogPage;
