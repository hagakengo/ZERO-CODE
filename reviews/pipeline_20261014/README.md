# ZERO CODE STUDIO 2D制作工程レビュー — DRAFT / HOLD

2026-10-14 JST。継続制作方針を監督指示書へ追記し、制作ツールとAI補助を併用する最初の工程を実行した。これは本編3秒の完成納品ではない。

## レビュー順

1. `lane1/gp_timing_DRAFT.mp4`：実際のBlender Grease Pencilによる球と追従線の3秒動作試験。360×640、72f、24fps。数式生成ストロークであり人手の手描きではない。
2. `lane1/gp_timing_DRAFT.blend` と `lane1/frames/`：ネイティブ編集データと連番。手順・環境制約はlane1 README。
3. `lane2/SCENE_DIRECTION_DRAFT.md` と同フォルダのコンテ・タイムシート：C/FILMの「異変に気づく」芝居設計。人型は位置記号で本人の原画ではない。
4. `lane3/ASSET_PIPELINE_DRAFT.md`：透明レイヤー、原画、中割りの管理と、作画監修の最小依頼範囲。
5. `lane4/AI_CITY_background_DRAFT.png`、同SVG、`mix_3s_DRAFT.wav`：独立背景レイアウトとオリジナル仮音。異変キューは1-based F025（1秒）。本編原画との合成・聴取未検証。
6. `lane5/PIPELINE_QA.md`、`technical_qa.json`、`native_reopen_qa.json`、`repro_audio_qa.json`：工程・依存関係・実測。

## 判定

技術試験MP4は全尺decode、3秒/24fps/72fを独立確認。Grease Pencilを別プロセスで再オープンし、1レイヤー72描画を確認。frame36再レンダリングは画素一致、PNGファイルバイトはメタデータ差により不一致。全72フレームの再レンダリング比較は未実施。72個の異なるPNGは自然な演技の証拠ではない。

C/FILM本人一致、顔の校正、原画・中割り、3秒本編映像は未達。通常速度連続視聴未実施。全成果DRAFT/HOLD、技術PASS≠作画PASS。次は基準顔と浅い3/4、閉瞼・眉・頬・口の主要キーの作画校正が先決。

## 並列実態・衝突回避

最大4枠を使用：root＝レーン5 QA/方針/統合、子担当1＝レーン1、子担当2＝レーン2+3、子担当3＝レーン4。5レーン同時に5担当ではない。ツール準備→レンダリング→独立再オープン/技術QAは依存順で実行。

基点 `2e6147a42f909a4df1f18628a278848329f1b796`、レビュー専用ブランチ `review/production-pipeline-20261014`。先行A/Bは別ブランチ `review/parts-inbetween-acting-20261014`、確認済 `67320ee33b0ffaa46b4ed9b57ce5db2dba8bc091`。先行成果は読取のみ、マージせず、無断修正なし。main/MASTER/原本/旧顔非表示パイロット/過去版は変更しない。
