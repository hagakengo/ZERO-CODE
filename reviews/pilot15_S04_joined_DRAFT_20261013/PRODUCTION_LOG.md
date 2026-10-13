# 制作ログ — 2026-10-13 JST

- Version / Status: Lane A S04 joined F216–245 / DRAFT / 技術PASS / 演出未判定。
- Tool: Python 3 + Pillow、FFmpeg H.264。新規モデル生成・外部素材・音源なし。
- Reference: AGENTS、理念、制作ルール、PROJECT_CONTEXT、README、Visual Bible、監督指示書、ROADMAP、既存PRODUCTION_LOG、タイムラインCSV/MD、音響キュー、連続性チェックリスト、両S04 README/ソース/検査資料。
- Input: ff5600598c95c00f39674ddc3683ef26a863bd43前半14f、f12ce0246ad152dbce62873d3893dde3c0e87745後半16fの原本PNG。
- Prompt version: ユーザーの2026-10-13 JST A/B/C並行制作指示（Aのみ）。
- Goal: 踏み込み→回避30fの通常速度レビューを可能にする。
- Result: 30f / 24fps / 1.25秒 / 1080×1920 / 無音の独立MP4。全PNGは原本バイト一致。全尺デコードPASS。境界姿勢パラメータ一致。既存701ファイル不変。
- What worked: 原本PNG採用によりフレーム数・順番・出典が明確。標準H.264で再生用MP4を用意。
- Limitation: MP4非可逆圧縮。通常速度視認未実施。原本の雨位相を保持し境界の再作画はしない。
- Change / Why: 新規レビュー専用フォルダだけ追加し、1.25秒の動作を一本で確認可能にした。
- Next: 監督がMP4を通常速度で連続視認し、重心・速度・足場・バッグ・雨位相を判定。案04HOLDと非統合を維持。

- 追加検査: 新規MP4のピクセル比をSAR 1:1として明示し、DAR 9:16をffprobeで検査。元PNG・既存原本には変更なし。
