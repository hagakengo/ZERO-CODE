# EP00 Yuna v05 — skin compositing correction

Status: TEST / overall REWORK remains.

The producer reported unnatural facial skin/shadow. Inspection confirmed that the eye/mouth cels had imported a different drawing's skin illumination, causing an under-eye band and a brighter mouth patch. This was a compositing defect, not intended lighting.

The correction keeps a static source-matched skin base, restores only the old feature holes using a clean skin plate, and transfers only eyelid/iris/sclera and mouth line features from the 16 cels. Temporal color grading, original camera, exposure timing and the five-second format are unchanged. No eye stretching or face optical flow.

The C04 cheek ROI before rigid-head compositing (x414..437,y122..129) had mean absolute RGB differences from the reference of 4.3646/3.8177/2.0938 before, and 0/0/0 after. This is a narrow diagnostic ROI, not a full-face quality score.

Rendered silent H.264 native-wide TEST: 920x340, 24fps, 120 frames, 5s. Full decode passed; inspected all 120 eye crops in contact sheets. Overall output remains REWORK because eye-model fidelity, cell transitions, acting, layer edges and true portrait originals still need review. No final aesthetic approval is claimed.

Original v05/v05b files and the first correction attempt remain preserved. One built-in image edit created a static skin restoration plate; exact model/billing unverified. No paid API, Kling generation, purchase, publication, OS mutation or MASTER promotion. Media remains local.
