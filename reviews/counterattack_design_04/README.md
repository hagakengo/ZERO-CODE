# 反撃→後退 動作設計案04

**DRAFT / 監督レビュー待ち。技術PASS。演出PASSは付けません。**

基準：案03 `173886a9c6d823267c1bd31477b4c159b16815c1`。独立した2D動作設計であり、完成映像・MASTERではありません。2026-10-13 JST。

## ZIP外の納品物

- [案04単独 H.264 MP4](video/counterattack_design_04_24fps.mp4)
- [案03/04比較 H.264 MP4](comparison/03_vs_04_24fps.mp4) 左03・右04。同一P番号。
- [キー姿勢](design_keyposes_04.png)、[全72フレーム](frames)、[全フレーム一覧](verification/all_72_frames.png)
- [全資料ZIP](ZERO_CODE_counterattack_design_04_review.zip)
- [技術検証](verification/submission_checks.json)、[保護ファイル検査](verification/protected_files.json)、[全72時点の解析](verification/temporal_analysis.json)、[SHA256](SHA256.json)

比較PNG：[P023](comparison/03_vs_04_P023.png)、[P024](comparison/03_vs_04_P024.png)、[P025](comparison/03_vs_04_P025.png)、[P026](comparison/03_vs_04_P026.png)、[P028](comparison/03_vs_04_P028.png)、[P031](comparison/03_vs_04_P031.png)、[P035](comparison/03_vs_04_P035.png)、[P040](comparison/03_vs_04_P040.png)、[P046](comparison/03_vs_04_P046.png)、[P050](comparison/03_vs_04_P050.png)、[P051](comparison/03_vs_04_P051.png)

単独1080×1920、比較2160×1920。固定カメラ、24fps、P000〜071、72フレーム、3.000秒、音声なし。GitHubで再生できない場合はRaw / Downloadを使用。ZIP外にも全動画・PNGを配置しています。

## 変更点

- P023の拳先と腹部に50pxの空隙。P024で空隙0px、P025で拳を52px押し込み、局所輪郭を52px圧縮。横長の拳とほぼ水平の前腕を最前面に描画し、縦向き前腕との一体化を避ける。
- 腹部P025、胸P026、頭P029以後、腰P031以後。胸が左へ退く間、頭は右に残り、腰はP030まで保持する。部位間の輪郭差を強調。
- バッグは独立した回転と位置遅れを追加。P028〜031で遅れ、P035〜040に揺り戻し、P042で収束。角形・無地・黒を維持。物理シミュレーションではなく演出的なキー補間。
- P042〜051の主人公姿勢は案03とデータ完全一致。P050接地・P051沈み込みを維持。フード、顔非表示を継承。脚の色線は従来のリグ検証表示。

## 自己点検と限界

主要11姿勢および全72フレーム一覧を目視確認。接点と局所圧縮、胸・頭・腰の姿勢差、バッグの遅れと揺り戻しを確認。H.264デコード、フレーム数、fps、長さを両動画で検査済み。

QuickTime通常速度で単独を2回再生開始し、終端到達を確認。比較も通常速度で2回再生し終端到達を確認。単独の再生はラベル修正前（動作同一）、比較は最終版。画面取得は離散的で、一部スクリーンショットはウインドウの変形を含みました。連続画面録画は取得していません。全72時点の直接幾何解析はタイミングと接触位置を示しますが、知覚的な読みやすさを証明しません。

したがって「通常速度の連続映像で一目で読める」は**未確定／監督レビュー待ち**。接触は短く、バッグの揺り戻しの大きさ、頭の残りの自然さは監督確認事項です。技術PASSを演出PASSに置き換えません。

## 保護・再現

基準の全追跡ファイルをバイト比較し一致。追加は案04ディレクトリのみ。案01〜03、既存素材、mainは変更なし。外部r15.2 f226〜233へアクセスなし。公開・MASTER昇格・本番反映なし。

Python3 / Pillow / ffmpeg / ffprobe / macOS Helvetica。案03を隣に保持し `python3 source/build_design_04.py` で描画・技術検証を再現。README・保護検査・ZIPは提出記録であり描画スクリプトの再実行で更新されません。
