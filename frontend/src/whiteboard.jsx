// Standalone tldraw board (no LiveKit call)

const Routes = window.Routes;

function whiteboardFeatureEnabled() {
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  if (!meta) return true;
  return meta.getAttribute('content') !== 'false';
}

function WhiteboardPage({ navigate, hashParams }) {
  const token = localStorage.getItem('access_token');
  const hostRef = React.useRef(null);
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const roomParam = (hashParams?.room || '').trim() || 'academy-studio';

  React.useEffect(() => {
    if (!token) return undefined;
    if (!whiteboardFeatureEnabled()) {
      setLoading(false);
      setError('Доска отключена на сервере.');
      return undefined;
    }

    let cancelled = false;
    let mounted = false;

    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await window.apiJson('/api/communication/whiteboard/studio/token/', {
          method: 'POST',
          auth: true,
          body: { room: roomParam },
        });
        if (cancelled) return;
        const api = window.BervinovWhiteboard;
        if (!api?.mount) {
          throw new Error('Whiteboard bundle не загружен. Обновите страницу.');
        }
        const host = hostRef.current;
        if (!host) return;
        api.mount(host, {
          roomId: data.room_id,
          syncToken: data.token,
          licenseKey: data.license_key || '',
        });
        mounted = true;
        setLoading(false);
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
  }, [token, roomParam]);

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
      <div className="shrink-0 h-12 px-4 sm:px-6 flex items-center justify-between border-b border-black/[0.06] bg-white/90">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-ink truncate">Доска Academy</div>
          <div className="text-[11px] text-ink/45 truncate">Комната: {roomParam}</div>
        </div>
        <button
          type="button"
          onClick={() => navigate(Routes.CONFERENCES)}
          className="h-9 px-3 rounded-lg text-sm font-medium text-violet-600 hover:bg-violet-50"
        >
          Созвоны
        </button>
      </div>
      <div className="relative flex-1 min-h-0">
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
        <div ref={hostRef} className="absolute inset-0 whiteboard-studio" />
      </div>
    </div>
  );
}

window.WhiteboardPage = WhiteboardPage;
