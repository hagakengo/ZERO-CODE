# 動画実証 — DRAFT / HOLD

全通常動画は1秒/24fps/24フレーム。半速は2秒/24fps/48フレーム。

- blink_key_replacement_DRAFT: 半眼7f→半閉2f→閉3f→半閉2f→半眼10f。同一シートの別描画を置換。微細な髪/輪郭差があり本人一致の保証はない。
- expression_exposure_DRAFT: neutral/smile/notice各8f。口中心の表情キー比較、スライドショー。
- head_angle_comparison_DRAFT: 正面/45/90各8f。中割りのない角度比較、自然な回転ではない。
- old_new_*: 左=前回（表情は画素ワープ、頭部はC未実装3D）、右=今回。試験・構図が異なるため動きの定量比較ではない。

render_tests.pyは保存PNGをFFmpegで切り出し、等比縮小・露出組立・HOLD表記・旧版横並びを作る。画像生成の代用描画をしない。単純画素ワープによる偽まばたき、モーフ、中割り補間は使わない。各フォルダkeys/frames/exposure.csvを参照。生成原画自体の厳密再現はできない。

初回の旧新表情半速に47f/1.958333秒を独立QAが検出。末尾露出を補完し48f/2秒へ修正。最終値はlane4/video_checks.jsonを参照。

静止画・抽出フレームは視認したが、制作側の通常速度連続実視聴は未実施。自然な動作の合格判定はしない。
