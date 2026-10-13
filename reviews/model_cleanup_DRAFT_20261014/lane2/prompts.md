# Generation prompts — DRAFT / HOLD

Date: 2026-10-14 JST. Tool: built-in `image_gen.imagegen` (called through functions); model identity is not exposed by this tool. Outputs are stochastic: replaying these prompts does not guarantee identical pixels. No image-generation API CLI was used. Existing PNGs remain unchanged.

## 1. Expression cleanup sheet

Inputs (actual paths passed):

- `/Users/hagakengo/Documents/Codex/2026-10-14/referenced-chatgpt-conversation-this-is-an-5/outputs/lane1/source/A_B_C_comparison_DRAFT.png`
- `/Users/hagakengo/Documents/Codex/2026-10-14/referenced-chatgpt-conversation-this-is-an-5/outputs/lane1/source/user_reference_original.png`

`transparent_background: false`

```text
Use case: identity-preserve. Produce a precise animation expression cleanup sheet for protagonist A. Reference image 1 ONLY rightmost column C / FILM is the drawing style/identity reference; ignore A/DENSE and B/TV columns. Reference image 2 ONLY black-haired protagonist A on left is original identity reference, never silver-haired B. Sheet white background, restrained black lineart and two-tone cel shades, adult youthful male, messy asymmetric black fringe, narrow half-lidded eyes, fine pointed jaw, no glasses. All faces must be exact same head angle and same scale matching large upper C/FILM face, with its slight lean preserved, identical hair silhouette and face contour across expressions. Top row three large face portraits NEUTRAL, SOFT SMILE, NOTICE with subtle credible expression changes. Bottom area a clean parts reference library with separate aligned paired eyelids OPEN, HALF, CLOSED, three paired eyebrows, separate irises, mouths NEUTRAL, SMILE, NOTICE, and cheek lines; open eyelid and iris must be separate drawings, fully closed eyelid is a hand-drawn curved upper lash line NOT flattened iris or warped photograph. Make drawings large and isolated with ample spacing. Small title 'EXPRESSION CLEANUP — DRAFT / HOLD'. No additional character or story design. This is a review draft requiring human identity validation. No colorful UI, no gradients, no painterly texture.
```

Output: `expression_cleanup_sheet_DRAFT.png`. Original generated file: `/Users/hagakengo/.codex/generated_images/01a13648-1a2d-74f1-a808-68a9af752af5/exec-524bfa0f-42ad-4604-983b-d77640526d8d.png`.

## 2. Blink keys

Input (actual path passed):

- `/Users/hagakengo/Documents/Codex/2026-10-14/referenced-chatgpt-conversation-this-is-an-7/work/ZERO-CODE/reviews/model_cleanup_DRAFT_20261014/lane2/expression_cleanup_sheet_DRAFT.png`

`transparent_background: false`

```text
Use case identity-preserve, precise-object-edit. Edit target is the top left NEUTRAL portrait in attached expression sheet. Produce a 3-column horizontal blink key strip, white background, each panel same size. ALL THREE PANELS use the identical top-left NEUTRAL portrait, identical hair, head contour, head lean, ears, nose, mouth, clothing, shadows and scale. Change only eyelid linework in panel 2 and 3. Panel 1 exact half-lidded neutral as reference; panel 2 both eyelids halfway closing with visible narrow iris sliver; panel 3 both eyes fully shut with curved hand-drawn lash line and no iris. Do NOT flatten or warp the existing open eyes. Redraw anatomically correct closure. The heavy asymmetric hair over the left eye must be retained unchanged. Give identical chest-up crop. No captions inside portraits. Small top header 'BLINK KEYS — DRAFT / HOLD'. Maintain C/FILM face identity aggressively. This is drawn key replacement test, not final animation.
```

Output: `blink_keys_DRAFT.png`. Original generated file: `/Users/hagakengo/.codex/generated_images/01a13648-1a2d-74f1-a808-68a9af752af5/exec-14bcb502-62b7-400c-9b6e-964392ae00f5.png`.

These are requested constraints, not proof that generated drawings satisfy them. See `README.md` and independent QA for observed failures and remaining human cleanup.
