// Занятия с ментором: кабинет ученика и панель ментора.

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const LESSON_STATUS = {
  booked: 'Записан',
  done: 'Проведён',
  missed: 'Не пришёл',
  cancelled: 'Отменён',
};

function rub(kop) {
  const value = Number(kop || 0) / 100;
  return value.toLocaleString('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  });
}

function moneyLine(kop) {
  const amount = Number(kop || 0);
  if (amount < 0) return `Долг ${rub(-amount)}`;
  if (amount > 0) return `Переплата ${rub(amount)}`;
  return 'Долга нет';
}

function whenLabel(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (_) {
    return String(iso);
  }
}

function localDay(offset) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

function tutoringFetch(path, opts = {}) {
  const tg = window.Telegram && window.Telegram.WebApp;
  const initData = tg && tg.initData;
  if (initData && !window.getAccessToken()) {
    try {
      tg.ready();
      tg.expand();
    } catch (_) { /* вне Telegram */ }
    return window.fetchApiJson(path, {
      ...opts,
      auth: false,
      headers: { ...(opts.headers || {}), Authorization: `tma ${initData}` },
    });
  }
  return window.fetchApiJson(path, { ...opts, auth: true });
}

function LessonsPage({ navigate }) {
  const [me, setMe] = React.useState(null);
  const [lessons, setLessons] = React.useState([]);
  const [day, setDay] = React.useState(() => localDay(1));
  const [duration, setDuration] = React.useState(null);
  const [slots, setSlots] = React.useState([]);
  const [movingId, setMovingId] = React.useState(null);
  const [payRub, setPayRub] = React.useState('');
  const [pendingPay, setPendingPay] = React.useState([]);
  const [error, setError] = React.useState('');
  const [hint, setHint] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const signedIn = !!window.getAccessToken() || !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);

  const reload = React.useCallback(async () => {
    const profile = await tutoringFetch('/api/tutoring/me/');
    setMe(profile);
    const data = await tutoringFetch('/api/tutoring/lessons/');
    setLessons(data.results || []);
    const claims = await tutoringFetch('/api/tutoring/payment-claims/');
    setPendingPay(claims.pending || []);
    const first = (profile.tariffs || [])[0];
    setDuration((current) => current || (first ? first.duration_minutes : null));
    return profile;
  }, []);

  React.useEffect(() => {
    if (!signedIn) {
      setLoading(false);
      return undefined;
    }
    let cancel = false;
    (async () => {
      try {
        await reload();
        if (!cancel) setError('');
      } catch (err) {
        if (!cancel) setError(err.message || 'Не удалось загрузить занятия');
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [signedIn, reload]);

  React.useEffect(() => {
    if (!me?.can_book || !duration || !day) {
      setSlots([]);
      return undefined;
    }
    let cancel = false;
    tutoringFetch(`/api/tutoring/slots/?date=${day}&duration=${duration}`)
      .then((data) => { if (!cancel) setSlots(data.slots || []); })
      .catch((err) => { if (!cancel) setError(err.message || 'Нет свободного времени'); });
    return () => { cancel = true; };
  }, [me, day, duration]);

  const bookOrMove = async (startsAt) => {
    setBusy(true);
    setError('');
    setHint('');
    try {
      if (movingId) {
        await tutoringFetch(`/api/tutoring/lessons/${movingId}/move/`, {
          method: 'POST',
          body: { starts_at: startsAt },
        });
        setMovingId(null);
        setHint('Занятие перенесено.');
      } else {
        await tutoringFetch('/api/tutoring/lessons/', {
          method: 'POST',
          body: { starts_at: startsAt, duration_minutes: duration },
        });
        setHint('Вы записаны.');
      }
      await reload();
    } catch (err) {
      setError(err.message || 'Не получилось записать');
    } finally {
      setBusy(false);
    }
  };

  const cancelLesson = async (id) => {
    setBusy(true);
    setError('');
    try {
      await tutoringFetch(`/api/tutoring/lessons/${id}/cancel/`, { method: 'POST' });
      setHint('Занятие отменено.');
      await reload();
    } catch (err) {
      setError(err.message || 'Не получилось отменить');
    } finally {
      setBusy(false);
    }
  };

  const linkTelegram = async () => {
    setBusy(true);
    setError('');
    try {
      const data = await window.fetchApiJson('/api/telegram/link/', { method: 'POST', auth: true });
      if (data.start_url) {
        window.open(data.start_url, '_blank', 'noopener');
        setHint('В Telegram нажмите Start, затем обновите эту страницу.');
        return;
      }
      setError('Бот ещё не настроен. Напишите администратору.');
    } catch (err) {
      setError(err.message || 'Не удалось открыть бота');
    } finally {
      setBusy(false);
    }
  };

  const sendPayment = async (event) => {
    event.preventDefault();
    const amount = Math.round(Number(String(payRub).replace(',', '.')) * 100);
    if (!amount || amount < 100) {
      setError('Укажите сумму в рублях.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await tutoringFetch('/api/tutoring/payment-claims/', {
        method: 'POST',
        body: { amount_kop: amount },
      });
      setPayRub('');
      setHint('Отметили оплату. Ментор подтвердит её в кабинете.');
      await reload();
    } catch (err) {
      setError(err.message || 'Не удалось отправить оплату');
    } finally {
      setBusy(false);
    }
  };

  if (!signedIn) {
    return (
      <section className="max-w-3xl mx-auto px-5 py-16">
        <h1 className="text-3xl font-extrabold">Занятия</h1>
        <p className="mt-3 text-ink/70">Войдите в кабинет, чтобы увидеть свои занятия.</p>
        <button type="button" onClick={() => navigate(window.Routes.AUTH)} className="mt-6 h-11 px-5 rounded-xl btn-grad text-white font-semibold">
          Войти
        </button>
      </section>
    );
  }

  const upcoming = lessons.filter((item) => item.status === 'booked' && new Date(item.starts_at) >= new Date());
  const history = lessons.filter((item) => !(item.status === 'booked' && new Date(item.starts_at) >= new Date()));

  return (
    <section className="max-w-3xl mx-auto px-5 py-10 space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Занятия</h1>
        <p className="mt-2 text-sm text-ink/60">
          Запись к своему ментору. Подписка с ответами и нейронкой сюда не входит.
        </p>
      </div>
      {error && <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-200">{error}</div>}
      {hint && <div className="p-4 rounded-xl bg-emerald-50 text-emerald-800 text-sm ring-1 ring-emerald-200">{hint}</div>}
      {loading || !me ? (
        <p className="text-sm text-ink/50">Загрузка…</p>
      ) : me.reason === 'no_access' ? (
        <div className="p-5 rounded-2xl bg-white ring-1 ring-black/[0.06]">
          <p className="font-semibold">Занятия с ментором вам не открыты.</p>
          <p className="mt-2 text-sm text-ink/65">Курс можно решать как раньше. Запись появляется, когда администратор выдаёт доступ.</p>
        </div>
      ) : me.reason === 'no_mentor' ? (
        <div className="p-5 rounded-2xl bg-white ring-1 ring-black/[0.06]">
          <p className="font-semibold">Ментор ещё не назначен.</p>
          <p className="mt-2 text-sm text-ink/65">Когда администратор укажет ментора, здесь появится свободное время.</p>
        </div>
      ) : (
        <>
          {!me.telegram_linked && window.getAccessToken() && (
            <div className="p-4 rounded-2xl bg-amber-50 ring-1 ring-amber-200 text-sm">
              <p>Привяжите Telegram, чтобы приходило напоминание за сутки и за час.</p>
              <button type="button" disabled={busy} onClick={linkTelegram} className="mt-3 h-10 px-4 rounded-xl bg-ink text-white text-sm font-semibold">
                Привязать Telegram
              </button>
            </div>
          )}
          <div className="p-5 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-2">
            <p className="text-sm text-ink/55">Ментор</p>
            <p className="font-semibold">{me.mentor?.name || '—'}</p>
            <p className="text-sm">{moneyLine(me.balance_kop)}</p>
            <form onSubmit={sendPayment} className="flex flex-wrap gap-2 pt-2">
              <input
                value={payRub}
                onChange={(event) => setPayRub(event.target.value)}
                inputMode="decimal"
                placeholder="Сумма, ₽"
                className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] text-sm w-36"
              />
              <button type="submit" disabled={busy} className="h-11 px-4 rounded-xl btn-grad text-white text-sm font-semibold">
                Я оплатил
              </button>
            </form>
            {pendingPay.length > 0 && (
              <p className="text-sm text-ink/60">Ждёт подтверждения: {pendingPay.map((item) => rub(item.amount_kop)).join(', ')}</p>
            )}
          </div>
          <div className="p-5 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-4">
            <div className="flex flex-wrap gap-3 items-end">
              <label className="text-sm">
                <span className="block text-ink/55 mb-1">День</span>
                <input type="date" value={day} onChange={(event) => setDay(event.target.value)} className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08]" />
              </label>
              <label className="text-sm">
                <span className="block text-ink/55 mb-1">Длительность</span>
                <select value={duration || ''} onChange={(event) => setDuration(Number(event.target.value))} className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] bg-white">
                  {(me.tariffs || []).map((tariff) => (
                    <option key={tariff.duration_minutes} value={tariff.duration_minutes}>
                      {tariff.duration_minutes} мин · {rub(tariff.price_kop)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {movingId && <p className="text-sm text-violet-700">Выберите новое время. Текущее занятие отменится только после успешного переноса.</p>}
            {(me.tariffs || []).length === 0 ? (
              <p className="text-sm text-ink/55">Ментор ещё не указал цены. Запись откроется после этого.</p>
            ) : slots.length === 0 ? (
              <p className="text-sm text-ink/55">На этот день свободного времени нет.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {slots.map((slot) => (
                  <button key={slot} type="button" disabled={busy} onClick={() => bookOrMove(slot)} className="h-10 px-3 rounded-xl bg-ink/[0.04] hover:bg-violet-500/10 text-sm font-semibold">
                    {whenLabel(slot)}
                  </button>
                ))}
              </div>
            )}
          </div>
          <LessonList title="Ближайшие" items={upcoming} busy={busy} onCancel={cancelLesson} onMove={setMovingId} movingId={movingId} />
          <LessonList title="Прошедшие" items={history} />
        </>
      )}
    </section>
  );
}

function LessonList({ title, items, busy, onCancel, onMove, movingId }) {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-bold">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-ink/45">Пока пусто.</p>
      ) : items.map((item) => (
        <article key={item.public_id} className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06]">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="font-semibold">{whenLabel(item.starts_at)}</p>
            <p className="text-sm text-ink/55">{LESSON_STATUS[item.status] || item.status} · {rub(item.price_kop)}</p>
          </div>
          <p className="text-sm text-ink/60 mt-1">{item.duration_minutes} мин · {item.mentor?.name}</p>
          {item.homework_status === 'done' && <p className="text-sm text-emerald-700 mt-2">Домашка сдана</p>}
          {item.homework_status === 'not_done' && <p className="text-sm text-amber-700 mt-2">Домашка не сдана</p>}
          {item.learned_note && <p className="text-sm text-ink/70 mt-1">Чему научился: {item.learned_note}</p>}
          {item.status === 'booked' && onCancel && (
            <div className="mt-3 flex gap-2">
              <button type="button" disabled={busy} onClick={() => onMove(movingId === item.public_id ? null : item.public_id)} className="h-9 px-3 rounded-lg text-sm font-semibold ring-1 ring-black/[0.08]">
                {movingId === item.public_id ? 'Отмена переноса' : 'Перенести'}
              </button>
              <button type="button" disabled={busy} onClick={() => onCancel(item.public_id)} className="h-9 px-3 rounded-lg text-sm font-semibold text-rose-600 bg-rose-50">
                Отменить
              </button>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function MentorLessonsPanel({ isAdmin, mentors }) {
  const [section, setSection] = React.useState('calendar');
  const [windows, setWindows] = React.useState(() => WEEKDAYS.map(() => ({ on: false, start: '16:00', end: '20:00' })));
  const [timezoneName, setTimezoneName] = React.useState('Europe/Moscow');
  const [tariffs, setTariffs] = React.useState([{ duration_minutes: 60, rub: '2000' }]);
  const [lessons, setLessons] = React.useState([]);
  const [money, setMoney] = React.useState({ pending: [], debtors: [] });
  const [stats, setStats] = React.useState(null);
  const [email, setEmail] = React.useState('');
  const [mentorId, setMentorId] = React.useState('');
  const [error, setError] = React.useState('');
  const [hint, setHint] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [journal, setJournal] = React.useState({});

  const load = React.useCallback(async () => {
    const [availability, price, rows, claims, month] = await Promise.all([
      window.fetchApiJson('/api/tutoring/availability/', { auth: true }),
      window.fetchApiJson('/api/tutoring/tariffs/', { auth: true }),
      window.fetchApiJson('/api/tutoring/lessons/', { auth: true }),
      window.fetchApiJson('/api/tutoring/payment-claims/', { auth: true }),
      window.fetchApiJson('/api/tutoring/stats/', { auth: true }),
    ]);
    setTimezoneName(availability.timezone || 'Europe/Moscow');
    setWindows(WEEKDAYS.map((_, index) => {
      const found = (availability.windows || []).find((item) => item.weekday === index);
      return found
        ? { on: true, start: found.start, end: found.end }
        : { on: false, start: '16:00', end: '20:00' };
    }));
    const nextTariffs = (price.tariffs || []).map((item) => ({
      duration_minutes: item.duration_minutes,
      rub: String(item.price_kop / 100),
    }));
    setTariffs(nextTariffs.length ? nextTariffs : [{ duration_minutes: 60, rub: '2000' }]);
    const loaded = rows.results || [];
    setLessons(loaded);
    setJournal(Object.fromEntries(loaded.map((item) => [item.public_id, {
      homework_status: item.homework_status || '',
      learned_note: item.learned_note || '',
    }])));
    setMoney(claims || { pending: [], debtors: [] });
    setStats(month);
  }, []);

  React.useEffect(() => {
    let cancel = false;
    load().catch((err) => { if (!cancel) setError(err.message || 'Не удалось загрузить занятия'); });
    return () => { cancel = true; };
  }, [load]);

  const saveWindows = async () => {
    setBusy(true);
    setError('');
    try {
      await window.fetchApiJson('/api/tutoring/availability/', {
        method: 'PUT',
        auth: true,
        body: {
          timezone: timezoneName,
          windows: windows.flatMap((item, weekday) => (
            item.on ? [{ weekday, start: item.start, end: item.end }] : []
          )),
        },
      });
      setHint('Расписание сохранено.');
    } catch (err) {
      setError(err.message || 'Не удалось сохранить окна');
    } finally {
      setBusy(false);
    }
  };

  const saveTariffs = async () => {
    setBusy(true);
    setError('');
    try {
      await window.fetchApiJson('/api/tutoring/tariffs/', {
        method: 'PUT',
        auth: true,
        body: {
          tariffs: tariffs.map((item) => ({
            duration_minutes: Number(item.duration_minutes),
            price_kop: Math.round(Number(String(item.rub).replace(',', '.')) * 100),
          })),
        },
      });
      setHint('Цены сохранены.');
    } catch (err) {
      setError(err.message || 'Не удалось сохранить цены');
    } finally {
      setBusy(false);
    }
  };

  const act = async (path) => {
    setBusy(true);
    setError('');
    try {
      await window.fetchApiJson(path, { method: 'POST', auth: true });
      await load();
    } catch (err) {
      setError(err.message || 'Не получилось');
    } finally {
      setBusy(false);
    }
  };

  const saveJournal = async (publicId) => {
    const draft = journal[publicId] || { homework_status: '', learned_note: '' };
    setBusy(true);
    setError('');
    try {
      await window.fetchApiJson(`/api/tutoring/lessons/${publicId}/notes/`, {
        method: 'POST',
        auth: true,
        body: {
          homework_status: draft.homework_status,
          learned_note: draft.learned_note,
        },
      });
      setHint('Заметка сохранена.');
      await load();
    } catch (err) {
      setError(err.message || 'Не удалось сохранить заметку');
    } finally {
      setBusy(false);
    }
  };

  const grant = async (event) => {
    event.preventDefault();
    if (!email.trim() || !mentorId) {
      setError('Укажите почту ученика и ментора.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await window.fetchApiJson('/api/tutoring/access/', {
        method: 'POST',
        auth: true,
        body: {
          email: email.trim(),
          enabled: true,
          mentor_public_id: mentorId || null,
        },
      });
      setHint('Доступ к занятиям включён.');
      setEmail('');
    } catch (err) {
      setError(err.message || 'Не удалось выдать доступ');
    } finally {
      setBusy(false);
    }
  };

  const tabs = [
    ['calendar', 'Окна'],
    ['prices', 'Цены'],
    ['list', 'Записи'],
    ['study', 'Домашка'],
    ['money', 'Оплаты'],
    ['stats', 'Статистика'],
  ];

  return (
    <div className="space-y-4">
      {error && <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-200">{error}</div>}
      {hint && <div className="p-4 rounded-xl bg-emerald-50 text-emerald-800 text-sm ring-1 ring-emerald-200">{hint}</div>}
      {isAdmin && (
        <form onSubmit={grant} className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-3">
          <p className="font-semibold">Выдать занятия ученику с Авито</p>
          <p className="text-sm text-ink/60">Подписка при этом не включается. Ученик платит за каждое занятие.</p>
          <div className="flex flex-wrap gap-2">
            <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Почта ученика" className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] text-sm min-w-[220px]" />
            <select value={mentorId} onChange={(event) => setMentorId(event.target.value)} className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] bg-white text-sm">
              <option value="">Ментор</option>
              {(mentors || []).map((mentor) => (
                <option key={mentor.public_id} value={mentor.public_id}>
                  {(mentor.first_name || '') + ' ' + (mentor.last_name || '')} {mentor.email ? `(${mentor.email})` : ''}
                </option>
              ))}
            </select>
            <button type="submit" disabled={busy} className="h-11 px-4 rounded-xl btn-grad text-white text-sm font-semibold">Включить</button>
          </div>
        </form>
      )}
      <div className="flex flex-wrap gap-2">
        {tabs.map(([id, label]) => (
          <button key={id} type="button" onClick={() => setSection(id)} className={`h-10 px-4 rounded-xl text-sm font-semibold ${section === id ? 'bg-ink text-white' : 'bg-white ring-1 ring-black/[0.06]'}`}>
            {label}
          </button>
        ))}
      </div>
      {section === 'calendar' && (
        <div className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-3">
          <label className="text-sm block">
            <span className="text-ink/55">Часовой пояс</span>
            <input value={timezoneName} onChange={(event) => setTimezoneName(event.target.value)} className="mt-1 h-11 px-3 rounded-xl ring-1 ring-black/[0.08] block w-full max-w-xs" />
          </label>
          {windows.map((item, index) => (
            <div key={WEEKDAYS[index]} className="flex flex-wrap items-center gap-2 text-sm">
              <label className="w-16 font-semibold">
                <input type="checkbox" className="mr-2" checked={item.on} onChange={(event) => {
                  const next = windows.slice();
                  next[index] = { ...item, on: event.target.checked };
                  setWindows(next);
                }} />
                {WEEKDAYS[index]}
              </label>
              <input type="time" value={item.start} disabled={!item.on} onChange={(event) => {
                const next = windows.slice();
                next[index] = { ...item, start: event.target.value };
                setWindows(next);
              }} className="h-10 px-2 rounded-lg ring-1 ring-black/[0.08]" />
              <span>—</span>
              <input type="time" value={item.end} disabled={!item.on} onChange={(event) => {
                const next = windows.slice();
                next[index] = { ...item, end: event.target.value };
                setWindows(next);
              }} className="h-10 px-2 rounded-lg ring-1 ring-black/[0.08]" />
            </div>
          ))}
          <button type="button" disabled={busy} onClick={saveWindows} className="h-11 px-4 rounded-xl btn-grad text-white text-sm font-semibold">Сохранить окна</button>
        </div>
      )}
      {section === 'prices' && (
        <div className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-3">
          {tariffs.map((item, index) => (
            <div key={index} className="flex flex-wrap gap-2">
              <input type="number" min="15" value={item.duration_minutes} onChange={(event) => {
                const next = tariffs.slice();
                next[index] = { ...item, duration_minutes: event.target.value };
                setTariffs(next);
              }} className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] w-28" />
              <input value={item.rub} onChange={(event) => {
                const next = tariffs.slice();
                next[index] = { ...item, rub: event.target.value };
                setTariffs(next);
              }} placeholder="Цена, ₽" className="h-11 px-3 rounded-xl ring-1 ring-black/[0.08] w-32" />
            </div>
          ))}
          <div className="flex gap-2">
            <button type="button" onClick={() => setTariffs(tariffs.concat([{ duration_minutes: 90, rub: '' }]))} className="h-10 px-3 rounded-xl ring-1 ring-black/[0.08] text-sm font-semibold">Ещё цена</button>
            <button type="button" disabled={busy} onClick={saveTariffs} className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold">Сохранить цены</button>
          </div>
        </div>
      )}
      {section === 'list' && (
        <div className="space-y-2">
          {lessons.length === 0 && <p className="text-sm text-ink/50">Записей нет.</p>}
          {lessons.map((item) => (
            <article key={item.public_id} className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06]">
              <p className="font-semibold">{whenLabel(item.starts_at)} · {item.student?.name}</p>
              <p className="text-sm text-ink/55">{LESSON_STATUS[item.status]} · {item.duration_minutes} мин · {rub(item.price_kop)}</p>
              {item.status === 'booked' && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button type="button" disabled={busy} onClick={() => act(`/api/tutoring/lessons/${item.public_id}/done/`)} className="h-9 px-3 rounded-lg text-sm font-semibold bg-emerald-50 text-emerald-800">Проведён</button>
                  <button type="button" disabled={busy} onClick={() => act(`/api/tutoring/lessons/${item.public_id}/missed/`)} className="h-9 px-3 rounded-lg text-sm font-semibold bg-amber-50 text-amber-800">Не пришёл</button>
                  <button type="button" disabled={busy} onClick={() => act(`/api/tutoring/lessons/${item.public_id}/cancel/`)} className="h-9 px-3 rounded-lg text-sm font-semibold text-rose-600 bg-rose-50">Отменить</button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {section === 'study' && (
        <div className="space-y-3">
          <p className="text-sm text-ink/60">После занятия отметьте, сдал ли ученик домашку, и коротко запишите, чему научился.</p>
          {lessons.filter((item) => item.status === 'done' && item.homework_status !== 'done').length > 0 && (
            <div className="p-4 rounded-2xl bg-amber-50 ring-1 ring-amber-200 text-sm">
              <p className="font-semibold mb-1">Ещё не отметили «сдал»</p>
              {lessons.filter((item) => item.status === 'done' && item.homework_status !== 'done').map((item) => (
                <p key={item.public_id}>{item.student?.name} · {whenLabel(item.starts_at)}</p>
              ))}
            </div>
          )}
          {lessons.filter((item) => item.status !== 'cancelled').length === 0 && <p className="text-sm text-ink/50">Занятий пока нет.</p>}
          {lessons.filter((item) => item.status !== 'cancelled').map((item) => {
            const draft = journal[item.public_id] || { homework_status: '', learned_note: '' };
            return (
              <article key={item.public_id} className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06] space-y-3">
                <p className="font-semibold">{item.student?.name} · {whenLabel(item.starts_at)}</p>
                <p className="text-sm text-ink/55">{LESSON_STATUS[item.status]}</p>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => setJournal({ ...journal, [item.public_id]: { ...draft, homework_status: 'done' } })} className={`h-9 px-3 rounded-lg text-sm font-semibold ${draft.homework_status === 'done' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-800'}`}>Сдал</button>
                  <button type="button" onClick={() => setJournal({ ...journal, [item.public_id]: { ...draft, homework_status: 'not_done' } })} className={`h-9 px-3 rounded-lg text-sm font-semibold ${draft.homework_status === 'not_done' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-800'}`}>Не сдал</button>
                </div>
                <label className="block text-sm">
                  <span className="text-ink/55">Чему научился</span>
                  <textarea value={draft.learned_note} onChange={(event) => setJournal({ ...journal, [item.public_id]: { ...draft, learned_note: event.target.value } })} rows={3} maxLength={2000} className="mt-1 w-full px-3 py-2 rounded-xl ring-1 ring-black/[0.08] text-sm" placeholder="Например: циклы и условие в задаче 17" />
                </label>
                <button type="button" disabled={busy} onClick={() => saveJournal(item.public_id)} className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold">Сохранить</button>
              </article>
            );
          })}
        </div>
      )}
      {section === 'money' && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-2">Ждут решения</h3>
            {(money.pending || []).length === 0 && <p className="text-sm text-ink/50">Никто не прислал оплату.</p>}
            {(money.pending || []).map((claim) => (
              <article key={claim.public_id} className="p-4 mb-2 rounded-2xl bg-white ring-1 ring-black/[0.06]">
                <p className="font-semibold">{claim.student?.name} · {rub(claim.amount_kop)}</p>
                <div className="mt-3 flex gap-2">
                  <button type="button" disabled={busy} onClick={() => act(`/api/tutoring/payment-claims/${claim.public_id}/confirm/`)} className="h-9 px-3 rounded-lg text-sm font-semibold bg-emerald-50 text-emerald-800">Подтвердить</button>
                  <button type="button" disabled={busy} onClick={() => act(`/api/tutoring/payment-claims/${claim.public_id}/reject/`)} className="h-9 px-3 rounded-lg text-sm font-semibold text-rose-600 bg-rose-50">Отклонить</button>
                </div>
              </article>
            ))}
          </div>
          <div>
            <h3 className="font-bold mb-2">Не оплатили</h3>
            {(money.debtors || []).length === 0 && <p className="text-sm text-ink/50">Долгов нет.</p>}
            {(money.debtors || []).map((row) => (
              <p key={row.student.public_id} className="text-sm py-1">{row.student.name} · {moneyLine(row.balance_kop)}</p>
            ))}
          </div>
        </div>
      )}
      {section === 'stats' && stats && (
        <div className="grid sm:grid-cols-3 gap-3">
          <StatCard title="Начислено за месяц" value={rub(stats.charged_kop)} />
          <StatCard title="Получено оплатами" value={rub(stats.received_kop)} />
          <StatCard title="Прогноз по будущим" value={rub(stats.forecast_kop)} />
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div className="p-4 rounded-2xl bg-white ring-1 ring-black/[0.06]">
      <p className="text-xs text-ink/50">{title}</p>
      <p className="mt-1 text-xl font-extrabold">{value}</p>
    </div>
  );
}

window.LessonsPage = LessonsPage;
window.MentorLessonsPanel = MentorLessonsPanel;
