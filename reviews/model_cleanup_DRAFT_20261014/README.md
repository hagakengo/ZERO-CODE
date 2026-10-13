# 主人公A — モデル・表情清書と動画実証

2026-10-14 JST / **全成果 DRAFT / HOLD**。ユーザー実視聴・承認前。C/FILMを本編第一候補として検証。正式モデル、完成アニメ、正史には昇格しない。

**同じ人物が自然に動くという目標は未達。** 前回の変形による偽まばたきから、描き起こした3枚の閉眼キーへ進めた。ただし顔・髪・輪郭の微差、頭部の角度整合、パーツの真の分離は解決していない。高品質な手描きアニメに必要な修正原画・中割りを今回の生成/組立で代替できていない。

## 最初に見るもの

1. [頭部モデルv2](lane1/head_model_v2_DRAFT.png) — 45/90の方向は修正。真正面の微傾斜と不正確なガイドは残る。
2. [表情清書シート](lane2/expression_cleanup_sheet_DRAFT.png)、[まばたき3キー](lane2/blink_keys_DRAFT.png)。
3. [まばたき通常1秒](lane3/blink_key_replacement_DRAFT/normal_24fps.mp4) / [半速2秒](lane3/blink_key_replacement_DRAFT/half_speed_24fps.mp4)。半眼→半閉→閉→半閉→半眼のキー置換試験。滑らかさの合格証拠ではない。
4. [表情通常1秒](lane3/expression_exposure_DRAFT/normal_24fps.mp4) / [半速2秒](lane3/expression_exposure_DRAFT/half_speed_24fps.mp4)。3枚を各8フレーム露出するスライド比較。
5. [頭部3角度通常1秒](lane3/head_angle_comparison_DRAFT/normal_24fps.mp4) / [半速2秒](lane3/head_angle_comparison_DRAFT/half_speed_24fps.mp4)。3枚の角度比較であり自然な頭部回転ではない。
6. [旧新まばたき比較](lane3/old_new_blink_comparison_DRAFT_24fps.mp4)、[旧新表情比較](lane3/old_new_expression_comparison_DRAFT_24fps.mp4)、[旧新頭部比較](lane3/old_new_head_comparison_DRAFT_24fps.mp4)。すべて左=前回、右=今回。異なる試験/構図であり定量品質スコアには使えない。
7. [独立QA](lane4/QA.md)、[機械検査](lane4/video_checks.json)、各レーンREADME。

## 編集素材と再現

[名前付きレイヤーSVG](lane2/expression_parts_layered_DRAFT.svg)は**白背景付きラスタ領域のクリップ分け**。透明に分離された瞼・眉・瞳・口ではなく、線画パスも編集できない。レイヤー操作の下地であり、要求した本番用分離素材は未達。[領域定義と再現](lane2/README.md)を参照。

動画再組立: `python3 lane3/render_tests.py`（Python標準ライブラリ、FFmpegが必要）。各動画フォルダのframesに全24フレーム、keysに使用原画、exposure.csvに露出を保存。通常24fps/1秒、半速も24fps/2秒で同じ原画露出を2倍にする。画素ワープ・モーフ・汎用3D人形・中割り捏造は使用しない。生成した原画自体はプロンプトから厳密再現できず、元PNGを保存して再組立する。生成は組み込みimagegen、プロンプトは各レーン記録。

## 並列実行の実態

利用可能最大**4枠を同時稼働**: root=レーン3動画/統合/保存、head=レーン1頭部、expression=レーン2表情、qa=レーン4独立QA。頭部と表情は同じ原本/C比較画像を参照し独立制作。QAは既存資料と到着した新規画像を並行検査。動画はレーン1v2・レーン2表情/まばたきPNG完成後に組立。最終動画QAは組立後に実施。4つの動画制作が独立同時完了したという意味ではない。

## 来歴と保護範囲

基点 `cc09f124e792b7b9a9f04b59d0aba3dfbcd4cbaf`。前段 `2b0f541ea9156b8e4c29e1299dbb7ede9eb783c4`（parallel-production）、`fcd6b31f58e77e04fee11e51b3601a5e7db40d7e`（protagonist-a-style-draft）を参照。原本SHA256 `bc3697df6c3c080985b226b285627d449124f1b9b58c9326ea6a316890057fad`、制作/QAで独立一致確認。

レビュー専用ブランチ `review/model-expression-cleanup-20261014`。main、MASTER、旧顔非表示パイロット、原本、過去版の上書きなし。追加フォルダと制作ログへの追記のみ。旧顔非表示規則は既存本編に保持し、今回のユーザー明示承認はこの顔あり検証に限定。A/DENSE・B/TV・C/FILMの候補役割を変更せず、ストーリーや能力を確定しない。

## 次に必要な校正

人がCの基準顔を1枚確定し、水平眼線と中央軸を描き直す。鼻根・鼻先・耳基部・顎・非対称前髪の対応を角度ごとに修正する。瞼/瞳/眉を重複しない透明レイヤーへ分解し、髪の前後関係を保って閉眼を組む。開眼と半眼を明確に描き分け、微笑/気づきは口だけでなく眉・眼・頬で設計する。これらの修正後に中割りと露出を調整して再視聴する。

技術PASS ≠ 作画/演出PASS。制作側・QAとも通常速度の連続実視聴は未実施。静止画・抽出フレームの視認と全尺デコードを視聴と呼ばない。
