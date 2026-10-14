# C/FILM provenance — DRAFT / HOLD

調査日: 2026-10-14 JST。外部生成サービスへの画像アップロードは実施していない。原本・既存枝は変更せずAPI読取とコピーのみ。

## ハッシュの対象を訂正

要求された SHA-256 bc3697df6c3c080985b226b285627d449124f1b9b58c9326ea6a316890057fad と一致する user_reference_original.png を回収した。1536×1024 PNG。これはユーザー添付の入力原本であり、C/FILM生成結果そのものではない。

根拠: reviews/protagonist_A_style_DRAFT_20261014/REVIEW.md および source/SHA256.txt。REVIEWには「ユーザーが本スレッドに添付した1536×1024 PNGをバイト単位でコピー」「ChatGPTのsandboxファイル自体は取得できていないため、それとのバイト一致は未検証」と明記。

## 回収画像

- user_reference_original.png: 入力原本、1536×1024、SHA-256 bc3697df6c3c080985b226b285627d449124f1b9b58c9326ea6a316890057fad。
- A_B_C_comparison_DRAFT.png: 生成比較シート全体、1536×1024、SHA-256 35e61d728ca2c6b9e7c0f3246157167687abe03552b8955ceee2549b99bf5a21。
- original_C_reference_DRAFT.png: C/FILM胸上切り出し、512×283、SHA-256 efac54c2cd52d93611c42d18ff6bc96d1270b92a76a1aad7838d9d0ef6cedb51。

既存C/FILM切り出しは比較シートの座標 x=1024..1535, y=49..331 とRGBピクセル完全一致。独立した高解像度のC/FILM顔原画は今回の確認範囲では未発見。比較シート全体が取得可能な生成出力で、顔領域の実解像度は512×283。

## 生成記録

REVIEW.mdは built-in imagegen を使用、モデル名詳細未提供と記載。作成コミット fcd6b31f58e77e04fee11e51b3601a5e7db40d7e の作者日時は 2026-10-14T01:42:41+09:00。これは保存コミットの日時であり正確な生成時刻ではない。

GENERATION_PROMPT.txt は初回保存コミットと現行の両方で文字列 `undefined` のみ。従ってC/FILM生成プロンプト全文と正確な生成日時は未確認。元入力画像を生成したGPT会話のプロンプト・日時・モデルも未確認。権利、第三者権利クリアランス、商用利用の承認は未確認。ハッシュ一致を権利確認として扱わない。

## 9:16適性

512×283の顔画像は既に頭上が切れている。高さ283を維持して9:16に切ると幅約159pxとなり、顔と髪を大きく失う。1080×1920全面に拡大するには約6.8倍、720×1280でも約4.5倍の拡大となる。縦型フル画面の完成顔アップには不適切。

Vコンテでは再描画・変形せず、既存512×283を等比の横長インセットとして表示し低解像度/HOLDを明示するか、明示プレースホルダーにする。新規高解像度顔生成や補完による原本扱いはしない。

## 参照

- https://github.com/hagakengo/ZERO-CODE/commit/fcd6b31f58e77e04fee11e51b3601a5e7db40d7e
- https://github.com/hagakengo/ZERO-CODE/blob/review/cfilm-eye-restore-20261014/reviews/protagonist_A_style_DRAFT_20261014/REVIEW.md
- https://github.com/hagakengo/ZERO-CODE/blob/review/cfilm-eye-restore-20261014/reviews/protagonist_A_style_DRAFT_20261014/source/SHA256.txt
- https://github.com/hagakengo/ZERO-CODE/blob/review/cfilm-eye-restore-20261014/reviews/cfilm_gp_acting_DRAFT_20261014/assets/SOURCE_SHA256.txt
