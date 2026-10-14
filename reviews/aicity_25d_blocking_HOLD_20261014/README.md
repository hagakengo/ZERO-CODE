# AI CITY 2.5D設計判断 — DRAFT / HOLD

2026-10-14 JST。完成採用 **0秒**。Astra選択はユーザー申告で確認、実行基盤のモデルIDは取得不能。

**推奨：Blenderの浅い3Dセットに手描き美術を投影・配置する。** 柱梁を接続した固定物として扱い、カメラを小さく横移動。近中遠の視差に加え、独立動体の隠れ／再出現で時間的出来事を作る。平面マルチプレーンだけでは隠れ面と接続問題が残り、フル3D都市は3秒の検証に過剰。

確認：最新24/60fpsソースは同一背景の拡大。旧版は柱だけ移動。両MP4の12時刻ずつを直接画像確認。主因候補はFPSより投影面・遮蔽・独立動体の欠如（推論）。通常速で差が小さいという知覚はユーザー報告。詳細の事実／推論は設計・引継ぎ書に記載。

## 今回の試験

- [3秒・24fps MP4](AI_CITY_BLOCKING_24fps_DRAFT_HOLD.mp4)：540×960、72枚、音声なし。
- [Blenderシーン](AI_CITY_BLOCKING_DRAFT_HOLD.blend)：B美術未投入。幾何学の動作検証専用。
- [時系列画像](BLOCKING_SEQUENCE_DRAFT_HOLD.jpg)：左上から0.25秒間隔、0〜2.75秒。
- [固定カメラ対照](FIXED_CAMERA_CONTROL_DRAFT_HOLD.jpg)：左からf1/24/30/36/48/72。建築が固定されたまま人物だけ横切る。
- [独立QA](QA_INDEPENDENT_DRAFT_HOLD.md) / [技術測定](QA_TECHNICAL.json)
- [具体的な設計・GPT-6 High引継ぎ](DESIGN_AND_HANDOFF_DRAFT_HOLD.md)

投影点の総変位は近景90.513px、中景19.100px、遠景7.272px。人物胴体中心はf24〜36で手前のポールに遮られ、前後は可視。これらは幾何学の証拠で、自然な歩行や芸術合格の証拠ではない。

**合格基準**：建築接続の維持、距離に応じた視差、独立動体の遮蔽と再出現に加え、通常速でユーザーが前後関係を読めること。最後の知覚項目は未確認のためHOLD。仮人物は正史・新キャラクターではない。霧・路面反射・音・自然な歩行は未実装／未完成。

**必要時間（見積もり）**：ブロッキング半日以内、B用描き足しと美術撮影・QAに追加1〜3日（承認待ち別）。**停止条件**：遮蔽が読めない、接続が滑る、隠れ面に穴、3日を超える大規模改作が必要なら美術投入を停止。今回1案で停止、FPS追加比較なし。

次はこのMP4を通常速で確認。自然な奥行きが成立してから、Bの消失点にセットを合わせ、始終端で露出する側面・柱裏・梁下面だけ描き足す。日本2Dアニメ寄りの面整理と筆致は新規DRAFT静止候補で確認してから撮影へ進む。

## 再現と保全

Blender 4.5.14 LTS、FFmpeg。新規review専用branchでこのフォルダーだけ追加。main/MASTER/B原本/過去版は変更なし。外部生成サービスに素材を送っていない。承認されたGitHubレビューbranchへの保存・pushのみ。

```sh
blender -b --python source/build_blocking.py -- --out /path/to/review-output --frames /path/to/scratch
python3 source/package_verify.py --out /path/to/review-output --frames /path/to/scratch
blender -b /path/to/review-output/AI_CITY_BLOCKING_DRAFT_HOLD.blend --python source/render_fixed_camera_samples.py -- /path/to/control-scratch
```

.blendはテクスチャ依存なし。直接再レンダーする場合、出力先は.blend横の`renders/`。72枚を24fpsでMP4へエンコードする。固定カメラ対照は静止サンプルであり通常速知覚の検査ではない。
