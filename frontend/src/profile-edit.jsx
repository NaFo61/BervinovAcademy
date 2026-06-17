// PROFILE EDIT — изменение имени, био и аватара

const I = window.I;
const FM = window.FM;
const Routes = window.Routes;

function ProfileEditPage({ navigate }) {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [firstName, setFirstName] = React.useState('');
  const [lastName, setLastName] = React.useState('');
  const [bio, setBio] = React.useState('');
  const [avatarFile, setAvatarFile] = React.useState(null);
  const [avatarPreview, setAvatarPreview] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [saveError, setSaveError] = React.useState('');
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      setLoading(false);
      setError('no_token');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await window.apiJson('/api/users/me/', { auth: true });
        if (cancelled) return;
        setUser(data);
        setFirstName(data.first_name || '');
        setLastName(data.last_name || '');
        setBio(data.bio || '');
        setAvatarPreview(data.avatar ? window.mediaUrl(data.avatar) : '');
        setError('');
      } catch (e) {
        if (!cancelled) setError(e.status === 401 ? 'auth' : (e.message || 'load'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  React.useEffect(() => {
    if (!avatarFile) return;
    const url = URL.createObjectURL(avatarFile);
    setAvatarPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [avatarFile]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaveError('');
    setSaved(false);
    if (!firstName.trim() || !lastName.trim()) {
      setSaveError('Укажи имя и фамилию.');
      return;
    }
    setSaving(true);
    try {
      let data;
      if (avatarFile) {
        const fd = new FormData();
        fd.append('first_name', firstName.trim());
        fd.append('last_name', lastName.trim());
        fd.append('bio', bio.trim());
        fd.append('avatar', avatarFile);
        data = await window.fetchApiForm('/api/users/me/', fd, { method: 'PATCH', auth: true });
      } else {
        data = await window.apiJson('/api/users/me/', {
          method: 'PATCH',
          auth: true,
          body: {
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            bio: bio.trim(),
          },
        });
      }
      setUser(data);
      setSaved(true);
      window.notifyAuthChanged();
      setTimeout(() => navigate(Routes.PROFILE), 700);
    } catch (err) {
      setSaveError(err.message || 'Не удалось сохранить');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3 text-ink/60">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем профиль…</div>
      </div>
    );
  }

  if (error === 'no_token' || error === 'auth') {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <p className="text-sm text-ink/60 mt-2">Войди, чтобы редактировать профиль.</p>
        <button type="button" onClick={() => navigate(Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold">
          Перейти ко входу
        </button>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Не удалось загрузить</div>
        <p className="text-sm text-ink/60 mt-2">{error || 'Ошибка'}</p>
      </div>
    );
  }

  const initials = ((firstName || '').charAt(0) + (lastName || '').charAt(0)).toUpperCase() || '?';

  return (
    <div data-screen-label="Profile Edit" className="min-h-screen pb-16 mesh-bg-dim">
      <div className="max-w-xl mx-auto px-5 sm:px-8 py-10">
        <button type="button" onClick={() => navigate(Routes.PROFILE)}
          className="inline-flex items-center gap-1.5 text-sm text-ink/60 hover:text-violet-600 transition-colors mb-8">
          <I.ChevronRight className="w-4 h-4 rotate-180"/> Назад в профиль
        </button>

        <h1 className="text-3xl font-extrabold tracking-tight">Редактирование профиля</h1>
        <p className="text-sm text-ink/60 mt-2">Имя, фамилия, о себе и фото — видны в публичном профиле.</p>

        <form onSubmit={handleSubmit} className="mt-8 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row items-center gap-5">
            <div className="avatar-ring shrink-0">
              {avatarPreview ? (
                <img src={avatarPreview} alt="" className="w-24 h-24 rounded-full object-cover bg-white"/>
              ) : (
                <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center text-3xl font-extrabold grad-text">
                  {initials}
                </div>
              )}
            </div>
            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold uppercase tracking-widest text-ink/55 mb-2">
                Аватар
              </label>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => setAvatarFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-ink/70 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-violet-500/10 file:text-violet-700 hover:file:bg-violet-500/15"
              />
              <p className="text-xs text-ink/45 mt-1.5">JPG, PNG или WebP</p>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Имя" value={firstName} onChange={setFirstName} required />
            <Field label="Фамилия" value={lastName} onChange={setLastName} required />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-ink/55 mb-2">
              О себе
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={4}
              maxLength={500}
              placeholder="Кратко о себе, целях обучения…"
              className="w-full rounded-xl border border-black/[0.08] px-4 py-3 text-sm resize-y min-h-[100px] ring-grad"
            />
            <p className="text-xs text-ink/45 mt-1 text-right">{bio.length}/500</p>
          </div>

          <div className="rounded-xl bg-black/[0.03] px-4 py-3 text-sm text-ink/60 space-y-1">
            {user.email && <div><span className="text-ink/45">Email: </span>{user.email}</div>}
            {user.phone && <div><span className="text-ink/45">Телефон: </span>{user.phone}</div>}
            <p className="text-xs text-ink/45 pt-1">Контакты пока нельзя изменить здесь.</p>
          </div>

          {saveError && (
            <p className="text-sm text-red-600 bg-red-50 rounded-xl px-4 py-3">{saveError}</p>
          )}
          {saved && (
            <p className="text-sm text-emerald-700 bg-emerald-50 rounded-xl px-4 py-3">Сохранено. Возвращаемся в профиль…</p>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <button type="submit" disabled={saving}
              className="h-11 px-6 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold disabled:opacity-60">
              {saving ? 'Сохраняем…' : 'Сохранить'}
            </button>
            <button type="button" onClick={() => navigate(Routes.PROFILE)}
              className="h-11 px-6 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold hover:border-violet-300">
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, required }) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-widest text-ink/55 mb-2">
        {label}{required ? ' *' : ''}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className="w-full h-11 rounded-xl border border-black/[0.08] px-4 text-sm ring-grad"
      />
    </div>
  );
}

window.ProfileEditPage = ProfileEditPage;
