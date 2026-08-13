// CERTIFICATE — именной документ после 100% курса

const Routes = window.Routes;
const I = window.I;

function formatCertDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch (_) {
    return String(iso);
  }
}

function CertificatePage({ navigate, hashParams }) {
  const certId = hashParams?.get('id') || '';
  const [cert, setCert] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!certId) {
      setLoading(false);
      setError('missing');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await window.apiJson(
          `/api/progress/certificates/${encodeURIComponent(certId)}/`,
        );
        if (!cancelled) {
          setCert(data);
          setError('');
        }
      } catch (e) {
        if (!cancelled) setError(e.status === 404 ? 'not_found' : (e.message || 'load'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [certId]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3 text-ink/60">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем сертификат…</div>
      </div>
    );
  }

  if (error || !cert) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Сертификат не найден</div>
        <p className="text-sm text-ink/60 mt-2">
          {error === 'missing' ? 'Нет номера в ссылке.' : 'Проверьте ссылку или пройдите курс до 100%.'}
        </p>
        <button type="button" onClick={() => navigate(Routes.PROFILE)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          В профиль
        </button>
      </div>
    );
  }

  const issued = formatCertDate(cert.issued_at);

  return (
    <div data-screen-label="Certificate" className="min-h-screen pb-16">
      <style>{`
        @media print {
          nav, footer, .no-print { display: none !important; }
          body { background: white !important; }
          .certificate-sheet {
            box-shadow: none !important;
            margin: 0 !important;
            max-width: none !important;
          }
        }
      `}</style>

      <div className="no-print max-w-4xl mx-auto px-5 sm:px-8 pt-8 pb-4 flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={() => navigate(Routes.PROFILE)}
          className="text-sm text-violet-600 font-semibold inline-flex items-center gap-1 hover:underline">
          <I.ChevronRight className="w-4 h-4 rotate-180"/> В профиль
        </button>
        <div className="flex gap-2">
          <button type="button" onClick={() => window.print()}
            className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold">
            Печать
          </button>
          {cert.course_public_id && (
            <button type="button"
              onClick={() => navigate(Routes.COURSE, { id: cert.course_public_id })}
              className="h-10 px-4 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
              К курсу
            </button>
          )}
        </div>
      </div>

      <div className="certificate-sheet max-w-4xl mx-auto px-4 sm:px-8">
        <div className="relative bg-[#FBF8F1] rounded-sm shadow-glow overflow-hidden"
          style={{ border: '1px solid rgba(37,99,235,0.18)' }}>
          <div className="m-3 sm:m-5 border-[3px] border-[#1D4ED8]/80 p-1">
            <div className="border border-[#06B6D4]/50 px-6 sm:px-14 py-10 sm:py-14 text-center">
              <div className="text-[11px] font-semibold uppercase tracking-[0.35em] text-[#1D4ED8]">
                Bervinov Academy
              </div>
              <div className="mt-2 h-px w-24 mx-auto bg-gradient-to-r from-transparent via-[#2563EB] to-transparent"/>
              <h1 className="mt-6 text-3xl sm:text-5xl font-extrabold tracking-tight text-ink"
                style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>
                Сертификат
              </h1>
              <p className="mt-3 text-sm text-ink/55">о прохождении курса</p>

              <p className="mt-10 text-sm uppercase tracking-widest text-ink/45">Настоящим подтверждается, что</p>
              <p className="mt-3 text-2xl sm:text-4xl font-bold text-ink leading-tight"
                style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>
                {cert.student_name}
              </p>
              <p className="mt-8 text-sm text-ink/60">успешно прошёл(а) курс</p>
              <p className="mt-2 text-xl sm:text-2xl font-extrabold text-[#1D4ED8] leading-snug">
                {cert.course_title}
              </p>
              <p className="mt-4 text-sm text-ink/50 max-w-lg mx-auto leading-relaxed">
                Все уроки и задания курса выполнены на 100%.
              </p>

              <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-6 text-left">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-ink/40">Дата</div>
                  <div className="text-sm font-semibold mt-0.5">{issued || '—'}</div>
                </div>
                <div className="w-16 h-16 rounded-full border-2 border-[#2563EB]/40 flex items-center justify-center text-[#2563EB]">
                  <I.Trophy className="w-7 h-7"/>
                </div>
                <div className="sm:text-right">
                  <div className="text-[10px] uppercase tracking-widest text-ink/40">Номер</div>
                  <div className="text-sm font-mono font-semibold mt-0.5">{cert.serial}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

window.CertificatePage = CertificatePage;
