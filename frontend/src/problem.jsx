// PROBLEM — legacy route: redirects into course learn flow

const Routes = window.Routes;

function ProblemPage({ hashParams, navigate }) {
  const challengeParam = hashParams && hashParams.get ? hashParams.get('challenge') : null;
  const [message, setMessage] = React.useState('Перенаправляем…');

  React.useEffect(() => {
    let cancelled = false;

    if (!challengeParam) {
      navigate(Routes.CATALOG);
      return;
    }

    (async () => {
      try {
        const d = await window.apiJson(
          `/api/content/challenges/${encodeURIComponent(challengeParam)}/`,
        );
        if (cancelled) return;
        if (d.course_public_id && d.module_public_id) {
          navigate(Routes.LEARN, {
            course: d.course_public_id,
            lesson: `coding-${d.public_id}`,
          });
          return;
        }
        setMessage('Задача не привязана к модулю курса. Откройте курс из каталога.');
      } catch (e) {
        if (!cancelled) {
          setMessage(e.message || 'Не удалось открыть задачу');
        }
      }
    })();

    return () => { cancelled = true; };
  }, [challengeParam, navigate]);

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center gap-3 text-ink/60 bg-paper px-6 text-center">
      <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
      <div className="text-sm">{message}</div>
    </div>
  );
}

window.ProblemPage = ProblemPage;
