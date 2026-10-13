# 顔固定・表情・頭部回転 検証 — DRAFT / HOLD
2026-10-14 JST。基点: 2b0f541ea9156b8e4c29e1299dbb7ede9eb783c4。ユーザー承認に基づく顔あり本編探索専用。C/FILM第一候補、正式採用なし。

**品質問題の解決は未達。完成アニメではない。** レーン2は同じ顔を使う局所変形試験、レーン3はC未実装の硬い3D人形。C固有性を保てない頭部回転作画は止めた。旧パイロット、main、MASTER、過去素材に変更なし。

## 見る順序
1. [表情 通常1秒](lane2/expression_DRAFT_24fps.mp4) / [半速2秒](lane2/expression_DRAFT_half_speed.mp4) / [比較](lane2/expression_comparison_DRAFT.png)
2. [頭部構造 通常1秒](lane3/head_turn_VOLUME_TEST_DRAFT_24fps.mp4) / [半速2秒](lane3/head_turn_VOLUME_TEST_DRAFT_half_speed.mp4) / [投影見本](lane3/key_poses_VOLUME_TEST_DRAFT.png)
3. [顔対応点](lane1/C_FILM_observed_landmarks_DRAFT.png) / [独立QA](lane4/REVIEW.md) / [方式提案](lane5/METHOD_RESEARCH.md)

## 並列の実態
使用可能最大4枠: root（取得・独立QA・保存）、face_model（レーン1）、expression（レーン2）、head_turn（レーン3）。3制作ワーカーを同時に起動し、それぞれ別フォルダで独立制作。レーン1完了後、同じワーカーが追加レーン5を担当。第5独立枠は使っていない。素材取得後、静止比較と全尺デコードQAを実施し、QA後にレビュー用パッケージへ集約。映像の合成・正式統合は未実施。

## 制作ログ
入力: 既存設定画、旧3秒MP4、原本。原本SHA指定一致をrootが確認。手法: 目視観察点、1枚の固定顔の連続局所変形、共通3D座標の投影。レーン2で画像生成した基礎顔は元顔と差があり不採用保存。フレームごとの独立生成なし。各24fを24枚独立作画と呼ばない。再現ソース・露出表・各REVIEWに制約を記録。
結果: 4動画全尺decode/尺/fpsは技術PASS、作画HOLD。連続再生は未視聴。顔の揺れを抑えることと生きた表情/回転を描くことを同時に達成できていない。次作業は整合したCの3方向と閉眼/表情パーツの手修正。能力・敵・D1・HUD・Bの詳細は確定しない。ユーザーの辛口実視聴レビュー待ち。
