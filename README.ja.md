# nixos-cp

NixOS上のAtCoder競技プログラミング環境。デスクトップ背景にダッシュボードを常時表示し、ターミナルから精進→提出→振り返りまでを完結させる。

![Dashboard](docs/screenshots/dashboard.png)

## 概要

NixOS flakeでマシンを競プロワークステーションに変える:

- **ダッシュボード** — Swayのデスクトップ背景に常時表示。レート推移、スキルツリー、ストリーク、コンテスト結果。問題を解くたびに自動更新。
- **CLIツール** — `cp-go` で問題選択からエディタ・ブラウザの起動まで一発。テスト、提出、振り返りまでターミナルで完結。
- **Neovim** — LSP、補完、エディタ内テストランナー (competitest)。nixvimで宣言的に管理。
- **完全再現可能** — `nixos-rebuild switch` 一発で環境構築完了。

## クイックスタート

### 前提条件

- flakes有効のNixOS
- Sway WM

### 1. クローンと設定

```bash
git clone https://github.com/MeJamoLeo/nixos-cp.git
cd nixos-cp
```

`dashboard/watchlist.json` にAtCoderユーザー名を設定:

```json
["あなたのユーザー名"]
```

### 2. ビルド

```bash
sudo nixos-rebuild switch --flake .
```

ダッシュボード、neovim、Firefox、CLIツール、フォント、入力メソッドが全てインストールされる。

### 3. AtCoderログイン

```bash
cp-login
```

Firefoxでatcoder.jpにログイン → DevToolsから `REVEL_SESSION` cookieをコピー → 貼り付け。

### 4. 精進開始

```bash
cp-go
```

これだけ。問題が自動選択され、ブラウザで問題ページが開き、nvimで解答ファイルが開く。

## ダッシュボードパネル

| パネル | 内容 |
|--------|------|
| **HUD** | レート、ストリーク、今日のAC数、次の色までの推定 |
| **Difficulty Log** | 週間練習量(棒) + レート推移(線) + 3ヶ月予測 |
| **Skill Graph** | ベンチマーク問題ACに基づく放射状スキルツリー (典型90, EDPC, ABC) |
| **Streak** | GitHub式20週カレンダー + 10日間タイムスキャッター |
| **Speed** | コンテストごとのラップタイム (A/B/C/D分割) |
| **Compare** | 月別AC比較 + 直近コンテストのperf/delta |
| **Language** | 言語別AC数 |

AtCoder/kenkoooo APIから2分ごとにデータ更新。

## CLIツール

```bash
cp-go              # 問題自動選択 → ブラウザ + nvim → テスト → 提出 → insight
cp-new abc453      # コンテスト全問題のディレクトリ作成 + テストケースDL
cp-submit main.py  # クリップボードにコピー + 提出ページを開く (コンテスト中は自動提出)
cp-review abc453   # コンテスト後の振り返り: タグ + insight
cp-demo            # 固定の簡単な問題でフルワークフロー体験
cp-login           # AtCoderセッションcookie設定
```

## Neovimキーバインド

| キー | 動作 |
|------|------|
| `Space+cr` | テストケース実行 (competitest) |
| `Space+cs` | 保存 + 提出 |
| `-` | ファイルエクスプローラー (oil.nvim) |
| `Space` | 全キーバインド表示 (which-key) |
| `gd` | 定義ジャンプ |
| `K` | ホバードキュメント |

## ウォッチリスト

他のユーザーのダッシュボードを閲覧:

```bash
# ウォッチリスト編集
vim dashboard/watchlist.json    # ["自分", "友達1", "友達2"]

# ユーザー切り替え
Super+`
```

## プロジェクト構成

```
├── flake.nix                   # NixOS flakeエントリポイント
├── hosts/x1carbon/             # マシン固有のNixOS設定
├── modules/
│   ├── sway.nix                # Sway WM設定 (キーバインド、入力、起動)
│   └── nvim/                   # Neovim設定 (nixvim)
├── dashboard/
│   ├── dashboard.py            # GTK4 + WebKit6 レンダラー
│   ├── fetch_stats.py          # AtCoder/kenkoooo APIデータ取得
│   ├── dashboard.html          # CSSレイアウト
│   └── js/                     # モジュラーJS (difficulty-log, streak, skill-graph等)
├── tools/                      # CLIツール (cp-go, cp-submit, cp-new等)
└── docs/                       # ワークフロー図 (mermaid)
```

## カスタマイズ

### 対象ユーザー変更

`dashboard/watchlist.json` を編集。最初のエントリがプライマリユーザー。

### キーバインド追加

`modules/sway.nix` を編集。修飾キーは `Super` (Mod4)。

### ダッシュボードパネル変更

各パネルは `dashboard/js/` 内の独立したJSファイル。個別に編集可能。

### スキルツリー調整

ベンチマーク問題は `dashboard/fetch_stats.py` の `BENCHMARKS` で定義。スキルノードごとに問題を追加・変更可能。

## 予測モデル

ダッシュボードは週間練習量に基づく3ヶ月のレート予測を表示:

- **効率はレートに応じて逓減** — 色変記事の統計から校正された指数減衰曲線
- **バンド目標** — 「3ヶ月で次の色に到達するには週Xのdiffが必要」
- **コンテストモード** — ライブコンテスト中を検出し、curl経由の自動提出を有効化

## ライセンス

MIT
