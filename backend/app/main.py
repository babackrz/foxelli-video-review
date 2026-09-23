import logging
import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from redis import Redis
from rq import Queue

from app import db, storage
from app.video import MAX_BYTES, duration_seconds, valid_second


log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app):
    db.initialize()
    Path(os.environ["VIDEO_DIR"]).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Foxelli Video Review", lifespan=lifespan)


def queue():
    return Queue("foxelli", connection=Redis.from_url(os.environ["REDIS_URL"]))


def daily_limit(action, allowed):
    redis = Redis.from_url(os.environ["REDIS_URL"])
    key = f"limit:{action}:{datetime.now(timezone.utc):%Y-%m-%d}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 86400)
    if count > allowed:
        raise HTTPException(429, f"Daily {action} limit reached")


def video_or_404(conn, video_id):
    video = conn.execute("SELECT * FROM videos WHERE id = %s", (video_id,)).fetchone()
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@app.get("/api/health")
def health():
    with db.connect() as conn:
        conn.execute("SELECT 1")
    return {"ok": True}


@app.get("/api/videos")
def list_videos():
    with db.connect() as conn:
        return conn.execute(
            "SELECT id, filename, duration_seconds, status, created_at FROM videos ORDER BY created_at DESC LIMIT 20"
        ).fetchall()


@app.post("/api/videos", status_code=201)
def upload_video(file: UploadFile = File(...)):
    daily_limit("uploads", 20)
    if not file.filename or Path(file.filename).suffix.lower() != ".mp4":
        raise HTTPException(400, "Upload an MP4 video")
    video_id = uuid4()
    object_key = f"videos/{video_id}.mp4"
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp:
        size = 0
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                raise HTTPException(413, "Video exceeds 250 MB")
            temp.write(chunk)
        if not size:
            raise HTTPException(400, "Video is empty")
        temp.flush()
        try:
            duration = duration_seconds(temp.name)
        except Exception as exc:
            log.info("Rejected video: %s", exc)
            raise HTTPException(400, "MP4 must contain a video stream and be at most 3 minutes long") from exc
        storage.save(temp.name, object_key)
    try:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO videos (id, filename, object_key, duration_seconds, status) VALUES (%s, %s, %s, %s, 'queued')",
                (video_id, Path(file.filename).name[:160], object_key, duration),
            )
        queue().enqueue("app.jobs.prepare_video", str(video_id), job_timeout="10m")
    except Exception:
        storage.delete(object_key)
        with db.connect() as conn:
            conn.execute("DELETE FROM videos WHERE id = %s", (video_id,))
        raise
    return {"id": video_id}


@app.get("/api/videos/{video_id}")
def get_video(video_id: UUID):
    with db.connect() as conn:
        video = video_or_404(conn, video_id)
        comments = conn.execute(
            "SELECT id, second, author, body, created_at FROM comments WHERE video_id = %s ORDER BY second, created_at",
            (video_id,),
        ).fetchall()
        turns = conn.execute(
            "SELECT id, prompt, status, reply, error, created_at FROM chat_turns WHERE video_id = %s ORDER BY created_at",
            (video_id,),
        ).fetchall()
    return {
        "id": video["id"],
        "filename": video["filename"],
        "duration_seconds": video["duration_seconds"],
        "status": video["status"],
        "error": video["error"],
        "comments": comments,
        "turns": turns,
    }


@app.get("/api/videos/{video_id}/file")
def get_video_file(video_id: UUID):
    with db.connect() as conn:
        video = video_or_404(conn, video_id)
    video_path = storage.path(video["object_key"])
    if not video_path.is_file():
        raise HTTPException(404, "Video file not found")
    return FileResponse(video_path, media_type="video/mp4", filename=video["filename"], content_disposition_type="inline")


@app.post("/api/videos/{video_id}/retry", status_code=202)
def retry_video(video_id: UUID):
    with db.connect() as conn:
        video = video_or_404(conn, video_id)
        if video["status"] != "error":
            raise HTTPException(400, "Only failed videos can be retried")
        conn.execute("UPDATE videos SET status = 'queued', error = NULL WHERE id = %s", (video_id,))
    try:
        queue().enqueue("app.jobs.prepare_video", str(video_id), job_timeout="10m")
    except Exception:
        with db.connect() as conn:
            conn.execute("UPDATE videos SET status = 'error', error = 'Queue unavailable' WHERE id = %s", (video_id,))
        raise HTTPException(503, "Analysis is temporarily unavailable")
    return {"id": video_id}


class CommentIn(BaseModel):
    second: int
    body: str = Field(min_length=1, max_length=1000)


@app.post("/api/videos/{video_id}/comments", status_code=201)
def add_comment(video_id: UUID, comment: CommentIn):
    body = comment.body.strip()
    if not body:
        raise HTTPException(400, "Comment cannot be blank")
    with db.connect() as conn:
        video = video_or_404(conn, video_id)
        if not valid_second(comment.second, video["duration_seconds"]):
            raise HTTPException(400, "Timestamp is outside the video")
        return conn.execute(
            "INSERT INTO comments (id, video_id, second, author, body) VALUES (%s, %s, %s, 'human', %s) RETURNING id, second, author, body, created_at",
            (uuid4(), video_id, comment.second, body),
        ).fetchone()


class ChatIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


@app.post("/api/videos/{video_id}/chat", status_code=202)
def ask_chat(video_id: UUID, chat: ChatIn):
    daily_limit("questions", 60)
    prompt = chat.prompt.strip()
    if not prompt:
        raise HTTPException(400, "Prompt cannot be blank")
    turn_id = uuid4()
    with db.connect() as conn:
        video_or_404(conn, video_id)
        conn.execute(
            "INSERT INTO chat_turns (id, video_id, prompt, status) VALUES (%s, %s, %s, 'queued')",
            (turn_id, video_id, prompt),
        )
    try:
        queue().enqueue("app.jobs.answer_chat", str(turn_id), job_timeout="10m")
    except Exception:
        with db.connect() as conn:
            conn.execute("UPDATE chat_turns SET status = 'error', error = 'Queue unavailable' WHERE id = %s", (turn_id,))
        raise HTTPException(503, "Chat is temporarily unavailable")
    return {"id": turn_id}
