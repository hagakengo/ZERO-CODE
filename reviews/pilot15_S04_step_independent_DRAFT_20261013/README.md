# Pilot15 S04 踏み込み 独立DRAFT

2026-10-13 JST。F216〜229の14fのみ。S04全体F216〜245のうち回避F230〜245は未制作。未採用・本編未統合・非公開。

- [MP4](video/S04_combat_step_DRAFT_24fps.mp4)
- [主要PNG](keyframes.png) / [全14フレーム](frames)
- [露出表](exposure_sheet.csv) / [技術検査](verification/technical_checks.json)
- [既存ファイル保護検査](verification/protected_files.json)
- [再現ソース](source/render_s04.py) / [検査ソース](source/verify.py)
- [制作ログ](PRODUCTION_LOG.md)

1080×1920、9:16、24fps、14f（0.583333秒）、瞬間動作の1コマ打ち、無音。S03終端の腰位置・足位置から開始。F216〜219で追加荷重、F220〜226で左足支持のまま右足を低く前方へ送る。F227で接地しF229まで腰で受ける。足位置は投影座標上のレイアウト案で、身体力学の演出PASSではない。

S03のPillow製2Dレイアウト描画を継承した実フレームアニメーション。正式な完成作画ではない。黒フード、顔非表示、無地角形黒バッグ、主人公非発光。敵は既存の特徴なし仮シルエットのまま。敵正式デザイン、D1、HUD、攻守・勝敗を確定していない。接触は描かない。

技術PASSは映像規格・デコード・フレーム対応・運動パラメータ・既存ファイル不変の検査結果。主要PNGの静止視認のみ実施。通常速度連続視聴・スマホ視認・監督承認は未実施、**演出未判定**。S01/S02未採用、S03演出未判定、案04 HOLDを維持。main/MASTER/既存素材の変更、統合、公開は行わない。

再現: `python3 source/render_s04.py`、検査: `python3 source/verify.py`。Python/Pillow/FFmpegを使用。S03コミットfc3fdecを基点に本フォルダのみ追加。
