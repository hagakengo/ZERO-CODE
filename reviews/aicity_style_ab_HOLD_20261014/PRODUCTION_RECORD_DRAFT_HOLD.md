# AI CITY 画風A/B — DRAFT / HOLD
2026-10-14 JST。採用済み完成映像0秒。動画生成なし。静止画承認待ち。

基準: commit d8f896fc69c18b76921ac5975bfeaa14c480d4e2 / reviews/aicity_cinematic_boards_HOLD_20261014/KF_015_DRAFT_HOLD.png。Git blob抽出とローカル参照のSHA-256一致を確認: dd3521115c23a728c970ae735e4e9b03ebb71f9fe662cedccdd2773338b24a4d。旧新比較画像も直接視認。

目的: 制作者が評価した暗い雨の都市・湿度・霧・黒・青帯光・少量の暖色を保ち、画風のみ比較する。
手法: 内蔵image_genを各案1回、同一基準PNGを編集参照として使用。内部生成モデルID・seedは未返却。GPT-6 High/Astraによる画像生成とは表記しない。外部の別サービスへ原画アップロードなし。C/FILMはQAでローカル視認のみ、生成入力に使用せず。

A: シネマティック陰影を残し、ぼけ・過剰反射・生成テクスチャ抑制。
B: 同じ画面を日本の2Dアニメ背景に近い面・筆致・光処理へ。
共通: 左の黒い遮蔽を建築の柱・梁の縁として明確化。新たな巨大建築・人物・D1・HUD設定なし。

結果: 各941×1672 PNG（生成時の原寸、拡大縮小なし）。同一サイズの横並び比較1882×1752 PNG。比較のラベル・配置だけPillowで組版、美術自体は画像生成。プロンプト全文はPROMPTS.json、寸法/ハッシュはASSET_CHECKS.json。構図のピクセル完全一致は保証しない。前景の輪郭と細部に差があり、Aにも筆致がある。詳細と芸術的限界はQA_INDEPENDENT.md。

保存: 新規review/aicity-style-ab-hold-20261014。追加はreviews/aicity_style_ab_HOLD_20261014内のみ。main・MASTER・原本・過去成果物は変更しない。既存PRODUCTION_LOGを変更せず、本記録を実験ログとする。
次: ユーザーによるA/B選択。承認前の動画化・MASTER昇格なし。
