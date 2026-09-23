# Video Review Lab

A one-page first-pass review tool for short video ads. Upload an MP4, use the video timeline to choose a frame, and leave a timed or general comment. You can also ask Gemini about the video, ask it to post timestamped comments, or remove a video and its review history. The strategist remains the editor of the final feedback.

## Run locally

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY` from your own Google AI Studio project.
2. Run `docker compose up --build -d`.
3. Open `http://localhost:8080/foxelli-test/`.

PostgreSQL and Redis start with the app. Videos are saved in `.local-videos/`; comments and chat survive container restarts in the PostgreSQL volume. The first Gemini upload can take a minute. `docker compose down` stops the app without deleting data.

## How it works

Next.js builds the static single page, served by Nginx. FastAPI validates MP4 files (250 MB and 3 minute limit), saves them in a private directory, and records videos, comments, and chat turns in PostgreSQL. Redis queues video processing and chat. The worker uploads the **original MP4** to Gemini's File API and sends that video reference, all existing timeline comments, previous chat, and the latest question on each turn. It re-uploads the original when Gemini's temporary file is near its 48-hour expiry.

The prompt asks for short, direct notes inspired by the supplied strategist feedback: one concrete issue per line, without headings, long explanations, or forced fixes. It does not include the reference comments from the ad being evaluated. Gemini receives the full video at high [media resolution](https://ai.google.dev/gemini-api/docs/media-resolution) with [2 FPS static sampling](https://ai.google.dev/gemini-api/docs/video-understanding) to inspect small text and quick cuts. This uses more input tokens than the default 1 FPS review. Gemini uses low thinking with a three-minute request timeout, and interaction storage is disabled because the app sends its own chat context. Gemini can return structured timeline comments only for an explicit posting request; the server checks their seconds, length, count, and duplicates before saving. The API key stays on the backend. See `VERIFICATION.md` for the blind comparison and the quality gaps it found.

Public API routes live under `/foxelli-test/api/`: `GET /videos`, `POST /videos` (multipart `file`), `GET /videos/{id}`, `DELETE /videos/{id}`, `GET /videos/{id}/file`, `POST /videos/{id}/comments` (`body`, optional `second`), `POST /videos/{id}/chat` (`prompt`), and `POST /videos/{id}/retry`. Deleting a video removes its saved comments, chat, and private MP4. Nginx removes `/foxelli-test` before forwarding to FastAPI. The UI polls video and chat status.

## Checks

```sh
docker compose run --rm -v "$PWD/backend/tests:/app/tests:ro" api python -m unittest discover -s tests
docker compose config --quiet
curl -f http://localhost:8080/foxelli-test/api/health
```

Use the three MP4s from the supplied Dropbox Replay folder for the final check. For each, test upload, playback, a manual comment, the example chat prompts, AI timeline posting, and persistence after reload. Compare first-pass output with that clip's strategist comments separately, so the model cannot repeat the reference answer. The original ads are intentionally excluded from the code package.

## Live deployment

The [private GitHub repository](https://github.com/babackrz/foxelli-video-review)'s `main` branch is the deployment source for `https://5.22.217.149/foxelli-test/`. A read-only deploy key lets the VM fetch it into `/opt/foxelli/source`. The `foxelli-deploy.timer` checks for a new commit every minute. On a change, `deploy/foxelli-deploy.sh` installs dependencies, builds the Next.js static page, runs the backend tests, creates an immutable release, switches `/opt/foxelli/current`, restarts FastAPI and RQ, and checks the API and HTTPS page. It restores the previous release if activation fails. `/opt/foxelli/deployed-revision` changes only after a successful check. Pushes to `main` therefore go live without a separate hosting service or GitHub write credential on the VM.

Nginx serves the current release and proxies the API. The FastAPI and RQ units run as the unprivileged `foxelli` user. PostgreSQL and Redis listen only locally. Videos remain in `/var/lib/foxelli/videos`; database and videos survive deployments. The PostgreSQL database and local OS role are both named `foxelli` and use Unix socket peer authentication. `GEMINI_API_KEY` stays in `/etc/foxelli.env` with mode `0600`; it is not in GitHub or the code package.

Check a deployment with `ssh root@5.22.217.149 'cat /opt/foxelli/deployed-revision; systemctl status foxelli-deploy.timer foxelli-api foxelli-worker --no-pager'`. For a failed update, inspect `journalctl -u foxelli-deploy.service -n 100 --no-pager`; the timer retries the unmarked commit. The hosted demo uses HTTP Basic authentication at Nginx for the page, assets, API, and video files. Its username is `foxelli`; the password is stored only as a server-side hash in `/etc/nginx/foxelli.htpasswd`. The local Docker demo has no password. Uploads are limited to 250 MB and 3 minutes, plus 20 uploads and 60 Gemini questions per UTC day across the demo. Set a spending cap in Google AI Studio before sharing the URL.

The bare-IP HTTPS certificate renews through the daily Certbot timer. Nginx keeps the HTTP challenge webroot at `/var/www/foxelli` while the HTTPS page follows the current release.

## Loom outline (15–20 minutes)

1. Show the supplied brief and the three reference ads (2 minutes).
2. Upload an ad; add a timed comment using the video timeline and a general comment by clearing the checkbox; ask about the hook and a specific second; ask Gemini to post comments (7 minutes).
3. Explain why the prompt demands visible or audible evidence, avoids duplicate notes, and withholds that ad's reference comments during evaluation (5 minutes).
4. Show the Gemini File API call, timestamp validation, data flow, and live hosted URL (4 minutes).

The tool cannot verify an exact brand logo without a brand reference. It reports visible anomalies while leaving brand approval to the strategist.
