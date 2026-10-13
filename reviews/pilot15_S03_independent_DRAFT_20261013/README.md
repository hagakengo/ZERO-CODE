# Pilot15 S03「踏み込み前の間」独立DRAFT

2026-10-13 JST。レビュー専用の実制作2Dレイアウトアニメーション。未採用・本編未統合。技術PASSと演出判定は別扱い。

- [MP4](video/S03_pre_dash_tension_DRAFT_24fps.mp4)
- [主要PNG](keyframes.png) / [全72フレーム](frames)
- [露出表CSV](exposure_sheet.csv) / [露出表JSON](verification/exposure_sheet.json)
- [技術検査](verification/technical_checks.json) / [保護555ファイル検査](verification/protected_files.json)
- [制作ログ](PRODUCTION_LOG.md) / [再現ソース](source/render_s03.py)

## 確定範囲

`TIMELINE_DRAFT.md` と `timeline_draft.csv` に基づき、S03は **F144〜215（終了排他216）、6.000〜9.000秒、72f**。「踏み込み前の間」であり、F144〜208は緊張維持、F209〜215は意図的静寂窓。戦闘の踏み込みはS04 F216〜229なので、本DRAFTでは開始しない。

1080×1920、9:16、24fps。F144〜208は通常動作の2コマ打ち、F209〜215は7f保持。S02終端の構えと足位置を継ぎ、両足を固定したまま腰と肩を低く前へ圧縮し、袖とバッグを遅れて収束させる。F216に荷重を渡せる姿勢で停止する。

背景、照明、人物サイズ、黒フード、顔非表示、無地角形黒バッグをS02から維持。敵は特徴のない低コントラスト仮シルエット。D1、HUD、文字、武器、接触、正式敵デザインを追加していない。音声ストリームなし。

## 判定と保護

技術検査は解像度、fps、尺、72f、全尺デコード、PNG読込、2f保持、7f静寂保持、両足固定、既存追跡ファイル不変を確認する。通常速度の連続視認とスマホ視認を実施していないため、**演出判定は未確定**。静止画と数値検査を演出PASSとして扱わない。

S01・S02は未採用のまま。案04は演出HOLD継続。main、MASTER、案01〜04、r15.2、v01/v02、既存資産を変更せず、本編統合・公開・MASTER昇格を行わない。

再現は `python3 source/render_s03.py`、検査は `python3 source/verify.py`。Python、Pillow、FFmpeg/ffprobeを使用。
