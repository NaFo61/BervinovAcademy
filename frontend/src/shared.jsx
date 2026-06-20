// Shared utilities, data, icons, layout chrome

const { motion, AnimatePresence, useScroll, useTransform, useInView, LayoutGroup } = window.Motion || window.framerMotion || {};
// framer-motion UMD exposes `Motion`
const FM = window.Motion || {};

const Routes = {
  LANDING: 'landing',
  CATALOG: 'catalog',
  COURSE: 'course',
  LEARN: 'learn',
  EXAM: 'exam',
  PROBLEM: 'problem',
  PROFILE: 'profile',
  PROFILE_EDIT: 'profile-edit',
  MENTOR: 'mentor',
  AUTH: 'auth',
  CALL: 'call',
  CONFERENCES: 'conferences',
};

function parseHashRoute() {
  const raw = location.hash.replace('#/', '') || Routes.LANDING;
  const qi = raw.indexOf('?');
  const path = (qi >= 0 ? raw.slice(0, qi) : raw) || Routes.LANDING;
  const qs = qi >= 0 ? raw.slice(qi + 1) : '';
  return { path, params: new URLSearchParams(qs) };
}

function useHashRoute() {
  const [state, setState] = React.useState(() => parseHashRoute());
  React.useEffect(() => {
    const onHash = () => setState(parseHashRoute());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const navigate = (r, query) => {
    let hash = '#/' + r;
    if (query) {
      const qs = query instanceof URLSearchParams
        ? query.toString()
        : typeof query === 'string'
          ? query.replace(/^\?/, '')
          : new URLSearchParams(query).toString();
      if (qs) hash += '?' + qs;
    }
    location.hash = hash;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return [state.path, navigate, state.params];
}

function initApiBase() {
  if (typeof window === 'undefined') return;
  if (typeof window.__API_BASE__ === 'string') return;
  const { hostname, port } = window.location;
  if ((hostname === 'localhost' || hostname === '127.0.0.1') && port === '3000') {
    window.__API_BASE__ = 'http://127.0.0.1:8000';
  } else {
    window.__API_BASE__ = '';
  }
}
initApiBase();

function getApiBase() {
  const b = typeof window !== 'undefined' && window.__API_BASE__;
  return typeof b === 'string' ? b.replace(/\/$/, '') : '';
}

const COURSE_PALETTE = [
  ['#2563EB', '#06B6D4'],
  ['#7C3AED', '#F97316'],
  ['#1D4ED8', '#0EA5E9'],
  ['#0EA5E9', '#22C55E'],
];

function coursePaletteFromId(publicId) {
  const h = String(publicId || '').split('').reduce((s, c) => s + c.charCodeAt(0), 0);
  return COURSE_PALETTE[Math.abs(h) % COURSE_PALETTE.length];
}

function mapApiCourseToCard(row) {
  const tags = (row.technology || []).map((t) => t.name || '').filter(Boolean);
  const cat = tags[0] || 'Курс';
  const [gradFrom, gradTo] = coursePaletteFromId(row.public_id);
  const img = row.image ? mediaUrl(row.image) : '';
  const title = (row.title || 'Курс').trim();
  const emoji = tags[0] ? tags[0].slice(0, 2) : title.slice(0, 2);
  const h = String(row.public_id || '').split('').reduce((s, c) => s + c.charCodeAt(0), 0);
  return {
    id: row.public_id,
    publicId: row.public_id,
    slug: row.slug,
    title: row.title,
    desc: (row.description || '').trim()
      || (tags.length ? `Технологии: ${tags.join(', ')}.` : 'Курс Академии Бервинова.'),
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

function mapApiCourseToCourse(row) {
  const tags = (row.technology || []).map((t) => t.name || '').filter(Boolean);
  const [gradFrom, gradTo] = coursePaletteFromId(row.public_id);
  const moduleCount = (row.modules || []).length;
  const description = (row.description || '').trim();
  return {
    id: row.public_id,
    slug: row.slug,
    title: row.title || 'Курс',
    desc: description || (tags.length ? `Технологии: ${tags.join(', ')}.` : 'Курс Академии Бервинова.'),
    tags: tags.length ? tags : ['Курс'],
    cat: tags[0] || 'Курс',
    level: 'Курс',
    rating: '—',
    students: 0,
    lessons: moduleCount,
    hours: moduleCount,
    price: 0,
    gradFrom,
    gradTo,
    accentEmoji: tags[0] ? tags[0].slice(0, 2) : (row.title || '').slice(0, 2),
    imageUrl: row.image ? mediaUrl(row.image) : '',
    popularity: 75,
    fromApi: true,
  };
}

const MODULE_ICONS = ['📚', '🔧', '⚡', '✅', '🚀', '🌐', '🧩', '📊'];

function mapApiModules(modules) {
  return (modules || []).map((mod, i) => {
    const theories = mod.lessons_theories || [];
    const radio = mod.lessons_radio || [];
    const checkbox = mod.lessons_checkbox || [];
    const coding = mod.lessons_coding || [];
    return {
      id: mod.public_id,
      title: mod.title,
      icon: MODULE_ICONS[i % MODULE_ICONS.length],
      lessons: theories.length,
      quizzes: radio.length + checkbox.length,
      hours: 0,
      tasks: coding.length,
      items: [],
      description: mod.description || '',
    };
  });
}

function apiPathFromNextUrl(nextUrl) {
  if (!nextUrl) return null;
  if (!/^https?:\/\//i.test(nextUrl)) {
    return nextUrl.startsWith('/') ? nextUrl : '/' + nextUrl;
  }
  const base = getApiBase();
  if (base && nextUrl.startsWith(base)) {
    const rest = nextUrl.slice(base.length);
    return rest.startsWith('/') ? rest : '/' + rest;
  }
  try {
    const u = new URL(nextUrl);
    return u.pathname + u.search;
  } catch (_) {
    return null;
  }
}

/** Загружает все страницы списка курсов (DRF pagination или один массив). */
async function fetchCoursesList() {
  const all = [];
  let path = '/api/content/courses/';
  for (;;) {
    const data = await fetchApiJson(path);
    if (Array.isArray(data)) return data;
    all.push(...(data.results || []));
    const nextPath = apiPathFromNextUrl(data.next);
    if (!nextPath) break;
    path = nextPath;
  }
  return all;
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;
  try {
    const data = await fetchApiJson('/api/auth/refresh/', {
      method: 'POST',
      body: { refresh },
      _retry: false,
    });
    if (data && data.access) {
      localStorage.setItem('access_token', data.access);
      if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
      notifyAuthChanged();
      return true;
    }
  } catch (_) {
    /* expired refresh */
  }
  return false;
}

function mediaUrl(path) {
  if (!path || typeof path !== 'string') return '';
  if (/^https?:\/\//i.test(path)) return path;
  const base = getApiBase();
  return base + (path.startsWith('/') ? path : '/' + path);
}

function formatDrfError(data, depth = 0) {
  if (depth > 8) return '…';
  if (data == null || typeof data !== 'object') return null;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length) {
    return data.non_field_errors.join(' ');
  }
  const parts = [];
  for (const [k, v] of Object.entries(data)) {
    if (k === 'detail') continue;
    if (Array.isArray(v)) {
      const flat = v.map((item) => (typeof item === 'string' ? item : JSON.stringify(item)));
      parts.push(`${k}: ${flat.join(' ')}`);
    } else if (v && typeof v === 'object') {
      const inner = formatDrfError(v, depth + 1);
      if (inner) parts.push(`${k}: ${inner}`);
    } else if (typeof v === 'string') parts.push(`${k}: ${v}`);
  }
  return parts.join('; ') || null;
}

async function fetchApiJson(path, opts = {}) {
  const {
    method = 'GET',
    body,
    auth = false,
    headers: extraHeaders = {},
    _retry = true,
  } = opts;
  const url = `${getApiBase()}${path.startsWith('/') ? path : '/' + path}`;
  const headers = { ...extraHeaders };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const t = localStorage.getItem('access_token');
    if (t) headers['Authorization'] = 'Bearer ' + t;
  }
  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'omit',
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {
    data = { _raw: text };
  }
  if (res.status === 401 && auth && _retry && !path.includes('/auth/refresh/')) {
    const renewed = await refreshAccessToken();
    if (renewed) {
      return fetchApiJson(path, { ...opts, _retry: false });
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    notifyAuthChanged();
  }
  if (!res.ok) {
    const msg = formatDrfError(data) || res.statusText || 'Ошибка запроса';
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

async function enrollInCourse(coursePublicId) {
  return fetchApiJson('/api/education/enrollments/', {
    method: 'POST',
    body: { course: coursePublicId },
    auth: true,
  });
}

async function fetchMyEnrollments() {
  if (!localStorage.getItem('access_token')) return [];
  try {
    return await fetchApiJson('/api/education/enrollments/', { auth: true });
  } catch (_) {
    return [];
  }
}

async function fetchCourseProgress(coursePublicId) {
  return fetchApiJson(
    `/api/progress/course/?course_public_id=${encodeURIComponent(coursePublicId)}`,
    { auth: true },
  );
}

function enrollmentsByCourseId(enrollments) {
  const map = {};
  for (const row of enrollments || []) {
    if (row.course_public_id) map[row.course_public_id] = row;
  }
  return map;
}

async function fetchApiForm(path, formData, opts = {}) {
  const {
    method = 'PATCH',
    auth = true,
    headers: extraHeaders = {},
    _retry = true,
  } = opts;
  const url = `${getApiBase()}${path.startsWith('/') ? path : '/' + path}`;
  const headers = { ...extraHeaders };
  if (auth) {
    const t = localStorage.getItem('access_token');
    if (t) headers['Authorization'] = 'Bearer ' + t;
  }
  const res = await fetch(url, {
    method,
    headers,
    body: formData,
    credentials: 'omit',
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {
    data = { _raw: text };
  }
  if (res.status === 401 && auth && _retry && !path.includes('/auth/refresh/')) {
    const renewed = await refreshAccessToken();
    if (renewed) {
      return fetchApiForm(path, formData, { ...opts, _retry: false });
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    notifyAuthChanged();
  }
  if (!res.ok) {
    const msg = formatDrfError(data) || res.statusText || 'Ошибка запроса';
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function parseJwtPayload(token) {
  try {
    const part = token.split('.')[1];
    const json = atob(part.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json);
  } catch (_) {
    return {};
  }
}

function buildLearnQuery(courseId, moduleId, lessonType, lessonId) {
  if (!courseId || !moduleId || !lessonType || !lessonId) return null;
  return {
    course: courseId,
    module: moduleId,
    lesson: `${lessonType}-${lessonId}`,
  };
}

function buildExamQuery(courseId, examId, stepType, stepId) {
  if (!courseId || !examId) return null;
  const q = { course: courseId, exam: examId };
  if (stepType && stepId) q.step = `${stepType}-${stepId}`;
  return q;
}

function openStudentProfile(navigate, userPublicId) {
  if (!userPublicId) return;
  navigate(Routes.PROFILE, { user: userPublicId });
}

async function createConference(guestPublicId) {
  return fetchApiJson('/api/communication/conferences/', {
    method: 'POST',
    body: { guest: guestPublicId },
    auth: true,
  });
}

function openConferenceCall(navigate, conferencePublicId) {
  if (!conferencePublicId) return;
  navigate(Routes.CALL, { conf: conferencePublicId });
}

async function fetchConferenceWhiteboard(conferencePublicId) {
  return fetchApiJson(
    `/api/communication/conferences/${encodeURIComponent(conferencePublicId)}/whiteboard/`,
    { auth: true },
  );
}

function WhiteboardPreviewModal({ conferenceId, title, onClose }) {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [board, setBoard] = React.useState(null);

  React.useEffect(() => {
    if (!conferenceId) return undefined;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await fetchConferenceWhiteboard(conferenceId);
        if (!cancelled) setBoard(data);
      } catch (e) {
        if (!cancelled) setError(e.message || 'Не удалось загрузить конспект');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [conferenceId]);

  React.useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8"
      role="dialog" aria-modal="true" aria-label="Конспект доски">
      <button type="button" aria-label="Закрыть" onClick={onClose}
        className="absolute inset-0 bg-ink/55 backdrop-blur-sm"/>
      <div className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-2xl shadow-glow ring-1 ring-black/[0.08] overflow-hidden flex flex-col">
        <div className="px-5 py-4 border-b border-black/[0.06] flex items-center justify-between gap-3">
          <div>
            <div className="font-bold text-lg">Конспект доски</div>
            {title && <div className="text-sm text-ink/55 mt-0.5">{title}</div>}
          </div>
          <button type="button" onClick={onClose}
            className="w-10 h-10 rounded-xl ring-1 ring-black/[0.08] hover:bg-black/[0.03] flex items-center justify-center">
            <I.X className="w-5 h-5"/>
          </button>
        </div>
        <div className="flex-1 min-h-0 overflow-auto bg-slate-50 p-4 sm:p-6">
          {loading && <div className="py-16 text-center text-sm text-ink/50">Загрузка…</div>}
          {!loading && error && (
            <div className="py-16 text-center text-sm text-red-600">{error}</div>
          )}
          {!loading && !error && board?.image_url && (
            <img src={board.image_url} alt="Конспект доски"
              className="w-full h-auto rounded-xl ring-1 ring-black/[0.06] bg-white"/>
          )}
        </div>
        {!loading && !error && board?.image_url && (
          <div className="px-5 py-4 border-t border-black/[0.06] flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-ink/45">
              {board.exported_at
                ? `Сохранено ${new Date(board.exported_at).toLocaleString('ru-RU')}`
                : ''}
            </div>
            <a href={board.image_url} download target="_blank" rel="noopener noreferrer"
              className="h-10 px-4 rounded-xl btn-grad text-white text-sm font-semibold inline-flex items-center">
              Скачать PNG
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

async function fetchNotifications(unreadOnly = true) {
  const qs = unreadOnly ? '?unread=1' : '';
  return fetchApiJson(`/api/communication/notifications/${qs}`, { auth: true });
}

function notifyAuthChanged() {
  window.dispatchEvent(new CustomEvent('auth-changed'));
}

function VideoExplanation({ video, title }) {
  if (!video || !video.embed_url) return null;
  const label = title || 'Видео-объяснение';
  const isFile = video.kind === 'file';
  return (
    <div className="mt-6">
      <div className="text-xs font-semibold uppercase tracking-widest text-ink/55 mb-2 flex items-center gap-2">
        <I.Play className="w-3.5 h-3.5"/>
        {label}
      </div>
      <div className="rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-black aspect-video shadow-soft">
        {isFile ? (
          <video controls className="w-full h-full bg-black" src={video.embed_url} />
        ) : (
          <iframe
            src={video.embed_url}
            className="w-full h-full border-0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            title={label}
          />
        )}
      </div>
    </div>
  );
}

// ------- Icons (line, 1.6 stroke) -------
const I = {
  Logo: ({ className = 'w-8 h-8' }) =>
  <svg viewBox="0 0 32 32" className={className} fill="none">
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="32" y2="32">
          <stop offset="0%" stopColor="#1D4ED8" />
          <stop offset="60%" stopColor="#0EA5E9" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="28" height="28" rx="9" fill="url(#lg)" />
      <path d="M10.5 9h6.2c2.4 0 4.1 1.3 4.1 3.5 0 1.6-1 2.7-2.4 3.1 1.7.3 2.9 1.5 2.9 3.4 0 2.4-1.8 3.9-4.5 3.9h-6.3V9z" fill="white" />
      <path d="M13.6 11.7v3.1h2.8c1.3 0 2-.5 2-1.6s-.7-1.5-2-1.5h-2.8zM13.6 17.2v3.5h3.1c1.4 0 2.2-.6 2.2-1.8 0-1.1-.8-1.7-2.2-1.7h-3.1z" fill="#1D4ED8" />
    </svg>,

  Search: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.6">
      <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" strokeLinecap="round" />
    </svg>,

  Bell: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.6">
      <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2H4.5L6 16z" strokeLinejoin="round" />
      <path d="M10 20a2 2 0 0 0 4 0" strokeLinecap="round" />
    </svg>,

  Mic: ({ className, off }) =>
  <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.6">
      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3z" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" strokeLinecap="round" />
      {off ? <path d="M4 4l16 16" strokeLinecap="round" /> : null}
    </svg>,

  Video: ({ className, off }) =>
  <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="6" width="13" height="12" rx="2" />
      <path d="M16 10l5-3v10l-5-3" strokeLinejoin="round" />
      {off ? <path d="M4 4l16 16" strokeLinecap="round" /> : null}
    </svg>,

  Monitor: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.6">
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8M12 16v4" strokeLinecap="round" />
    </svg>,

  Play: ({ className }) =>
  <svg viewBox="0 0 24 24" className={className}><path d="M8 5v14l11-7z" fill="currentColor" /></svg>,

  Check: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="m5 12 5 5L20 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  X: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    </svg>,

  Star: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="m12 2 3 6.9 7.5.7-5.7 5 1.7 7.4L12 18l-6.5 4 1.7-7.4L1.5 9.6 9 8.9z" />
    </svg>,

  Users: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.4 3.3-5.5 6.5-5.5s5.9 2.1 6.5 5.5" />
      <circle cx="17" cy="7" r="2.8" /><path d="M16 14.5c2.8.3 4.8 2.3 5.3 5.5" />
    </svg>,

  Maximize: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M21 16v5h-5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 9 3.8 3.8M15 9l5.2-5.2M9 15l-5.2 5.2M15 15l5.2 5.2" strokeLinecap="round" />
    </svg>,

  Book: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5z" /><path d="M4 19a2 2 0 0 1 2-2h13" />
    </svg>,

  Flame: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M13 2s4 4 4 8a4 4 0 1 1-8 0c0-1 .3-2 .8-2.8C9 8.6 8 10.8 8 13a5 5 0 0 0 10 0c0-5-5-11-5-11z" />
    </svg>,

  Bolt: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" />
    </svg>,

  Chat: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 21l1.8-4.9A8.5 8.5 0 1 1 21 11.5z" />
    </svg>,

  Code: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  Sparkle: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 2l1.8 5.5L19.5 9 14 11l-2 5.5L10 11l-5.5-2L10 7.5z" />
    </svg>,

  Brain: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-2 5 3 3 0 0 0 2 5v1a3 3 0 0 0 3 3h1V4H9zM15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 2 5 3 3 0 0 1-2 5v1a3 3 0 0 1-3 3h-1V4h1z" />
    </svg>,

  Heart: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M12 21s-7-4.5-9-9.5C1.5 6.5 6 3 9 5.5L12 8l3-2.5C18 3 22.5 6.5 21 11.5 19 16.5 12 21 12 21z" />
    </svg>,

  Trophy: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M6 4h12v4a6 6 0 0 1-12 0V4z" /><path d="M6 6H3v2a3 3 0 0 0 3 3M18 6h3v2a3 3 0 0 1-3 3M9 20h6M12 14v6" />
    </svg>,

  Lock: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <rect x="4.5" y="11" width="15" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>,

  Eye: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" />
    </svg>,

  Filter: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M3 5h18l-7 9v6l-4-2v-4L3 5z" />
    </svg>,

  Send: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="m4 12 16-8-6 18-3-7-7-3z" strokeLinejoin="round" />
    </svg>,

  Refresh: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M4 4v5h5M20 20v-5h-5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20.5 9A8.5 8.5 0 0 0 5.5 7.5L4 10M3.5 15A8.5 8.5 0 0 0 18.5 16.5L20 14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  Mail: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 7 9-7" />
    </svg>,

  ChevronRight: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <path d="m9 6 6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  ChevronDown: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  Plus: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path d="M12 5v14M5 12h14" strokeLinecap="round" />
    </svg>,

  Clock: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" strokeLinecap="round" />
    </svg>,

  Calendar: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 9h18M8 3v4M16 3v4" />
    </svg>,

  Layers: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="m12 2 10 6-10 6L2 8l10-6zM2 14l10 6 10-6M2 18l10 6 10-6" strokeLinejoin="round" />
    </svg>,

  GitHub: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.8 10.9.6.1.8-.2.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2 1-.3 2-.4 3-.4s2 .1 3 .4c2.3-1.5 3.3-1.2 3.3-1.2.7 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.5-2.7 5.5-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.5-1.5 7.8-5.8 7.8-10.9C23.5 5.7 18.3.5 12 .5z" />
    </svg>,

  Telegram: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M21.5 4.2 18.3 20c-.2 1.1-.9 1.4-1.8.9l-5-3.7-2.4 2.3c-.3.3-.5.5-1 .5l.4-5.1 9.2-8.3c.4-.4-.1-.6-.6-.3L6 12.4l-5-1.6c-1.1-.3-1.1-1.1.2-1.6L20.1 3c.9-.3 1.7.2 1.4 1.2z" />
    </svg>

};

// ------- Course catalog -------
const CATEGORIES = ['Все', 'Python', 'Web', 'Алгоритмы', 'ML', 'Базы данных'];

const COURSES = [
{
  id: 'python-junior', title: 'Python с нуля до Junior',
  desc: 'Базовый синтаксис, ООП, асинхронность, тестирование, чистый код. Проект — Telegram-бот в проде.',
  rating: 4.9, students: 1240, lessons: 42, hours: 86, price: 14900, level: 'Новичок', lang: 'RU',
  cat: 'Python', tags: ['Python', 'ООП', 'Async'],
  gradFrom: '#1D4ED8', gradTo: '#22D3EE', accentEmoji: 'Py', popularity: 92
},
{
  id: 'algo', title: 'Алгоритмы и структуры данных',
  desc: 'Big-O, графы, ДП, сегментные деревья — то, что реально спрашивают на собеседованиях.',
  rating: 4.8, students: 980, lessons: 35, hours: 64, price: 16900, level: 'Средний', lang: 'RU',
  cat: 'Алгоритмы', tags: ['DP', 'Графы', 'Хэши'],
  gradFrom: '#1E3A8A', gradTo: '#3B82F6', accentEmoji: '∑', popularity: 86
},
{
  id: 'web-react-fastapi', title: 'Веб-разработка: React + FastAPI',
  desc: 'Full-stack: React 18, TanStack Query, FastAPI, Postgres, Docker, деплой. Один проект — от макета до прода.',
  rating: 4.9, students: 1560, lessons: 58, hours: 124, price: 19900, level: 'Средний', lang: 'RU',
  cat: 'Web', tags: ['React', 'FastAPI', 'Docker'],
  gradFrom: '#0891B2', gradTo: '#2563EB', accentEmoji: '⌘', popularity: 98
},
{
  id: 'ml-essentials', title: 'ML без магии',
  desc: 'Numpy, pandas, sklearn, основы DL. Без воды и хайпа — только то, что работает в проде.',
  rating: 4.7, students: 620, lessons: 31, hours: 52, price: 17900, level: 'Средний', lang: 'RU',
  cat: 'ML', tags: ['sklearn', 'pandas'],
  gradFrom: '#2563EB', gradTo: '#06B6D4', accentEmoji: 'ML', popularity: 74
},
{
  id: 'postgres-pro', title: 'PostgreSQL для разработчика',
  desc: 'Индексы, EXPLAIN, оконные функции, репликация. Почему ваш JOIN медленный — и как это лечить.',
  rating: 4.8, students: 480, lessons: 24, hours: 38, price: 12900, level: 'Продвинутый', lang: 'RU',
  cat: 'Базы данных', tags: ['SQL', 'Index'],
  gradFrom: '#0E7490', gradTo: '#22D3EE', accentEmoji: 'SQL', popularity: 68
},
{
  id: 'system-design', title: 'System Design на пальцах',
  desc: 'Очереди, кэш, шардирование, eventual consistency. От лайков до распределённых счётчиков.',
  rating: 4.9, students: 740, lessons: 28, hours: 42, price: 18900, level: 'Продвинутый', lang: 'RU',
  cat: 'Web', tags: ['Архитектура', 'Очереди'],
  gradFrom: '#4F46E5', gradTo: '#0EA5E9', accentEmoji: 'SD', popularity: 81
}];


// ------- Layout chrome -------
function NotificationBell({ navigate }) {
  const [open, setOpen] = React.useState(false);
  const [items, setItems] = React.useState([]);
  const wrapRef = React.useRef(null);

  const load = React.useCallback(async () => {
    if (!localStorage.getItem('access_token')) {
      setItems([]);
      return;
    }
    try {
      const data = await fetchNotifications(true);
      setItems(Array.isArray(data) ? data : []);
    } catch (_) {
      setItems([]);
    }
  }, []);

  React.useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    const onAuth = () => load();
    window.addEventListener('auth-changed', onAuth);
    return () => {
      clearInterval(id);
      window.removeEventListener('auth-changed', onAuth);
    };
  }, [load]);

  React.useEffect(() => {
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const join = async (note) => {
    const confId = note.conference?.public_id;
    if (!confId) return;
    try {
      await fetchApiJson(
        `/api/communication/notifications/${encodeURIComponent(note.public_id)}/read/`,
        { method: 'POST', auth: true },
      );
    } catch (_) { /* ignore */ }
    setOpen(false);
    openConferenceCall(navigate, confId);
  };

  const dismiss = async (note) => {
    try {
      await fetchApiJson(
        `/api/communication/notifications/${encodeURIComponent(note.public_id)}/dismiss/`,
        { method: 'POST', auth: true },
      );
      load();
    } catch (_) { /* ignore */ }
  };

  if (!localStorage.getItem('access_token')) return null;

  return (
    <div className="relative" ref={wrapRef}>
      <button type="button" onClick={() => setOpen((v) => !v)} aria-label="Уведомления"
        className="relative w-10 h-10 rounded-xl hover:bg-black/[0.04] flex items-center justify-center text-ink/70">
        <I.Bell className="w-5 h-5" />
        {items.length > 0 && (
          <span className="absolute top-1 right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
            {items.length > 9 ? '9+' : items.length}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] bg-white rounded-2xl shadow-glow ring-1 ring-black/[0.08] z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-black/[0.06] font-semibold text-sm">Уведомления</div>
          {items.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-ink/45">Нет новых</div>
          ) : (
            <ul className="max-h-80 overflow-y-auto divide-y divide-black/[0.06]">
              {items.map((note) => (
                <li key={note.public_id} className="px-4 py-3">
                  <div className="text-sm font-medium">{note.title}</div>
                  {note.body ? <div className="text-xs text-ink/55 mt-0.5">{note.body}</div> : null}
                  {note.kind === 'conference_invite' && note.conference && (
                    <div className="mt-2 flex gap-2">
                      <button type="button" onClick={() => join(note)}
                        className="h-8 px-3 rounded-lg btn-grad text-white text-xs font-semibold">
                        Присоединиться
                      </button>
                      <button type="button" onClick={() => dismiss(note)}
                        className="h-8 px-3 rounded-lg text-xs font-semibold text-ink/55 hover:bg-black/[0.04]">
                        Отклонить
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
          <div className="px-4 py-2 border-t border-black/[0.06]">
            <button type="button" onClick={() => { setOpen(false); navigate(Routes.CONFERENCES); }}
              className="text-xs font-semibold text-violet-600 hover:underline">
              Все созвоны
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TopNav({ route, navigate }) {
  const [session, setSession] = React.useState(() => !!localStorage.getItem('access_token'));
  const [searchDraft, setSearchDraft] = React.useState('');
  const searchRef = React.useRef(null);

  React.useEffect(() => {
    const sync = () => setSession(!!localStorage.getItem('access_token'));
    window.addEventListener('auth-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('auth-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const access = session ? localStorage.getItem('access_token') : null;
  const payload = access ? parseJwtPayload(access) : {};
  const displayName = [payload.first_name, payload.last_name].filter(Boolean).join(' ').trim();
  const isMentor = payload.role === 'mentor' || payload.role === 'admin';

  const submitSearch = (e) => {
    e?.preventDefault();
    const q = searchDraft.trim();
    const params = q ? new URLSearchParams({ q }) : null;
    navigate(Routes.CATALOG, params);
    setSearchDraft('');
  };

  const handleLogout = async (e) => {
    e.preventDefault();
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      try {
        await fetchApiJson('/api/auth/logout/', { method: 'POST', body: { refresh }, auth: true });
      } catch (_) {/* ignore invalid/expired */}
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setSession(false);
    notifyAuthChanged();
    navigate(Routes.LANDING);
  };

  const links = [
    { id: Routes.LANDING, label: 'Главная' },
    { id: Routes.CATALOG, label: 'Каталог' },
    { id: Routes.PROFILE, label: 'Профиль' },
    ...(isMentor ? [{ id: Routes.MENTOR, label: 'Ментор' }] : []),
  ];

  return (
    <header className="sticky top-0 z-40">
      <div className="glass border-b border-black/5">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 h-16 flex items-center gap-6">
          <button onClick={() => navigate(Routes.LANDING)} className="flex items-center gap-2.5 group">
            <I.Logo className="w-9 h-9 drop-shadow-[0_4px_12px_rgba(37,99,235,0.4)] group-hover:scale-105 transition-transform" />
            <div className="leading-tight">
              <div className="font-bold tracking-tight text-[15px]">Bervinov<span className="grad-text">Academy</span></div>
              <div className="text-[10px] text-ink/50 uppercase tracking-widest">онлайн‑школа</div>
            </div>
          </button>
          <nav className="hidden md:flex items-center gap-1 ml-4">
            {links.map((l) => (
              <button key={l.id} onClick={() => navigate(l.id)}
                className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${route === l.id ? 'bg-violet-500/10 text-violet-600' : 'text-ink/70 hover:bg-black/[0.03] hover:text-ink'}`}>
                {l.label}
              </button>
            ))}
          </nav>
          <div className="flex-1" />
          <form onSubmit={submitSearch} className="hidden sm:flex items-center gap-2 px-3 h-10 rounded-xl border border-black/[0.06] bg-white text-sm w-56 hover:border-violet-300 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-500/15 transition-colors">
            <I.Search className="w-4 h-4 text-ink/50 shrink-0" />
            <input
              ref={searchRef}
              type="search"
              value={searchDraft}
              onChange={(e) => setSearchDraft(e.target.value)}
              placeholder="Поиск курсов…"
              className="flex-1 min-w-0 bg-transparent text-ink/80 placeholder:text-ink/40 outline-none"
              aria-label="Поиск курсов"
            />
            <kbd className="shrink-0 text-[10px] px-1.5 py-0.5 rounded border border-black/10 text-ink/40 font-mono">⌘K</kbd>
          </form>
          {session ? (
            <div className="flex items-center gap-2">
              <NotificationBell navigate={navigate} />
              {displayName ? (
                <span className="hidden sm:inline max-w-[140px] truncate text-sm text-ink/70" title={displayName}>
                  {displayName}
                </span>
              ) : null}
              <button type="button" onClick={handleLogout} className="h-10 px-4 rounded-xl text-sm font-semibold text-rose-600 ring-1 ring-rose-200 hover:bg-rose-50 transition-colors">
                Выйти
              </button>
            </div>
          ) : (
            <button onClick={() => navigate(Routes.AUTH)} className="btn-grad btn-shimmer h-10 px-5 rounded-xl text-white text-sm font-semibold shadow-soft">
              Войти
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

function Footer({ navigate }) {
  return (
    <footer className="mt-20 border-t border-black/5 bg-white">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-14 grid grid-cols-2 md:grid-cols-5 gap-10">
        <div className="col-span-2">
          <div className="flex items-center gap-2.5 mb-4">
            <I.Logo className="w-9 h-9" />
            <div>
              <div className="font-bold tracking-tight">Bervinov<span className="grad-text">Academy</span></div>
              <div className="text-[10px] text-ink/50 uppercase tracking-widest">онлайн‑школа</div>
            </div>
          </div>
          <p className="text-sm text-ink/60 max-w-sm">
            Учим программированию вживую: ментор смотрит твой код, отвечает на вопросы и помогает не сдаваться.
          </p>
          <div className="mt-5 flex items-center gap-3">
            <a className="w-10 h-10 rounded-xl bg-black/[0.04] hover:bg-violet-500/10 hover:text-violet-600 flex items-center justify-center transition-colors text-ink/60" href="#"><I.Telegram className="w-4 h-4" /></a>
            <a className="w-10 h-10 rounded-xl bg-black/[0.04] hover:bg-violet-500/10 hover:text-violet-600 flex items-center justify-center transition-colors text-ink/60" href="#"><I.GitHub className="w-4 h-4" /></a>
            <a className="w-10 h-10 rounded-xl bg-black/[0.04] hover:bg-violet-500/10 hover:text-violet-600 flex items-center justify-center transition-colors text-ink/60" href="#"><I.Mail className="w-4 h-4" /></a>
          </div>
        </div>
        <FooterCol title="Учёба" items={[
        { label: 'Каталог курсов', onClick: () => navigate(Routes.CATALOG) },
        { label: 'Мой профиль', onClick: () => navigate(Routes.PROFILE) },
        { label: 'Сертификаты', onClick: () => {} }]
        } />
        <FooterCol title="Компания" items={[
        { label: 'О школе' }, { label: 'Блог' }, { label: 'Карьера' }, { label: 'Контакты' }]
        } />
        <FooterCol title="Поддержка" items={[
        { label: 'База знаний' }, { label: 'Сообщество' }, { label: 'Стать ментором' }, { label: 'Партнёрам' }]
        } />
      </div>
      <div className="border-t border-black/5">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-ink/50">
          <div>© 2026 Bervinov Academy. Сделано с <span className="text-flame-500">♥</span> для тех, кто учится.</div>
          <div className="flex items-center gap-5">
            <a href="#">Условия</a><a href="#">Конфиденциальность</a><a href="#">Cookies</a>
          </div>
        </div>
      </div>
    </footer>);

}

function FooterCol({ title, items }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-widest text-ink/80 mb-3">{title}</div>
      <ul className="space-y-2 text-sm text-ink/60">
        {items.map((it, i) =>
        <li key={i}><button onClick={it.onClick} className="hover:text-violet-600 transition-colors text-left">{it.label}</button></li>
        )}
      </ul>
    </div>);

}

// ------- Reusable building blocks -------
function CourseCover({ course, className = '', big = false }) {
  const gridKey = String(course.id).replace(/[^a-zA-Z0-9_-]/g, '_');
  return (
    <div className={`relative overflow-hidden ${big ? 'h-44' : 'h-32'} ${className}`}
      style={{ background: `linear-gradient(135deg, ${course.gradFrom} 0%, ${course.gradTo} 100%)` }}>
      {course.imageUrl
        ? <img src={course.imageUrl} alt="" className="absolute inset-0 w-full h-full object-cover opacity-95" />
        : null}
      {/* decorative grid lines */}
      <svg className="absolute inset-0 w-full h-full opacity-25" viewBox="0 0 400 200" preserveAspectRatio="none">
        <defs>
          <pattern id={`grid-${gridKey}`} width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M32 0H0V32" stroke="white" strokeWidth="0.5" fill="none" />
          </pattern>
        </defs>
        <rect width="400" height="200" fill={`url(#grid-${gridKey})`} />
      </svg>
      {/* glow blob */}
      <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-white/25 blur-2xl" />
      <div className="absolute bottom-3 left-4 text-white">
        <div className={`font-bold ${big ? 'text-5xl' : 'text-3xl'} font-mono leading-none opacity-90`}>{course.accentEmoji}</div>
        <div className="text-[10px] uppercase tracking-widest opacity-80 mt-1">{course.cat}</div>
      </div>
    </div>);

}

function CourseCard({ course, onOpen, delay = 0, enrollment = null }) {
  const M = FM.motion;
  const progress = enrollment?.percent ?? 0;
  const enrolled = Boolean(enrollment);
  return (
    <M.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -4 }}
      className="bg-white rounded-2xl shadow-soft overflow-hidden ring-1 ring-black/[0.04] hover:shadow-glow transition-shadow cursor-pointer flex flex-col"
      onClick={onOpen}>

      <CourseCover course={course} />
      <div className="p-5 flex flex-col gap-3 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          {enrolled && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-500/12 text-emerald-700 uppercase tracking-wider">
              {enrollment.status === 'completed' ? 'Завершён' : `В процессе · ${progress}%`}
            </span>
          )}
          {course.tags.slice(0, 3).map((t) =>
          <span key={t} className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-600 uppercase tracking-wider">{t}</span>
          )}
        </div>
        <h3 className="font-semibold text-lg leading-snug">{course.title}</h3>
        <p className="text-sm text-ink/60 line-clamp-2">{course.desc}</p>
        <div className="flex items-center gap-4 text-xs text-ink/60 mt-1">
          <span className="flex items-center gap-1"><I.Star className="w-3.5 h-3.5 text-flame-500" />{course.rating}</span>
          <span className="flex items-center gap-1"><I.Users className="w-3.5 h-3.5" />{course.students.toLocaleString('ru-RU')}</span>
          <span className="flex items-center gap-1"><I.Book className="w-3.5 h-3.5" />{course.lessons} уроков</span>
        </div>
        <div className="mt-1">
          <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-ink/40 mb-1.5">
            <span>{enrolled ? 'Ваш прогресс' : 'Популярность'}</span>
            <span>{enrolled ? `${progress}%` : `${course.popularity}%`}</span>
          </div>
          <div className="h-1.5 bg-black/[0.05] rounded-full overflow-hidden">
            <M.div initial={{ width: 0 }} whileInView={{ width: `${enrolled ? progress : course.popularity}%` }}
            viewport={{ once: true }} transition={{ duration: 1, delay: delay + 0.2, ease: 'easeOut' }}
            className="h-full grad-bg rounded-full" />
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 pt-3 border-t border-black/[0.05]">
          <div className="text-[15px] font-bold">
            {course.fromApi ? <span className="text-ink/50 font-medium text-sm">Из каталога</span> : `${course.price.toLocaleString('ru-RU')} ₽`}
          </div>
          <button className="text-sm font-semibold text-violet-600 inline-flex items-center gap-1 group/btn">
            Подробнее <I.ChevronRight className="w-4 h-4 group-hover/btn:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </M.div>);

}

// Mock floating shapes for hero bg — blue/cyan family with drifting auroras
function FloatingShapes() {
  const shapes = [
  { left: '6%',  top: '15%', size: 64, hue: '#2563EB', delay: 0,   round: true },
  { left: '88%', top: '20%', size: 48, hue: '#22D3EE', delay: 1,   round: false },
  { left: '12%', top: '70%', size: 40, hue: '#0EA5E9', delay: 2,   round: true },
  { left: '82%', top: '75%', size: 80, hue: '#1D4ED8', delay: 3,   round: false },
  { left: '50%', top: '85%', size: 32, hue: '#06B6D4', delay: 1.5, round: true }];

  const auroras = [
  { left: '-8%',  top: '5%',   w: 420, h: 360, hue: 'rgba(37,99,235,0.35)',  delay: 0 },
  { left: '60%',  top: '-10%', w: 480, h: 380, hue: 'rgba(34,211,238,0.30)', delay: 6 },
  { left: '30%',  top: '60%',  w: 520, h: 420, hue: 'rgba(14,165,233,0.22)', delay: 12 }];

  return (
    <div aria-hidden className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* slow-spinning conic field */}
      <div className="aurora-conic" />
      {/* drifting aurora blobs */}
      {auroras.map((a, i) =>
        <div key={`aur-${i}`} className="aurora"
          style={{ left: a.left, top: a.top, width: a.w, height: a.h,
            background: `radial-gradient(circle at 35% 35%, ${a.hue}, transparent 65%)`,
            animationDelay: `-${a.delay}s` }} />
      )}
      {/* small floating chips */}
      {shapes.map((s, i) =>
        <div key={`shp-${i}`} className="absolute animate-float"
          style={{ left: s.left, top: s.top, width: s.size, height: s.size,
            animationDelay: `${s.delay}s`,
            background: `radial-gradient(circle at 30% 30%, ${s.hue}, transparent 70%)`,
            borderRadius: s.round ? '999px' : '24px',
            opacity: 0.40, filter: 'blur(1px)' }} />
      )}
    </div>);

}

Object.assign(window, {
  Routes,
  useHashRoute,
  getApiBase,
  apiJson: fetchApiJson,
  fetchApiJson,
  fetchApiForm,
  fetchCoursesList,
  enrollInCourse,
  fetchMyEnrollments,
  fetchCourseProgress,
  enrollmentsByCourseId,
  refreshAccessToken,
  formatDrfError,
  mediaUrl,
  parseJwtPayload,
  notifyAuthChanged,
  buildLearnQuery,
  buildExamQuery,
  openStudentProfile,
  createConference,
  openConferenceCall,
  fetchConferenceWhiteboard,
  fetchNotifications,
  WhiteboardPreviewModal,
  VideoExplanation,
  mapApiCourseToCard,
  mapApiCourseToCourse,
  mapApiModules,
  MODULE_ICONS,
  I,
  NotificationBell,
  TopNav,
  Footer,
  CourseCover,
  CourseCard,
  COURSES,
  CATEGORIES,
  FloatingShapes,
  FM,
});
