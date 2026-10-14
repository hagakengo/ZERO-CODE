# AI CITY「生きている世界」3秒候補 — DRAFT/HOLD

演出DRAFT「日常→異常→反応」。新しい正史・キャラクター設定ではない。制作者の最終承認前につき採用0秒。

- `ZERO_CODE_AI_CITY_LIVING_3s_DRAFT_HOLD.mp4`: 1080×1920 / 24fps / 3.000秒 / 音声付き。
- `AI_CITY_LIVING_DRAFT_HOLD.blend`: B背景、2.5D投影、照明、人物72ポーズを内包した編集可能シーン。
- `source/`: 人物・音響・Blenderシーン・照明マスク生成ソース。`pedestrian/`: 透過原画72枚。
- `background_B_approved_reuse.png`: 承認済みB背景の来歴コピー。
- `QA_ART_DRAFT_HOLD.md` と `QA_TECHNICAL.json`: 芸術QAと技術QA。

再レンダリングにはBlender 4.5とPillowが必要。`pedestrian.py`を実行して連番を再生成し、B背景から`make_mask.py`で照明マスクを作る。次に `Blender -b --python source/build_scene.py -- --repo <ZERO-CODE repo> --out <このレビュー folder> --frames <scratch folder>` を実行し、生成された72枚を24fpsでFFmpegに渡し、`audio.wav`をAAC音声としてmuxする。

入力再利用: approved B `e9bde71c3d97b18c74552b520e7763b0b730a210`; 2.5D blocking `54b71ea`; production candidate branch baseline `13e5ef5`。既存カメラ構成を固定し、柱/梁は分離移動させない。
