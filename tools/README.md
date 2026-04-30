# CP Tools

AtCoderの精進ワークフローをターミナルから完結させるCLIツール群。
ブラウザは問題閲覧と提出のみ。SNSやトップページを経由しない。

## セットアップ

```bash
cp-login          # ブラウザからREVEL_SESSION cookieを貼り付け（初回 or 6ヶ月ごと）
```

## ワークフロー

### 精進 (`cp-go`)

`cp-go` 一本で「問題選択 → 解答 → 提出 → 記録」のループを回す。問題選択は
[AtCoder Problems Recommendation](https://kenkoooo.com/atcoder/) のアルゴリズムを
忠実に移植したもの。

```bash
cp-go                            # 1問目=Easy、以降=Moderate
cp-go easy                       # セッション全部 Easy で固定
cp-go moderate                   # 同 Moderate
cp-go difficult                  # 同 Difficult
```

1. AtCoder Problems Recommendation から未提出問題を選択
2. Firefoxで問題ページ + nvimが開く
3. 解く → `Space+cr` テスト → `:wq`
4. oj test → cp-submit → 結果入力 → タグ選択 → insight記入
5. 次へ

### コンテスト (`cp-new`)

```bash
cp-new abc453                    # 全問題(a-f)のディレクトリ作成 + テストケースDL
cd ~/cp/contests/abc453/a
nvim main.py                     # 解く + Space+cr テスト
:wq
cp-submit main.py                # コンテスト中: curl自動提出
                                 # コンテスト外: クリップボード + ブラウザ
cd ../b                          # 次の問題へ（insightは後回し）
...

# コンテスト後に振り返るときは各問題ディレクトリで cp-finish を再実行
cd ~/cp/contests/abc453/a && cp-finish main.py
```

- コンテスト中はinsight/タグをスキップ（速度優先）
- 後で `cp-finish` を再実行すると insight/タグが追記できる

## 提出 (`cp-submit`)

```bash
cp-submit main.py
```

| 状況 | 動作 |
|------|------|
| コンテスト中 | curl POSTで自動提出（速い） |
| コンテスト外 | クリップボードにコピー + ブラウザで提出ページを開く |
| 自動提出失敗時 | ブラウザにフォールバック |

コンテスト中かどうかは `stats.json` のコンテスト情報から自動判定。

## ローカルテスト

nvim内で `Space+cr` (competitest) または:

```bash
cp-test main.py                  # oj test のラッパー（.py→python3, .cpp→g++自動判定）
```

## Insight

`~/cp/insights/<problem_id>.md` に1問1ファイルで蓄積。

```markdown
# abc453_d

## WA 2026-04-17 21:30
tags: [BFS/DFS]
くそ、TLEかよ

## AC 2026-04-17 22:10
tags: [Union-Find]
辺を頂点に変換する発想、これ覚えておく
```

- 提出ごとに追記（ACでもWAでも）
- タグはスキルツリーのノード名からfzfで選択（フォーマット統一）
- `:wq` で保存、`:q!` でスキップ

## ディレクトリ構成

```
~/cp/
├── contests/              # コンテスト・精進の解答
│   ├── abc453/
│   │   ├── .contest_mode  # cp-newが作成（コンテスト中フラグ）
│   │   ├── a/
│   │   │   ├── main.py
│   │   │   ├── .problem_url
│   │   │   └── test/      # oj downloadのテストケース
│   │   └── b/ ...
│   └── abc086/ ...
├── insights/              # 1問1ファイル、追記型
│   ├── abc453_d.md
│   └── abc086_a.md
├── library/               # 自作スニペット（将来）
└── templates/             # 解答テンプレート（将来）
```
