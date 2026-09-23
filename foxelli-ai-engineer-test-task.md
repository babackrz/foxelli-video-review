# AI Engineer Test Tasks

Hi there! Welcome to the AI Engineer Test Task! We're excited to see what we can create together.

## Test Task

Our creative strategist reviews video ads daily on Dropbox Replay, leaving timestamped feedback for video editors.

The comments are repetitive - same hook issues, pacing notes, CTA placement. We want to test whether Gemini's video understanding can take a first pass on this feedback so the strategist only needs to refine. And your task is to build a tool to help with that:

### What to Build

A simple internal web tool with:

1. Video upload
2. Timestamped comments - click the timeline to leave a comment at a specific second
3. Chat panel with LLM that:
   - Sees the actual video content
   - Sees all existing comments left by user or by LLM and their timestamps
   - Responds to prompts like "what are the top 3 issues?", "is the hook working?", "what would you say about 0:08?"
   - When asked, can post comments directly into the timeline at specific timestamps

## Scope and Constraints

- Single page. No auth, no multi-user, no polished UI.
- Tech stack you need to use - Next.js, FastAPI, Postgress, Redis, Nginx
- Gemini must actually see the video frames (not thumbnails or transcripts). Use Gemini's File API or equivalent.
- Time budget: 1–3 days of focused work. Don't over-engineer.

## What We Provide

- 3 sample video ads from our brands
- ~15 real comments from our strategist on past ads - so you can see the tone, depth, and patterns we're after
- API key (we’d cover the cost after you submit your work as part of your compensation for the task)
- HERE - https://replay.dropbox.com/share-folder/YrKEVIxfK0zmfIhZ

## How We Evaluate

- Does it work? We test it on the sample videos.
- Is the AI output close to what a real strategist would write? Compared against the sample comments.
- Product sense. Bonus signal: ask us questions about the use case before you start building.

## Deliverables

- Working code (GitHub repo or zip); The tool needs to be published, hosted and live, so we could test it.
- A 15–20 minute Loom covering:
  - Demo of the tool
  - Your prompt design and reasoning

## Payment and Logistics

- €250 flat fee, paid via Wise/Revolut within 5 days of submission, regardless of outcome.
- Submit within 7 days of accepting the task.
- IP: code and prompts you write for this task become ours.
- We will give you written technical feedback within 3 business days of submission, whether or not we move forward.
