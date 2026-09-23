# Verification status

## Completed locally

- Production Docker build of the Next.js/Nginx page and FastAPI/worker services succeeded.
- The two backend tests pass; `docker compose config --quiet` and the API health check pass.
- All three supplied MP4s uploaded, appeared in the page, played through the private video route, and returned HTTP 206 for range requests. Their rounded durations are 27, 31, and 20 seconds.
- Each ad accepted a manual comment at second 5. All three comments remained after restarting the API and web containers.
- The temporary test comments and two synthetic test clips were removed afterward, leaving the three supplied ads ready for a blind first pass.
- Invalid seconds are rejected. A failed Gemini upload can be retried without losing comments. A failed chat job leaves no AI comments and reports an error.
- The page upload control and timestamped comment control were exercised in the browser. The frontend production dependency audit reported zero high-severity vulnerabilities.

## Completed on the test server

- The native deployment is live at `https://5.22.217.149`: Nginx is public, while FastAPI, PostgreSQL, and Redis listen locally. FastAPI and the RQ worker run as the unprivileged `foxelli` user.
- All three supplied ads uploaded through the public HTTPS endpoint and each live video route returned HTTP 206. PostgreSQL and local video files persisted after restarting both app services.
- The VM has 1 vCPU, 842 MiB usable RAM, and 25 GB disk. With the three ads and all services running, it had 333 MiB RAM available, 18 GB disk free, and 34 MiB of its 2 GB swap in use. This is enough for the small test workload; increase RAM if concurrent uploads or reviews become routine.
- A trusted IP certificate is installed. Its daily renewal timer is active and the production renewal command exits successfully when the certificate is not yet due. The staging dry-run endpoint was temporarily rate limited during verification.
- All three full MP4s were accepted by Gemini. The public deployment completed all 12 chat checks (the four example prompts on each ad), saved 9 valid AI timeline comments, and has no pending or failed turns. The browser showed the saved comments and played an ad in Chrome without console warnings or errors. The in-app browser crashed when starting playback, so media was checked in Chrome and with an HTTP 206 range request.

## GitHub deployment

- The repository is private. The VM has a read-only deploy key; the Gemini key is absent from tracked files and stays in the server environment file.
- The initial GitHub revision `b899d52` built and passed the server checks. After pushing `88840c0` to `main`, the systemd timer deployed it without a manual trigger; `/opt/foxelli/deployed-revision` matched the new commit and the deploy unit finished successfully.
- The build fits this small VM with swap. The first server build peaked at about 522 MiB service memory and 825 MiB swap; afterward the VM had about 385 MiB RAM available and 17 GB disk free. No resource increase is needed for this test workload.

## Blind feedback comparison

After the live checks, the prompt was adjusted to rank concrete production defects ahead of general hook and CTA advice. A fresh first-pass probe for each ad used the full Gemini video file with **no comments or chat history**. These probes did not alter the saved demo conversations. The reference comments were compared only afterward.

| Ad | Strategist themes | Revised Gemini first pass | Assessment |
| --- | --- | --- | --- |
| 26W10 | Robotic voice, suspect logo/text, pale or soft frames | Flagged synthetic voice; raised tablet graphic and product continuity | Voice issue matched. Missed the logo, text, and image-quality notes. |
| 26W07 | AI-looking opening, unnatural emotion, unclear fabric scene, limited variety, unreal kitty bag | Flagged synthetic opening; raised voice shift and CTA | Opening issue matched. Missed most scene-specific visual notes. |
| 26W04 | AI-looking person, yarn scenes and text; unclear visual explanation; unreal later frame | Raised dubbed voice, blank monitor and project continuity | Did not capture the strategist's main visual concerns. |

The tool works end to end, but this sample does **not** support claiming strategist-level feedback quality. A higher Gemini thinking setting on 26W04 did not materially improve overlap, so the deployed setting remains low. The strategist should review AI notes before treating them as edit instructions. Exact logo correctness also needs a brand reference.

## User-owned delivery item

- The user will record the 15–20 minute Loom. The timed outline in `README.md` is ready.

The three source videos and their reference comments are not included in the code package. They are available through the supplied Dropbox Replay folder. During evaluation, ask Gemini for its first pass **before** entering that video's strategist comments into the tool.
