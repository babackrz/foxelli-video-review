# Foxelli Video Review Lab — task list

Status as of 2026-09-23. **Codex** owns implementation and technical checks; **Baback** owns account settings, recording, and submission.

| Status | Owner | Task |
| --- | --- | --- |
| Done | Codex | Read the brief, inspect the three Replay ads and 15 strategist comments, and define the scope. |
| Done | Codex | Compare hosting options, check the existing server's capacity, and use it for this low-traffic test. |
| Done | Baback | Provide server access, the Gemini API key, and the demo password. |
| Done | Codex | Build the single-page upload, playback, timestamped manual comments, chat, and AI comment interface. |
| Done | Codex | Build the FastAPI, PostgreSQL, and Redis backend with private video storage, Gemini full-video processing, expiring-file re-upload, and timestamp validation. |
| Done | Codex | Add upload and request limits, failed-job handling, and persistent comments and chat. |
| Done | Codex | Test all three ads, playback, manual and AI comments, the example chat questions, reload persistence, and failed Gemini jobs. |
| Done | Codex | Run blind first-pass comparisons against each ad's strategist comments and document the quality gaps in `VERIFICATION.md`. |
| Done | Codex | Publish the app on the existing server with HTTPS at `https://5.22.217.149/foxelli-test/` and password-protect the page, assets, API, and video. |
| Done | Codex | Create the private GitHub repository, make semantic commits, prepare the source ZIP, and set up automatic deployment from `main` with health checks and rollback. |
| Needs doing | Codex | Improve first-pass feedback on missed visual, logo, text, and image-quality issues; repeat the blind three-ad comparison without giving Gemini that ad's reference comments. Current feedback is useful but does not yet match strategist depth. |
| Needs doing | Baback | Set a Gemini spending cap in Google AI Studio before sharing the live demo. |
| Needs doing | Baback | Record the 15–20 minute Loom demo and prompt-design explanation. |
| Needs doing | Baback | Share the private repo or source ZIP, live URL and password, and Loom with Foxelli before the agreed deadline. |
