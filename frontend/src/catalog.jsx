// CATALOG page — API courses + search / sort



const mapApiCourseToCard = window.mapApiCourseToCard;

const CATALOG_PAGE_SIZE = 12;



function catalogPageNumbers(current, total) {

  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const set = new Set([1, total, current, current - 1, current + 1]);

  return [...set].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b);

}



function CatalogPagination({ page, totalPages, totalItems, pageSize, onPageChange }) {

  const I = window.I;

  if (totalPages <= 1) return null;



  const from = (page - 1) * pageSize + 1;

  const to = Math.min(page * pageSize, totalItems);

  const nums = catalogPageNumbers(page, totalPages);



  const go = (p) => {

    const next = Math.max(1, Math.min(p, totalPages));

    onPageChange(next);

    window.scrollTo({ top: 0, behavior: 'smooth' });

  };



  const btnBase = 'inline-flex items-center justify-center h-10 min-w-[2.5rem] px-3 rounded-xl text-sm font-medium transition-all disabled:opacity-40 disabled:pointer-events-none';

  const btnIdle = 'bg-black/[0.04] text-ink/70 hover:bg-black/[0.08]';

  const btnActive = 'grad-bg text-white shadow-soft';



  return (

    <nav className="mt-10 flex flex-col sm:flex-row items-center justify-between gap-4" aria-label="Страницы каталога">

      <div className="text-sm text-ink/55 order-2 sm:order-1">

        Курсы <span className="font-semibold text-ink">{from}–{to}</span> из{' '}

        <span className="font-semibold text-ink">{totalItems}</span>

      </div>

      <div className="flex items-center gap-1.5 flex-wrap justify-center order-1 sm:order-2">

        <button type="button" aria-label="Предыдущая страница" disabled={page <= 1}

          onClick={() => go(page - 1)} className={`${btnBase} ${btnIdle}`}>

          <I.ChevronRight className="w-4 h-4 rotate-180"/>

        </button>

        {nums.map((n, i) => {

          const prev = nums[i - 1];

          const gap = prev != null && n - prev > 1;

          return (

            <React.Fragment key={n}>

              {gap ? <span className="px-1 text-ink/35 select-none">…</span> : null}

              <button type="button" aria-label={`Страница ${n}`} aria-current={n === page ? 'page' : undefined}

                onClick={() => go(n)}

                className={`${btnBase} ${n === page ? btnActive : btnIdle}`}>

                {n}

              </button>

            </React.Fragment>

          );

        })}

        <button type="button" aria-label="Следующая страница" disabled={page >= totalPages}

          onClick={() => go(page + 1)} className={`${btnBase} ${btnIdle}`}>

          <I.ChevronRight className="w-4 h-4"/>

        </button>

      </div>

    </nav>

  );

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

  const [page, setPage] = React.useState(1);

  const [enrollMap, setEnrollMap] = React.useState({});

  const filterKeyRef = React.useRef(null);



  React.useEffect(() => {

    let cancelled = false;

    (async () => {

      const list = await window.fetchMyEnrollments();

      if (!cancelled) setEnrollMap(window.enrollmentsByCourseId(list));

    })();

    return () => { cancelled = true; };

  }, []);



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

        const list = await window.fetchCoursesList();

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



  const totalPages = Math.max(1, Math.ceil(filtered.length / CATALOG_PAGE_SIZE));

  const safePage = Math.min(page, totalPages);



  React.useEffect(() => {

    if (page !== safePage) setPage(safePage);

  }, [page, safePage]);



  React.useEffect(() => {

    const key = `${cat}|${query}|${sort}`;

    if (filterKeyRef.current === null) {

      filterKeyRef.current = key;

      return;

    }

    if (filterKeyRef.current !== key) {

      filterKeyRef.current = key;

      setPage(1);

    }

  }, [cat, query, sort]);



  const pageItems = React.useMemo(() => {

    const start = (safePage - 1) * CATALOG_PAGE_SIZE;

    return filtered.slice(start, start + CATALOG_PAGE_SIZE);

  }, [filtered, safePage]);



  const listFrom = filtered.length === 0 ? 0 : (safePage - 1) * CATALOG_PAGE_SIZE + 1;

  const listTo = Math.min(safePage * CATALOG_PAGE_SIZE, filtered.length);



  return (

    <div data-screen-label="02 Catalog" className="min-h-screen mesh-bg-dim pb-16">

      <div className="max-w-7xl mx-auto px-5 sm:px-8 pt-12 pb-8">

        <div className="text-xs font-semibold uppercase tracking-widest text-violet-600 mb-3">Каталог</div>

        <div className="flex items-end justify-between flex-wrap gap-4">

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">

            Найди свой <span className="grad-text">курс</span>

          </h1>

          <div className="text-sm text-ink/55">

            {filtered.length > 0 ? (

              <>

                На странице <span className="font-semibold text-ink">{listFrom}–{listTo}</span>

                {' · '}

                найдено <span className="font-semibold text-ink">{filtered.length}</span>

              </>

            ) : (

              <>Найдено <span className="font-semibold text-ink">0</span></>

            )}

            {loadState === 'ok' ? (

              <span> · всего в каталоге <span className="font-semibold text-ink">{courses.length}</span></span>

            ) : null}

          </div>

        </div>



        {loadState === 'err' && (

          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-sm px-4 py-3">

            {loadError}

          </div>

        )}



      </div>



      <div className="max-w-7xl mx-auto px-5 sm:px-8">

        <div className="grid lg:grid-cols-[280px_1fr] gap-6 items-start">

          <aside className="lg:sticky lg:top-24 space-y-4">

            <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-5">

              <div className="flex items-center gap-2 mb-4">

                <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-600">

                  <I.Filter className="w-4 h-4"/>

                </div>

                <div className="text-sm font-bold">Фильтры</div>

              </div>



              <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-2">Поиск</div>

              <div className="flex items-center gap-2 px-3 h-11 rounded-xl border border-black/[0.06] bg-black/[0.02] focus-within:border-violet-300 focus-within:ring-2 focus-within:ring-violet-500/10 transition-all">

                <I.Search className="w-4 h-4 text-ink/45 shrink-0"/>

                <input value={query} onChange={(e) => setQuery(e.target.value)}

                  placeholder="Название, технология…"

                  className="bg-transparent text-sm flex-1 placeholder:text-ink/40 focus:outline-none"/>

                {query && (

                  <button type="button" onClick={() => setQuery('')} className="text-ink/40 hover:text-ink shrink-0">

                    <I.X className="w-3.5 h-3.5"/>

                  </button>

                )}

              </div>



              <div className="mt-5 text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-3">Технологии</div>

              <div className="grid grid-cols-2 gap-2">

                {categories.map((c) => (

                  <button key={c} type="button" onClick={() => setCat(c)}

                    className={`px-3 py-2.5 rounded-xl text-sm font-medium text-left transition-all ${

                      cat === c

                        ? 'grad-bg text-white shadow-soft'

                        : 'bg-black/[0.03] text-ink/70 hover:bg-violet-500/[0.08] hover:text-violet-700 ring-1 ring-black/[0.04]'

                    }`}>

                    {c}

                  </button>

                ))}

              </div>



              <div className="mt-5 text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-3">Сортировка</div>

              <div className="space-y-1.5">

                {['Новизна', 'Название', 'Популярность'].map((s) => (

                  <button key={s} type="button" onClick={() => setSort(s)}

                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-left transition-all ${

                      sort === s

                        ? 'bg-violet-500/10 text-violet-700 ring-1 ring-violet-500/25'

                        : 'text-ink/65 hover:bg-black/[0.03]'

                    }`}>

                    <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${

                      sort === s ? 'border-violet-600' : 'border-ink/20'

                    }`}>

                      {sort === s && <span className="w-2 h-2 rounded-full bg-violet-600"/>}

                    </span>

                    {s}

                  </button>

                ))}

              </div>



              {(cat !== 'Все' || query) && (

                <button type="button"

                  onClick={() => { setCat('Все'); setQuery(''); }}

                  className="mt-5 w-full h-10 rounded-xl border border-black/[0.08] text-sm font-medium text-ink/60 hover:border-violet-300 hover:text-violet-600 transition-colors">

                  Сбросить фильтры

                </button>

              )}

            </div>

          </aside>



          <div>

        {loadState === 'loading' && (

          <div className="flex flex-col items-center justify-center py-24 text-ink/55 gap-3">

            <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>

            <div className="text-sm">Загружаем курсы…</div>

          </div>

        )}



        {loadState !== 'loading' && pageItems.length > 0 && (

          <FM.LayoutGroup>

            <M.div layout className="grid sm:grid-cols-2 xl:grid-cols-3 gap-6">

              <FM.AnimatePresence mode="popLayout">

                {pageItems.map((c, i) => (

                  <M.div layout key={c.id}

                    initial={{ opacity: 0, y: 14, scale: 0.96 }}

                    animate={{ opacity: 1, y: 0, scale: 1 }}

                    exit={{ opacity: 0, scale: 0.94 }}

                    transition={{ duration: 0.35, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}>

                    <CourseCard

                      course={c}

                      enrollment={enrollMap[c.id] || null}

                      onOpen={() => navigate(window.Routes.COURSE, { id: c.id })}

                      delay={0}

                    />

                  </M.div>

                ))}

              </FM.AnimatePresence>

            </M.div>

          </FM.LayoutGroup>

        )}



        {loadState !== 'loading' && (

          <CatalogPagination

            page={safePage}

            totalPages={totalPages}

            totalItems={filtered.length}

            pageSize={CATALOG_PAGE_SIZE}

            onPageChange={setPage}

          />

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

      </div>

    </div>

  );

}



window.CatalogPage = CatalogPage;
