# ZERO CODE — AI CITY 3秒映像候補

2026-10-14 JST / DRAFT・HOLD / 本編採用0秒、採用候補3秒。

`ZERO_CODE_AI_CITY_3s_DRAFT_HOLD.mp4`：1080×1920、24fps、72f、3.000秒、AAC 48kHz stereo。既存Bの構図を保つ固定カメラ、橋上の遠景車両、雨、波紋。背景は最小限のエッジ/暗部調整。霧と塔の灯りには微弱な2D撮影処理を追加。人物なし。外部生成・素材アップロード・有料サービス使用なし、支出0円。

再利用可能素材3点：調整B背景、packed Blenderシーン、3秒環境音WAV。映像MP4とQA画像はこの数に含めない。

## QA

技術PASS：3秒/72f/24fps/1080×1920/音声48kHz stereo/全編デコード。QA_TECHNICAL.json参照。
芸術HOLD：始端から終端まで7枚の連続時間サンプルを目視し、構図維持と車両の位置変化を確認。通常速度の連続視聴、実聴、知覚的な音同期、紙芝居感の解消は未検証。日本2Dアニメ方向への調整は控えめで、全面的な画風転換の達成を主張しない。

制約：固定カメラのため視差改善は未達。Bの焼込み雨/霧が残る。追加雨は深度別の実形状だが、屋根全体による降雨遮蔽は未対応。霧は2D合成で物理volumeではない。遠景車両は小さく、通常速度での読みやすさは制作者確認待ち。照明変化は塔帯のみで路面反射の厳密連動は未対応。時間切れでなく最初の再生可能候補ができた段階で提出し、追加検証を広げていない。

来歴：B e9bde71c3d97b18c74552b520e7763b0b730a210、既存blend 54b71ea、旧比較6fe3fcd。main/MASTER/旧成果物/原本は変更していない。モデル選択をこの作業から変更/独立認証する手段はないためGPT-6 Highでの実行を認証済みとは記さない。

## 再現

Python + Pillow + numpy、Blender 4.5、FFmpeg。リポジトリrootから実行。`<review>`は本フォルダ、`<scratch>`は任意の作業用ディレクトリ。

1. `python <review>/source/art.py reviews/aicity_style_ab_HOLD_20261014/B_HANDPAINTED_DRAFT_HOLD.png <review>/background_B_grade.png`
2. `python <review>/source/audio.py --output <review>/audio.wav`
3. `Blender -b --python <review>/source/build_production.py -- --out <scratch>/scene --frames <scratch>/frames --art <review>/background_B_grade.png`
4. `python <review>/source/atmosphere.py <scratch>/frames <scratch>/final_frames`
5. `ffmpeg -framerate 24 -i <scratch>/final_frames/frame_%04d.png -i <review>/audio.wav -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -t 3 -movflags +faststart <scratch>/candidate.mp4`
6. `python <review>/source/verify.py <scratch>/candidate.mp4 <scratch>/QA_TECHNICAL.json`

packed blendのrender filepathは保存時プレビュー先。全編を再描画する場合は別scratchへfilepathを設定する。
