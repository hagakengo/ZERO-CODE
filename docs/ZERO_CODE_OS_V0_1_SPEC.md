# ZERO CODE OS v0.1 — Product & Technical Specification

> Status: BUILD READY
> Goal: Turn real-world channel metrics and revenue into a game-like operating system for ZERO CODE.

---

## 1. Product concept

ZERO CODE OS is a personal operating system that converts real-world progress into game state.

It should answer, at a glance:

- What happened today?
- How far did the player progress?
- What mission is active?
- What changed on YouTube / TikTok?
- How much revenue exists?
- What should become the next story beat?

Core principle:

> Reality is the database. ZERO CODE is the interface.

---

## 2. v0.1 scope

### Automated
- YouTube channel metrics via API

### Manual input
- TikTok metrics
- Revenue

### UI
- One main dashboard screen
- Mission progress
- Current day / player status
- Platform metrics

### Out of scope for v0.1
- TikTok API automation
- Automatic video rendering
- Auto-upload to social platforms
- Multi-user accounts
- Payments
- Complex achievements engine

---

## 3. Recommended stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Python

### Database
- SQLite for v0.1
- PostgreSQL migration path reserved

### External APIs
- YouTube Data API
- YouTube Analytics API

---

## 4. Core dashboard

Example:

```text
ZERO CODE SYSTEM

DAY 001
LV.01

YouTube
Subscribers 0
Views 0

TikTok
Followers 0
Views 0

TOTAL REVENUE
¥0

MISSION 01
最初の1円を生み出せ。

PROGRESS
0%
```

---

## 5. Data model

### daily_metrics

| field | type | notes |
|---|---|---|
| id | integer | PK |
| date | date | unique per day |
| youtube_subscribers | integer | API |
| youtube_views | integer | API |
| youtube_watch_minutes | integer | optional |
| youtube_likes | integer | optional |
| youtube_comments | integer | optional |
| tiktok_followers | integer | manual in v0.1 |
| tiktok_views | integer | manual in v0.1 |
| total_revenue_yen | integer | manual in v0.1 |
| created_at | datetime | |
| updated_at | datetime | |

### missions

| field | type | notes |
|---|---|---|
| id | integer | PK |
| code | string | e.g. MISSION_01 |
| title | string | human-readable |
| description | text | |
| metric_type | string | revenue / followers / views / custom |
| target_value | integer | |
| current_value | integer | derived or manual |
| status | string | locked / active / completed |
| started_at | datetime | nullable |
| completed_at | datetime | nullable |

### achievements

Reserved for v0.2+.

Potential examples:
- FIRST_YEN
- FIRST_100_YEN
- FIRST_100_FOLLOWERS
- FIRST_1000_FOLLOWERS
- FIRST_VIRAL_VIDEO

---

## 6. Initial mission

```yaml
code: MISSION_01
title: 最初の1円を生み出せ。
metric_type: revenue
target_value: 1
status: active
```

Progress rule:

```text
progress = min(current_revenue / target_value, 1.0)
```

For MISSION 01 this intentionally jumps from 0% to 100% after first revenue.

---

## 7. API design

### Status

`GET /api/status`

Returns the current ZERO CODE system state.

Example response:

```json
{
  "day": 1,
  "level": 1,
  "mission": {
    "code": "MISSION_01",
    "title": "最初の1円を生み出せ。",
    "status": "active",
    "progress": 0
  },
  "youtube": {
    "subscribers": 0,
    "views": 0
  },
  "tiktok": {
    "followers": 0,
    "views": 0
  },
  "total_revenue_yen": 0
}
```

### Metrics

- `GET /api/metrics/latest`
- `GET /api/metrics/history`
- `POST /api/metrics/manual`

Manual endpoint is used for TikTok and revenue in v0.1.

### YouTube sync

- `POST /api/integrations/youtube/sync`
- `GET /api/integrations/youtube/status`

### Missions

- `GET /api/missions`
- `GET /api/missions/current`
- `PATCH /api/missions/{id}`

---

## 8. YouTube integration flow

```text
YouTube
  ↓
YouTube Data API / Analytics API
  ↓
FastAPI integration service
  ↓
daily_metrics
  ↓
status service
  ↓
Next.js dashboard
```

v0.1 sync strategy:

- Manual "SYNC YOUTUBE" button first
- Daily automatic sync later

This keeps OAuth/API debugging separate from dashboard development.

---

## 9. UI direction

Visual language should match ZERO CODE canon:

- black / charcoal base
- cyan system glow
- no unnecessary bright colors
- translucent HUD panels
- strong monospace / game-system typography
- subtle scanline / terminal feel
- restrained animation

Primary sections:

1. SYSTEM HEADER
2. PLAYER STATUS
3. PLATFORM METRICS
4. TOTAL REVENUE
5. ACTIVE MISSION
6. SYNC / MANUAL UPDATE controls

---

## 10. v0.1 screen layout

```text
┌───────────────────────────────────┐
│ ZERO CODE SYSTEM        ONLINE    │
│ DAY 001                 LV.01     │
├───────────────────────────────────┤
│ YOUTUBE                           │
│ Subscribers  0                    │
│ Views        0                    │
├───────────────────────────────────┤
│ TIKTOK                            │
│ Followers     0                   │
│ Views         0                   │
├───────────────────────────────────┤
│ TOTAL REVENUE                     │
│ ¥0                                │
├───────────────────────────────────┤
│ MISSION 01                        │
│ 最初の1円を生み出せ。              │
│ [--------------------] 0%         │
├───────────────────────────────────┤
│ [SYNC YOUTUBE] [UPDATE MANUAL]    │
└───────────────────────────────────┘
```

---

## 11. Build order

### Phase 1 — Local skeleton
- FastAPI project
- Next.js project
- SQLite
- health check
- shared env conventions

### Phase 2 — Data layer
- daily_metrics table
- missions table
- seed MISSION 01
- CRUD/service layer

### Phase 3 — Dashboard
- /api/status
- main dashboard
- manual TikTok/revenue form

### Phase 4 — YouTube
- Google Cloud project
- OAuth/API credentials
- channel metric fetch
- sync endpoint
- dashboard sync button

### Phase 5 — Story output
- status snapshot export
- reusable HUD JSON payload
- future PNG/video template generation

---

## 12. Definition of done for v0.1

v0.1 is complete when:

- Dashboard runs locally
- MISSION 01 is visible
- TikTok followers/views can be entered manually
- Revenue can be entered manually
- YouTube metrics can be synced from API
- Current state persists in the DB
- `GET /api/status` returns the same state shown in the UI
- The dashboard visually feels like ZERO CODE

---

## 13. Future roadmap

### v0.2
- metric history chart
- achievements
- daily deltas
- automatic daily sync

### v0.3
- TikTok API / import automation
- revenue source breakdown
- episode / mission linkage

### v0.4
- auto-generate status card image
- auto-generate HUD data for video templates

### v1.0
- ZERO CODE OS becomes the canonical source of truth for public story state

---

## 14. Canonical rule

The dashboard must never invent success.

If real-world metrics are zero, show zero.

If a mission fails, record the failure.

If revenue does not exist, show ¥0.

> The real world decides the story.
