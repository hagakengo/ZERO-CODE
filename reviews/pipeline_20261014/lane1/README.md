# レーン1 — 実ツール検証 / DRAFT・HOLD

観測日: 2026-10-14 JST。Apple Silicon arm64 macOS。

## 実測した結果

- 初期状態の `/Applications`、ユーザーApplications、Homebrew Caskroom、PATH で Blender / Krita / OpenToonz を確認できなかった。インストール済み版は未取得。
- Blender **4.5.14 LTS** 公式Apple Silicon DMGを作業領域 `work/tools` にダウンロードし、アプリをそこへコピー。システムApplicationsや既存アプリを変更していない。
- SHA256: `65134d9b07b20e2fa8d3c9e44f6f44ffb5c9774dd521b95f50387310241ca170`。公式チェックサムに一致。
- ヘッドレス実行、実際の `GREASEPENCIL` オブジェクト・レイヤー・72枚の編集可能なdrawing生成、保存、72PNGレンダリングを実施。
- GUI起動と `gp_timing_DRAFT.blend - Blender 4.5.14 LTS` ウィンドウを CUA で確認し、`gui_verified.png` 保存。初回Quick Setup画面が重なるため、GUI編集・タイムライン再生を検証済みとは扱わない。手動の設定変更は行っていない。ただしGUI初回起動により `~/Library/Application Support/Blender/4.5/config/userpref.blend` が自動生成されたことをGUIログで確認した。作業領域外へのこの設定保存を隠さず記録し、削除・上書きしない。
- Krita / OpenToonz は未インストール、ローカルGUI・ヘッドレス実行は未検証。利用不能と断定していない。今回は Blender の実証を優先し両ソフトの導入は実施しなかった。

## 納品

- `gp_timing_DRAFT.blend`: 本物のGrease Pencilネイティブプロジェクト。1レイヤー、72 drawing keys、各3 strokes。個別点を編集可能。
- `frames/frame_0001.png`〜`frame_0072.png`: 360×640、24fps、3秒。
- `gp_timing_DRAFT.mp4`: 通常速度、H.264。
- `build_gp_test.py`: 完全な再生成ソース。
- `render.log`, `render_manifest.json`, `ffprobe.json`: 実行・構造・尺の証拠。
- `build_vector_test.py`: 未実行のCurve fallback案として保存。今回の動画はこれを使用していない。

## 再現手順

リポジトリルートで、Blender実行ファイルを `BLENDER_BIN` に設定する。今回の実パスはリポジトリの兄弟 `../tools/Blender.app/Contents/MacOS/Blender`。

```sh
BLENDER_BIN='../tools/Blender.app/Contents/MacOS/Blender'
"$BLENDER_BIN" --background --factory-startup --python reviews/pipeline_20261014/lane1/build_gp_test.py
ffmpeg -hide_banner -loglevel error -framerate 24 -start_number 1 -i reviews/pipeline_20261014/lane1/frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -movflags +faststart reviews/pipeline_20261014/lane1/gp_timing_DRAFT.mp4
```

既存成果を保護するため、再実行はこのフォルダをコピーしてから行う。Blenderのネイティブファイル単独からも保存済み72枚のGP drawingを再レンダリングできる。

## 制作実験の意味と限界

目的はネイティブ作画データ→連番→MP4の再現可能な入口を作ること。ボールの接地付近の潰れと軌道、リボンの遅れを実装した。数式から座標を生成したベクター線画であり、人間の手描き作画ではない。C/FILMの顔・髪・衣装は使用せず、同一性・表情芝居は未検証。

技術的な生成成功を、日本の2Dアニメ品質や作画PASSと同一視しない。通常速度のユーザー視聴前につき演出HOLD。簡略化した接地判定、線の見え方、余韻のタイミングには校正余地があり、この試作を本編へ転用しない。

## 公式資料 / 導入制約

- [Blender 4.5公式配布](https://download.blender.org/release/Blender4.5/): 今回実行版4.5.14とSHA256。
- [Krita公式ダウンロード](https://krita.org/en/download/): macOS配布あり。ウェブ表示版とローカル導入版を混同しない。
- [OpenToonz公式配布と利用規約](https://opentoonz.github.io/download/opentoonz.html): macOS配布あり。Apple Silicon上の互換性、描画、書き出しは別途実測が必要。

いずれも導入しただけで作画品質が上がる保証はない。Blender本体は無償で入手できた。外部アセット、商用アドオン、音楽は使用していない。Krita/OpenToonzのネイティブ資産相互運用とライセンス条件の個別評価は未実施。

## 独立QAの結果

親レーンが保存済み.blendを別プロセスで再オープンし、1レイヤー・72 drawing keys・24fps・F1〜72を確認。F36再レンダリングは画素単位一致。PNGバイト列はメタデータで異なるためバイト完全一致は主張しない。MP4全72フレームのデコード、24fps、3秒も確認した。
