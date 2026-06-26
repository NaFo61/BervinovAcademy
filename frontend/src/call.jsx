// CALL page — видеоконференция через LiveKit

const Routes = window.Routes;
const I = window.I;

const STATUS_LABELS = {
  waiting: 'Ожидание',
  active: 'Идёт',
  completed: 'Завершена',
  declined: 'Отклонена',
  cancelled: 'Отменена',
  expired: 'Истекла',
};

const WHITEBOARD_TILE_KEY = 'shared:whiteboard';
const WHITEBOARD_DATA_TOPIC = 'whiteboard_visibility';

function isWhiteboardFeatureEnabled() {
  if (typeof document === 'undefined') return false;
  const meta = document.querySelector('meta[name="whiteboard-enabled"]');
  return meta?.getAttribute('content') !== 'false';
}

const WHITEBOARD_FEATURE_ENABLED = isWhiteboardFeatureEnabled();

function participantName(p) {
  if (!p) return 'Участник';
  if (typeof p.name === 'string' && p.name.trim()) return p.name.trim();
  return [p.first_name, p.last_name].filter(Boolean).join(' ').trim() || 'Участник';
}

function trackId(pub, participant, suffix) {
  return [
    participant?.identity || (participant?.isLocal ? 'local' : 'unknown'),
    pub?.source || suffix || 'media',
    pub?.trackSid || pub?.sid || pub?.track?.sid || '',
  ].join(':');
}

function isVideoPublication(pub, LK) {
  const kind = pub?.kind || pub?.track?.kind;
  return kind === LK.Track.Kind.Video || kind === 'video';
}

function isAudioPublication(pub, LK) {
  const kind = pub?.kind || pub?.track?.kind;
  return kind === LK.Track.Kind.Audio || kind === 'audio';
}

function isScreenPublication(pub, LK) {
  return pub?.source === LK.Track.Source.ScreenShare || pub?.source === 'screen_share';
}

function publicationsOf(participant) {
  if (!participant?.trackPublications) return [];
  return Array.from(participant.trackPublications.values());
}

function buildTiles(room, LK) {
  if (!room || !LK) return { tiles: [], audioPubs: [] };
  const participants = [
    room.localParticipant,
    ...Array.from(room.remoteParticipants?.values?.() || []),
  ].filter(Boolean);
  const tiles = [];
  const audioPubs = [];

  participants.forEach((participant) => {
    const pubs = publicationsOf(participant);
    const videoPubs = pubs.filter((pub) => pub?.track && isVideoPublication(pub, LK));
    pubs
      .filter((pub) => !participant.isLocal && pub?.track && isAudioPublication(pub, LK))
      .forEach((pub) => audioPubs.push({ key: trackId(pub, participant, 'audio'), pub }));

    if (videoPubs.length === 0) {
      tiles.push({
        key: `${participant.identity || 'local'}:placeholder`,
        participant,
        publication: null,
        isLocal: Boolean(participant.isLocal),
        isScreen: false,
        label: participant.isLocal ? 'Вы' : participantName(participant),
        placeholder: true,
      });
      return;
    }

    videoPubs.forEach((pub) => {
      const screen = isScreenPublication(pub, LK);
      tiles.push({
        key: trackId(pub, participant, screen ? 'screen' : 'camera'),
        participant,
        publication: pub,
        isLocal: Boolean(participant.isLocal),
        isScreen: screen,
        label: screen
          ? `${participant.isLocal ? 'Ваша' : participantName(participant)} демонстрация`
          : (participant.isLocal ? 'Вы' : participantName(participant)),
        placeholder: false,
      });
    });
  });

  return { tiles, audioPubs };
}

function publishWhiteboardVisibility(room, LK, enabled) {
  if (!room?.localParticipant) return;
  const payload = new TextEncoder().encode(JSON.stringify({ enabled: Boolean(enabled) }));
  try {
    room.localParticipant.publishData(payload, { reliable: true, topic: WHITEBOARD_DATA_TOPIC });
    return;
  } catch (_) { /* older LiveKit signature */ }
  try {
    room.localParticipant.publishData(payload, LK?.DataPacket_Kind?.RELIABLE, { topic: WHITEBOARD_DATA_TOPIC });
  } catch (_) { /* best-effort UI sync */ }
}

function MediaTrack({ publication, muted = false, fit = 'cover' }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    const track = publication?.track;
    const node = ref.current;
    if (!track || !node) return undefined;
    const el = track.attach();
    el.autoplay = true;
    el.playsInline = true;
    el.muted = muted;
    el.className = `w-full h-full ${fit === 'contain' ? 'object-contain' : 'object-cover'}`;
    node.innerHTML = '';
    node.appendChild(el);
    if (el.play) el.play().catch(() => {});
    return () => {
      track.detach(el);
      el.remove();
    };
  }, [publication?.trackSid, publication?.track?.sid, muted, fit]);

  return <div ref={ref} className="absolute inset-0" />;
}

function AudioTrack({ publication }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    const track = publication?.track;
    const node = ref.current;
    if (!track || !node) return undefined;
    const el = track.attach();
    el.autoplay = true;
    node.innerHTML = '';
    node.appendChild(el);
    if (el.play) el.play().catch(() => {});
    return () => {
      track.detach(el);
      el.remove();
    };
  }, [publication?.trackSid, publication?.track?.sid]);

  return <div ref={ref} className="hidden" aria-hidden />;
}

function CallPage({ navigate, hashParams }) {
  const WhiteboardPreviewModal = window.WhiteboardPreviewModal;
  const confId = hashParams?.get('conf') || null;
  const [phase, setPhase] = React.useState('loading');
  const [error, setError] = React.useState('');
  const [conference, setConference] = React.useState(null);
  const [muted, setMuted] = React.useState(false);
  const [videoOff, setVideoOff] = React.useState(false);
  const [sharing, setSharing] = React.useState(false);
  const [whiteboardEnabled, setWhiteboardEnabled] = React.useState(WHITEBOARD_FEATURE_ENABLED);
  const [mediaWarning, setMediaWarning] = React.useState('');
  const [isMentor, setIsMentor] = React.useState(false);
  const [layoutTick, setLayoutTick] = React.useState(0);
  const [selectedTileKey, setSelectedTileKey] = React.useState(null);
  const [displayMode, setDisplayMode] = React.useState('focus');
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const [whiteboardSyncToken, setWhiteboardSyncToken] = React.useState('');
  const [whiteboardLicenseKey, setWhiteboardLicenseKey] = React.useState('');
  const [whiteboardNotice, setWhiteboardNotice] = React.useState('');
  const [whiteboardSaving, setWhiteboardSaving] = React.useState(false);
  const [whiteboardSaved, setWhiteboardSaved] = React.useState(false);
  const [endedWhiteboard, setEndedWhiteboard] = React.useState(null);
  const [showEndedPreview, setShowEndedPreview] = React.useState(false);
  const [chatOpen, setChatOpen] = React.useState(true);
  const [chatThread, setChatThread] = React.useState(null);
  const [chatLoadError, setChatLoadError] = React.useState('');
  const [callChatUnread, setCallChatUnread] = React.useState(0);
  const [callWhiteboardPreview, setCallWhiteboardPreview] = React.useState(null);

  const ChatThreadView = window.ChatThreadView;

  const callRootRef = React.useRef(null);
  const roomRef = React.useRef(null);
  const endSentRef = React.useRef(false);
  const whiteboardEnabledRef = React.useRef(true);
  const LK = window.LivekitClient || window.LiveKit;

  const bumpLayout = React.useCallback(() => {
    setLayoutTick((v) => v + 1);
  }, []);

  React.useEffect(() => {
    whiteboardEnabledRef.current = whiteboardEnabled;
  }, [whiteboardEnabled]);

  React.useEffect(() => {
    if (!confId || phase !== 'in_call') {
      setChatThread(null);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      setChatLoadError('');
      try {
        const thread = await window.fetchApiJson(
          `/api/communication/chat/threads/open/?conference=${encodeURIComponent(confId)}`,
          { auth: true },
        );
        if (!cancelled) setChatThread(thread);
      } catch (e) {
        if (!cancelled) {
          setChatThread(null);
          setChatLoadError(e.message || 'Не удалось открыть чат');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [confId, phase]);

  React.useEffect(() => {
    if (phase !== 'in_call') return undefined;
    const onKey = (event) => {
      if (event.key === 'Escape' && chatOpen) setChatOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [phase, chatOpen]);

  React.useEffect(() => {
    if (chatOpen) setCallChatUnread(0);
  }, [chatOpen]);

  React.useEffect(() => {
    if (!confId) return undefined;
    const stored = localStorage.getItem(`call-chat-open-${confId}`);
    if (stored === '0') setChatOpen(false);
    return undefined;
  }, [confId]);

  React.useEffect(() => {
    if (!confId) return undefined;
    localStorage.setItem(`call-chat-open-${confId}`, chatOpen ? '1' : '0');
    return undefined;
  }, [confId, chatOpen]);

  React.useEffect(() => {
    if (!WHITEBOARD_FEATURE_ENABLED || !confId || phase !== 'in_call') {
      setWhiteboardSyncToken('');
      setWhiteboardLicenseKey('');
      return undefined;
    }

    let cancelled = false;
    let timerId = null;

    const fetchToken = async () => {
      try {
        const data = await window.fetchApiJson(
          `/api/communication/conferences/${encodeURIComponent(confId)}/whiteboard/token/`,
          { method: 'POST', auth: true },
        );
        if (!cancelled) {
          setWhiteboardSyncToken(data.token || '');
          setWhiteboardLicenseKey(data.license_key || '');
        }
      } catch (_) {
        if (!cancelled) {
          setWhiteboardSyncToken('');
          setWhiteboardLicenseKey('');
        }
      }
    };

    fetchToken();
    timerId = setInterval(fetchToken, 50 * 60 * 1000);

    return () => {
      cancelled = true;
      if (timerId) clearInterval(timerId);
    };
  }, [confId, phase]);

  React.useEffect(() => {
    if (!whiteboardNotice) return undefined;
    const timerId = setTimeout(() => setWhiteboardNotice(''), 4000);
    return () => clearTimeout(timerId);
  }, [whiteboardNotice]);

  const saveWhiteboard = React.useCallback(async () => {
    if (!confId || whiteboardSaving) return;
    const api = window.BervinovWhiteboard;
    if (!api?.exportPngBlob) {
      setWhiteboardNotice('Доска ещё не загружена');
      return;
    }
    setWhiteboardSaving(true);
    try {
      const blob = await api.exportPngBlob();
      const form = new FormData();
      form.append('image', blob, 'whiteboard.png');
      if (api.exportSnapshotJson) {
        try {
          const snapshot = api.exportSnapshotJson();
          form.append('snapshot', JSON.stringify(snapshot));
        } catch (_) { /* snapshot optional */ }
      }
      await window.fetchApiForm(
        `/api/communication/conferences/${encodeURIComponent(confId)}/whiteboard/export/`,
        form,
        { method: 'POST', auth: true },
      );
      setWhiteboardSaved(true);
      setWhiteboardNotice('Конспект сохранён');
    } catch (err) {
      setWhiteboardNotice(err?.message || 'Не удалось сохранить доску');
    } finally {
      setWhiteboardSaving(false);
    }
  }, [confId, whiteboardSaving]);

  React.useEffect(() => {
    if (phase !== 'ended' || !confId) {
      setEndedWhiteboard(null);
      setShowEndedPreview(false);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await window.fetchConferenceWhiteboard(confId);
        if (!cancelled) setEndedWhiteboard(data);
      } catch (_) {
        if (!cancelled) setEndedWhiteboard(null);
      }
    })();
    return () => { cancelled = true; };
  }, [phase, confId]);

  React.useEffect(() => {
    const syncFullscreen = () => {
      setIsFullscreen(document.fullscreenElement === callRootRef.current);
    };
    document.addEventListener('fullscreenchange', syncFullscreen);
    return () => document.removeEventListener('fullscreenchange', syncFullscreen);
  }, []);

  const cleanupRoom = React.useCallback(async () => {
    const room = roomRef.current;
    roomRef.current = null;
    if (room) {
      try {
        await room.disconnect();
      } catch (_) { /* ignore */ }
    }
  }, []);

  const notifyLeave = React.useCallback((keepalive = false) => {
    if (!confId || endSentRef.current) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      window.fetch(
        `${window.getApiBase()}/api/communication/conferences/${encodeURIComponent(confId)}/leave/`,
        {
          method: 'POST',
          headers: { Authorization: 'Bearer ' + token },
          keepalive,
        },
      ).catch(() => {});
    } catch (_) { /* ignore */ }
  }, [confId]);

  React.useEffect(() => {
    if (!confId) {
      setPhase('error');
      setError('Не указана конференция');
      return undefined;
    }
    if (!localStorage.getItem('access_token')) {
      setPhase('auth');
      return undefined;
    }
    if (!LK) {
      setPhase('error');
      setError('LiveKit SDK не загружен');
      return undefined;
    }

    let cancelled = false;
    (async () => {
      setPhase('loading');
      setError('');
      try {
        const join = await window.fetchApiJson(
          `/api/communication/conferences/${encodeURIComponent(confId)}/join/`,
          { method: 'POST', auth: true },
        );
        if (cancelled) return;

        const payload = window.parseJwtPayload(localStorage.getItem('access_token') || '');
        const mentor = join.conference?.mentor?.public_id === payload.public_id;
        const room = new LK.Room({ adaptiveStream: true, dynacast: true });
        roomRef.current = room;
        setConference(join.conference);
        setIsMentor(mentor);

        const events = [
          LK.RoomEvent.ParticipantConnected,
          LK.RoomEvent.ParticipantDisconnected,
          LK.RoomEvent.TrackSubscribed,
          LK.RoomEvent.TrackUnsubscribed,
          LK.RoomEvent.TrackPublished,
          LK.RoomEvent.TrackUnpublished,
          LK.RoomEvent.LocalTrackPublished,
          LK.RoomEvent.LocalTrackUnpublished,
          LK.RoomEvent.ActiveSpeakersChanged,
        ].filter(Boolean);
        events.forEach((eventName) => room.on(eventName, bumpLayout));
        if (LK.RoomEvent.DataReceived) {
          room.on(LK.RoomEvent.DataReceived, (payload, participant, kind, topic) => {
            if (topic !== WHITEBOARD_DATA_TOPIC) return;
            try {
              const text = new TextDecoder().decode(payload);
              const data = JSON.parse(text);
              setWhiteboardEnabled(Boolean(data.enabled));
              if (!data.enabled) {
                setSelectedTileKey((key) => (key === WHITEBOARD_TILE_KEY ? null : key));
              }
              bumpLayout();
            } catch (_) { /* ignore malformed data packets */ }
          });
        }
        if (LK.RoomEvent.ParticipantConnected) {
          room.on(LK.RoomEvent.ParticipantConnected, () => {
            if (mentor) publishWhiteboardVisibility(room, LK, whiteboardEnabledRef.current);
          });
        }
        room.on(LK.RoomEvent.Disconnected, () => {
          if (!cancelled) setPhase('ended');
        });

        await room.connect(join.livekit_url, join.token);
        if (cancelled) {
          await room.disconnect();
          return;
        }

        const warnings = [];
        try {
          await room.localParticipant.setMicrophoneEnabled(true);
          setMuted(false);
        } catch (_) {
          warnings.push('Микрофон недоступен');
          setMuted(true);
        }
        try {
          await room.localParticipant.setCameraEnabled(true);
          setVideoOff(false);
        } catch (_) {
          warnings.push('Камера недоступна — можно участвовать без своего видео');
          setVideoOff(true);
        }
        if (warnings.length) setMediaWarning(warnings.join(' · '));
        setPhase('in_call');
        bumpLayout();
      } catch (e) {
        if (!cancelled) {
          setPhase('error');
          const msg = e?.message || 'Не удалось подключиться';
          setError(/device in use/i.test(msg)
            ? 'Камера или микрофон заняты другим окном. Закройте первый созвон или подключитесь без камеры.'
            : msg);
        }
      }
    })();

    return () => {
      cancelled = true;
      notifyLeave(true);
      cleanupRoom();
    };
  }, [confId, cleanupRoom, bumpLayout, notifyLeave, LK]);

  React.useEffect(() => {
    if (!isMentor || phase !== 'in_call') return undefined;
    const onBeforeUnload = (event) => {
      event.preventDefault();
      event.returnValue = 'Вы покинете созвон. Завершить его можно кнопкой внутри звонка.';
      return event.returnValue;
    };
    const onPageHide = () => notifyLeave(true);
    window.addEventListener('beforeunload', onBeforeUnload);
    window.addEventListener('pagehide', onPageHide);
    return () => {
      window.removeEventListener('beforeunload', onBeforeUnload);
      window.removeEventListener('pagehide', onPageHide);
    };
  }, [isMentor, phase, notifyLeave]);

  const leaveCall = async () => {
    setPhase('ending');
    try {
      await window.fetchApiJson(
        `/api/communication/conferences/${encodeURIComponent(confId)}/leave/`,
        { method: 'POST', auth: true },
      );
    } catch (_) { /* ignore */ }
    await cleanupRoom();
    setPhase('ended');
  };

  const finishCall = async () => {
    if (!isMentor) return leaveCall();
    if (whiteboardEnabled && !whiteboardSaved) {
      const saveFirst = window.confirm(
        'Сохранить доску как конспект перед завершением созвона?',
      );
      if (saveFirst) {
        await saveWhiteboard();
      }
    }
    if (!window.confirm('Завершить конференцию для всех участников?')) return;
    setPhase('ending');
    try {
      endSentRef.current = true;
      await window.fetchApiJson(
        `/api/communication/conferences/${encodeURIComponent(confId)}/end/`,
        { method: 'POST', auth: true },
      );
    } catch (_) { /* ignore */ }
    await cleanupRoom();
    setPhase('ended');
  };

  const toggleMute = async () => {
    const room = roomRef.current;
    if (!room) return;
    const next = !muted;
    await room.localParticipant.setMicrophoneEnabled(!next);
    setMuted(next);
    bumpLayout();
  };

  const toggleVideo = async () => {
    const room = roomRef.current;
    if (!room) return;
    const next = !videoOff;
    await room.localParticipant.setCameraEnabled(!next);
    setVideoOff(next);
    bumpLayout();
  };

  const toggleScreen = async () => {
    const room = roomRef.current;
    if (!room) return;
    const next = !sharing;
    await room.localParticipant.setScreenShareEnabled(next);
    setSharing(next);
    bumpLayout();
  };

  const toggleWhiteboard = () => {
    if (!isMentor) return;
    const room = roomRef.current;
    const next = !whiteboardEnabled;
    setWhiteboardEnabled(next);
    if (!next) {
      setSelectedTileKey((key) => (key === WHITEBOARD_TILE_KEY ? null : key));
    } else {
      setSelectedTileKey(WHITEBOARD_TILE_KEY);
      setDisplayMode('focus');
    }
    if (room) publishWhiteboardVisibility(room, LK, next);
    bumpLayout();
  };

  const selectTile = React.useCallback((tileKey) => {
    setSelectedTileKey(tileKey);
    setDisplayMode('focus');
    bumpLayout();
  }, [bumpLayout]);

  const toggleFullscreen = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await callRootRef.current?.requestFullscreen();
    } catch (_) { /* ignore */ }
  };

  if (phase === 'auth') {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <button type="button" onClick={() => navigate(Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          Войти
        </button>
      </div>
    );
  }

  if (phase === 'loading' || phase === 'ending') {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3 text-ink/60">
        <span className="w-10 h-10 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">{phase === 'ending' ? 'Завершаем…' : 'Подключаемся…'}</div>
      </div>
    );
  }

  if (phase === 'ended') {
    const endedTitle = conference
      ? `${participantName(conference.mentor)} ↔ ${participantName(conference.guest)}`
      : '';
    return (
      <div className="max-w-lg mx-auto px-5 py-20 text-center">
        {showEndedPreview && endedWhiteboard?.image_url && WhiteboardPreviewModal && (
          <WhiteboardPreviewModal
            conferenceId={confId}
            title={endedTitle}
            onClose={() => setShowEndedPreview(false)}
          />
        )}
        <div className="text-2xl font-bold">Созвон завершён</div>
        <p className="text-sm text-ink/60 mt-2">Спасибо за встречу!</p>
        {endedWhiteboard?.image_url && (
          <div className="mt-6 text-left">
            <div className="text-xs font-semibold uppercase tracking-widest text-ink/45 mb-2">
              Конспект доски
            </div>
            <button type="button" onClick={() => setShowEndedPreview(true)}
              className="block w-full rounded-2xl overflow-hidden ring-1 ring-black/[0.08] bg-white hover:ring-violet-300 transition-shadow">
              <img src={endedWhiteboard.image_url} alt="Конспект доски"
                className="w-full h-auto max-h-56 object-contain bg-slate-50"/>
            </button>
            <button type="button" onClick={() => setShowEndedPreview(true)}
              className="mt-3 h-10 px-4 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
              Открыть конспект
            </button>
          </div>
        )}
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <button type="button" onClick={() => navigate(Routes.CONFERENCES)}
            className="h-11 px-6 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
            История созвонов
          </button>
          <button type="button" onClick={() => navigate(Routes.PROFILE)}
            className="h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
            В профиль
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className="max-w-lg mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Не удалось подключиться</div>
        <p className="text-sm text-ink/60 mt-2">{error}</p>
        <button type="button" onClick={() => navigate(Routes.CONFERENCES)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          К истории
        </button>
      </div>
    );
  }

  const { tiles: mediaTiles, audioPubs } = buildTiles(roomRef.current, LK);
  const whiteboardTile = whiteboardEnabled ? {
    key: WHITEBOARD_TILE_KEY,
    type: 'whiteboard',
    label: 'Общая доска',
    isLocal: false,
    isScreen: false,
    placeholder: false,
  } : null;
  const visibleTiles = whiteboardTile ? [...mediaTiles, whiteboardTile] : mediaTiles;
  const screenTile = visibleTiles.find((tile) => tile.isScreen && !tile.placeholder);
  const selectedTile = visibleTiles.find((tile) => tile.key === selectedTileKey);
  const mainTile = selectedTile || screenTile || visibleTiles.find((tile) => !tile.isLocal && !tile.placeholder) || visibleTiles[0];
  const sideTiles = visibleTiles.filter((tile) => tile.key !== mainTile?.key);
  const isCleanMode = displayMode === 'clean' || isFullscreen;
  const isGridMode = displayMode === 'grid';
  const title = conference
    ? `${participantName(conference.mentor)} ↔ ${participantName(conference.guest)}`
    : 'Созвон';

  return (
    <div ref={callRootRef} data-screen-label="Call"
      className={`${isFullscreen ? 'h-screen max-h-screen' : 'h-[calc(100dvh-4rem)] max-h-[calc(100dvh-4rem)]'} overflow-hidden bg-[#070b18] text-white flex flex-col relative`}>
      {callWhiteboardPreview && WhiteboardPreviewModal && (
        <WhiteboardPreviewModal
          conferenceId={callWhiteboardPreview}
          onClose={() => setCallWhiteboardPreview(null)}
        />
      )}
      {chatThread && ChatThreadView && phase === 'in_call' && (
        <aside className={`absolute inset-y-0 right-0 z-30 w-full sm:w-[min(100%,380px)] shadow-2xl border-l border-white/10 flex flex-col min-h-0 ${
          chatOpen ? '' : 'hidden'
        }`}>
          <ChatThreadView
            thread={chatThread}
            compact
            embedded
            inCall
            navigate={navigate}
            markReadOnView={chatOpen}
            onBack={() => setChatOpen(false)}
            onOpenWhiteboard={(id) => setCallWhiteboardPreview(id)}
            onUnreadMessage={() => setCallChatUnread((n) => n + 1)}
            onMarkedRead={() => {
              setCallChatUnread(0);
              window.refreshChatUnread?.();
            }}
          />
        </aside>
      )}
      {!chatOpen && phase === 'in_call' && !chatThread && chatLoadError && (
        <aside className="absolute inset-y-0 right-0 z-30 w-full sm:w-[min(100%,380px)] bg-[#0a1020] border-l border-white/10 p-4 flex items-center justify-center text-sm text-red-300">
          {chatLoadError}
        </aside>
      )}
      {!isCleanMode && (
        <div className="px-4 sm:px-6 py-3 flex items-center justify-between border-b border-white/10 bg-white/[0.03]">
          <div>
            <div className="font-semibold">{title}</div>
            <div className="text-xs text-white/50">
              {STATUS_LABELS[conference?.status] || 'Созвон'}
              {screenTile ? ' · идёт демонстрация экрана' : ''}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={leaveCall}
              className="h-9 px-4 rounded-lg bg-white/10 hover:bg-white/15 text-sm font-semibold">
              Выйти
            </button>
            {isMentor && (
              <button type="button" onClick={finishCall}
                className="h-9 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-sm font-semibold">
                Завершить для всех
              </button>
            )}
          </div>
        </div>
      )}

      {mediaWarning && !isCleanMode && (
        <div className="mx-4 mt-3 px-4 py-2 rounded-xl bg-amber-500/15 text-amber-100 text-xs border border-amber-400/30">
          {mediaWarning}
        </div>
      )}

      {whiteboardNotice && !isCleanMode && (
        <div className="mx-4 mt-3 px-4 py-2 rounded-xl bg-emerald-500/15 text-emerald-100 text-xs border border-emerald-400/30">
          {whiteboardNotice}
        </div>
      )}

      <div className={`flex-1 min-h-0 overflow-hidden ${isCleanMode ? 'relative p-0' : 'p-3 sm:p-4'}`}>
        {isGridMode ? (
          <div className={`h-full min-h-0 grid auto-rows-fr gap-3 ${visibleTiles.length <= 1 ? 'grid-cols-1' : visibleTiles.length === 2 ? 'md:grid-cols-2' : visibleTiles.length <= 4 ? 'sm:grid-cols-2' : 'sm:grid-cols-2 xl:grid-cols-3'}`}>
            {visibleTiles.map((tile) => (
              <VideoTile
                key={tile.key}
                tile={tile}
                main
                fit="contain"
                roomId={confId}
                syncToken={whiteboardSyncToken}
                licenseKey={whiteboardLicenseKey}
                selected={tile.key === selectedTileKey}
                onSelect={() => selectTile(tile.key)}
                isGridMode
              />
            ))}
          </div>
        ) : (
          <div className={`h-full min-h-0 grid gap-3 ${isCleanMode ? 'grid-cols-1' : sideTiles.length ? 'lg:grid-cols-[minmax(0,1fr)_280px]' : 'grid-cols-1'}`}>
            <VideoTile
              tile={mainTile}
              main
              clean={isCleanMode}
              fit="contain"
              roomId={confId}
              syncToken={whiteboardSyncToken}
              licenseKey={whiteboardLicenseKey}
              isGridMode={false}
              onSelect={() => selectTile(mainTile?.key)}
            />

            {sideTiles.length > 0 && (
              <aside className={isCleanMode
                ? 'absolute right-3 top-3 z-10 flex flex-col gap-2 w-48 max-h-[calc(100%-7rem)] overflow-y-auto'
                : 'grid gap-3 content-start max-h-full overflow-y-auto pr-1'}>
                {sideTiles.map((tile) => (
                  <VideoTile
                    key={tile.key}
                    tile={tile}
                    compact={isCleanMode}
                    clean={isCleanMode}
                    fit="contain"
                    roomId={confId}
                    syncToken={whiteboardSyncToken}
                licenseKey={whiteboardLicenseKey}
                    isGridMode={false}
                    selected={tile.key === selectedTileKey}
                    onSelect={() => selectTile(tile.key)}
                  />
                ))}
              </aside>
            )}
          </div>
        )}
      </div>

      {audioPubs.map((item) => <AudioTrack key={item.key} publication={item.pub} />)}

      <div className={`${isCleanMode ? 'fixed bottom-4 left-1/2 -translate-x-1/2 z-20 rounded-2xl bg-black/45 backdrop-blur-xl px-4 py-3' : 'p-4 pb-6'} flex flex-wrap items-center justify-center gap-3`}>
        <div className="flex items-center gap-1 rounded-full bg-white/10 p-1">
          <ModeButton active={displayMode === 'grid'} onClick={() => setDisplayMode('grid')}>Мозаика</ModeButton>
          <ModeButton active={displayMode === 'focus'} onClick={() => setDisplayMode('focus')}>Важное</ModeButton>
        </div>
        <CallControl label={muted ? 'Вкл. звук' : 'Без звука'} active={muted} onClick={toggleMute}>
          <I.Mic className="w-5 h-5" off={muted} />
        </CallControl>
        <CallControl label={videoOff ? 'Вкл. камеру' : 'Без видео'} active={videoOff} onClick={toggleVideo}>
          <I.Video className="w-5 h-5" off={videoOff} />
        </CallControl>
        <CallControl label={sharing ? 'Стоп экран' : 'Экран'} active={sharing} onClick={toggleScreen}>
          <I.Monitor className="w-5 h-5" />
        </CallControl>
        <CallControl label={chatOpen ? 'Скрыть чат' : 'Чат'} active={chatOpen} onClick={() => setChatOpen((v) => !v)} badge={callChatUnread}>
          <I.Chat className="w-5 h-5" />
        </CallControl>
        {WHITEBOARD_FEATURE_ENABLED && isMentor && whiteboardEnabled && (
          <CallControl
            label={whiteboardSaving ? 'Сохранение…' : 'Сохранить доску'}
            active={whiteboardSaving}
            onClick={saveWhiteboard}
          >
            <I.Check className="w-5 h-5" />
          </CallControl>
        )}
        {WHITEBOARD_FEATURE_ENABLED && isMentor && (
          <CallControl label={whiteboardEnabled ? 'Скрыть доску' : 'Доска'} active={whiteboardEnabled} onClick={toggleWhiteboard}>
            <I.Layers className="w-5 h-5" />
          </CallControl>
        )}
        <CallControl label="Полный экран" active={false} onClick={toggleFullscreen}>
          <I.Maximize className="w-5 h-5" />
        </CallControl>
      </div>
    </div>
  );
}

function VideoTile({ tile, main = false, compact = false, clean = false, fit = 'cover', selected = false, onSelect, roomId, syncToken, licenseKey, isGridMode = false }) {
  const base = compact
    ? 'h-28 cursor-pointer'
    : main
      ? 'h-full min-h-0'
      : 'h-36 sm:h-40 cursor-pointer';
  const rounded = clean ? 'rounded-none' : (main ? 'rounded-2xl' : 'rounded-xl');
  const chrome = clean ? 'ring-0 border-0' : 'ring-1 ring-white/10';
  const selectedClass = clean ? '' : (selected ? 'ring-2 ring-cyan-300' : 'hover:ring-white/30');
  const isWhiteboard = tile?.type === 'whiteboard';
  const tileLabel = tile?.label || 'Участник';
  const whiteboardActive = isWhiteboard && main && !isGridMode;
  const shellClass = `relative block text-left overflow-hidden bg-[#111827] ${chrome} ${selectedClass} ${rounded} ${base} ${
    whiteboardActive ? '' : 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-300'
  }`;

  if (isWhiteboard) {
    if (whiteboardActive) {
      return (
        <div className={shellClass} aria-label={tileLabel}>
          <WhiteboardTile roomId={roomId} syncToken={syncToken} licenseKey={licenseKey} />
          {!clean && (
            <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 to-transparent pointer-events-none z-10">
              <div className="flex items-center gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-white text-slate-900">доска</span>
                <span className={`${main ? 'text-sm' : 'text-xs'} font-semibold truncate`}>{tileLabel}</span>
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <button
        type="button"
        className={shellClass}
        onClick={onSelect}
        aria-label={`Показать: ${tileLabel}`}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-white to-slate-100 text-slate-700 gap-2 px-3 text-center">
          <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center">
            <I.Layers className="w-5 h-5" />
          </div>
          <div className="text-xs font-semibold">Общая доска</div>
          <div className="text-[10px] text-slate-500">Нажмите, чтобы открыть</div>
        </div>
        {!clean && (
          <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 to-transparent pointer-events-none z-10">
            <div className="flex items-center gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded bg-white text-slate-900">доска</span>
              <span className={`${main ? 'text-sm' : 'text-xs'} font-semibold truncate`}>{tileLabel}</span>
            </div>
          </div>
        )}
      </button>
    );
  }

  return (
    <button type="button" onClick={onSelect} aria-label={`Показать: ${tileLabel}`}
      className={shellClass}>
      {tile?.publication && !tile.placeholder ? (
        <MediaTrack publication={tile.publication} muted={tile.isLocal} fit={fit} />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
          <div className="flex flex-col items-center gap-3 px-4 text-center">
            <div className={`${main ? 'w-24 h-24 text-3xl' : 'w-12 h-12 text-base'} rounded-full bg-white/10 flex items-center justify-center font-bold`}>
              {(tile?.label || 'У').slice(0, 1).toUpperCase()}
            </div>
            {main && (
              <div>
                <div className="text-xl sm:text-2xl font-bold">{tile?.label || 'Участник'}</div>
                <div className="text-sm text-white/45 mt-1">Камера выключена</div>
              </div>
            )}
          </div>
        </div>
      )}
      {!clean && <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 to-transparent">
        <div className="flex items-center gap-2">
          {tile?.isScreen && <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-400/20 text-cyan-100">экран</span>}
          {isWhiteboard && <span className="text-[10px] px-2 py-0.5 rounded bg-white text-slate-900">доска</span>}
          <span className={`${main ? 'text-sm' : 'text-xs'} font-semibold truncate`}>{tile?.label || 'Участник'}</span>
        </div>
      </div>}
    </button>
  );
}

function WhiteboardTile({ roomId, syncToken, licenseKey }) {
  const hostRef = React.useRef(null);

  React.useEffect(() => {
    const host = hostRef.current;
    const api = window.BervinovWhiteboard;
    if (!host || !roomId || !syncToken || !api?.mount) return undefined;

    api.mount(host, { roomId, syncToken, licenseKey });

    return () => {
      api.unmount?.(host);
    };
  }, [roomId, syncToken, licenseKey]);

  if (!window.BervinovWhiteboard?.mount) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-white text-slate-600 text-xs px-4 text-center">
        Доска загружается…
      </div>
    );
  }

  if (!syncToken) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-white text-slate-600 text-xs px-4 text-center">
        Получение доступа…
      </div>
    );
  }

  return <div ref={hostRef} className="absolute inset-0 bg-[#f6f8fc] z-[1] pointer-events-auto touch-none" />;
}

function ModeButton({ active, onClick, children }) {
  return (
    <button type="button" onClick={onClick}
      className={`h-9 px-3 rounded-full text-xs font-semibold transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-300 ${
        active ? 'bg-cyan-400 text-slate-950' : 'text-white/70 hover:bg-white/10'
      }`}>
      {children}
    </button>
  );
}

function CallControl({ children, label, active, onClick, badge = 0 }) {
  return (
    <button type="button" onClick={onClick} title={label}
      className={`relative flex flex-col items-center gap-1 min-w-[72px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-300 rounded-xl ${active ? 'text-cyan-200' : 'text-white/90'}`}>
      <span className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
        active ? 'bg-cyan-500/70' : 'bg-white/12 hover:bg-white/20'
      }`}>
        {children}
        {badge > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
            {badge > 99 ? '99+' : badge}
          </span>
        )}
      </span>
      <span className="text-[10px] text-white/60">{label}</span>
    </button>
  );
}

window.CallPage = CallPage;
