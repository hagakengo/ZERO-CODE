# Codex Task — ZERO CODE OS Phase 1

## Repository
`hagakengo/ZERO-CODE`

## Primary spec
`docs/ZERO_CODE_OS_V0_1_SPEC.md`

## Goal
Build the local development skeleton for ZERO CODE OS v0.1.

## Required stack
- Backend: FastAPI
- Frontend: Next.js + TypeScript + Tailwind CSS
- Database: SQLite

## Phase 1 requirements
1. Create a clean project structure for frontend and backend.
2. Add a FastAPI health-check endpoint.
3. Add SQLite setup with an initial minimal schema for:
   - `daily_metrics`
   - `missions`
4. Seed the initial mission:
   - code: `MISSION_01`
   - title: `最初の1円を生み出せ。`
   - metric_type: `revenue`
   - target_value: `1`
   - status: `active`
5. Create an initial Next.js dashboard page that visually matches ZERO CODE:
   - dark / charcoal base
   - cyan system glow
   - restrained HUD styling
   - display only real stored values
   - zero values must remain zero
6. Add an initial status API endpoint returning:
   - day
   - level
   - YouTube subscribers/views
   - TikTok followers/views
   - total revenue
   - active mission
7. Add `.env.example` files where useful.
8. Update README with local setup/start commands.
9. Add basic backend tests for the health/status endpoints if practical.

## Do NOT implement yet
- YouTube API integration
- TikTok API integration
- automatic social posting
- video rendering
- auth
- multi-user support
- achievements engine beyond placeholders

## Canon rules
- Never fabricate metrics.
- Initial values are zero.
- The real world decides the story.
- Keep the protagonist / visual lore out of the app code unless needed for UI assets.
- Treat this repository as the canonical source of truth.

## Expected deliverable
A runnable local skeleton where:
- backend starts successfully
- frontend starts successfully
- SQLite persists state
- `GET /api/status` returns current state
- dashboard renders that same state
- MISSION 01 appears as active
- README explains how to run everything locally

## Completion note
When done, summarize:
- files created/changed
- commands used
- tests run
- any blockers
- recommended next task for Phase 2
