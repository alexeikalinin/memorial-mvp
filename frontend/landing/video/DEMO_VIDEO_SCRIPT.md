# Memorial landing demo — locked script (EN)

**Target duration:** 85 seconds (within 75–90s). **Aspect:** 16:9, 1080p.  
**Hero Q/A (same as [`landing/index.html`](../index.html) typewriter):**

- **User:** What made you happiest in life?
- **Avatar:** Honestly? Saturday mornings at Manly Beach with your grandmother. We'd get there before anyone else, just the two of us with coffee in those old thermoses. Didn't need anything else. That was the whole world right there.

---

## Voice-over (optional recording)

Read calmly; ~130–140 words total. Pauses where noted.

1. **Hook (0:00–0:10)**  
   “A photograph is a moment frozen. / Without the story… the person fades.” *(pause)*

2. **Promise (0:10–0:20)**  
   “Memorial keeps their voice, their stories, and your family — in one place.”

3. **Memories (0:20–0:38)**  
   “You add what you already have. Photos. Voice notes. The small details only your family remembers.”

4. **Chat (0:38–0:55)**  
   “Ask anything. The answers come from what you shared — not from thin air. / You can see where each reply comes from.”

5. **Family (0:55–1:12)**  
   “And the people around them appear on one living map — generation after generation.”

6. **CTA (1:12–1:25)**  
   “Talk to them again. / Create a memorial — it’s free.”

---

## On-screen titles (burned into generated asset)

Matches segments in `build_landing_demo.sh`.

| Timecode | Title / body |
|----------|----------------|
| 0:00–0:10 | Line 1: *Photos remember the moment.* Line 2: *Stories remember them.* |
| 0:10–0:20 | *Their voice. Their stories. Your family — one place.* |
| 0:20–0:38 | *Add memories and media — building blocks for the avatar.* (over timeline still) |
| 0:38–0:55 | *Ask in their name. Answers grounded in what you uploaded.* + hero Q/A over chat still |
| 0:55–1:12 | *See the family — across generations.* (over tree still) |
| 1:12–1:25 | *Talk to them again.* / *Create a memorial — it’s free* / `/app/register` |

---

## Ethics line (optional end bumper, 2s)

*Illustrative product tour. AI responses use only memories your family adds.*

(Add in a future edit if legal asks; not in default `build_landing_demo.sh`.)

---

## Build & verify

- From repo: `cd frontend/landing/video && ./build_landing_demo.sh` — runs `render_landing_demo.py`, writes `demo.mp4` (~85s, ~1080p) and `../images/demo-poster.png`.
- Landing `#demo` (`frontend/landing/index.html` and root `landing/index.html`): `<video>` has **`controls`**, **`preload="metadata"`**, **no `autoplay`**; optional captions **`/video/demo.vtt`**.
- Dev server: `vite.config.js` serves `/video/*.mp4` and `/video/*.vtt` with correct `Content-Type`.
