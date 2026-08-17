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
  AUTH_CALLBACK: 'auth-callback',
  CALL: 'call',
  CONFERENCES: 'conferences',
  MESSAGES: 'messages',
  PRO: 'pro',
  CERTIFICATE: 'certificate',
  PLAYGROUND: 'playground',
  WHITEBOARD: 'whiteboard',
};

const KNOWN_ROUTES = new Set(Object.values(Routes));

/** Sanitize HTML before dangerouslySetInnerHTML (DOMPurify CDN). */
function sanitizeHtml(dirty) {
  if (!dirty) return '';
  const purify = window.DOMPurify;
  if (!purify || typeof purify.sanitize !== 'function') {
    return String(dirty)
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
  return purify.sanitize(String(dirty), {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['target', 'rel'],
  });
}

function getAppBase() {
  if (typeof document === 'undefined') return '';
  const meta = document.querySelector('meta[name="app-base"]');
  const content = meta?.getAttribute('content') || '';
  return content.replace(/\/$/, '');
}

function pathForRoute(routeId) {
  const base = getAppBase();
  if (!routeId || routeId === Routes.LANDING) {
    return `${base}/` || '/';
  }
  return `${base}/${routeId}`;
}

function stripAppBase(pathname) {
  const base = getAppBase();
  let path = pathname || '/';
  if (base && (path === base || path.startsWith(`${base}/`))) {
    path = path.slice(base.length) || '/';
  }
  return path;
}

/** Старые закладки /#/catalog → /catalog */
function migrateLegacyHashRoute() {
  if (typeof location === 'undefined') return;
  if (!location.hash.startsWith('#/')) return;
  const raw = location.hash.slice(2);
  const qi = raw.indexOf('?');
  const routePart = ((qi >= 0 ? raw.slice(0, qi) : raw) || '').replace(/^\/+|\/+$/g, '');
  const qs = qi >= 0 ? raw.slice(qi) : '';
  const routeId = !routePart || routePart === Routes.LANDING
    ? Routes.LANDING
    : routePart.split('/')[0];
  const next = pathForRoute(KNOWN_ROUTES.has(routeId) ? routeId : Routes.LANDING) + qs;
  history.replaceState(null, '', next);
}

function parsePathRoute() {
  migrateLegacyHashRoute();
  const trimmed = stripAppBase(location.pathname).replace(/^\/+|\/+$/g, '');
  const routeId = trimmed ? trimmed.split('/')[0] : Routes.LANDING;
  return {
    path: KNOWN_ROUTES.has(routeId) ? routeId : Routes.LANDING,
    params: new URLSearchParams(location.search.replace(/^\?/, '')),
  };
}

function useAppRoute() {
  const [state, setState] = React.useState(() => parsePathRoute());
  React.useEffect(() => {
    const onPop = () => setState(parsePathRoute());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (r, query) => {
    let qs = '';
    if (query) {
      qs = query instanceof URLSearchParams
        ? query.toString()
        : typeof query === 'string'
          ? query.replace(/^\?/, '')
          : new URLSearchParams(query).toString();
    }
    const url = pathForRoute(r) + (qs ? `?${qs}` : '');
    const current = `${location.pathname}${location.search}`;
    if (current !== url) {
      history.pushState(null, '', url);
    }
    setState(parsePathRoute());
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return [state.path, navigate, state.params];
}

/** @deprecated имя оставлено для совместимости; роутинг без hash. */
const useHashRoute = useAppRoute;

function initApiBase() {
  if (typeof window === 'undefined') return;
  if (typeof window.__API_BASE__ === 'string') return;
  const { hostname, port } = window.location;
  const appBase = getAppBase();
  if ((hostname === 'localhost' || hostname === '127.0.0.1') && port === '3000') {
    window.__API_BASE__ = 'http://127.0.0.1:8000';
  } else {
    window.__API_BASE__ = appBase;
  }
}
initApiBase();

function getApiBase() {
  const b = typeof window !== 'undefined' && window.__API_BASE__;
  return typeof b === 'string' ? b.replace(/\/$/, '') : '';
}

const AUTH_ACCESS_KEY = 'access_token';
const AUTH_REFRESH_KEY = 'refresh_token';
const AUTH_REMEMBER_KEY = 'auth_remember';

function isRememberAuth() {
  if (typeof localStorage === 'undefined') return true;
  return localStorage.getItem(AUTH_REMEMBER_KEY) !== '0';
}

function getAccessToken() {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(AUTH_ACCESS_KEY) || sessionStorage.getItem(AUTH_ACCESS_KEY);
}

function getRefreshToken() {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(AUTH_REFRESH_KEY) || sessionStorage.getItem(AUTH_REFRESH_KEY);
}

function hasAuthSession() {
  return !!getAccessToken();
}

/** Persist JWT. remember=true → localStorage (после закрытия браузера); false → sessionStorage. */
function setAuthTokens(access, refresh, remember) {
  if (typeof localStorage === 'undefined') return;
  let keep = remember;
  if (typeof keep !== 'boolean') {
    if (localStorage.getItem(AUTH_ACCESS_KEY) || localStorage.getItem(AUTH_REFRESH_KEY)) {
      keep = true;
    } else if (sessionStorage.getItem(AUTH_ACCESS_KEY) || sessionStorage.getItem(AUTH_REFRESH_KEY)) {
      keep = false;
    } else {
      keep = isRememberAuth();
    }
  } else {
    localStorage.setItem(AUTH_REMEMBER_KEY, keep ? '1' : '0');
  }
  const store = keep ? localStorage : sessionStorage;
  const other = keep ? sessionStorage : localStorage;
  other.removeItem(AUTH_ACCESS_KEY);
  other.removeItem(AUTH_REFRESH_KEY);
  if (access) store.setItem(AUTH_ACCESS_KEY, access);
  else store.removeItem(AUTH_ACCESS_KEY);
  if (refresh) store.setItem(AUTH_REFRESH_KEY, refresh);
  else if (refresh === null) store.removeItem(AUTH_REFRESH_KEY);
}

function clearAuthTokens() {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(AUTH_ACCESS_KEY);
  localStorage.removeItem(AUTH_REFRESH_KEY);
  sessionStorage.removeItem(AUTH_ACCESS_KEY);
  sessionStorage.removeItem(AUTH_REFRESH_KEY);
}

function brandIconUrl(name) {
  return `${getAppBase()}/icons/${name}.svg`;
}

function getWsBase() {
  const api = getApiBase();
  if (api) {
    if (/^https?:\/\//i.test(api)) {
      return api.replace(/^https/i, 'wss').replace(/^http/i, 'ws');
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}${api}`;
  }
  if (typeof window === 'undefined') return '';
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}`;
}

function openChatThreadWs(threadPublicId, onEvent) {
  const token = getAccessToken();
  if (!token || !threadPublicId) return () => {};
  const url = `${getWsBase()}/ws/chat/threads/${encodeURIComponent(threadPublicId)}/?token=${encodeURIComponent(token)}`;
  let ws;
  let stopped = false;
  let retryTimer = null;

  const connect = () => {
    if (stopped) return;
    ws = new WebSocket(url);
    ws.onopen = () => {
      try { ws.send(JSON.stringify({ event: 'ping' })); } catch (_) { /* ignore */ }
    };
    ws.onmessage = (event) => {
      try {
        onEvent?.(JSON.parse(event.data));
      } catch (_) { /* ignore malformed */ }
    };
    ws.onclose = () => {
      if (!stopped) {
        retryTimer = setTimeout(connect, 3000);
      }
    };
  };

  connect();

  return () => {
    stopped = true;
    if (retryTimer) clearTimeout(retryTimer);
    if (ws && ws.readyState <= WebSocket.OPEN) {
      try { ws.close(); } catch (_) { /* ignore */ }
    }
  };
}

function openChatWithUser(navigate, userPublicId) {
  if (!userPublicId) return;
  navigate(Routes.MESSAGES, { user: userPublicId });
}

function openChatWithCourse(navigate, coursePublicId) {
  if (!coursePublicId) return;
  navigate(Routes.MESSAGES, { course: coursePublicId });
}

async function fetchChatUnreadTotal() {
  try {
    const data = await fetchApiJson('/api/communication/chat/threads/unread_total/', { auth: true });
    return Number(data?.total) || 0;
  } catch (_) {
    return 0;
  }
}

function refreshChatUnread() {
  window.dispatchEvent(new CustomEvent('chat-unread-changed'));
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
    const shortAnswer = mod.lessons_short_answer || [];
    const coding = mod.lessons_coding || [];
    return {
      id: mod.public_id,
      title: mod.title,
      icon: MODULE_ICONS[i % MODULE_ICONS.length],
      lessons: theories.length,
      quizzes: radio.length + checkbox.length + shortAnswer.length,
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
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const data = await fetchApiJson('/api/auth/refresh/', {
      method: 'POST',
      body: { refresh },
      _retry: false,
    });
    if (data && data.access) {
      setAuthTokens(data.access, data.refresh || refresh);
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
    const t = getAccessToken();
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
    clearAuthTokens();
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
  if (!getAccessToken()) return [];
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
    const t = getAccessToken();
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
    clearAuthTokens();
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

/** UUID текущего пользователя из access JWT (public_id или user_id после refresh). */
function currentUserPublicId(payloadOrToken) {
  const payload = typeof payloadOrToken === 'string'
    ? parseJwtPayload(payloadOrToken)
    : (payloadOrToken || {});
  return String(payload.public_id || payload.user_id || '');
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
  try {
    const here = `${location.pathname}${location.search}`;
    if (!/\/call(?:\?|$)/.test(here)) {
      sessionStorage.setItem('ba_call_return', here);
    }
  } catch (_) { /* private mode */ }
  navigate(Routes.CALL, { conf: conferencePublicId });
}

function consumeCallReturnPath() {
  try {
    return sessionStorage.getItem('ba_call_return') || '';
  } catch (_) {
    return '';
  }
}

function goAfterCall(navigate) {
  const raw = consumeCallReturnPath();
  try {
    sessionStorage.removeItem('ba_call_return');
  } catch (_) { /* private mode */ }
  try {
    const url = new URL(raw, location.origin);
    const params = Object.fromEntries(url.searchParams.entries());
    if (url.pathname.includes('/learn') && params.course) {
      navigate(window.Routes.LEARN, params);
      return;
    }
    if (url.pathname.includes('/course') && params.id) {
      navigate(window.Routes.COURSE, params);
      return;
    }
  } catch (_) { /* ignore */ }
  navigate(window.Routes.CONFERENCES);
}

function formatCallDuration(seconds) {
  const n = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(n / 3600);
  const m = Math.floor((n % 3600) / 60);
  const s = n % 60;
  if (h) return `${h} ч ${m} мин`;
  if (m) return `${m} мин ${s} с`;
  return `${s} с`;
}

function formatFileSize(bytes) {
  const n = Number(bytes) || 0;
  if (n < 1024) return `${n} Б`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} КБ`;
  return `${(n / (1024 * 1024)).toFixed(1)} МБ`;
}

function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = 'Продолжить',
  cancelLabel = 'Отмена',
  extraLabel,
  danger = false,
  hideCancel = false,
  onConfirm,
  onExtra,
  onCancel,
}) {
  React.useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === 'Escape') onCancel?.();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onCancel]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[90] flex items-end sm:items-center justify-center p-0 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ba-confirm-title"
    >
      <button type="button" className="absolute inset-0 bg-ink/50" aria-label="Закрыть" onClick={onCancel} />
      <div className="relative w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl bg-white p-5 shadow-glow ring-1 ring-black/[0.08]">
        <div id="ba-confirm-title" className="text-lg font-bold text-ink">{title}</div>
        {body ? <p className="mt-2 text-sm text-ink/65 whitespace-pre-wrap">{body}</p> : null}
        <div className="mt-5 flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
          {!hideCancel ? (
            <button
              type="button"
              onClick={onCancel}
              className="h-11 px-4 rounded-xl text-sm font-semibold ring-1 ring-black/[0.08] bg-white"
            >
              {cancelLabel}
            </button>
          ) : null}
          {extraLabel ? (
            <button
              type="button"
              onClick={onExtra}
              className="h-11 px-4 rounded-xl text-sm font-semibold ring-1 ring-violet-200 text-violet-700 bg-violet-50"
            >
              {extraLabel}
            </button>
          ) : null}
          <button
            type="button"
            onClick={onConfirm}
            className={`h-11 px-4 rounded-xl text-sm font-semibold text-white ${
              danger ? 'bg-rose-600 hover:bg-rose-500' : 'btn-grad'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function AppNoticeHost() {
  const [notice, setNotice] = React.useState(null);
  React.useEffect(() => {
    window.showAppNotice = (opts) => {
      const payload = typeof opts === 'string'
        ? { title: 'Сообщение', body: opts }
        : (opts || {});
      setNotice({
        title: payload.title || 'Сообщение',
        body: payload.body || '',
        confirmLabel: payload.confirmLabel || 'Понятно',
      });
    };
    return () => {
      if (window.showAppNotice) delete window.showAppNotice;
    };
  }, []);
  return (
    <ConfirmDialog
      open={!!notice}
      title={notice?.title}
      body={notice?.body}
      confirmLabel={notice?.confirmLabel || 'Понятно'}
      hideCancel
      onConfirm={() => setNotice(null)}
      onCancel={() => setNotice(null)}
    />
  );
}

function notifyUser(title, body) {
  if (typeof window.showAppNotice === 'function') {
    window.showAppNotice({ title, body });
  }
}

const LESSON_BOARD_IMPORT_KEY = 'bervinov.lessonBoardImport';

function whiteboardFeatureEnabled() {
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  if (!meta) return true;
  return meta.getAttribute('content') !== 'false';
}

function isLessonImageAttachment(row) {
  const ct = String(row?.content_type || '').toLowerCase();
  if (ct.startsWith('image/')) return true;
  const name = String(row?.name || row?.url || '').toLowerCase();
  return /\.(png|jpe?g|gif|webp|svg)$/i.test(name);
}

function consumeLessonBoardImport() {
  try {
    const raw = sessionStorage.getItem(LESSON_BOARD_IMPORT_KEY);
    sessionStorage.removeItem(LESSON_BOARD_IMPORT_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    const urls = Array.isArray(data?.urls) ? data.urls.filter(Boolean) : [];
    if (!urls.length) return null;
    return {
      urls,
      backRoute: data.backRoute || '',
      backQuery: data.backQuery && typeof data.backQuery === 'object' ? data.backQuery : {},
      title: data.title || '',
    };
  } catch (_) {
    return null;
  }
}

function openLessonImagesOnBoard(navigate, { urls, title } = {}) {
  const list = (urls || []).filter(Boolean);
  if (!list.length || typeof navigate !== 'function') return;
  const trimmed = stripAppBase(location.pathname).replace(/^\/+|\/+$/g, '');
  const routeId = trimmed.split('/')[0] || Routes.LEARN;
  try {
    sessionStorage.setItem(LESSON_BOARD_IMPORT_KEY, JSON.stringify({
      urls: list,
      backRoute: KNOWN_ROUTES.has(routeId) ? routeId : Routes.LEARN,
      backQuery: Object.fromEntries(new URLSearchParams(location.search)),
      title: title || '',
    }));
  } catch (_) { /* quota */ }
  navigate(Routes.WHITEBOARD);
}

function LessonAttachments({ items, navigate, lessonTitle }) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return null;
  const images = list.filter(isLessonImageAttachment);
  const files = list.filter((row) => !isLessonImageAttachment(row));
  const loggedIn = !!getAccessToken();
  const canBoard = loggedIn && whiteboardFeatureEnabled() && images.length > 0 && typeof navigate === 'function';

  return (
    <div className="mt-5 space-y-4">
      {images.length > 0 && (
        <div className="rounded-2xl ring-1 ring-black/[0.06] bg-white p-3 sm:p-4">
          <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-3">
            Схема к заданию
          </div>
          <div className="space-y-3">
            {images.map((row) => {
              const href = mediaUrl(row.url) || row.url || '';
              return (
                <figure key={row.public_id || row.name} className="overflow-hidden rounded-xl ring-1 ring-black/[0.06] bg-[#fafafa]">
                  <img
                    src={href}
                    alt={row.name || 'Схема задания'}
                    className="w-full max-h-[min(72vh,720px)] object-contain bg-white"
                  />
                </figure>
              );
            })}
          </div>
          {canBoard && (
            <button
              type="button"
              onClick={() => openLessonImagesOnBoard(navigate, {
                urls: images.map((row) => mediaUrl(row.url) || row.url).filter(Boolean),
                title: lessonTitle,
              })}
              className="mt-3 min-h-11 w-full sm:w-auto px-4 rounded-xl text-sm font-semibold text-violet-800 bg-violet-50 ring-1 ring-violet-200 hover:bg-violet-100"
            >
              На личную доску
            </button>
          )}
          {canBoard && (
            <p className="mt-2 text-[12px] text-ink/45 leading-relaxed">
              Картинка откроется на вашей доске. Можно рисовать сверху. Это черновик, на оценку не влияет.
            </p>
          )}
          {!loggedIn && images.length > 0 && whiteboardFeatureEnabled() && (
            <p className="mt-2 text-[12px] text-ink/45">
              Войдите, чтобы рисовать на личной доске.
            </p>
          )}
        </div>
      )}
      {files.length > 0 && (
        <div className="rounded-2xl ring-1 ring-black/[0.06] bg-white p-4">
          <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-3">
            Материалы к заданию
          </div>
          <ul className="space-y-2">
            {files.map((row) => {
              const href = mediaUrl(row.url) || row.url || '';
              return (
                <li key={row.public_id || row.name}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 min-h-11 px-3 py-2 rounded-xl ring-1 ring-black/[0.06] hover:bg-violet-50/70 hover:ring-violet-200 transition-colors"
                  >
                    <span className="w-9 h-9 rounded-lg bg-violet-50 text-violet-700 flex items-center justify-center text-[11px] font-bold shrink-0">
                      {(row.name || 'файл').split('.').pop()?.slice(0, 4).toUpperCase()}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-semibold text-ink truncate">{row.name || 'Файл'}</span>
                      <span className="block text-[11px] text-ink/45">{formatFileSize(row.size)}</span>
                    </span>
                    <span className="text-[12px] font-semibold text-violet-700 shrink-0">Скачать</span>
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
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
  const [viewMode, setViewMode] = React.useState('auto');
  const viewerRef = React.useRef(null);

  React.useEffect(() => {
    if (!conferenceId) return undefined;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await fetchConferenceWhiteboard(conferenceId);
        if (!cancelled) {
          setBoard(data);
          setViewMode(data?.has_snapshot ? 'board' : 'image');
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'Не удалось загрузить конспект');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [conferenceId]);

  React.useEffect(() => {
    const host = viewerRef.current;
    const api = window.BervinovWhiteboard;
    if (!host || !board?.has_snapshot || viewMode !== 'board' || !api?.mountReadOnly) {
      return undefined;
    }
    api.mountReadOnly(host, {
      snapshot: board.snapshot_json,
      licenseKey: board.license_key || '',
    });
    return () => api.unmount?.(host);
  }, [board, viewMode]);

  React.useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose?.();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const showBoard = !loading && !error && viewMode === 'board' && board?.has_snapshot;
  const showImage = !loading && !error && viewMode === 'image' && board?.image_url;

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
          <div className="flex items-center gap-2">
            {board?.has_snapshot && board?.image_url && (
              <div className="flex rounded-lg ring-1 ring-black/[0.08] p-0.5 text-xs font-semibold">
                <button type="button" onClick={() => setViewMode('board')}
                  className={`px-3 py-1.5 rounded-md ${viewMode === 'board' ? 'bg-violet-500/10 text-violet-600' : 'text-ink/55'}`}>
                  Доска
                </button>
                <button type="button" onClick={() => setViewMode('image')}
                  className={`px-3 py-1.5 rounded-md ${viewMode === 'image' ? 'bg-violet-500/10 text-violet-600' : 'text-ink/55'}`}>
                  PNG
                </button>
              </div>
            )}
            <button type="button" onClick={onClose}
              className="w-10 h-10 rounded-xl ring-1 ring-black/[0.08] hover:bg-black/[0.03] flex items-center justify-center">
              <I.X className="w-5 h-5"/>
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-0 overflow-auto bg-slate-50 p-4 sm:p-6">
          {loading && <div className="py-16 text-center text-sm text-ink/50">Загрузка…</div>}
          {!loading && error && (
            <div className="py-16 text-center text-sm text-red-600">{error}</div>
          )}
          {!loading && !error && !board?.has_snapshot && !board?.image_url && (
            <div className="py-16 text-center text-sm text-ink/50">Конспект ещё не сохранён</div>
          )}
          {showBoard && (
            <div ref={viewerRef} className="relative w-full min-h-[min(60vh,520px)] rounded-xl ring-1 ring-black/[0.06] bg-white overflow-hidden"/>
          )}
          {showImage && (
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

const SOLUTION_FAIL_THRESHOLD = 3;

function LessonInstructorNote({ text }) {
  if (!text || !String(text).trim()) return null;
  return (
    <div className="mt-5 p-4 rounded-xl bg-violet-50/80 border border-violet-100">
      <div className="text-[11px] font-semibold uppercase tracking-widest text-violet-600/80 mb-2">
        Заметка преподавателя
      </div>
      <p className="text-[14px] text-ink/75 leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  );
}

function formatCommentDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (_) {
    return '';
  }
}

function pluralErrors(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return 'ошибка';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'ошибки';
  return 'ошибок';
}

function scrollToLessonReferenceSolution() {
  document.getElementById('lesson-reference-solution')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function ReferenceSolutionContent({ referenceSolution }) {
  const hasText = !!(referenceSolution && referenceSolution.text);
  const hasVideoContent = !!(referenceSolution && (referenceSolution.video || referenceSolution.has_video || referenceSolution.video_requires_pro));
  if (!referenceSolution || (!hasText && !hasVideoContent)) {
    return (
      <p className="text-[13px] text-ink/45 text-center py-2">
        Материал эталонного решения ещё не добавлен.
      </p>
    );
  }
  return (
    <>
      {referenceSolution.video ? (
        <VideoExplanation video={referenceSolution.video} title="Видео-разбор"/>
      ) : referenceSolution.video_requires_pro ? (
        <div className={`rounded-xl ring-1 ring-amber-200/80 bg-amber-50/80 p-4 ${hasText ? 'mb-6' : ''}`}>
          <div className="flex items-start gap-3">
            <I.Play className="w-5 h-5 text-amber-700 shrink-0 mt-0.5"/>
            <div>
              <p className="text-[14px] font-semibold text-ink">Видео-разбор — в тарифе Про</p>
              <p className="text-[12px] text-ink/55 mt-1 leading-relaxed">
                Текст эталона доступен всем. Видео с объяснением открывается по тарифу Про.
              </p>
            </div>
          </div>
        </div>
      ) : null}
      {hasText && (
        <div
          className={`theory-content text-[15px] text-ink/85 leading-relaxed ${referenceSolution.video || referenceSolution.video_requires_pro ? 'mt-6' : ''}`}
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(referenceSolution.text) }}
        />
      )}
    </>
  );
}

function InlineReferenceSolution({ referenceSolution, unlocked, loggedIn, onLogin, wrongAttempts, sessionFails }) {
  const fails = (wrongAttempts || 0) + (sessionFails || 0);
  const remaining = Math.max(0, SOLUTION_FAIL_THRESHOLD - fails);

  if (unlocked && loggedIn) {
    return (
      <div id="lesson-reference-solution" className="rounded-2xl ring-1 ring-violet-200/60 bg-white p-5 shadow-soft">
        <div className="flex items-center gap-2 mb-4">
          <I.Play className="w-4 h-4 text-violet-600"/>
          <h3 className="text-[14px] font-bold text-ink">Эталонное решение</h3>
        </div>
        <ReferenceSolutionContent referenceSolution={referenceSolution} />
      </div>
    );
  }

  return (
    <div id="lesson-reference-solution" className="relative rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-white">
      <div className="p-5 blur-md select-none pointer-events-none opacity-70" aria-hidden="true">
        <div className="aspect-video bg-gradient-to-br from-violet-100/80 to-cyan-100/80 rounded-xl mb-4 flex items-center justify-center">
          <div className="w-14 h-14 rounded-full bg-white/60 flex items-center justify-center">
            <I.Play className="w-6 h-6 text-violet-400"/>
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-black/[0.08] rounded-full w-full"/>
          <div className="h-3 bg-black/[0.08] rounded-full w-4/5"/>
          <pre className="mt-3 p-3 rounded-lg bg-black/[0.04] text-[11px] font-mono text-ink/40 leading-relaxed">{`def solve():\n    return answer`}</pre>
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/55 backdrop-blur-[2px]">
        <div className="text-center px-6 py-4 max-w-sm">
          {!unlocked ? (
            <>
              <div className="text-2xl mb-2 opacity-80">🔒</div>
              <p className="text-[14px] font-semibold text-ink/80">Эталонное решение</p>
              <p className="text-[12px] text-ink/50 mt-2 leading-relaxed">
                Откроется после правильного ответа
                {remaining > 0 && (
                  <> или ещё {remaining} {pluralErrors(remaining)} ({fails} из {SOLUTION_FAIL_THRESHOLD})</>
                )}
              </p>
            </>
          ) : (
            <>
              <p className="text-[14px] font-semibold text-violet-800">Разбор доступен</p>
              <p className="text-[12px] text-ink/50 mt-1 mb-3">Войдите, чтобы посмотреть</p>
              {onLogin && (
                <button type="button" onClick={onLogin}
                  className="h-10 px-5 rounded-xl btn-grad text-white text-sm font-semibold">
                  Войти
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function LessonCommentsBlock({ lessonKind, lessonId, onLogin, className }) {
  const loggedIn = !!getAccessToken();
  const [items, setItems] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [text, setText] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState('');

  const load = React.useCallback(() => {
    if (!lessonKind || !lessonId) return Promise.resolve();
    setLoading(true);
    const qs = `?lesson_kind=${encodeURIComponent(lessonKind)}&lesson=${encodeURIComponent(lessonId)}`;
    return window.fetchApiJson(`/api/progress/lesson-comments/${qs}`)
      .then((data) => {
        setItems(Array.isArray(data) ? data : (data?.results || []));
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [lessonKind, lessonId]);

  React.useEffect(() => {
    load();
  }, [load]);

  const submit = async () => {
    const body = (text || '').trim();
    if (!body || submitting) return;
    if (!loggedIn) {
      onLogin?.();
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const created = await window.fetchApiJson('/api/progress/lesson-comments/', {
        method: 'POST',
        body: {
          lesson_kind: lessonKind,
          lesson_public_id: lessonId,
          body,
        },
        auth: true,
      });
      setItems((prev) => [...prev, created]);
      setText('');
    } catch (e) {
      setError(e.message || 'Не удалось отправить комментарий');
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (publicId) => {
    if (!loggedIn || !publicId) return;
    try {
      await window.fetchApiJson(
        `/api/progress/lesson-comments/${encodeURIComponent(publicId)}/`,
        { method: 'DELETE', auth: true },
      );
      setItems((prev) => prev.filter((c) => c.public_id !== publicId));
    } catch (e) {
      setError(e.message || 'Не удалось удалить комментарий');
    }
  };

  return (
    <div className={className || 'mt-12 pt-8 border-t border-black/[0.06]'}>
      <div className="flex items-center gap-2 mb-5">
        <I.Chat className="w-4 h-4 text-ink/45"/>
        <h2 className="text-[15px] font-bold text-ink">Обсуждение</h2>
        <span className="text-[11px] text-ink/40">{items.length}</span>
      </div>

      {loading ? (
        <p className="text-sm text-ink/45">Загружаем комментарии…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-ink/45 mb-5">Пока нет комментариев. Будьте первым!</p>
      ) : (
        <div className="space-y-4 mb-6">
          {items.map((c) => (
            <div key={c.public_id} className="flex gap-3">
              <div className="w-9 h-9 rounded-full bg-violet-500/10 shrink-0 overflow-hidden flex items-center justify-center text-sm font-bold text-violet-600">
                {c.author?.avatar ? (
                  <img src={c.author.avatar} alt="" className="w-full h-full object-cover"/>
                ) : (
                  (c.author?.display_name || '?').slice(0, 1).toUpperCase()
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="text-[13px] font-semibold text-ink">
                    {c.author?.display_name || 'Пользователь'}
                  </span>
                  <span className="text-[11px] text-ink/40">{formatCommentDate(c.created_at)}</span>
                  {c.is_mine && (
                    <button type="button" onClick={() => remove(c.public_id)}
                      className="text-[11px] text-rose-500 hover:text-rose-700 ml-auto">
                      Удалить
                    </button>
                  )}
                </div>
                <p className="mt-1 text-[14px] text-ink/75 leading-relaxed whitespace-pre-wrap">{c.body}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {loggedIn ? (
        <div className="rounded-2xl ring-1 ring-black/[0.06] bg-white p-4 shadow-soft">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            maxLength={4000}
            placeholder="Напишите комментарий…"
            className="w-full resize-y text-[14px] text-ink/80 placeholder:text-ink/35 focus:outline-none"
          />
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          <div className="mt-3 flex justify-end">
            <button type="button" onClick={submit} disabled={!text.trim() || submitting}
              className="h-10 px-5 rounded-xl btn-grad text-white text-sm font-semibold disabled:opacity-40">
              {submitting ? 'Отправка…' : 'Отправить'}
            </button>
          </div>
        </div>
      ) : (
        <button type="button" onClick={onLogin}
          className="text-sm text-violet-600 font-semibold hover:text-violet-800 transition-colors">
          Войдите, чтобы оставить комментарий →
        </button>
      )}
    </div>
  );
}

function LessonUserComments(props) {
  return <LessonCommentsBlock {...props} />;
}

function LessonDiscussionSection({
  lessonKind,
  lessonId,
  onLogin,
  showReferenceSolution,
  referenceSolution,
  solutionUnlocked,
  wrongAttempts,
  sessionFails,
}) {
  const loggedIn = !!getAccessToken();

  return (
    <div id="lesson-discussion" className="mt-12 pt-8 border-t border-black/[0.06]">
      {showReferenceSolution && (
        <InlineReferenceSolution
          referenceSolution={referenceSolution}
          unlocked={solutionUnlocked}
          loggedIn={loggedIn}
          onLogin={onLogin}
          wrongAttempts={wrongAttempts}
          sessionFails={sessionFails}
        />
      )}
      <LessonCommentsBlock
        lessonKind={lessonKind}
        lessonId={lessonId}
        onLogin={onLogin}
        className={showReferenceSolution ? 'mt-8' : ''}
      />
    </div>
  );
}

function hasReferenceSolutionMaterial(lesson) {
  if (!lesson) return false;
  if (lesson.has_reference_solution === true) return true;
  if (lesson.has_reference_solution === false) return false;
  if (lesson.reference_solution) return true;
  return false;
}

function computeSolutionUnlocked(lesson, sessionFails, justCorrect) {
  if (!lesson) return false;
  if (justCorrect || lesson.solution_unlocked) return true;
  const fails = (lesson.wrong_attempts || 0) + (sessionFails || 0);
  return fails >= SOLUTION_FAIL_THRESHOLD;
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

  Settings: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3v2.2M12 18.8V21M4.9 6.5l1.6 1.6M17.5 15.9l1.6 1.6M3 12h2.2M18.8 12H21M4.9 17.5l1.6-1.6M17.5 8.1l1.6-1.6" strokeLinecap="round" />
    </svg>,

  LogOut: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="M10 7V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-7a2 2 0 0 1-2-2v-1" strokeLinecap="round" />
      <path d="M15 12H3m0 0 3-3m-3 3 3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  Send: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="m4 12 16-8-6 18-3-7-7-3z" strokeLinejoin="round" />
    </svg>,

  Paperclip: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <path d="m21.4 11.6-8.5 8.5a5 5 0 0 1-7.1-7.1l9.2-9.2a3.2 3.2 0 0 1 4.5 4.5l-9.2 9.2a1.4 1.4 0 0 1-2-2l8.1-8.1" strokeLinecap="round" strokeLinejoin="round" />
    </svg>,

  Copy: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className}>
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M6 16H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeLinecap="round" />
    </svg>,

  More: ({ className }) =>
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <circle cx="5" cy="12" r="1.7" /><circle cx="12" cy="12" r="1.7" /><circle cx="19" cy="12" r="1.7" />
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

  // Official brand marks (Wikimedia / VK brand kit), served from /icons/*.svg
  Yandex: ({ className }) =>
  <img src={brandIconUrl('yandex')} alt=""
      className={`block shrink-0 object-contain ${className || ''}`}
      width="20" height="20" aria-hidden="true" />,

  VK: ({ className }) =>
  <img src={brandIconUrl('vk')} alt=""
      className={`block shrink-0 object-contain ${className || ''}`}
      width="20" height="20" aria-hidden="true" />,

};

// ------- Course catalog -------
const CATEGORIES = ['Все', 'ЕГЭ', 'Информатика'];

const COURSES = [
{
  id: 'ege-informatika', title: 'ЕГЭ-информатика',
  desc: 'Подготовка к ЕГЭ по информатике: графы, кодирование и поиск, электронные таблицы и контрольная.',
  rating: 4.9, students: 1240, lessons: 41, hours: 60, price: 14900, level: 'ЕГЭ', lang: 'RU',
  cat: 'ЕГЭ', tags: ['ЕГЭ', 'Информатика'],
  gradFrom: '#1D4ED8', gradTo: '#22D3EE', accentEmoji: 'ЕГЭ', popularity: 98
},
];

// ------- Layout chrome -------
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

async function enableWebPushNotifications() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    notifyUser('Не получится', 'Этот браузер не умеет принимать уведомления с сайта.');
    return false;
  }
  if (!getAccessToken()) {
    notifyUser('Нужен вход', 'Сначала войдите в аккаунт, потом включим уведомления.');
    return false;
  }
  try {
    const reg = await navigator.serviceWorker.register('/sw.js');
    await navigator.serviceWorker.ready;
    const vapid = await fetchApiJson('/api/push/vapid/', { auth: true });
    if (!vapid.configured || !vapid.public_key) {
      notifyUser('Пока недоступно', 'Уведомления на сервере ещё не настроены.');
      return false;
    }
    const perm = await Notification.requestPermission();
    if (perm !== 'granted') {
      notifyUser('Нужно разрешение', 'Разрешите уведомления в настройках браузера и попробуйте снова.');
      return false;
    }
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapid.public_key),
      });
    }
    const json = sub.toJSON();
    await fetchApiJson('/api/push/subscribe/', {
      method: 'POST',
      auth: true,
      body: {
        endpoint: json.endpoint,
        keys: json.keys,
      },
    });
    notifyUser('Готово', 'Push включены. Будем присылать важные уведомления.');
    return true;
  } catch (e) {
    const msg = e?.message || String(e);
    if (msg.includes('MIME type') || msg.includes('ServiceWorker')) {
      notifyUser('Обновите страницу', 'Push пока недоступны. Обновите страницу и попробуйте снова.');
    } else {
      notifyUser('Не удалось включить', msg || 'Не получилось включить уведомления.');
    }
    return false;
  }
}

function NotificationBell({ navigate }) {
  const [open, setOpen] = React.useState(false);
  const [items, setItems] = React.useState([]);
  const wrapRef = React.useRef(null);

  const load = React.useCallback(async () => {
    if (!getAccessToken()) {
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

  if (!getAccessToken()) return null;

  return (
    <div className="relative" ref={wrapRef}>
      <button type="button" onClick={() => setOpen((v) => !v)} aria-label="Уведомления"
        className="site-header__icon-btn relative">
        <I.Bell className="w-5 h-5" />
        {items.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[17px] h-[17px] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
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
                  {note.kind === 'subscription_expiring' && (
                    <div className="mt-2 flex gap-2">
                      <button type="button" onClick={() => {
                        dismiss(note);
                        setOpen(false);
                        navigate(Routes.PRO);
                      }}
                        className="h-8 px-3 rounded-lg btn-grad text-white text-xs font-semibold">
                        О тарифе Про
                      </button>
                      <button type="button" onClick={() => dismiss(note)}
                        className="h-8 px-3 rounded-lg text-xs font-semibold text-ink/55 hover:bg-black/[0.04]">
                        Скрыть
                      </button>
                    </div>
                  )}
                  {(note.kind === 'mentor_message' || note.kind === 'study_reminder' || note.kind === 'streak_reminder') && (
                    <div className="mt-2 flex gap-2">
                      <button type="button" onClick={() => {
                        dismiss(note);
                        setOpen(false);
                        if (note.kind === 'mentor_message') navigate(Routes.MESSAGES);
                        else if (note.kind === 'study_reminder' || note.kind === 'streak_reminder') navigate(Routes.CATALOG);
                      }}
                        className="h-8 px-3 rounded-lg btn-grad text-white text-xs font-semibold">
                        Открыть
                      </button>
                      <button type="button" onClick={() => dismiss(note)}
                        className="h-8 px-3 rounded-lg text-xs font-semibold text-ink/55 hover:bg-black/[0.04]">
                        Скрыть
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
          <div className="px-4 py-2 border-t border-black/[0.06] flex items-center justify-between gap-2">
            <button type="button" onClick={() => { setOpen(false); navigate(Routes.CONFERENCES); }}
              className="text-xs font-semibold text-violet-600 hover:underline">
              Все созвоны
            </button>
            <button type="button" onClick={() => window.enableWebPushNotifications?.()}
              className="text-xs font-semibold text-ink/45 hover:text-violet-600">
              Push в браузере
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function UserMenu({
  route,
  navigate,
  displayName,
  email,
  initials,
  isMentor,
  isAdmin,
  onLogout,
}) {
  const [open, setOpen] = React.useState(false);
  const wrapRef = React.useRef(null);

  React.useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    window.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  React.useEffect(() => {
    setOpen(false);
  }, [route]);

  const go = (id) => {
    setOpen(false);
    navigate(id);
  };

  const items = [
    { id: 'profile', label: 'Профиль', icon: I.Users, action: () => go(Routes.PROFILE), active: route === Routes.PROFILE },
    { id: 'settings', label: 'Настройки', icon: I.Settings, action: () => go(Routes.PROFILE_EDIT), active: route === Routes.PROFILE_EDIT },
    { id: 'pro', label: 'Тариф Про', icon: I.Star, action: () => go(Routes.PRO), active: route === Routes.PRO },
    { id: 'conferences', label: 'Созвоны', icon: I.Video, action: () => go(Routes.CONFERENCES), active: route === Routes.CONFERENCES },
    ...(isMentor ? [{ id: 'mentor', label: 'Ментор', icon: I.Brain, action: () => go(Routes.MENTOR), active: route === Routes.MENTOR }] : []),
    ...(isAdmin ? [{ id: 'school', label: 'Школа', icon: I.Book, href: '/admin/' }] : []),
  ];

  return (
    <div className="site-header__user" ref={wrapRef}>
      <button
        type="button"
        className="site-header__user-trigger"
        aria-label="Меню аккаунта"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sky-50 text-[11px] font-bold text-sky-700 ring-1 ring-sky-200/80">
          {initials}
        </span>
        <I.ChevronDown className={`w-3.5 h-3.5 text-ink/45 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="site-header__user-menu" role="menu">
          <div className="site-header__user-head">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-50 text-sm font-bold text-sky-700 ring-1 ring-sky-200/80 shrink-0">
              {initials}
            </span>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-ink truncate">{displayName || 'Аккаунт'}</div>
              {email ? <div className="text-xs text-ink/45 truncate mt-0.5">{email}</div> : null}
            </div>
          </div>
          {items.map((item) => {
            const Icon = item.icon;
            if (item.href) {
              return (
                <a
                  key={item.id}
                  href={item.href}
                  role="menuitem"
                  className="site-header__user-item"
                >
                  <Icon className="site-header__user-ico" />
                  <span>{item.label}</span>
                </a>
              );
            }
            return (
              <button
                key={item.id}
                type="button"
                role="menuitem"
                onClick={item.action}
                className={`site-header__user-item ${item.active ? 'is-active' : ''}`}
              >
                <Icon className="site-header__user-ico" />
                <span>{item.label}</span>
              </button>
            );
          })}
          <div className="site-header__user-sep" />
          <button
            type="button"
            role="menuitem"
            onClick={(e) => {
              setOpen(false);
              onLogout(e);
            }}
            className="site-header__user-item is-danger"
          >
            <I.LogOut className="site-header__user-ico" />
            <span>Выйти</span>
          </button>
        </div>
      )}
    </div>
  );
}

function TopNav({ route, navigate }) {
  const [session, setSession] = React.useState(() => !!getAccessToken());
  const [searchDraft, setSearchDraft] = React.useState('');
  const [chatUnread, setChatUnread] = React.useState(0);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);
  const searchRef = React.useRef(null);

  const syncChatUnread = React.useCallback(async () => {
    if (!getAccessToken()) {
      setChatUnread(0);
      return;
    }
    setChatUnread(await fetchChatUnreadTotal());
  }, []);

  React.useEffect(() => {
    const sync = () => setSession(!!getAccessToken());
    window.addEventListener('auth-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('auth-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  React.useEffect(() => {
    if (!session) {
      setChatUnread(0);
      return undefined;
    }
    syncChatUnread();
    const onUnread = () => syncChatUnread();
    window.addEventListener('chat-unread-changed', onUnread);
    const timerId = setInterval(syncChatUnread, 60000);
    return () => {
      window.removeEventListener('chat-unread-changed', onUnread);
      clearInterval(timerId);
    };
  }, [session, syncChatUnread]);

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (window.matchMedia('(max-width: 1279px)').matches) {
          setMobileOpen(true);
          setTimeout(() => searchRef.current?.focus(), 0);
        } else {
          searchRef.current?.focus();
        }
      }
      if (e.key === 'Escape') setMobileOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  React.useEffect(() => {
    setMobileOpen(false);
  }, [route]);

  const access = session ? getAccessToken() : null;
  const payload = access ? parseJwtPayload(access) : {};
  const displayName = [payload.first_name, payload.last_name].filter(Boolean).join(' ').trim();
  const email = payload.email || '';
  const initials = displayName
    ? displayName.split(/\s+/).slice(0, 2).map((p) => p[0]?.toUpperCase() || '').join('')
    : (email?.[0] || 'U').toUpperCase();
  const isMentor = payload.role === 'mentor' || payload.role === 'admin';
  const isAdmin = payload.role === 'admin';

  const submitSearch = (e) => {
    e?.preventDefault();
    const q = searchDraft.trim();
    const params = q ? new URLSearchParams({ q }) : null;
    navigate(Routes.CATALOG, params);
    setSearchDraft('');
    setMobileOpen(false);
  };

  const handleLogout = async (e) => {
    e.preventDefault();
    const refresh = getRefreshToken();
    if (refresh) {
      try {
        await fetchApiJson('/api/auth/logout/', { method: 'POST', body: { refresh }, auth: true });
      } catch (_) {/* ignore invalid/expired */}
    }
    clearAuthTokens();
    setSession(false);
    notifyAuthChanged();
    navigate(Routes.LANDING);
  };

  /* Ментор / Школа / Профиль — в меню аккаунта, чтобы шапка не разъезжалась */
  const links = [
    { id: Routes.LANDING, label: 'Главная' },
    { id: Routes.CATALOG, label: 'Каталог' },
    { id: Routes.PLAYGROUND, label: 'Python' },
    { id: Routes.WHITEBOARD, label: 'Доска' },
    { id: Routes.PRO, label: 'Про' },
  ];

  const go = (id) => {
    navigate(id);
    setMobileOpen(false);
  };

  return (
    <header className={`site-header sticky top-0 z-40 ${scrolled ? 'site-header--scrolled' : ''}`}>
      <div className="site-header__inner">
        <button
          type="button"
          onClick={() => go(Routes.LANDING)}
          className="flex items-center gap-2 group shrink-0"
          aria-label="Bervinov Academy — на главную"
        >
          <span className="site-header__mark">
            <I.Logo className="w-6 h-6" />
          </span>
          <span className="leading-none hidden sm:block">
            <span className="block font-extrabold tracking-tight text-[14px] text-ink">
              Bervinov<span className="grad-text">Academy</span>
            </span>
            <span className="mt-0.5 block text-[9px] uppercase tracking-[0.18em] text-ink/40">
              учись вживую
            </span>
          </span>
        </button>

        <nav className="site-header__nav" aria-label="Основное меню">
          {links.map((l) => (
            <button
              key={l.id}
              type="button"
              onClick={() => go(l.id)}
              className={`site-header__nav-item ${route === l.id ? 'is-active' : ''}`}
            >
              {l.label}
            </button>
          ))}
        </nav>

        <div className="flex-1 min-w-0" />

        <form onSubmit={submitSearch} className="site-header__search">
          <I.Search className="w-4 h-4 text-ink/40 shrink-0" />
          <input
            ref={searchRef}
            type="search"
            value={searchDraft}
            onChange={(e) => setSearchDraft(e.target.value)}
            placeholder="Найти курс…"
            className="flex-1 min-w-0 bg-transparent text-sm text-ink/80 placeholder:text-ink/35 outline-none"
            aria-label="Поиск курсов"
          />
        </form>

        <div className="flex items-center gap-0.5 shrink-0">
          <button
            type="button"
            className="site-header__icon-btn xl:hidden"
            aria-label="Поиск курсов"
            onClick={() => {
              setMobileOpen(true);
              setTimeout(() => searchRef.current?.focus(), 0);
            }}
          >
            <I.Search className="w-5 h-5" />
          </button>

          {session ? (
            <>
              <button
                type="button"
                onClick={() => go(Routes.MESSAGES)}
                aria-label={chatUnread > 0 ? `Сообщения, непрочитанных: ${chatUnread}` : 'Сообщения'}
                className={`site-header__icon-btn relative ${route === Routes.MESSAGES ? 'is-active' : ''}`}
              >
                <I.Chat className="w-5 h-5" />
                {chatUnread > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 min-w-[17px] h-[17px] px-1 rounded-full grad-bg text-white text-[10px] font-bold flex items-center justify-center">
                    {chatUnread > 99 ? '99+' : chatUnread}
                  </span>
                )}
              </button>
              <NotificationBell navigate={navigate} />
              <UserMenu
                route={route}
                navigate={navigate}
                displayName={displayName}
                email={email}
                initials={initials}
                isMentor={isMentor}
                isAdmin={isAdmin}
                onLogout={handleLogout}
              />
            </>
          ) : (
            <button
              type="button"
              onClick={() => go(Routes.AUTH)}
              className="btn-grad h-11 px-4 rounded-xl text-white text-sm font-semibold"
            >
              Войти
            </button>
          )}

          <button
            type="button"
            className="site-header__icon-btn site-header__menu-btn"
            aria-label={mobileOpen ? 'Закрыть меню' : 'Открыть меню'}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
          >
            <span className="site-header__burger" data-open={mobileOpen ? '1' : '0'}>
              <span /><span /><span />
            </span>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="site-header__panel xl:hidden">
          <form
            onSubmit={submitSearch}
            className="flex items-center gap-2 h-11 px-3 mb-3 rounded-xl bg-ink/[0.035] border border-ink/[0.08]"
          >
            <I.Search className="w-4 h-4 text-ink/40 shrink-0" />
            <input
              ref={searchRef}
              type="search"
              value={searchDraft}
              onChange={(e) => setSearchDraft(e.target.value)}
              placeholder="Найти курс…"
              className="flex-1 min-w-0 bg-transparent text-sm outline-none"
              aria-label="Поиск курсов"
            />
          </form>
          <nav className="grid grid-cols-2 gap-1.5" aria-label="Меню">
            {links.map((l) => (
              <button
                key={l.id}
                type="button"
                onClick={() => go(l.id)}
                className={`h-11 rounded-xl text-sm font-semibold transition-colors ${
                  route === l.id
                    ? 'bg-sky-50 text-sky-800 ring-1 ring-sky-200'
                    : 'bg-ink/[0.03] text-ink/75 hover:bg-ink/[0.06]'
                }`}
              >
                {l.label}
              </button>
            ))}
            {session && (
              <>
                <button
                  type="button"
                  onClick={() => go(Routes.PROFILE)}
                  className={`h-11 rounded-xl text-sm font-semibold transition-colors ${
                    route === Routes.PROFILE
                      ? 'bg-sky-50 text-sky-800 ring-1 ring-sky-200'
                      : 'bg-ink/[0.03] text-ink/75 hover:bg-ink/[0.06]'
                  }`}
                >
                  Профиль
                </button>
                <button
                  type="button"
                  onClick={() => go(Routes.PROFILE_EDIT)}
                  className={`h-11 rounded-xl text-sm font-semibold transition-colors ${
                    route === Routes.PROFILE_EDIT
                      ? 'bg-sky-50 text-sky-800 ring-1 ring-sky-200'
                      : 'bg-ink/[0.03] text-ink/75 hover:bg-ink/[0.06]'
                  }`}
                >
                  Настройки
                </button>
                {isMentor && (
                  <button
                    type="button"
                    onClick={() => go(Routes.MENTOR)}
                    className={`h-11 rounded-xl text-sm font-semibold transition-colors ${
                      route === Routes.MENTOR
                        ? 'bg-sky-50 text-sky-800 ring-1 ring-sky-200'
                        : 'bg-ink/[0.03] text-ink/75 hover:bg-ink/[0.06]'
                    }`}
                  >
                    Ментор
                  </button>
                )}
                {isAdmin && (
                  <a href="/admin/" className="h-11 rounded-xl text-sm font-semibold bg-ink/[0.03] text-ink/75 flex items-center justify-center">
                    Школа
                  </a>
                )}
                <button
                  type="button"
                  onClick={handleLogout}
                  className="h-11 rounded-xl text-sm font-semibold text-rose-600 bg-rose-50/80 col-span-2"
                >
                  Выйти
                </button>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

/** Мягкий баннер: пароль / контакты после OAuth + подтверждение почты. */
function RecoveryBanner({ navigate }) {
  const [recovery, setRecovery] = React.useState(null);
  const [me, setMe] = React.useState(null);
  const [dismissed, setDismissed] = React.useState(false);
  const [emailDismissed, setEmailDismissed] = React.useState(false);

  const load = React.useCallback(async () => {
    if (!getAccessToken()) {
      setRecovery(null);
      setMe(null);
      return;
    }
    try {
      const data = await fetchApiJson('/api/users/me/', { auth: true });
      setMe(data);
      setRecovery(data.recovery || null);
      if (data.public_id) {
        try {
          localStorage.removeItem(`ba_recovery_snooze:${data.public_id}`);
          const until = localStorage.getItem(`ba_email_verify_snooze:${data.public_id}`);
          if (until && Number(until) > Date.now()) setEmailDismissed(true);
          else setEmailDismissed(false);
        } catch (_) { /* ignore */ }
      }
    } catch (_) {
      setRecovery(null);
      setMe(null);
    }
  }, []);

  React.useEffect(() => {
    load();
    const onAuth = () => {
      setDismissed(false);
      load();
    };
    window.addEventListener('auth-changed', onAuth);
    return () => window.removeEventListener('auth-changed', onAuth);
  }, [load]);

  const needsEmailVerify = !!(me?.email && !me?.email_verified && !emailDismissed);
  const needsRecovery = !dismissed && !!recovery?.needs_setup;

  if (!needsRecovery && !needsEmailVerify) {
    return null;
  }

  const hint = needsRecovery
    ? ((!recovery.has_email && !recovery.has_phone)
      ? 'Лучше указать и почту, и телефон — так надёжнее. Достаточно и одного.'
      : (!recovery.has_email || !recovery.has_phone)
        ? 'Можно добавить ещё один контакт — так безопаснее.'
        : '')
    : '';

  const onLater = () => setDismissed(true);
  const onEmailLater = () => {
    setEmailDismissed(true);
    if (me?.public_id) {
      try {
        localStorage.setItem(
          `ba_email_verify_snooze:${me.public_id}`,
          String(Date.now() + 7 * 24 * 60 * 60 * 1000),
        );
      } catch (_) { /* ignore */ }
    }
  };

  return (
    <>
      {needsRecovery ? (
        <div
          role="region"
          aria-label="Восстановление доступа"
          className="border-b border-amber-200/80 bg-amber-50/95 text-ink"
        >
          <div className="max-w-7xl mx-auto px-5 sm:px-8 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold">Добавь пароль на всякий случай</div>
              <p className="text-xs sm:text-sm text-ink/65 mt-0.5">
                Тогда сможешь войти и без VK или Яндекса. Можно сделать позже.
                {hint ? <> {hint}</> : null}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => navigate(Routes.PROFILE_EDIT)}
                className="h-9 px-4 rounded-xl text-sm font-semibold btn-grad text-white inline-flex items-center justify-center w-auto shrink-0 whitespace-nowrap"
              >
                Задать пароль
              </button>
              <button
                type="button"
                onClick={onLater}
                className="h-9 px-3 rounded-xl text-sm font-semibold text-ink/60 hover:bg-black/[0.04] shrink-0"
              >
                Позже
              </button>
              <button
                type="button"
                onClick={onLater}
                aria-label="Закрыть"
                className="w-9 h-9 rounded-xl text-ink/45 hover:bg-black/[0.04] text-lg leading-none shrink-0"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      ) : null}
      {needsEmailVerify ? (
        <div
          role="region"
          aria-label="Подтверждение почты"
          className="border-b border-sky-200/80 bg-sky-50/95 text-ink"
        >
          <div className="max-w-7xl mx-auto px-5 sm:px-8 py-3 flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold">Подтверди почту</div>
              <p className="text-xs sm:text-sm text-ink/65 mt-0.5">
                Пришлём код на {me.email}. Так можно восстановить пароль, если забудешь.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => navigate(Routes.PROFILE_EDIT)}
                className="h-9 px-4 rounded-xl text-sm font-semibold btn-grad text-white inline-flex items-center justify-center w-auto shrink-0 whitespace-nowrap"
              >
                Подтвердить
              </button>
              <button
                type="button"
                onClick={onEmailLater}
                className="h-9 px-3 rounded-xl text-sm font-semibold text-ink/60 hover:bg-black/[0.04] shrink-0"
              >
                Позже
              </button>
              <button
                type="button"
                onClick={onEmailLater}
                aria-label="Закрыть"
                className="w-9 h-9 rounded-xl text-ink/45 hover:bg-black/[0.04] text-lg leading-none shrink-0"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
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
            <a className="w-10 h-10 rounded-xl bg-black/[0.04] hover:bg-violet-500/10 hover:text-violet-600 flex items-center justify-center transition-colors text-ink/60" href="#"><I.VK className="w-4 h-4" /></a>
            <a className="w-10 h-10 rounded-xl bg-black/[0.04] hover:bg-violet-500/10 hover:text-violet-600 flex items-center justify-center transition-colors text-ink/60" href="#"><I.Mail className="w-4 h-4" /></a>
          </div>
        </div>
        <FooterCol title="Учёба" items={[
        { label: 'Каталог курсов', onClick: () => navigate(Routes.CATALOG) },
        { label: 'Python-интерпретатор', onClick: () => navigate(Routes.PLAYGROUND) },
        { label: 'Доска', onClick: () => navigate(Routes.WHITEBOARD) },
        { label: 'Тариф Про', onClick: () => navigate(Routes.PRO) },
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
  sanitizeHtml,
  useHashRoute,
  useAppRoute,
  getApiBase,
  getWsBase,
  getAccessToken,
  getRefreshToken,
  hasAuthSession,
  isRememberAuth,
  setAuthTokens,
  clearAuthTokens,
  brandIconUrl,
  openChatThreadWs,
  openChatWithUser,
  openChatWithCourse,
  fetchChatUnreadTotal,
  refreshChatUnread,
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
  currentUserPublicId,
  notifyAuthChanged,
  buildLearnQuery,
  buildExamQuery,
  openStudentProfile,
  createConference,
  openConferenceCall,
  goAfterCall,
  consumeCallReturnPath,
  formatCallDuration,
  formatFileSize,
  ConfirmDialog,
  AppNoticeHost,
  LessonAttachments,
  consumeLessonBoardImport,
  enableWebPushNotifications,
  fetchConferenceWhiteboard,
  fetchNotifications,
  WhiteboardPreviewModal,
  VideoExplanation,
  LessonInstructorNote,
  LessonUserComments,
  LessonDiscussionSection,
  scrollToLessonReferenceSolution,
  hasReferenceSolutionMaterial,
  computeSolutionUnlocked,
  SOLUTION_FAIL_THRESHOLD,
  mapApiCourseToCard,
  mapApiCourseToCourse,
  mapApiModules,
  MODULE_ICONS,
  I,
  NotificationBell,
  TopNav,
  RecoveryBanner,
  Footer,
  CourseCover,
  CourseCard,
  COURSES,
  CATEGORIES,
  FloatingShapes,
  FM,
});
