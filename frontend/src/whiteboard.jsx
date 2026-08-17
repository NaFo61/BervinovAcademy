// Standalone tldraw board (no LiveKit call)

const Routes = window.Routes;

function whiteboardFeatureEnabled() {
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  if (!meta) return true;
  return meta.getAttribute('content') !== 'false';
}

function WhiteboardPage({ navigate }) {
  const token = window.getAccessToken();
  const hostRef = React.useRef(null);
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [roomId, setRoomId] = React.useState('');
  const [importNotice, setImportNotice] = React.useState('');
  const [backNav, setBackNav] = React.useState(null);
  const [sideImages, setSideImages] = React.useState([]);

  React.useEffect(() => {
    if (!token) return undefined;
    if (!whiteboardFeatureEnabled()) {
      setLoading(false);
      setError('Доска отключена на сервере.');
      return undefined;
    }

    let cancelled = false;
    let mounted = false;
    const pending = window.consumeLessonBoardImport ? window.consumeLessonBoardImport() : null;
    if (pending?.backRoute) {
      setBackNav({ route: pending.backRoute, query: pending.backQuery || {} });
    }

    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await window.apiJson('/api/communication/whiteboard/studio/token/', {
          method: 'POST',
          auth: true,
          body: {},
        });
        if (cancelled) return;
        const api = window.BervinovWhiteboard;
        if (!api?.mount) {
          throw new Error('Whiteboard bundle не загружен. Обновите страницу.');
        }
        const host = hostRef.current;
        if (!host) return;
        setRoomId(data.room_id || '');
        api.mount(host, {
          roomId: data.room_id,
          syncToken: data.token,
          licenseKey: data.license_key || '',
        });
        mounted = true;
        setLoading(false);
        if (pending?.urls?.length) {
          const notice = pending.title
            ? `Картинка с задания «${pending.title}». Рисуйте на доске — это черновик.`
            : 'Картинка задания. Рисуйте на доске — это черновик.';
          if (api.createImagesFromUrls) {
            setImportNotice(notice);
            try {
              await api.createImagesFromUrls(pending.urls);
            } catch (err) {
              if (!cancelled) {
                setSideImages(pending.urls);
                setImportNotice(err?.message || 'Схема слева. Рисуйте на доске справа.');
              }
            }
          } else if (!cancelled) {
            setSideImages(pending.urls);
            setImportNotice(notice);
          }
        }
      } catch (err) {
        if (cancelled) return;
        setLoading(false);
        setError(err?.message || 'Не удалось открыть доску.');
      }
    })();

    return () => {
      cancelled = true;
      if (mounted && hostRef.current && window.BervinovWhiteboard?.unmount) {
        window.BervinovWhiteboard.unmount(hostRef.current);
      }
    };
  }, [token]);

  if (!token) {
    return (
      <div className="mx-auto max-w-md px-5 py-20 text-center">
        <div className="text-2xl font-bold text-ink">Нужен вход</div>
        <p className="mt-2 text-sm text-ink/60">Доска доступна после авторизации.</p>
        <button
          type="button"
          onClick={() => navigate(Routes.AUTH)}
          className="btn-grad mt-6 h-11 rounded-xl px-6 text-sm font-semibold text-white"
        >
          Войти
        </button>
      </div>
    );
  }

  return (
    <div className="h-full min-h-0 bg-[#F6F8FC] flex flex-col">
      <div className="shrink-0 h-14 px-3 sm:px-5 flex items-center gap-3 border-b border-black/[0.08] bg-white">
        <button
          type="button"
          onClick={() => {
            if (backNav?.route) navigate(backNav.route, backNav.query);
            else navigate(Routes.PROFILE);
          }}
          className="h-9 px-3 rounded-lg text-sm font-medium text-ink/70 hover:bg-black/[0.04] shrink-0"
        >
          ← {backNav?.route ? 'К заданию' : 'Назад'}
        </button>
        <div className="min-w-0 flex-1">
          <div className="text-base font-semibold text-ink truncate">Моя доска</div>
          <div className="text-xs text-ink/50 truncate">
            Личная — только вы. В созвоне доска общая.
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate(Routes.CONFERENCES)}
          className="h-9 px-3 rounded-lg text-sm font-semibold text-sky-700 hover:bg-sky-50 shrink-0"
        >
          Созвоны
        </button>
      </div>
      <div className="relative flex-1 min-h-0 overflow-hidden flex flex-col lg:flex-row">
        {sideImages.length > 0 && (
          <div className="shrink-0 lg:w-[42%] max-h-[38vh] lg:max-h-none lg:h-full overflow-auto bg-white border-b lg:border-b-0 lg:border-r border-black/[0.08] p-3">
            <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-2">
              Схема задания
            </div>
            {sideImages.map((src) => (
              <img
                key={src}
                src={src}
                alt="Схема задания"
                className="w-full h-auto rounded-lg ring-1 ring-black/[0.06] bg-[#fafafa] mb-3"
              />
            ))}
          </div>
        )}
        <div className="relative flex-1 min-h-0 overflow-hidden">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center text-sm text-ink/50 bg-white/60">
            Подключение к доске…
          </div>
        )}
        {error && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 px-6 text-center">
            <div className="text-sm text-rose-600">{error}</div>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold"
            >
              Обновить
            </button>
          </div>
        )}
        <div ref={hostRef} className="absolute inset-0 whiteboard-studio" data-room={roomId} />
        {importNotice && !error && (
          <div className="absolute left-3 right-3 sm:left-auto sm:right-4 top-3 z-20 max-w-md rounded-xl bg-white/95 ring-1 ring-violet-200 shadow-soft px-4 py-3 text-sm text-ink/80">
            {importNotice}
            <button
              type="button"
              onClick={() => setImportNotice('')}
              className="mt-2 block text-[12px] font-semibold text-violet-700"
            >
              Скрыть
            </button>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { WhiteboardPage });
