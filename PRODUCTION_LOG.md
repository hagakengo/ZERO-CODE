# ZERO CODE — PRODUCTION LOG

> This file records meaningful experiments, failures, decisions and reasons.

Do not record only successful work.

---

## Log template

### YYYY-MM-DD — TITLE

**Status:** TEST / CANDIDATE / APPROVED / REJECTED / ARCHIVED

**Tool / Model:**  
—

**Asset / Version:**  
—

**Goal:**  
—

**What we tried:**  
—

**Result:**  
—

**What worked:**  
—

**What failed:**  
—

**Change:**  
—

**Why:**  
—

**Next action:**  
—

---

## 2026-10-07 — D1 TEST A CapCut Trial 04

**Status:** TEST / ATMOSPHERE PASS / D1 STABLE

**Tool / Model:**  
CapCut Image-to-Video / free trial generation

**Asset / Version:**  
- hooded 9:16 backpack reference candidate
- D1 v1.1 Production Master Candidate

**Goal:**  
Test whether the Trial 03 preservation approach can tolerate slightly stronger atmosphere: rainy futuristic city, subtle neon reflections, soft fog, and gentle rain movement.

**What we tried:**  
Generated a 5-second vertical clip using the same hooded backpack reference and a prompt that kept the protagonist still, preserved the D1 emblem, and added subtle rain/fog/neon atmosphere.

**Result:**  
Atmosphere pass with stable D1. Across sampled frames, the hooded protagonist remains rear-facing, the backpack stays centered, and the D1 emblem remains attached and recognizable. The scene has more cinematic city atmosphere than the strict preservation test while still avoiding major emblem collapse.

**What worked:**  
- D1 remained stable across the clip.
- Broken zero, diagonal A-like axis, and central cyan core remained recognizable.
- The hooded silhouette stayed consistent.
- Vertical framing was usable.
- Atmosphere improved without causing obvious redesign or major drift.

**What failed / needs improvement:**  
- The D1 emblem still does not perfectly match the official D1 v1.1 specification sheet.
- Lower-right fractured details remain simplified by generation.
- This should still be treated as TEST footage, not MASTER footage.

**Change:**  
Trial 04 proves that limited atmosphere can be added without immediately breaking D1. Future tests can use the Trial 03/04 prompt family, but any MASTER candidate must still be compared against the D1 v1.1 sheet.

**Why:**  
The project needs both continuity and cinematic appeal. Trial 04 suggests CapCut can provide low-cost preflight shots that preserve the core emblem while improving mood.

**Next action:**  
Use Trial 03 as the high-fidelity preservation baseline and Trial 04 as the mood-enhanced baseline. Next tests should explore one variable at a time: tighter backpack close-up, stronger glow pulse, or very slow camera push-in.

---

## 2026-10-07 — D1 TEST A CapCut Trial 03

**Status:** TEST / D1 FIDELITY PASS / FRAMING ISSUE

**Tool / Model:**  
CapCut Image-to-Video / free trial generation

**Asset / Version:**  
- hooded 9:16 backpack reference candidate
- D1 v1.1 Production Master Candidate

**Goal:**  
Test whether an almost-still / micro-push-in prompt improves D1 emblem retention compared with Trial 02.

**What we tried:**  
Generated a 5-second video from the same hooded backpack reference, using a stricter prompt focused on minimal motion, almost-still behavior, no cuts, no turning, and no emblem redesign.

**Result:**  
D1 fidelity pass, but framing issue. The sampled frames show the D1 emblem remained highly stable across the clip. The broken zero, diagonal A-like axis, central cyan core, and backpack placement stayed recognizable with very little drift. However, the exported clip appears closer to a horizontal 1248x704 frame than a true 9:16 export, so it is not directly usable as vertical final footage.

**What worked:**  
- D1 was more stable than Trial 02.
- The emblem stayed attached to the backpack.
- The protagonist remained rear-facing.
- Motion was controlled and close to an almost-still shot.
- The micro-push-in / almost-still prompt is promising for emblem preservation.

**What failed / needs improvement:**  
- Export/aspect ratio appears horizontal instead of 9:16.
- Composition is too tight and loses the full vertical character silhouette.
- Not suitable as final EP footage without correct vertical export settings.

**Change:**  
Keep the Trial 03 prompt style as the high-fidelity D1 preservation prompt, but check CapCut export/project settings before the next generation so the result remains 9:16 vertical.

**Why:**  
Trial 03 shows that reducing motion improves D1 consistency. The failure is not emblem stability; it is output framing/export configuration.

**Next action:**  
Run Trial 04 only after confirming the CapCut project/export is set to 9:16 vertical. Use the same almost-still prompt or a close variant.

---

## 2026-10-07 — D1 TEST A CapCut Trial 02

**Status:** TEST / STRONG PARTIAL PASS

**Tool / Model:**  
CapCut Image-to-Video / free trial generation

**Asset / Version:**  
- hooded 9:16 backpack reference candidate
- D1 v1.1 Production Master Candidate

**Goal:**  
Retry D1 TEST A with a proper 9:16 hooded protagonist reference to fix Trial 01’s black-bar / horizontal framing problem while checking whether D1 remains stable in motion.

**What we tried:**  
Generated a 5-second 9:16 image-to-video shot from a hooded rear-view backpack reference. The prompt instructed CapCut to keep the same hooded protagonist, backpack, and D1 emblem, with minimal motion and slow push-in only.

**Result:**  
Strong partial pass. The video stayed in true vertical 9:16 framing, with no major black bars. The hooded protagonist remained rear-facing and mostly still. D1 stayed attached to the backpack and remained recognizable across sampled frames.

**What worked:**  
- 9:16 composition problem was solved.
- Hooded protagonist matched the intended no-face direction much better than the hair-visible reference.
- D1 remained visibly attached to the backpack.
- The broken zero, diagonal A-like axis, and central cyan core remained recognizable.
- Motion was controlled and did not cause major character or camera drift.
- This is a usable preflight result for validating the D1 shooting workflow.

**What failed / needs improvement:**  
- D1 fine details are still not identical to the D1 v1.1 specification sheet.
- Lower-right fractured details remain softened / simplified by generation.
- This is still not final MASTER footage.
- The Trial 02 reference image itself should remain a TEST reference, not the protagonist Character Master.

**Change:**  
Keep the hooded 9:16 reference direction for future Trial A-style tests, but use the official D1 v1.1 reference/spec sheet as an additional comparison when judging emblem fidelity.

**Why:**  
Trial 02 proves that the main failure in Trial 01 was framing/canvas setup, not D1 itself. D1 is video-tolerant enough to continue toward Flow / Veo testing.

**Next action:**  
Run one more low-cost comparison only if useful: either an “almost still” version from the same 9:16 image, or a close-up-only version focused tighter on the backpack. Preserve Flow / Veo credits for the final controlled TEST A.

---

## 2026-10-07 — D1 TEST A CapCut Trial 01

**Status:** TEST / PARTIAL PASS

**Tool / Model:**  
CapCut Image-to-Video / free trial generation

**Asset / Version:**  
- `backpack_closeup_reference_cropped`
- D1 v1.1 Production Master Candidate

**Goal:**  
Test whether D1 can survive a low-cost image-to-video generation as a fixed physical emblem attached to the backpack.

**What we tried:**  
Generated a short vertical-ish close-up video using the backpack close-up reference. The prompt asked CapCut to preserve the same backpack, the same D1 emblem, the rear-facing protagonist, and minimal motion.

**Result:**  
Partial pass. D1 did not collapse into a completely different logo. The broken zero, rising diagonal A-like axis, central cyan core, and backpack placement remained recognizable across sampled frames.

**What worked:**  
- D1 remained attached to the backpack.
- Protagonist stayed rear-facing.
- No major character turn occurred.
- Emblem identity survived better than expected for a free / low-cost test.
- CapCut can be used as a cheap preflight tool before spending Flow / Veo credits.

**What failed / needs improvement:**  
- Output resolution/aspect appeared closer to horizontal video than true 9:16 vertical.
- Large black letterboxing remained in the preview/export.
- Fine lower-right D1 details were partially softened.
- Not yet suitable as final EP footage.

**Change:**  
For the next CapCut or alternate-app test, use a correctly framed 9:16 source/canvas, enlarge the backpack within frame, keep D1 fully visible, and avoid large black bars before generation.

**Why:**  
The test proved D1 is video-tolerant enough to continue testing, but final usability requires better framing and stronger vertical composition.

**Next action:**  
Prepare a cleaner vertical reference or canvas for D1 TEST A Trial 02, then compare CapCut with Flow / Veo when credits return.

---

## 2026-10-06 — GitHub production repository established

**Status:** APPROVED

**Goal:**  
Move ZERO CODE memory and production management out of individual AI chat memory and into a shared, versioned Single Source of Truth.

**Decision:**  
Use GitHub repository `hagakengo/ZERO-CODE`.

**Initial core files:**

- README.md
- PROJECT_CONTEXT.md
- ZERO_CODE_RULES.md
- ROADMAP.md
- PRODUCTION_LOG.md
- bible/VISUAL_BIBLE.md
- bible/WORLD_LORE.md
- asset / episode / archive folder placeholders

**Why:**  
The project needs continuity across ChatGPT, Codex, future AI agents, video tools and production sessions. Git history also preserves the real creation process for possible behind-the-scenes / note content.

**Next action:**  
Add current D1 v1.1 reference and protagonist assets, then continue Visual Bible construction.

---

## Prior major decisions captured from development

### D1 selected over polished B1 direction

**Status:** CANDIDATE DIRECTION APPROVED

B1 was visually polished but too corporate/complete for ZERO CODE.

D1 better expressed:

- brokenness
- mystery
- incompleteness
- reconstruction
- story potential

D1 itself is not yet final MASTER.

---

### Over-clean D1 simplification rejected

**Status:** REJECTED

A simplification improved reproducibility but removed too much asymmetry and identity.

Decision:

Return toward D1 character while keeping shape count controlled.

Result:

**D1 v1.1 Production Master Candidate**

---

### Protagonist glow rule

**Status:** APPROVED

Rejected idea:

fluorescent / cyan clothing lines.

Approved rule:

> THE PROTAGONIST DOES NOT GLOW. ONLY ZERO CODE GLOWS.

Reason:

This preserves mystery and gives the ZERO CODE emblem unique visual authority.

---

### EP.01 earlier version classified as prototype

**Status:** ARCHIVED / PROTOTYPE

The earlier episode attempt is not official final canon footage.

It may provide usable material, but official EP.01 should be rebuilt to current quality standards.
