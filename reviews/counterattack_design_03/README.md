# 反撃→後退 動作設計案03

**DRAFT / 監督レビュー待ち。技術PASSは演出PASSではありません。**

案02 c83da181e2239ebf29268cd2c0806ff714a20d04を基準とする2D動作設計案です。完成映像・MASTERではありません。

## 直接確認できる納品物

- [案03単独 H.264 MP4](video/counterattack_design_03_24fps.mp4)
- [案02/03 同フレーム比較 H.264 MP4](comparison/02_vs_03_24fps.mp4)：左02 HOLD、右03 DRAFT
- [主要姿勢PNG](design_keyposes_03.png)
- [全72フレームPNG](frames)、[一覧PNG](verification/all_72_frames.png)
- [全資料ZIP](ZERO_CODE_counterattack_design_03_review.zip)
- [検証結果](verification/submission_checks.json)、[既存ファイル保護検査](verification/protected_files.json)、[SHA256](SHA256.json)

比較PNG：[P023](comparison/02_vs_03_P023.png)、[P024](comparison/02_vs_03_P024.png)、[P025](comparison/02_vs_03_P025.png)、[P026](comparison/02_vs_03_P026.png)、[P028](comparison/02_vs_03_P028.png)、[P031](comparison/02_vs_03_P031.png)、[P035](comparison/02_vs_03_P035.png)、[P046](comparison/02_vs_03_P046.png)、[P050](comparison/02_vs_03_P050.png)、[P051](comparison/02_vs_03_P051.png)

ZIP外に動画・PNGを配置。GitHubで再生できない場合はRaw / Downloadで端末へ保存してください。比較MP4は2160×1920のため端末によって互換性に制限があります。単独は1080×1920。両MP4は固定カメラ・24fps・72フレーム・3.000秒、音声なし、P000〜071。P番号は案02と同一、時刻=P/24秒。比較左側は提出済み案02MP4をデコードしています。

## 案02からの差分

- P023は拳と腹の空隙、P024は拳先の左辺と腹部輪郭を一致させる初接触、P025は腹部局所輪郭を34px圧縮。拳・前腕を胴体より手前に描画し、灰色の非発光輪郭で接点の重なりを分離。腹部輪郭の屈曲を胸とは別に作成。
- 腹部変形はP025開始、胸の後退はP026以後、頭はP028まで保持し以後反応、腰はP028まで保持し以後後退。P035以後は案02の後退へ戻す。バッグは3フレーム遅れの体幹角度を参照し、P040までに元の姿勢へ戻す。
- P042〜051の主人公の姿勢データは案02と完全一致。低い足運び、P050接地、P051沈み込みを維持。
- 黒フード・顔非表示・無地角形黒バッグを継承。脚の色線は従来のリグ検証表示で、衣装の発光ではありません。

## 検証と制約

2026-10-13 JST。両MP4をffprobeで検査しH.264・24/1fps・72フレーム・3秒を確認、ffmpeg全デコードエラーなし。既存追跡ファイルを基準コミットとバイト比較し全一致。変更はこのレビュー追加だけです。

QuickTime Playerで単独・比較を既定の通常速度で開始し、終端到達を確認。再生中UIのサンプル画像と主要10姿勢の一覧を目視確認しました。連続全フレームをリアルタイムに観察した録画検査ではありません。GitHub内蔵プレイヤーは未検証です。

目視では拳の露出と腹の局所輪郭変化を確認。ただし短い接触区間が通常速度で一目で読めるか、胸・頭・腰の因果とバッグの慣性が十分かは監督判定待ち。演出PASSは付けません。静止画中の1-frame/2-frame表示は継承元の注記で、実ファイルのfpsや同一画像保持の検証値ではありません。

案01・案02・main・既存素材・r15.2 f226〜233は変更しません。外部r15.2を開く処理もありません。公開・MASTER昇格・本番反映なし。

## 再現

macOS / Python 3 + Pillow / ffmpeg・ffprobe / Helvetica.ttc。案02を同じreviewsディレクトリに置き `python3 source/build_design_03.py` を実行。ソースは案02姿勢JSONを読み取り、独立した案03へ描画します。README・制作ログ・パッケージ検査は提出時の記録です。
