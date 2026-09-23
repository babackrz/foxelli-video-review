CREATE TABLE IF NOT EXISTS videos (
  id uuid PRIMARY KEY,
  filename text NOT NULL,
  object_key text NOT NULL UNIQUE,
  duration_seconds integer NOT NULL CHECK (duration_seconds > 0),
  status text NOT NULL CHECK (status IN ('queued', 'processing', 'ready', 'error')),
  error text,
  gemini_name text,
  gemini_uri text,
  gemini_uploaded_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comments (
  id uuid PRIMARY KEY,
  video_id uuid NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  second integer CHECK (second >= 0),
  author text NOT NULL CHECK (author IN ('human', 'ai')),
  body text NOT NULL CHECK (length(body) BETWEEN 1 AND 1000),
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE comments ALTER COLUMN second DROP NOT NULL;

CREATE INDEX IF NOT EXISTS comments_video_time ON comments(video_id, second, created_at);

CREATE TABLE IF NOT EXISTS chat_turns (
  id uuid PRIMARY KEY,
  video_id uuid NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  prompt text NOT NULL,
  status text NOT NULL CHECK (status IN ('queued', 'processing', 'done', 'error')),
  reply text,
  error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_turns_video_created ON chat_turns(video_id, created_at);
