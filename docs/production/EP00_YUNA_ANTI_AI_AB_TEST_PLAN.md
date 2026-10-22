# ZERO CODE STUDIO｜AI感低減・EP00ユナ5秒テスト制作パッケージ r01

**Date:** 2026-10-22  
**Status:** DIRECTOR DRAFT / 検証用指示書・比較実験計画 / 動画未制作  
**Applies to:** 小説版EP00『正しい世界』v08 第05節・ユナの雨粒シーン  
**Sources:** [5秒ショット設計](EP00_YUNA_RAIN_5S_SHOTBOARD_DRAFT.md)、[演技設計r02](EP00_ACTING_TEST_5S_DRAFT.md)、[素材受入台帳](EP00_ASSET_INTAKE_DRAFT.md)  
**Rights:** 実ファイルと公開条件未確認。生成・課金・公開・MASTER昇格は未承認。

## 0. 目標
AI動画らしい「全体が常に揺れる」「顔や小物が溶ける」「意味なくズームする」「表情が急に変わる」を減らす。アニメーションの良し悪しは滑らかさだけでなく、視線の動機、溜め、呼吸、表情の変化、キャラと背景の一貫性で判定する。

## 1. ロック対象と可動対象
| 要素 | ロック / 可動 | 許容内容 |
|---|---|---|
| 顔の輪郭・鼻・耳・髪の分け目・目の色 | 形状をロック | 瞳とまぶた、口角の意図した小さな変化だけ |
| 制服・淡色パーカー | 形状・模様をロック | 肩の呼吸による局所変形のみ。衣服全体の周期揺れは禁止 |
| カップ・端末・テーブル・窓枠 | 完全ロック | 画面内の座標・個数・形・接触点を保持 |
| 雨粒A/B | ガラス面上で可動 | Aは途中で止まり、Bが流下。二粒の相対位置と視線が対応 |
| カメラ | 固定を基本 | 生成モデルの勝手なドリー、ズーム、パン、回転は禁止 |
| 髪 | 原則ロック | 髪を払う動作は今回の5秒に入れない。小さな自然変化のみ |
| 表情 | 可動 | 無表情→観察→つぶやき→小さな笑み。急な大笑いは禁止 |
| 照明 | 固定 | ランプ・反射の位置を保持。脈動、過剰なグロー、フレア増殖は禁止 |

## 2. 5秒・24fpsの検証用タイムライン
- F000–023 (0.000–0.958秒): ユナは雨粒二つを観察。呼吸以外の人物の大きな動作はなし。
- F024–053 (1.000–2.208秒): Aが止まり、Bが流れる。瞳がBを追い、首はわずかに遅れる。
- F054–083 (2.250–3.458秒): つぶやきの口元の変化。声を入れる場合はセリフ原文・音声タイミングを別途照合。
- F084–119 (3.500–4.958秒): 小さな笑み、余韻、次カットへの接続。
- **5.000秒は終了境界**。24fpsの120フレームはF000–F119でありF120を追加しない。

## 3. 比較実験A：動画生成AI主体（画像参照固定）
**前提:** BG-A2、ユナ正式参照、P0/P1/P2が実ファイル・権利・承認範囲の確認を通過。モデルが参照画像または始終フレームを受け付けること。未確認のサービス仕様を前提にしない。

### Prompt / 英語（汎用モデル向けの制作指示）
```text
A restrained 5-second hand-drawn Japanese anime character acting shot, portrait 9:16.
Use the supplied approved Yuna character and café reference images as strict visual identity anchors.
One continuous locked-off medium-close side-profile shot of Yuna seated by a rainy café window.
Two raindrops on the glass: one stops, the other slowly slides downward. Yuna notices and follows the moving droplet with only her eyes first, then a barely perceptible head adjustment.
After a small, understated murmured reaction, the corners of her mouth soften into a gentle, involuntary smile. Let the smile settle naturally.
Preserve the same face geometry, amber eyes, dark-brown hairstyle, pale hoodie over uniform, café cup, terminal, table edges, window frame, and perspective in every frame.
Only intentional animation: eye movement, slight eyelid change, subtle breath, restrained mouth movement, two raindrops.
Consistent 2D anime linework, stable flat shading, natural compositing, warm café interior and cool rainy exterior.
Camera fixed, no cuts, no zoom, no orbit, no dramatic parallax. Understated acting and pauses.
```

### Negative constraints
```text
No identity drift, no face morphing, no changing eye color, no extra fingers, no hand reaching to touch the window, no floating cup, no changing table props, no flickering background, no wavy window frame, no breathing buildings, no unnecessary hair or clothing motion, no over-smiling, no lip-sync hallucination, no glossy plastic skin, no excessive bloom, no artificial lens flare, no random camera movement, no invented story events, no text overlays or watermarks added by prompt.
```

**実行条件:** 先に低コスト/無課金のプレビュー可否と利用規約を確認。承認のない有料生成をしない。モデルが厳密な可動範囲を守れなければ不合格にする。

## 4. 比較実験B：原画・中割り主体
- 同じP0/P1/P2、同じ背景、同じ5秒のタイムラインを使用。
- 背景・カップ・端末・窓枠は固定レイヤー。
- 雨粒はガラス面の別レイヤーで軌跡を設計。
- 瞳・まぶた・口角は差分原画。必要な場合だけ首の微小回転と肩の呼吸を別レイヤーで加える。
- 3枚のキーポーズを**全画面クロスフェードするだけではアニメーション合格にしない**。顔や服のゴーストを避け、動かす部位だけを中割り・差分合成する。
- 2コマ打ちを基準候補にし、視線の追従や雨粒は必要に応じて細かくする。全区間の機械的な60fps補間を避ける。
- 目線移動→間→つぶやき→笑みを明確に分け、微小な動作でも視聴者が読めるか確認。

## 5. A/Bの比較条件と判定
- **同一素材、同一脚本、同一尺、同一音声条件**で比較。BGM/効果音による印象差を避け、最初は無音で視聴。
- 各評価を0–5点で記録：①顔・衣装の同一性 ②視線と雨粒の因果 ③表情の自然さ ④背景・小道具の安定 ⑤原作整合 ⑥不自然なAI動作の少なさ。
- 合計30点中**25点以上**を次の試作に進める暫定目安。ただし重大な顔崩壊、指の異常、窓枠の変形、原作外の行動が1件でもあれば点数に関係なく**REWORK/FAIL**。
- 3人以上の実視聴ができる場合、制作方式を伏せたブラインド比較も追加する。人数が足りなければ未実施と記録する。
- 生成費用（円/クレジット）、試行回数、作業時間、修正時間、権利条件を記録。ゼロと未計測を混同しない。
- 実時間再生、フレーム単位の破綻検査、スマホ視聴、聴感評価は独立したゲート。

## 6. コンセプト絵コンテ画像 r02：監督レビュー
- ChatGPT画像生成による参考シートを2026-10-22に試作。Generation ID: `b910a71a-cf8c-4d78-a4ca-301184ad27db`。
- **良い点:** 指で窓に触れる動作を中心にした前回案から、雨粒観察・視線移動・小さな笑みに寄せた。暖色カフェと青い雨の対比は演出参考になる。
- **修正点:** 8つの別カットを描いたコンセプトシートであり、今回の比較条件である「固定カメラ1カット5秒」の連続性を証明しない。顔や髪の細部、衣装、小道具の位置に一貫性検証が必要。フレームラベルは参考で、120フレームの厳密な原画ではない。
- **権利/出典:** 正式BG-A/BG-A2/ユナ参照画像を入力していない。公式キャラ設定の承認や公開用MASTERの根拠にしない。画像バイナリはこのGitHubコミットには含めない。
- **判定:** CONCEPT TEST / REWORK。静止画なので動画品質はUNVERIFIED。

## 7. 次の制作作業
1. 既存BG-A/BG-A2/ユナ承認参照の実ファイルを照合する（SHA、寸法、承認範囲、権利）。
2. 正式参照を固定してP0/P1/P2の**同一構図**原画を制作。差分だけが動くことを確認。
3. 比較実験A/Bをそれぞれ5秒で作り、無音・同条件で採点。
4. 修正した方式を採用候補として提出。MASTER・公開・課金は別承認。

## 現状
**完了:** 制作指示・比較条件・AI感低減QC基準・コンセプトシート試作。  
**未完了:** 公式素材の実ファイル照合、3枚の正式原画、5秒動画A/B、音声検証、OS同期、公開条件確認。
