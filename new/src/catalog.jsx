// CATALOG page — filters + grid

function CatalogPage({ navigate }) {
  const M = FM.motion;
  const [cat, setCat] = React.useState('Все');
  const [query, setQuery] = React.useState('');
  const [sort, setSort] = React.useState('Популярность');
  const [price, setPrice] = React.useState(20000);
  const [levels, setLevels] = React.useState({ Новичок: true, Средний: true, Продвинутый: true });
  const [durations, setDurations] = React.useState({ 'до 40ч': true, '40–80ч': true, '80ч+': true });
  const [langs, setLangs] = React.useState({ RU: true, EN: false });

  const filtered = React.useMemo(() => {
    let out = COURSES.filter((c) => {
      if (cat !== 'Все' && c.cat !== cat) return false;
      if (c.price > price) return false;
      if (!levels[c.level]) return false;
      if (query && !(`${c.title} ${c.desc} ${c.tags.join(' ')}`.toLowerCase().includes(query.toLowerCase()))) return false;
      const dKey = c.hours <= 40 ? 'до 40ч' : c.hours <= 80 ? '40–80ч' : '80ч+';
      if (!durations[dKey]) return false;
      if (!langs[c.lang]) return false;
      return true;
    });
    if (sort === 'Популярность') out = out.sort((a, b) => b.popularity - a.popularity);
    if (sort === 'Новизна') out = [...out].reverse();
    if (sort === 'Рейтинг') out = [...out].sort((a, b) => b.rating - a.rating);
    return out;
  }, [cat, query, sort, price, levels, durations, langs]);

  return (
    <div data-screen-label="02 Catalog" className="min-h-screen mesh-bg-dim pb-16">
      {/* Header strip */}
      <div className="max-w-7xl mx-auto px-5 sm:px-8 pt-12 pb-8">
        <div className="text-xs font-semibold uppercase tracking-widest text-violet-600 mb-3">Каталог</div>
        <div className="flex items-end justify-between flex-wrap gap-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            Найди свой <span className="grad-text">курс</span>
          </h1>
          <div className="text-sm text-ink/55">
            Показано <span className="font-semibold text-ink">{filtered.length}</span> из <span className="font-semibold text-ink">{COURSES.length}</span>
          </div>
        </div>

        {/* Top control bar */}
        <div className="mt-8 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-4 flex flex-col gap-4">
          {/* row 1 — pills + search */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pr-2">
              {CATEGORIES.map((c) => (
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
                placeholder="React, FastAPI, ДП…"
                className="bg-transparent text-sm flex-1 placeholder:text-ink/40"/>
              {query && (
                <button onClick={() => setQuery('')} className="text-ink/40 hover:text-ink">
                  <I.X className="w-3.5 h-3.5"/>
                </button>
              )}
            </div>
          </div>
          {/* row 2 — price + sort */}
          <div className="flex items-center gap-6 flex-wrap pt-1">
            <div className="flex items-center gap-3 min-w-[260px]">
              <div className="text-xs font-semibold uppercase tracking-widest text-ink/50">Цена до</div>
              <div className="flex-1 relative">
                <input type="range" min="5000" max="25000" step="500" value={price}
                  onChange={(e) => setPrice(+e.target.value)}
                  className="w-full accent-violet-600 h-1.5"/>
              </div>
              <div className="font-mono text-sm font-semibold text-violet-600 tabular-nums w-24 text-right">
                {price.toLocaleString('ru-RU')} ₽
              </div>
            </div>
            <div className="flex-1"/>
            <div className="flex items-center gap-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-ink/50">Сортировка</div>
              {['Популярность', 'Новизна', 'Рейтинг'].map((s) => (
                <button key={s} onClick={() => setSort(s)}
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

      {/* Body — sidebar + grid */}
      <div className="max-w-7xl mx-auto px-5 sm:px-8 grid lg:grid-cols-[260px,1fr] gap-8">
        <aside className="space-y-5">
          <FilterGroup title="Уровень" items={levels} onChange={setLevels}/>
          <FilterGroup title="Длительность" items={durations} onChange={setDurations}/>
          <FilterGroup title="Язык" items={langs} onChange={setLangs}/>
          <button onClick={() => { setCat('Все'); setQuery(''); setPrice(25000);
            setLevels({ Новичок: true, Средний: true, Продвинутый: true });
            setDurations({ 'до 40ч': true, '40–80ч': true, '80ч+': true });
            setLangs({ RU: true, EN: true });
          }} className="w-full h-10 rounded-xl text-sm font-medium text-violet-600 bg-violet-500/10 hover:bg-violet-500/15 transition-colors">
            Сбросить фильтры
          </button>
        </aside>

        <div>
          <FM.LayoutGroup>
            <M.div layout className="grid sm:grid-cols-2 xl:grid-cols-3 gap-6">
              <FM.AnimatePresence mode="popLayout">
                {filtered.map((c, i) => (
                  <M.div layout key={c.id}
                    initial={{ opacity: 0, y: 14, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.94 }}
                    transition={{ duration: 0.35, delay: i * 0.04, ease: [0.16, 1, 0.3, 1] }}>
                    <CourseCard course={c} onOpen={() => navigate(Routes.PROBLEM)} delay={0}/>
                  </M.div>
                ))}
              </FM.AnimatePresence>
            </M.div>
          </FM.LayoutGroup>

          {filtered.length === 0 && (
            <div className="text-center py-20 text-ink/50">
              <div className="text-5xl mb-3">🔍</div>
              <div className="text-lg font-semibold text-ink/70">Ничего не нашлось</div>
              <div className="text-sm mt-1">Попробуй ослабить фильтры</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterGroup({ title, items, onChange }) {
  return (
    <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] p-5">
      <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-3">{title}</div>
      <div className="space-y-2.5">
        {Object.entries(items).map(([k, v]) => (
          <label key={k} className="flex items-center gap-3 cursor-pointer group">
            <span className={`w-5 h-5 rounded-md flex items-center justify-center transition-all
              ${v ? 'grad-bg' : 'bg-black/[0.06] group-hover:bg-black/[0.1]'}`}>
              {v && <I.Check className="w-3.5 h-3.5 text-white"/>}
            </span>
            <span className="text-sm text-ink/80 select-none">{k}</span>
            <input type="checkbox" checked={v} onChange={() => onChange({ ...items, [k]: !v })} className="sr-only"/>
          </label>
        ))}
      </div>
    </div>
  );
}

window.CatalogPage = CatalogPage;
