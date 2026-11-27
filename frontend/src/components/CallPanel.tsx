import { useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Mic, MicOff, PhoneOff, SwitchCamera } from "lucide-react";
import { openCallSocket, type CallSignal } from "../api/calls";

type Props = { conversationId: string; peerName: string; mode: "audio" | "video"; onClose: () => void };

const DEFAULT_ICE: RTCIceServer[] = [{ urls: "stun:stun.l.google.com:19302" }];

function iceServers(): RTCIceServer[] {
  const username = import.meta.env.VITE_TURN_USERNAME?.trim();
  const credential = import.meta.env.VITE_TURN_CREDENTIAL?.trim();
  const urls = (import.meta.env.VITE_TURN_URLS || import.meta.env.VITE_TURN_URL || "")
    .split(",")
    .map((url: string) => url.trim())
    .filter(Boolean);

  if (!username || !credential || urls.length === 0) {
    if (import.meta.env.PROD) {
      console.warn("Metered TURN is not configured; calls may fail behind restrictive NATs.");
    }
    return DEFAULT_ICE;
  }

  return [...DEFAULT_ICE, { urls, username, credential }];
}

export default function CallPanel({ conversationId, peerName, mode, onClose }: Props) {
  const socketRef = useRef<WebSocket | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localRef = useRef<MediaStream | null>(null);
  const remoteRef = useRef<MediaStream | null>(null);
  const localVideo = useRef<HTMLVideoElement>(null);
  const remoteVideo = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState("Connecting…");
  const [mic, setMic] = useState(true);
  const [camera, setCamera] = useState(mode === "video");
  const [error, setError] = useState<string | null>(null);
  const pendingIceRef = useRef<RTCIceCandidateInit[]>([]);

  function send(type: string, data?: unknown) { socketRef.current?.send(JSON.stringify({ type, data })); }

  async function startMedia() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: mode === "video" });
    localRef.current = stream;
    if (localVideo.current) { localVideo.current.srcObject = stream; localVideo.current.muted = true; }
    const pc = new RTCPeerConnection({ iceServers: iceServers() });
    pcRef.current = pc;
    stream.getTracks().forEach((track) => pc.addTrack(track, stream));
    pc.onicecandidate = (event) => { if (event.candidate) send("ice", event.candidate.toJSON()); };
    pc.ontrack = (event) => {
      const [stream] = event.streams;
      if (stream) { remoteRef.current = stream; if (remoteVideo.current) remoteVideo.current.srcObject = stream; }
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "connected") setStatus("Connected");
      if (["failed", "disconnected", "closed"].includes(pc.connectionState)) setStatus("Call ended");
    };
  }

  useEffect(() => {
    let active = true;
    const socket = openCallSocket(conversationId);
    socketRef.current = socket;
    socket.onopen = async () => {
      try { await startMedia(); socket.send(JSON.stringify({ type: "invite", mode })); }
      catch { setError("Camera or microphone permission is required for calls."); setStatus("Permission needed"); }
    };
    socket.onmessage = async (event) => {
      const msg = JSON.parse(event.data) as CallSignal;
      const pc = pcRef.current;
      if (msg.type === "presence") {
        if (!msg.peer_online) setStatus("Waiting for the other person…");
        return;
      }
      if (msg.type === "peer_joined") {
        setStatus("Calling…");
        if (pc) { const offer = await pc.createOffer(); await pc.setLocalDescription(offer); send("offer", offer); }
        return;
      }
      if (!pc) return;
      if (msg.type === "offer") {
        await pc.setRemoteDescription(msg.data as RTCSessionDescriptionInit);
        for (const candidate of pendingIceRef.current.splice(0)) await pc.addIceCandidate(candidate).catch(() => undefined);
        const answer = await pc.createAnswer(); await pc.setLocalDescription(answer); send("answer", answer); setStatus("Connecting…");
      } else if (msg.type === "answer") {
        await pc.setRemoteDescription(msg.data as RTCSessionDescriptionInit);
        for (const candidate of pendingIceRef.current.splice(0)) await pc.addIceCandidate(candidate).catch(() => undefined);
      } else if (msg.type === "ice" && msg.data) {
        const candidate = msg.data as RTCIceCandidateInit;
        if (!pc.remoteDescription) pendingIceRef.current.push(candidate);
        else try { await pc.addIceCandidate(candidate); } catch { /* stale candidate */ }
      } else if (msg.type === "quota_exceeded") {
        if (active) { setError("You’ve run out of call minutes for today."); setStatus("Call ended"); window.setTimeout(onClose, 1500); }
      } else if (["hangup", "reject", "peer_left"].includes(msg.type)) {
        if (active) { setStatus("Call ended"); window.setTimeout(onClose, 500); }
      }
    };
    socket.onerror = () => { if (active) setError("Unable to connect to the call service."); };
    return () => {
      active = false;
      localRef.current?.getTracks().forEach((track) => track.stop());
      pcRef.current?.close(); socket.close(); socketRef.current = null;
    };
  }, [conversationId, mode]);

  function endCall() { send("hangup"); onClose(); }
  function toggleMic() { const next = !mic; localRef.current?.getAudioTracks().forEach((t) => { t.enabled = next; }); setMic(next); }
  function toggleCamera() { const next = !camera; localRef.current?.getVideoTracks().forEach((t) => { t.enabled = next; }); setCamera(next); }
  async function switchCamera() {
    const track = localRef.current?.getVideoTracks()[0];
    if (!track || !("getCapabilities" in track)) return;
    // Mobile browsers expose facingMode through applyConstraints.
    const current = track.getSettings().facingMode;
    await track.applyConstraints({ facingMode: current === "user" ? "environment" : "user" }).catch(() => undefined);
  }

  return <div className="call-overlay" role="dialog" aria-modal="true" aria-label={`${mode} call with ${peerName}`}>
    <div className="call-stage">
      {mode === "video" ? <>
        <video ref={remoteVideo} autoPlay playsInline className="call-remote-video" />
        <video ref={localVideo} autoPlay playsInline className="call-local-video" />
      </> : <div className="call-audio-avatar">{peerName.slice(0, 1).toUpperCase()}</div>}
      <div className="call-status"><strong>{peerName}</strong><span>{status}</span>{error && <small>{error}</small>}</div>
      <div className="call-controls">
        <button className={`call-control ${mic ? "" : "is-off"}`} onClick={toggleMic} aria-label={mic ? "Mute microphone" : "Unmute microphone"}>{mic ? <Mic /> : <MicOff />}</button>
        {mode === "video" && <button className={`call-control ${camera ? "" : "is-off"}`} onClick={toggleCamera} aria-label={camera ? "Turn camera off" : "Turn camera on"}>{camera ? <Camera /> : <CameraOff />}</button>}
        {mode === "video" && <button className="call-control" onClick={() => void switchCamera()} aria-label="Switch camera"><SwitchCamera /></button>}
        <button className="call-control call-control--hangup" onClick={endCall} aria-label="End call"><PhoneOff /></button>
      </div>
    </div>
  </div>;
}
