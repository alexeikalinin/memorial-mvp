# Screen recording — live UI walkthrough (replace stills)

The automated build uses marketing stills (`../images/feat-*.png`). For a **full screen capture** of the running app:

## Prerequisites

- Backend: `uvicorn` on `:8000`, seed EN demo (`backend/seed_english_all.py` or existing DB with demo memorials).
- Frontend: `npm run dev` in `frontend/` (Vite `:5173`).
- Browser: Chromium or Safari, **125% zoom**, **English** UI, hide bookmarks bar.

## Flow (match the plan)

1. **Home** → open a memorial card (e.g. George Thompson or any EN seed with memories).
2. **Memories** tab → scroll existing memories; optionally add one short line (Manly / coffee) to show typing.
3. **Chat** tab → ask: `What made you happiest in life?` → wait for reply → expand **Sources** for 1–2s.
4. **Family** tab → **Fit whole tree** (if available) → slow pan/zoom → click a node to open another memorial.

## Capture settings

- **Resolution:** 1920×1080 or higher; crop to 16:9 in post.
- **Frame rate:** 30 fps.
- **Cursor:** macOS Accessibility → **Pointer** → increase size; move slowly (ease curves in post).
- **No autoplay** of unrelated audio; mute system alerts.

## Replace asset

1. Export `demo.mp4` (H.264 + AAC, ~1080p, CRF 23–28).
2. Overwrite `frontend/landing/video/demo.mp4`.
3. Run `ffmpeg -ss 00:00:46 -i demo.mp4 -vframes 1 -q:v 2 ../images/demo-poster.png` (adjust `-ss` to a strong frame).
4. Rebuild `frontend` so `dist/` picks up the new file.
