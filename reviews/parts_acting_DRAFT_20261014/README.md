# ZERO CODE — 共通顔でのA/B表情実験

2026-10-14 JST。**全成果DRAFT/HOLD。本人一致・自然な芝居は未達。**

## すぐ評価する

- [A/B通常比較・1秒](laneD/AB_comparison_normal_24fps_DRAFT.mp4) / [半速・2秒](laneD/AB_comparison_half_24fps_DRAFT.mp4)
- [4場面比較画像](laneD/review_preview_DRAFT.png) / [全24コマ](laneD/AB_comparison_all24_DRAFT.png)
- [前回3キー版との比較](laneD/previous_AB_normal_24fps_DRAFT.mp4) / [半速](laneD/previous_AB_half_24fps_DRAFT.mp4)
- [A通常](laneA/normal_24fps.mp4) / [A半速](laneA/half_speed_24fps.mp4) / [パーツシート](laneA/parts_sheet_DRAFT.png)
- [B通常](laneB/normal_24fps.mp4) / [B半速](laneB/half_speed_24fps.mp4)
- [共通基準](laneC/landmark_guide_DRAFT.png) / [QA](laneD/QA.md) / [独立視覚レビュー](laneD/independent_visual_QA.md)

A/Bは同じC/FILMの512×283pxクロップを使用。比較では絵部分を同じ640×354pxへ合わせた。共通の予定は0–5視線、6–11まばたき、12–17笑み、18–23気づき。閉眼のピークはAが0始まり8–9、Bが9で、完全に同じ露出ではない。前回版はまばたきのみで構図も異なるため、同一芝居の厳密比較ではない。

## 何ができたか、何が未達か

Aは瞼・瞳・白目・眉・口・頬の独立ベクターパスと透過PNG、ラスターのベース・前髪を制作。白背景の矩形クリップからは進んだ。ただし肌補修帯、粗いマット、眉の重複、ベースに残る髪は未解決。本番用の完全分離リグではない。24コマは手続き描画で、人手の手描き中割りは0。

Bは6キー、直接座標を指定した中間瞼輪郭9、数値補間9。9枚はスクリプトで個別設計したベクター輪郭であり、人が描いた原画や全顔を描き直した中割りではない（ともに0）。閉瞼の肌塗りと元の眼線の重複が残り、眉は静止したまま。要求した作画修正工程の部分検証に留まる。

Cは傾いた既存顔のランドマークと修正候補を整理。原本のSHA256は一致するが、原本Aと派生したC/FILM比較シートは別画像。Cの斜め顔を真正面とは認定していない。無傾斜正面と角度間の顎・前髪対応の校正は未達。

DはA/B制作を担当せず、共通基準と既存QAを並行確認し、到着したフレーム・ソース・透過を検査。C担当にも独立の視覚確認を依頼。初回不具合をA/Bへ戻し、修正後を再検査した。新規8動画＋参照1動画が24fps・所定尺・全尺decode PASS。通常速度の連続実視聴は**未視聴**。技術PASSは作画・演出PASSではない。

## 実行と保存

最大利用可能4枠を実際に同時稼働：A、B、C、root/D。A/Bの制作、Cの基準・校正候補、Dの検査準備を並行実行。共通クロップはCが先に共有、最終比較とdecodeはA/B完成後。4本の動画を独立同時に完成したという意味ではない。

基点 `2e6147a42f909a4df1f18628a278848329f1b796`、レビュー専用ブランチ `review/parts-inbetween-acting-20261014`。main、MASTER、旧パイロット、原本、過去版を上書きしない。C/FILMは第一候補で正式採用ではない。A/DENSE、B/TVの候補役割と未確定ストーリーを変更しない。

各レーンにソースと露出表を同梱。A再現はPillow/CairoSVG/FFmpeg、B・CはPillow、DはPillow/FFmpeg/ffprobe。macOSフォントパスは他環境で変更が必要。参照画像はreferenceへ同梱。Dの再現：

```sh
python3 laneD/compare_and_check.py laneA/normal_24fps.mp4 laneB/normal_24fps.mp4 reference/previous_blink_normal_24fps.mp4
```

## 次に必要な作業

同じ塗り潰し方法で試作を増やす段階は終了。レイヤーを扱える作画・アニメーションツール上で、専門の作画担当がCの眼窩・閉瞼・眉・前髪の重なりと清潔な顔ベースを手描き校正し、表情キーを承認する必要がある。笑みと気づきは瞼・眉・頬・口を一緒に設計し、実再生で露出と尺を調整する。今回の固定頭部試験は頭部回転や髪の二次動作の解決を証明しない。
