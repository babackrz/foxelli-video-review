"use client";

import { ChangeEvent, FormEvent, useCallback, useEffect, useRef, useState } from "react";

type VideoSummary = { id: string; filename: string; duration_seconds: number; status: string };
type Comment = { id: string; second: number | null; author: "human" | "ai"; body: string };
type Turn = { id: string; prompt: string; status: string; reply: string | null; error: string | null };
type Video = VideoSummary & { error: string | null; comments: Comment[]; turns: Turn[] };
const BASE_PATH = "/foxelli-test";

function stamp(second: number) {
  return `${Math.floor(second / 60)}:${String(second % 60).padStart(2, "0")}`;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export default function Home() {
  const [videos, setVideos] = useState<VideoSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [video, setVideo] = useState<Video | null>(null);
  const [second, setSecond] = useState(0);
  const [timestamped, setTimestamped] = useState(true);
  const [comment, setComment] = useState("");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [confirmRemoveId, setConfirmRemoveId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const player = useRef<HTMLVideoElement>(null);
  const conversation = useRef<HTMLDivElement>(null);

  const refreshList = useCallback(async () => {
    const list = await request<VideoSummary[]>(`${BASE_PATH}/api/videos`);
    setVideos(list);
    setSelectedId((id) => list.some((item) => item.id === id) ? id : list[0]?.id || null);
  }, []);

  const refreshVideo = useCallback(async (id: string) => {
    const detail = await request<Video>(`${BASE_PATH}/api/videos/${id}`);
    setVideo(detail);
  }, []);

  useEffect(() => {
    refreshList().catch((err) => setError(err.message));
  }, [refreshList]);

  useEffect(() => {
    if (!selectedId) { setVideo(null); return; }
    setVideo(null);
    setSecond(0);
    refreshVideo(selectedId).catch((err) => setError(err.message));
    const timer = window.setInterval(() => {
      refreshVideo(selectedId).catch(() => {});
      refreshList().catch(() => {});
    }, 2500);
    return () => window.clearInterval(timer);
  }, [selectedId, refreshVideo, refreshList]);

  useEffect(() => { if (conversation.current) conversation.current.scrollTop = conversation.current.scrollHeight; }, [video?.turns.length]);

  function seek(value: number) {
    setSecond(value);
    if (player.current) player.current.currentTime = value;
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const result = await request<{ id: string }>(`${BASE_PATH}/api/videos`, { method: "POST", body: form });
      await refreshList();
      setSelectedId(result.id);
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); event.target.value = ""; }
  }

  async function removeVideo(item: VideoSummary) {
    setError("");
    setRemovingId(item.id);
    try {
      await request<void>(`${BASE_PATH}/api/videos/${item.id}`, { method: "DELETE" });
      setConfirmRemoveId(null);
      await refreshList();
    } catch (err) { setError((err as Error).message); }
    finally { setRemovingId(null); }
  }

  async function addComment(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || !comment.trim()) return;
    setError("");
    try {
      await request(`${BASE_PATH}/api/videos/${selectedId}/comments`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ second: timestamped ? second : null, body: comment.trim() }),
      });
      setComment("");
      await refreshVideo(selectedId);
    } catch (err) { setError((err as Error).message); }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || !prompt.trim()) return;
    setError("");
    try {
      await request(`${BASE_PATH}/api/videos/${selectedId}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      setPrompt("");
      await refreshVideo(selectedId);
    } catch (err) { setError((err as Error).message); }
  }

  async function retry() {
    if (!selectedId) return;
    setError("");
    try {
      await request(`${BASE_PATH}/api/videos/${selectedId}/retry`, { method: "POST" });
      await refreshVideo(selectedId);
    } catch (err) { setError((err as Error).message); }
  }

  return <main className="app">
    <header className="topbar">
      <div><span className="eyebrow">CREATIVE REVIEW</span><h1>Video Review Lab</h1></div>
      <label className={`upload ${busy ? "disabled" : ""}`}>+ {busy ? "Uploading…" : "Upload MP4"}<input type="file" accept="video/mp4,.mp4" disabled={busy} onChange={upload} /></label>
    </header>
    {error && <div className="banner" role="alert">{error}<button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
    <div className="columns">
      <aside className="library panel">
        <div className="section-head"><h2>Videos</h2><span>{videos.length}</span></div>
        {videos.length === 0 && <p className="muted">Upload an MP4 to start a review.</p>}
        {videos.map((item) => <div key={item.id}><div className="video-item-row"><button className={`video-item ${selectedId === item.id ? "active" : ""}`} onClick={() => { setSelectedId(item.id); setConfirmRemoveId(null); }}>
          <span className="video-icon">▶</span><span className="video-item-text"><strong title={item.filename}>{item.filename}</strong><small>{stamp(item.duration_seconds)} · {item.status}</small></span>
        </button><button className="video-remove" type="button" title={`Remove ${item.filename}`} aria-label={`Remove ${item.filename}`} disabled={removingId === item.id} onClick={() => setConfirmRemoveId(item.id)}>×</button></div>
          {confirmRemoveId === item.id && <div className="remove-confirm"><span>Remove video, comments and chat?</span><div><button type="button" disabled={removingId === item.id} onClick={() => removeVideo(item)}>{removingId === item.id ? "Removing…" : "Remove"}</button><button type="button" onClick={() => setConfirmRemoveId(null)}>Cancel</button></div></div>}
        </div>)}
      </aside>
      <section className="review panel">
        {!video ? <div className="empty">{selectedId ? "Loading video…" : "Choose or upload a video"}</div> : <>
          <div className="section-head review-head"><div><span className="eyebrow">CURRENT REVIEW</span><h2 title={video.filename}>{video.filename}</h2></div><span className={`status ${video.status}`}>{video.status}</span></div>
          <div className="player-wrap"><video key={video.id} ref={player} controls preload="metadata" src={`${BASE_PATH}/api/videos/${video.id}/file`} onTimeUpdate={(event) => setSecond(Math.min(video.duration_seconds - 1, Math.floor(event.currentTarget.currentTime)))} /></div>
          <form className="comment-form" onSubmit={addComment}><label htmlFor="comment">Leave a comment</label><textarea id="comment" placeholder="What should the editor change?" value={comment} onChange={(event) => setComment(event.target.value)} maxLength={1000} /><label className="timestamp-option"><input type="checkbox" checked={timestamped} onChange={(event) => setTimestamped(event.target.checked)} /> Comment on current frame {timestamped && <strong>{stamp(second)}</strong>}</label><button disabled={!comment.trim()}>Add comment</button></form>
          <div className="comments"><div className="section-head"><h2>Comments</h2><span>{video.comments.length}</span></div>
            {video.comments.length === 0 && <p className="muted">No comments yet. Use the video timeline to choose a frame, or leave a general comment.</p>}
            {video.comments.map((item) => <div key={item.id} className="comment-card">{item.second === null ? <span className="time">General</span> : <button type="button" className="time" aria-label={`Jump to comment at ${stamp(item.second)}`} onClick={() => seek(item.second!)}>{stamp(item.second)}</button>}<span><small>{item.author === "ai" ? "Gemini" : "You"}</small><p>{item.body}</p></span></div>)}
          </div>
        </>}
      </section>
      <section className="chat panel"><div className="section-head"><div><span className="eyebrow">VIDEO + COMMENTS</span><h2>Ask Gemini</h2></div><span className="spark">✦</span></div>
        <p className="chat-intro">Ask about the whole ad or a specific moment. Ask it to post comments when you want notes on the timeline.</p>
        {video?.status === "error" && <div className="inline-error">{video.error}<button onClick={retry}>Retry analysis</button></div>}
        <div className="suggestions">{["What are the top 3 issues?", "Is the hook working?", "What would you say about 0:08?", "Post the top 3 issues as timeline comments."].map((text) => <button key={text} onClick={() => setPrompt(text)}>{text}</button>)}</div>
        <div className="conversation" ref={conversation}>{video?.turns.map((turn) => <div key={turn.id} className="turn"><div className="bubble user">{turn.prompt}</div><div className="bubble ai">{turn.status === "done" ? turn.reply : turn.status === "error" ? turn.error : <span className="working">Reviewing video…</span>}</div></div>)}</div>
        <form className="chat-form" onSubmit={ask}><textarea aria-label="Message Gemini" placeholder={video?.status === "ready" ? "Ask about the video…" : "Video is processing…"} value={prompt} onChange={(event) => setPrompt(event.target.value)} disabled={video?.status !== "ready"} /><button disabled={video?.status !== "ready" || !prompt.trim()}>Send ↗</button></form>
      </section>
    </div>
  </main>;
}
