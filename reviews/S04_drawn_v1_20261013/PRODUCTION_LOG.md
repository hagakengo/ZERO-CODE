# 制作ログ 2026-10-13 JST

- Version: S04 drawn v1 / DRAFT / 第1弾作画テスト。
- Goal: 固定リグ移動から脱し、踏み込み→回避の姿勢・荷重・緩急を作画で検討。
- Tool/model: Python 3 / Pillowによる輪郭描画、FFmpeg H.264。AI画像／動画生成モデルなし。
- Prompt: 今回のユーザー制作指示。追加の生成プロンプトなし。
- Input/reference: DIRECTOR_GUIDELINES.md、AGENTS.md、理念、制作ルール、PROJECT_CONTEXT、README、ROADMAP、PRODUCTION_LOG、bible/VISUAL_BIBLE.md、タイムライン、既存S04ソース／README／制作ログ／原画一覧。
- Sources: 踏み込み ff5600598c95c00f39674ddc3683ef26a863bd43、回避 f12ce0246ad152dbce62873d3893dde3c0e87745。比較元は origin/review/s04-joined-f216-245-20261013 のMP4。
- Review: ユーザーの「紙芝居っぽい」「動きが不自然」「アニメではない」を最優先課題として扱った。GitHub PR一覧にS04レビューPRはなかった。リポジトリの接続版READMEにある演出未判定、通常速度視認の必要性、過去レビューのHOLDを確認。
- Changed/why: 独立新規フォルダのみ追加。18枚の明示作画により、固定胴体のワープを置き換えた。背景は既存踏み込みソースの背景部分を新規フォルダ内に複製して固定使用。補間や雨で動きを隠さない。
- Iteration: 露出合計の初回検査で28fを検出し、加速と接地の中割り2枚を追加して30fに修正。作画一覧の初回配置で最後2枚が収まらなかったため高さを修正。静止確認で足の影位置を足別に直し、爪先支点回転を追加。
- Result: 単独、通常比較、0.5倍比較、通常比較6回ループ、18作画PNG、全30f、露出表、再現ソース、技術検査を制作。技術検査結果は verification/technical.json。
- Worked: 個別ポーズと3/2/1コマの配分を再現可能な形で提出。前後差を比較可能。
- Failed/limitations: 完成作画の柔らかさ・立体感には不足。通常速度を制作側が連続視認できておらず、動きの改善は未判定。詳細な自己批評はREADME。
- Status: 技術検査PASSは仕様・デコードのみ。演出未判定、未採用、非統合。案04 HOLD。
- Next action: ソラが通常速度で見て、踏み込みの重さ、回避の読み、足滑り、身体の硬さ、バッグの慣性を辛口批評。その判断前に本編昇格しない。
