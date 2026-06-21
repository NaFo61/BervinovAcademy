// MENTOR page — статистика курсов и ответы учеников

const I = window.I;
const Routes = window.Routes;

function studentName(row) {
  if (row.student) {
    return [row.student.first_name, row.student.last_name].filter(Boolean).join(' ').trim() || 'Ученик';
  }
  return [row.first_name, row.last_name].filter(Boolean).join(' ').trim() || 'Ученик';
}

function studentPublicId(row) {
  return row.user_public_id || row.student?.public_id || null;
}

function MentorLink({ children, onClick, className }) {
  return (
    <button type="button" onClick={onClick}
      className={`text-violet-600 text-xs font-semibold hover:underline inline-flex items-center gap-1 ${className || ''}`}>
      {children}
    </button>
  );
}

function SubmissionFeedback({ testResults }) {
  const tr = testResults || {};
  if (!tr.failed_test_number && !tr.actual_output && !tr.expected_output) return null;
  return (
    <div className="mt-3 p-3 rounded-xl bg-amber-50 ring-1 ring-amber-200 text-xs text-amber-900">
      {tr.failed_test_number != null && (
        <div>Упал тест №{tr.failed_test_number}</div>
      )}
      {tr.actual_output != null && (
        <div className="mt-1 font-mono whitespace-pre-wrap">Факт: {tr.actual_output}</div>
      )}
      {tr.expected_output != null && (
        <div className="mt-1 font-mono whitespace-pre-wrap text-emerald-800">Ожидалось: {tr.expected_output}</div>
      )}
    </div>
  );
}

function ChallengeTestsPanel({ challenge, loading, onClose }) {
  if (!challenge && !loading) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-glow max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <div className="text-lg font-bold">{loading ? 'Загрузка…' : challenge?.title}</div>
            {!loading && challenge && (
              <div className="text-xs text-ink/50 mt-1">
                {challenge.course_title} · {challenge.test_cases?.length || 0} тестов (включая скрытые)
              </div>
            )}
          </div>
          <button type="button" onClick={onClose} className="text-ink/45 hover:text-ink text-xl leading-none">×</button>
        </div>
        {loading ? (
          <div className="py-8 text-center text-sm text-ink/50">Загружаем тесты…</div>
        ) : (
          <div className="space-y-3">
            {(challenge?.test_cases || []).map((tc, i) => (
              <div key={tc.public_id || i}
                className={`rounded-xl ring-1 p-4 text-[13px] font-mono ${tc.is_hidden ? 'ring-amber-200 bg-amber-50/50' : 'ring-black/[0.06] bg-black/[0.02]'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-semibold uppercase tracking-widest text-ink/45">
                    Тест {tc.order_index ?? (i + 1)}
                  </span>
                  {tc.is_hidden && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-800">скрытый</span>
                  )}
                </div>
                <div><span className="text-ink/50">вход: </span><pre className="whitespace-pre-wrap mt-0.5">{tc.input_data}</pre></div>
                <div className="mt-2"><span className="text-ink/50">ожидается: </span><pre className="whitespace-pre-wrap mt-0.5 text-emerald-700">{tc.expected_output}</pre></div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MentorPage({ navigate }) {
  const [accessState, setAccessState] = React.useState('checking');
  const [tab, setTab] = React.useState('courses');
  const [courses, setCourses] = React.useState([]);
  const [selectedCourse, setSelectedCourse] = React.useState(null);
  const [students, setStudents] = React.useState([]);
  const [codeRows, setCodeRows] = React.useState([]);
  const [quizRows, setQuizRows] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [selectedStudent, setSelectedStudent] = React.useState(null);
  const [testsModal, setTestsModal] = React.useState(null);
  const [testsLoading, setTestsLoading] = React.useState(false);

  const openLearn = (courseId, moduleId, lessonType, lessonId) => {
    const q = window.buildLearnQuery(courseId, moduleId, lessonType, lessonId);
    if (q) navigate(Routes.LEARN, q);
  };

  const openProfile = (userId) => {
    window.openStudentProfile(navigate, userId);
  };

  const startCallWith = async (userPublicId) => {
    setError('');
    try {
      const conf = await window.createConference(userPublicId);
      window.openConferenceCall(navigate, conf.public_id);
    } catch (e) {
      setError(e.message || 'Не удалось создать созвон');
    }
  };

  const openAllTests = async (challengePublicId) => {
    setTestsModal(null);
    setTestsLoading(true);
    try {
      const data = await window.fetchApiJson(
        `/api/mentoring/challenges/${encodeURIComponent(challengePublicId)}/`,
        { auth: true },
      );
      setTestsModal(data);
    } catch (e) {
      setError(e.message || 'Не удалось загрузить тесты');
    } finally {
      setTestsLoading(false);
    }
  };

  React.useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setAccessState('guest');
      setLoading(false);
      return;
    }
    const payload = window.parseJwtPayload(token);
    if (payload.role !== 'mentor' && payload.role !== 'admin') {
      setAccessState('forbidden');
      setLoading(false);
      return;
    }
    setAccessState('ok');
  }, []);

  React.useEffect(() => {
    if (accessState !== 'ok') return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await window.fetchApiJson('/api/mentoring/courses/', { auth: true });
        if (!cancelled) {
          setCourses(data || []);
          if ((data || []).length && !selectedCourse) {
            setSelectedCourse(data[0].course_public_id);
          }
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Ошибка загрузки');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [accessState]);

  React.useEffect(() => {
    if (accessState !== 'ok' || !selectedCourse) return;
    let cancelled = false;
    (async () => {
      try {
        const [studentsResp, codeResp, quizResp] = await Promise.all([
          window.fetchApiJson(`/api/mentoring/courses/${encodeURIComponent(selectedCourse)}/students/`, { auth: true }),
          window.fetchApiJson(`/api/mentoring/code-submissions/?course_public_id=${encodeURIComponent(selectedCourse)}`, { auth: true }),
          window.fetchApiJson(`/api/mentoring/quiz-answers/?course_public_id=${encodeURIComponent(selectedCourse)}`, { auth: true }),
        ]);
        if (!cancelled) {
          setStudents(studentsResp?.students || []);
          setCodeRows(codeResp || []);
          setQuizRows(quizResp || []);
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Ошибка загрузки данных курса');
      }
    })();
    return () => { cancelled = true; };
  }, [accessState, selectedCourse]);

  const filteredCode = selectedStudent
    ? codeRows.filter((r) => r.student?.public_id === selectedStudent)
    : codeRows;
  const filteredQuiz = selectedStudent
    ? quizRows.filter((r) => r.student?.public_id === selectedStudent)
    : quizRows;

  const courseMeta = courses.find((c) => c.course_public_id === selectedCourse);

  if (accessState === 'guest') {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <p className="text-sm text-ink/60 mt-2">Панель ментора доступна после авторизации.</p>
        <button type="button" onClick={() => navigate(Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          Войти
        </button>
      </div>
    );
  }

  if (accessState === 'forbidden') {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нет доступа</div>
        <p className="text-sm text-ink/60 mt-2">Раздел только для менторов и администраторов.</p>
        <button type="button" onClick={() => navigate(Routes.CATALOG)}
          className="mt-6 h-11 px-6 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
          В каталог
        </button>
      </div>
    );
  }

  return (
    <div data-screen-label="Mentor" className="min-h-screen pb-16 bg-paper">
      {(testsModal || testsLoading) && (
        <ChallengeTestsPanel
          challenge={testsModal}
          loading={testsLoading}
          onClose={() => { setTestsModal(null); setTestsLoading(false); }}
        />
      )}

      <section className="mesh-bg border-b border-black/[0.04] py-10">
        <div className="max-w-7xl mx-auto px-5 sm:px-8">
          <h1 className="text-3xl font-extrabold tracking-tight">Панель ментора</h1>
          <p className="text-sm text-ink/60 mt-2 max-w-2xl">
            Статистика курсов, прогресс учеников, отправленный код и ответы на тесты.
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-8 space-y-6">
        {error && (
          <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-200">{error}</div>
        )}

        <div className="flex flex-wrap gap-2">
          {['courses', 'students', 'code', 'quiz', 'calls'].map((id) => (
            <button key={id} type="button" onClick={() => setTab(id)}
              className={`h-10 px-4 rounded-xl text-sm font-semibold transition-colors ${
                tab === id ? 'grad-bg text-white shadow-soft' : 'bg-white ring-1 ring-black/[0.06] text-ink/70'
              }`}>
              {id === 'courses' && 'Курсы'}
              {id === 'students' && 'Ученики'}
              {id === 'code' && 'Код'}
              {id === 'quiz' && 'Тесты'}
              {id === 'calls' && 'Созвоны'}
            </button>
          ))}
          <button type="button" onClick={() => navigate(Routes.CONFERENCES)}
            className="h-10 px-4 rounded-xl text-sm font-semibold bg-white ring-1 ring-black/[0.06] text-violet-600 ml-auto">
            История созвонов →
          </button>
        </div>

        <div className="flex flex-wrap gap-3 items-center">
          <label className="text-sm text-ink/55">Курс:</label>
          <select value={selectedCourse || ''} onChange={(e) => { setSelectedCourse(e.target.value); setSelectedStudent(null); }}
            className="h-10 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm min-w-[220px]">
            {courses.map((c) => (
              <option key={c.course_public_id} value={c.course_public_id}>{c.course_title}</option>
            ))}
          </select>
          {selectedCourse && (
            <MentorLink onClick={() => navigate(Routes.COURSE, { id: selectedCourse })}>
              <I.Book className="w-3.5 h-3.5"/> Страница курса
            </MentorLink>
          )}
          {selectedStudent && (
            <button type="button" onClick={() => setSelectedStudent(null)}
              className="text-xs text-violet-600 underline">
              Сбросить фильтр ученика
            </button>
          )}
        </div>

        {loading ? (
          <div className="py-16 text-center text-ink/50 text-sm">Загрузка…</div>
        ) : tab === 'courses' ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((c) => (
              <div key={c.course_public_id}
                className="text-left bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5">
                <div className="font-bold text-lg">{c.course_title}</div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-ink/45">Учеников</span><div className="font-semibold">{c.students_count}</div></div>
                  <div><span className="text-ink/45">Средний %</span><div className="font-semibold">{c.avg_percent}%</div></div>
                  <div><span className="text-ink/45">В процессе</span><div className="font-semibold">{c.active_count}</div></div>
                  <div><span className="text-ink/45">Завершили</span><div className="font-semibold">{c.completed_count}</div></div>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <MentorLink onClick={() => { setSelectedCourse(c.course_public_id); setTab('students'); }}>
                    Ученики →
                  </MentorLink>
                  <MentorLink onClick={() => navigate(Routes.COURSE, { id: c.course_public_id })}>
                    Курс →
                  </MentorLink>
                </div>
              </div>
            ))}
          </div>
        ) : tab === 'calls' ? (
          <div className="space-y-4">
            <p className="text-sm text-ink/55">
              Пригласите любого пользователя на видеозвонок или откройте полную историю.
            </p>
            <button type="button" onClick={() => navigate(Routes.CONFERENCES)}
              className="h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
              Новый созвон / история
            </button>
          </div>
        ) : tab === 'students' ? (
          <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink/45 border-b border-black/[0.06]">
                  <th className="p-4 font-semibold">Ученик</th>
                  <th className="p-4 font-semibold">Email</th>
                  <th className="p-4 font-semibold">Прогресс</th>
                  <th className="p-4 font-semibold">Статус</th>
                  <th className="p-4 font-semibold">Действия</th>
                </tr>
              </thead>
              <tbody>
                {students.length === 0 ? (
                  <tr><td colSpan={5} className="p-8 text-center text-ink/45">Пока никто не записался</td></tr>
                ) : students.map((s) => (
                  <tr key={s.user_public_id} className="border-b border-black/[0.04] hover:bg-black/[0.015]">
                    <td className="p-4">
                      <MentorLink onClick={() => openProfile(s.user_public_id)} className="text-sm font-medium">
                        {studentName(s)}
                      </MentorLink>
                    </td>
                    <td className="p-4 text-ink/60">{s.email || s.phone || '—'}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-black/[0.06] rounded-full overflow-hidden">
                          <div className="h-full grad-bg" style={{ width: `${s.percent}%` }}/>
                        </div>
                        <span>{s.percent}%</span>
                      </div>
                      <div className="text-xs text-ink/45 mt-1">{s.completed_steps}/{s.total_steps} шагов</div>
                    </td>
                    <td className="p-4">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                        s.enrollment_status === 'completed' ? 'bg-emerald-500/12 text-emerald-700' : 'bg-violet-500/10 text-violet-600'
                      }`}>
                        {s.enrollment_status === 'completed' ? 'Завершён' : 'В процессе'}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-x-3 gap-y-1">
                        <MentorLink onClick={() => openProfile(s.user_public_id)}>Профиль</MentorLink>
                        <MentorLink onClick={() => window.openChatWithUser(navigate, s.user_public_id)}>Написать</MentorLink>
                        <MentorLink onClick={() => startCallWith(s.user_public_id)}>Созвон</MentorLink>
                        <MentorLink onClick={() => { setSelectedStudent(s.user_public_id); setTab('code'); }}>Код</MentorLink>
                        <MentorLink onClick={() => { setSelectedStudent(s.user_public_id); setTab('quiz'); }}>Тесты</MentorLink>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : tab === 'code' ? (
          <div className="space-y-3">
            {courseMeta && (
              <div className="text-sm text-ink/55">{courseMeta.course_title} · отправок: {filteredCode.length}</div>
            )}
            {filteredCode.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-2xl text-ink/45 text-sm">Нет отправок кода</div>
            ) : filteredCode.map((row) => (
              <div key={row.public_id} className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <MentorLink
                      className="text-base font-semibold"
                      onClick={() => openLearn(row.course_public_id, row.module_public_id, 'coding', row.challenge_public_id)}>
                      {row.challenge_title}
                    </MentorLink>
                    <div className="text-xs text-ink/50 mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                      <MentorLink onClick={() => openProfile(row.student?.public_id)}>
                        {studentName(row)}
                      </MentorLink>
                      {row.student?.email ? <span>· {row.student.email}</span> : null}
                    </div>
                  </div>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                    row.status === 'completed' ? 'bg-emerald-500/12 text-emerald-700' : 'bg-amber-500/12 text-amber-700'
                  }`}>
                    {row.status} · {row.tests_passed}/{row.total_tests}
                  </span>
                </div>
                <pre className="mt-4 p-4 rounded-xl bg-[#0f172a] text-slate-100 text-xs font-mono overflow-x-auto whitespace-pre-wrap">{row.code}</pre>
                <SubmissionFeedback testResults={row.test_results}/>
                {row.error_message && (
                  <p className="mt-2 text-xs text-red-600">{row.error_message}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-3 items-center">
                  <MentorLink onClick={() => openLearn(row.course_public_id, row.module_public_id, 'coding', row.challenge_public_id)}>
                    <I.Play className="w-3.5 h-3.5"/> Открыть задание
                  </MentorLink>
                  <MentorLink onClick={() => openAllTests(row.challenge_public_id)}>
                    <I.Code className="w-3.5 h-3.5"/> Все тесты
                  </MentorLink>
                  <MentorLink onClick={() => openProfile(row.student?.public_id)}>Профиль ученика</MentorLink>
                  <span className="text-[11px] text-ink/40 ml-auto">
                    {new Date(row.submitted_at).toLocaleString('ru-RU')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredQuiz.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-2xl text-ink/45 text-sm">Нет ответов на тесты</div>
            ) : filteredQuiz.map((row) => (
              <div key={`${row.kind}-${row.public_id}`} className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <MentorLink
                    className="text-base font-semibold"
                    onClick={() => openLearn(row.course_public_id, row.module_public_id, row.kind, row.question_public_id)}>
                    {row.question_title}
                  </MentorLink>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                    row.is_correct ? 'bg-emerald-500/12 text-emerald-700' : 'bg-red-500/12 text-red-700'
                  }`}>
                    {row.is_correct ? 'Верно' : 'Ошибка'}
                  </span>
                </div>
                <div className="text-xs text-ink/50 mt-1 flex flex-wrap items-center gap-x-2">
                  <MentorLink onClick={() => openProfile(row.student?.public_id)}>
                    {studentName(row)}
                  </MentorLink>
                  {row.student?.email ? <span>· {row.student.email}</span> : null}
                  {row.course_title ? <span>· {row.course_title}</span> : null}
                </div>
                <div className="mt-3 text-sm text-ink/75">
                  {row.kind === 'radio' ? (
                    <span>Ответ: <strong>{row.selected_answer}</strong></span>
                  ) : (
                    <span>Ответы: {(row.selected_answers || []).join(', ') || '—'}</span>
                  )}
                </div>
                <div className="mt-3 flex flex-wrap gap-3 items-center">
                  <MentorLink onClick={() => openLearn(row.course_public_id, row.module_public_id, row.kind, row.question_public_id)}>
                    <I.Play className="w-3.5 h-3.5"/> Открыть задание
                  </MentorLink>
                  <MentorLink onClick={() => openProfile(row.student?.public_id)}>Профиль ученика</MentorLink>
                  <span className="text-[11px] text-ink/40 ml-auto">
                    {new Date(row.created_at).toLocaleString('ru-RU')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

window.MentorPage = MentorPage;
