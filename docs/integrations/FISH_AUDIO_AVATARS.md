# Fish Audio video avatars — feasibility checkpoint

Checked: 2026-10-07. Status: OAuth connection and tool discovery verified; generation, pricing and application integration NOT verified.

## Decision
Try Fish Audio as an additional video provider. Preserve HeyGen unchanged as the fallback candidate. Do not assume Fish Audio is cheaper until an equivalent clip is quoted.

## Verified
- Official MCP endpoint: https://api.fish.audio/mcp.
- Codex connection `fish-audio` was added and OAuth login succeeded.
- Authenticated tool discovery returned talking-avatar generation, uploads, estimates and status polling. Captured public tool contracts: [fish-audio-mcp-schema.json](fish-audio-mcp-schema.json). No credentials are stored in this repository.
- Talking avatars accept image role `ref` and audio role `sourceAudio`; capability `avatar_audio`.
- `list_media_models` provides default credits or credits per input second; `get_media_model` provides actual input limits and parameters. These must be fetched before choosing a model.
- `generate_video` requires the estimate's `expected_credits`, `pricing_version`, and an `idempotency_key` (16–128 characters).
- Uploaded media is scoped to a Fish workspace. Use `create_media_upload`, then upload exact bytes using its returned instructions.
- Poll according to `poll_after_seconds`; terminal status already includes results.

## Still unknown
Account plan, credit balance, available avatar models and prices, output quality, latency, and whether unattended server-side production use with renewable OAuth credentials is supported. Codex OAuth is a local experiment connection, not backend authentication. Existing FISH_AUDIO_API_KEY is not established as valid for this video workflow.

## Next experiment
1. Reload the Codex connection in the chat; use native Fish tools to call `get_credit_balance`, `list_my_workspaces`, and `list_media_models` with `media_type=video`, `capability=avatar_audio`.
2. Inspect candidate model schemas; select a low-cost model based on returned pricing, not an assumed model ID.
3. Choose a user-approved portrait and short audio sample, upload, estimate, and show the exact credits before paid generation.
4. Generate one short clip after quote acceptance; measure quality, duration, latency and actual credits.
5. Only then implement a separately selectable backend provider, with secure OAuth storage/refresh, persisted provider/task identity, ownership checks, quota accounting, bounded polling and durable output storage. Retain HeyGen and existing voice cloning.

## Current connection limitation
The new tools are discoverable through a separate local client but are not exposed to this already-running chat. Attempting to attach that client to the active chat was rejected with `already has an active writer`; the task was not interrupted or taken over. No paid generation, upload, production database mutation or application-code change was performed.

## Existing application integration points
- `backend/app/services/ai_tasks.py`: existing voice providers and D-ID/HeyGen animation services.
- `backend/app/api/ai.py`: photo animation and voice-chat animation flow.
- `backend/app/workers/worker.py`: background rendering and result persistence.
- Existing chat code imports `animate_photo` and then defines a route function with the same name; inspect this shadowing before wiring a new provider into chat. This was observed but not changed during feasibility work.

## Official sources
- https://docs.fish.audio/overview/mcp — OAuth, package billing, estimate-before-generation workflow.
- https://beta.fish.audio/ai-avatar-generator/ — talking-avatar product.
- https://api.fish.audio/openapi.json — public REST schema inspected; no video generation endpoint found.
