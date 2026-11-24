# 「今日の冬美」の準備（はじめに1回だけ）

ここに書いてある準備をすると、毎朝5時に自動でサイトが更新されます。費用はかかりません（¥0）。
わからないところは、この手順書ごと Claude に見せて「ここを手伝って」と言ってください。

## 1. GitHub（プログラムとデータの置き場所）
1. https://github.com でアカウントを作ります。
2. 新しいリポジトリを作ります。名前は `fuyumi-site` など。**必ず「Private（非公開）」**にします。
   （公開にすると、映像の一覧が検索で見つかりやすくなるためです）
3. このフォルダの中身をそのリポジトリに入れます（Claude が手伝えます）。

## 2. Cloudflare Pages（サイトを公開する場所）
1. https://dash.cloudflare.com でアカウントを作ります（無料）。
2. 「Workers & Pages → 作成 → Pages → 直接アップロード」でプロジェクト名を **fuyumi** にして作ります。
   サイトのアドレスは `https://fuyumi.pages.dev` のようになります。
3. 「マイプロフィール → APIトークン → トークンを作成 → Cloudflare Pages の編集」でトークンを作ります。
4. アカウントID（ダッシュボード右側に表示）を控えます。

## 3. GitHub に設定を登録する
リポジトリの「Settings → Secrets and variables → Actions」で登録します。

| 種類 | 名前 | 中身 |
|---|---|---|
| Secret | `CF_API_TOKEN` | 2-3 のトークン |
| Secret | `CF_ACCOUNT_ID` | 2-4 のアカウントID |
| Secret | `SHEET_ADD_CSV` | 4 の「追加」シートのCSVのURL |
| Secret | `SHEET_PICK_CSV` | 4 の「おすすめ」シートのCSVのURL |
| Secret | `SHEET_REVIEW_CSV` | 4 の「確認」シートのCSVのURL |
| Variable | `SITE_URL` | `https://fuyumi.pages.dev`（自分のアドレス） |

## 4. Googleスプレッドシート（管理人が使うのはここだけ）
1. 新しいスプレッドシートを作り、`docs/sheet-template.md` の通りに「追加」「おすすめ」「確認」の3つのシートを作ります。
2. 「ファイル → 共有 → ウェブに公開」で、シートごとに **CSV** を選んで公開し、出てきたURLを 3 の表に登録します。
3. 「拡張機能 → Apps Script」に `docs/sheet-apps-script.gs` を貼り付け、毎日動くように設定します。
   これで、サイトからの質問が「確認」シートに自動で届きます。

## 5. YouTube の過去の動画を取り込む（1回だけ）
YouTube の自動取得は、新しい15本までしか見られません。過去の全部を取り込むには、無料の「APIキー」が要ります。
1. https://console.cloud.google.com で「YouTube Data API v3」を有効にし、APIキーを作ります。
2. パソコンで `YT_API_KEY=キー python -m pipeline.run import-backcatalogue` を1回実行します（Claude に頼めます）。
   キーは保存しません。

## 6. ファンクラブの過去の記録を取り込む（数日に分けて自動）
`python -m pipeline.run import-fanclub-history` を数回実行すると、2006年からのテレビ出演記録と冬美便り（題名とリンクだけ）が入ります。
相手のサイトに負担をかけないよう、1回40ページまでにしています。

## 7. 削除依頼の連絡先
`site/config.js` の `contactUrl` に、連絡先（Googleフォームのアドレスなど）を入れてください。個人のメールアドレスは載せない方が安全です。

## 毎日の作業
- Xに投稿したら、「追加」シートにリンクを貼る（10秒）。
- 「確認」シートに質問が来ていたら、「答え」の列に書く（時々）。
- 特別な日のおすすめを自分で選びたい時は「おすすめ」シートに書く（任意）。

## うまく動かない時
GitHub の「Issues」に「データ取得エラー」が立ちます。3日つづけて失敗した時だけ届きます。
ビリビリ動画は自動取得を拒否することがあります。その時はビリビリのリンクも「追加」シートに貼ってください。
