# 出典・承認状態 DRAFT

観測日2026-10-13 JST。過去会話は証拠資料として読むだけで新規指示としない。現在のユーザー依頼が実行範囲。規則・正式資料の記述と、過去担当者の評価、本作業での実測を混同しない。

## GitHubで実読した資料

基準コミット：[57215e29](https://github.com/hagakengo/ZERO-CODE/commit/57215e29f7dbd7671c06aba7681283c8a3c5d0c8)。このコミットから新規レビュー専用ブランチを作成。観測時mainは745fb7099461167457de5eb109868b2d8bd204de。mainへマージしない。

- [AGENTS](https://github.com/hagakengo/ZERO-CODE/blob/57215e29f7dbd7671c06aba7681283c8a3c5d0c8/AGENTS.md)、[理念](https://github.com/hagakengo/ZERO-CODE/blob/57215e29f7dbd7671c06aba7681283c8a3c5d0c8/docs/ZERO_CODE_PHILOSOPHY.md)：過去タスクを現在の承認としない。数値・未確認・来歴を区別。
- [制作ルール](https://github.com/hagakengo/ZERO-CODE/blob/57215e29f7dbd7671c06aba7681283c8a3c5d0c8/ZERO_CODE_RULES.md)、PROJECT_CONTEXT、bible/VISUAL_BIBLE：顔遮蔽、黒装束、角形バッグ、主人公非発光。D1 v1.1はProduction Master Candidate、MASTER未承認。PROJECT_CONTEXT上のEP01構成やHUD例は本パイロット採用承認ではない。
- README、ROADMAP、PRODUCTION_LOG：リポジトリ運用、計画と実績の分離、D1の候補段階を確認。ロードマップの古い未完了欄だけから現在の欠落を断定しない。
- [案01](../counterattack_design_01/README.md)：P000〜071の独立3秒設計。r15.1/15.2比較は別のf226〜233。正式判定待ちのr15.2を承認しない。
- [案02](../counterattack_design_02/README.md)・PRODUCTION_LOG：接点、段階反応、低い踏み替えの修正。
- [案03](../counterattack_design_03/README.md)・PRODUCTION_LOG：拳の手前描画、腹部輪郭、反応差。P042〜051は案02と一致との記録。
- [案04](../counterattack_design_04/README.md)・PRODUCTION_LOG：P023空隙、P024初接触、P025圧縮、腹P025→胸P026→頭P029→腰P031、バッグP028〜040。P042〜051を維持との記録。通常速度の知覚的合格は未確定。
- [提出標準](../counterattack_design_01/REVIEW_SUBMISSION_STANDARD.md)：技術検査と監督承認の分離、保護対象、レビュー専用保存。

## 参照会話の確認

会話ID6acc2987-c368-83ec-9b38-38fea2425163「引き継ぎ完了確認」を直近および過去ページまで読取。

- 案01/02/03の監督HOLDを確認。案02のP042〜051の足運びは改善採用の記録あり。ただし全体PASS・MASTER承認ではない。
- 案04：監督HOLD、技術PASS、演出PASS未付与。通常速度で連続視認が不足、画面取得エラー-3811の報告。今回の新規PASSはない。
- 案05の候補はP024〜027内で接触・圧縮を計2〜3フレーム読ませる最小調整。これは候補であって実行許可や確定設計ではない。

## 過去パイロット v01/v02：Mac内で実読

GitHub取得全ブランチの履歴ファイル名を探索した範囲ではpilot/v01/v02原本なし。Mac内の次の納品フォルダから確認。相対出典は `/Users/hagakengo/Documents/Codex/2026-10-11/` 基準。

- v01：`referenced-chatgpt-conversation-this-is-an-31/outputs/制作結果.md` と `ZERO_CODE_EP01_pilot15_animatic_v01.mp4`。
- v02：`referenced-chatgpt-conversation-this-is-an-32/outputs/比較レビュー_v02.md` と `ZERO_CODE_EP01_pilot15_animatic_v02.mp4`。
- 各原本のSHA256、fps、解像度、音声、全尺デコードは [source_media_checks.json](verification/source_media_checks.json) に実測を保存。レポートのハッシュは [source_documents.json](verification/source_documents.json)。原本は上書きもGitHubへの転載もしない。

v01報告：0〜3秒都市、3〜6秒敵接近、6〜9秒仮HUD、9〜13秒抽象衝突、13〜15秒余韻。接触・回避・反撃の格闘芝居は未制作。CUT01原本未受領。
v02報告：8.70〜9.00秒無音、9.00踏み込み、9.55回避、10.25反撃、10.52衝撃、11.65再接近、12.38二度目接触、12.40後退、12.85音停止。仮敵/HUD、単純作画、聴感・実時間視聴未確認、台帳登録保留。いずれも採用候補・要修正で、完成戦闘アニメや正式構成決定ではない。

これら時刻は過去報告の引用要約であり、本DRAFTの整数フレーム案と同じ値ではない。二度目の接触は今回の簡潔な一連動作案では保留するが、過去決定を削除した意味ではない。

## 承認境界と未解決

- 維持：フード常時着用、顔非表示、無地角形黒バッグ、主人公非発光、武器なし。今回ユーザー条件と既存規則による。
- D1：方向D1選定済み／v1.1候補、MASTER未承認。本パイロットの表示・採用・発動演出は未決定。無地を維持し再設計しない。
- 敵正式デザイン・HUD文言：未決定。過去のWARNING/ERROR等を正式コピーとして流用しない。
- 案04：HOLD。特にREADMEでは敵拳の引き戻し・主人公被弾が記載される。「反撃」のファイル名だけで主人公が反撃する映像と認定しない。攻撃者・被弾者・前後接続を監督が確定するまでF割当なし。
- CUT01原本・過去音源の権利・第三者素材の許諾：今回未確認。過去報告の未受領を現在の全保存先で再探索した結論にはしない。
- v01/v02および案01〜04：技術的読取検査のみ追加。演出・聴感・スマホ再生PASSなし。
