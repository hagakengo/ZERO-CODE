# 背景・音響 独立制作 DRAFT / HOLD

2026-10-14 JST。AI CITYの空間・色彩と、3秒芝居の音響を、本編の作画から切り離して制作した。正式採用・正史統合・本編完成・公開許可ではない。

## 納品物

- `AI_CITY_background_DRAFT.svg`：1080×1920、編集可能な純ベクター背景レイアウト。7個の名前付きグループ（空／遠景／中景／濡れた道／前景／環境照明／霧）。キャラクター、D1、敵、HUD文字は含まない。
- `AI_CITY_background_DRAFT.png`：同SVGからbundled sharpでレンダリングした1080×1920確認用画像。
- `stem_air_DRAFT.wav`：空気の低域ノイズ。中央配置。
- `stem_city_hum_DRAFT.wav`：低い都市設備音。やや左。
- `stem_notice_cue_DRAFT.wav`：異変への注意を促す仮の短音。やや右。音源・原因・能力・敵を設定しない。
- `mix_3s_DRAFT.wav`：上記3ステムのミックス。3秒、48kHz、16bit、stereo。
- `build_assets.py`：SVGと音の再現ソース。Python標準ライブラリのみ。
- `qa_manifest.json`：実測時間、sample数、peak/RMS、seed、SHA256。

## 背景・色彩の狙いと制約

Visual Bible §4/8を参照し、暗い巨大建築、濡れた道、シアン／青、霧、少量の橙を配置。黒 #060c19、建築 #0a1523、奥の青 #142a3d、シアン #3bb8ca、橙 #bd794d。中央は芝居用の余白を残す。手前が濃く奥が明るい値設計で深度を作る。

現状は幾何学的なレイアウト検査で、完成美術ではない。反射は簡略記号、霧はグラデーション、背景の筆致・材質・光の整合・人物との接地／影は未実装。実際のC/FILM作画と合成して視線誘導をレビューするまでHOLD。服を発光させる処理は行っていない。

## 3秒音響プラン

レーン2共通の1-based F001–072 / 24fps。空気音と設備音は全尺。レーン2との共通合図に合わせ、異変の仮音開始はF025（1.000秒、sample 48000、0-basedならF024）。短いattackと減衰で視線先行のきっかけを提示する。画の完成後に音量・パン・余韻を合わせ直す。仮音は台詞ではなく、声の主や異変の正体を確定しない。既存の旧3秒案F048異変とは別の今回用案で、過去版を変更しない。

実測mix peak -22.91 dBFS、RMS -37.90 dBFS。余裕を残したレビュー用小音量で、納品ラウドネス規格を満たした宣言ではない。通常速度のユーザー視聴・聴取、人物との音画同期、スマートフォン再生は未検証。評価時はまず小音量から適切な聴取レベルに調整する。

## 再現手順

リポジトリrootから `python3 reviews/pipeline_20261014/lane4/build_assets.py`。既存本編／MASTERは変更せず、このlane4内の生成物だけを再生成する。

PNGはNode.js + sharpでSVGを開き、`.png().toFile(...)` を使う。実測で利用したNodeは `/Users/hagakengo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`、sharpは同dependencies内 `node/node_modules/sharp`。別環境はNode + sharpの設置が必要。macOS Quick Lookのサムネイルは正方形にcropされたため納品から除外し、代用しない。

SVGは一般的なSVG編集ソフトで7グループを編集できる。Kritaは通常SVGをラスタライズするため、このSVGをKritaネイティブのレイヤー構造として扱ったとは主張しない。Krita/OpenToonz/Blenderへの読込・変換・レイヤー保持は本レーン未検証。

## 来歴・権利・検証

参照：AGENTS、理念、制作規則、PROJECT_CONTEXT、README、ROADMAP、PRODUCTION_LOG、DIRECTOR_GUIDELINES、Visual Bible、過去parallel_production lane4演出メモ。既存参照画像をコピーせず、今回のベクター図形と波形は全てこのソースから独立生成。音楽・音声・市販録音・外部サンプルなし。権利者への譲渡や商標調査を完了したという主張ではない。

SVG XML parseと1080×1920 PNG寸法、全WAVの144000 sample/ch stereo/48kHz/16bit、sample peak、SHA256を確認。背景を実見し、簡素な都市レイアウトとして確認。音の聴取は未実施。技術検査と作画／演出／音響承認を分ける。

次工程：人物原画の位置と目線に合わせレイアウト調整→背景担当の作画校正→人物shadow/濡れた面反射の合成→完成芝居に同期した音編集→ユーザー通常速度視聴で評価。全素材DRAFT/HOLDのまま維持する。
