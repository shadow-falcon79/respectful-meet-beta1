import { useEffect, useRef, useState } from "react";
import { Volume2, VolumeX, X } from "lucide-react";
import { startAdSession, confirmMockAdWatched, type AdRewardType } from "../api/ads";

type Props = {
  rewardType: AdRewardType;
  conversationId?: string;
  onGranted: (bonus: { messages?: number; callMinutes?: number }) => void;
  onClose: () => void;
};

type Phase = "loading" | "playing" | "granting" | "granted" | "error";

/**
 * Simulates a rewarded offerwall video ad the way real providers (AdMantum
 * and similar) present them: a full-screen video player, a progress bar,
 * a "Skip in Xs" control that only becomes active once the ad has fully
 * played, and a reward screen at the end. This is a stand-in for the real
 * provider SDK — swap the <video> + timer below for their embed once the
 * publisher account is approved; the session/postback plumbing underneath
 * (api/ads.ts) is already built for that handoff.
 */
export default function AdRewardModal({ rewardType, conversationId, onGranted, onClose }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [secondsLeft, setSecondsLeft] = useState(20);
  const [totalSeconds, setTotalSeconds] = useState(20);
  const [muted, setMuted] = useState(false);
  const externalRefRef = useRef<string | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    startAdSession(rewardType, conversationId)
      .then((session) => {
        if (cancelledRef.current) return;
        externalRefRef.current = session.external_ref;
        const duration = session.mock_duration_seconds ?? 20;
        setTotalSeconds(duration);
        setSecondsLeft(duration);
        setPhase("playing");
      })
      .catch(() => setPhase("error"));
    return () => {
      cancelledRef.current = true;
    };
  }, [rewardType, conversationId]);

  useEffect(() => {
    if (phase !== "playing") return;
    if (secondsLeft <= 0) {
      void finishAd();
      return;
    }
    const timer = setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, secondsLeft]);

  async function finishAd() {
    if (!externalRefRef.current) return;
    setPhase("granting");
    try {
      const result = await confirmMockAdWatched(externalRefRef.current);
      if (result.status === "completed") {
        setPhase("granted");
        onGranted({
          messages: result.bonus_messages ?? undefined,
          callMinutes: result.bonus_call_minutes ?? undefined,
        });
      } else {
        setPhase("error");
      }
    } catch {
      setPhase("error");
    }
  }

  const progressPct = phase === "playing" ? ((totalSeconds - secondsLeft) / totalSeconds) * 100 : 0;
  const canSkip = phase === "playing" && secondsLeft <= 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90">
      <div className="relative w-full max-w-sm mx-4 rounded-2xl overflow-hidden bg-neutral-900 text-white">
        {phase !== "granted" && phase !== "error" && (
          <button
            onClick={onClose}
            disabled={phase === "playing" && !canSkip}
            aria-label="Fermer"
            className="absolute top-3 right-3 z-10 rounded-full bg-black/50 p-1.5 disabled:opacity-30"
          >
            <X size={18} />
          </button>
        )}

        {phase === "loading" && (
          <div className="flex flex-col items-center justify-center h-72 gap-3">
            <div className="h-8 w-8 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            <p className="text-sm text-white/70">Chargement de la publicité…</p>
          </div>
        )}

        {phase === "playing" && (
          <div className="flex flex-col">
            <div className="relative h-72 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center">
              <span className="absolute top-3 left-3 text-xs bg-black/40 px-2 py-0.5 rounded">Publicité</span>
              <span className="text-lg font-semibold opacity-90">▶ Vidéo en cours…</span>
              <button
                onClick={() => setMuted((m) => !m)}
                className="absolute bottom-3 right-3 rounded-full bg-black/40 p-1.5"
                aria-label="Son"
              >
                {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </button>
            </div>
            <div className="h-1 bg-white/10">
              <div className="h-full bg-white transition-all duration-1000 ease-linear" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="px-4 py-3 text-sm text-white/70 text-center">
              {canSkip ? "Vous pouvez fermer" : `Récompense dans ${secondsLeft}s`}
            </div>
          </div>
        )}

        {phase === "granting" && (
          <div className="flex flex-col items-center justify-center h-72 gap-3">
            <div className="h-8 w-8 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            <p className="text-sm text-white/70">Validation de la récompense…</p>
          </div>
        )}

        {phase === "granted" && (
          <div className="flex flex-col items-center justify-center h-72 gap-3 px-6 text-center">
            <p className="text-2xl">🎉</p>
            <p className="font-semibold">Récompense débloquée</p>
            <button onClick={onClose} className="mt-2 rounded-full bg-white text-black px-5 py-2 text-sm font-medium">
              Continuer
            </button>
          </div>
        )}

        {phase === "error" && (
          <div className="flex flex-col items-center justify-center h-72 gap-3 px-6 text-center">
            <p className="text-sm text-white/80">La publicité n'a pas pu être validée. Réessaie plus tard.</p>
            <button onClick={onClose} className="mt-2 rounded-full bg-white/10 px-5 py-2 text-sm font-medium">
              Fermer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
