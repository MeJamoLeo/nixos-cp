# nixos-cp

NixOS上のAtCoder競技プログラミング環境。デスクトップ背景にダッシュボードを常時表示し、ターミナルから精進→提出→振り返りまでを完結させる。

![Dashboard](docs/screenshots/dashboard.png)

## 概要

NixOS flakeでマシンを競プロワークステーションに変える:

- **ダッシュボード** — Swayのデスクトップ背景に常時表示。レート推移、スキルツリー、ストリーク、コンテスト結果。問題を解くたびに自動更新。
- **CLIツール** — `cp-go` で問題選択からエディタ・ブラウザの起動まで一発。テスト、提出、振り返りまでターミナルで完結。
- **忘却曲線復習** — SRSが苦手な問題を記録し、最適なタイミングで再出題する。
- **Neovim** — LSP、補完、エディタ内テストランナー (competitest)。nixvimで宣言的に管理。
- **完全再現可能** — `nixos-rebuild switch` 一発で環境構築完了。

## クイックスタート

### 前提条件

- flakes有効のNixOS
- Sway WM (full/x1nano構成の場合)

### 1. クローンと設定

```bash
git clone https://github.com/MeJamoLeo/nixos-cp.git
cd nixos-cp
```

`dashboard/watchlist.json` にAtCoderユーザー名を設定:

```json
["あなたのユーザー名"]
```

### 2. 構成を選んでビルド

```bash
# CLIツール + ダッシュボードのみ（エディタ・ブラウザは自前）
sudo nixos-rebuild switch --flake .#minimal

# フルGUI: minimal + Neovim + Firefox + Sway + fcitx5
sudo nixos-rebuild switch --flake .#full

# X1 Carbon: full + ハードウェア設定 + 指紋認証 + TLP
sudo nixos-rebuild switch --flake .#x1nano
```

`minimal` と `full` では自分のマシンの `hardware-configuration.nix` が必要:

```bash
sudo nixos-generate-config --show-hardware-config > hosts/minimal/hardware-configuration.nix
# hosts/minimal/configuration.nix の imports に追加
```

### 3. AtCoderログイン

```bash
cp-login
```

Firefoxでatcoder.jpにログイン → DevToolsから `REVEL_SESSION` cookieをコピー → 貼り付け。

### 4. 精進開始

```bash
cp-go
# または Super+G (full/x1nano構成のみ)
```

これだけ。問題が自動選択され、ブラウザで問題ページが開き、nvimで解答ファイルが開く。

## 構成ティア

| ティア | 内容 |
|--------|------|
| **minimal** | ダッシュボード + CLIツール。エディタ・ブラウザ・WMなし。 |
| **full** | minimal + Neovim (nixvim) + Firefox + Sway + fcitx5 + wofi + フォント |
| **x1nano** | full + X1 Carbonハードウェア設定 + 指紋認証 + TLP省電力 |

## ダッシュボードパネル

| パネル | 内容 |
|--------|------|
| **HUD** | レート、ストリーク、今日のAC数、次の色までの推定 |
| **Difficulty Log** | 週間練習量(棒) + レート推移(線) + 3ヶ月予測 |
| **Skill Graph** | ベンチマーク問題ACに基づく放射状スキルツリー (典型90, EDPC, ABC) |
| **Streak** | GitHub式20週カレンダー + 10日間タイムスキャッター |
| **Insight** | 直近の振り返りメモ |
| **Speed** | コンテストごとのラップタイム (A/B/C/D分割) |
| **Compare** | 月別AC比較 + 直近コンテストのperf/delta |
| **Language** | 言語別AC数 |

AtCoder/kenkoooo APIから2分ごとにデータ更新。

## CLIツール

```bash
cp-go              # 練習セッション: AtCoder Problems Recommendation → nvim → テスト → 提出
cp-new abc453      # コンテスト全問題のディレクトリ作成 + テストケースDL
cp-submit main.py  # クリップボードにコピー + 提出ページを開く (コンテスト中は自動提出)
cp-finish main.py  # テスト → 提出 → 結果記録 → insight (cp-goから呼ばれる)
cp-login           # AtCoderセッションcookie設定
```

## 精進ワークフロー

`cp-go` は連続精進セッションを実行:

1. **問題選択** — AtCoder Problems Recommendation を移植 (Easy/Moderate/Difficult)
   - デフォルト: 1問目=Easy、以降=Moderate
   - `cp-go [easy|moderate|difficult]` でセッション全体の難易度固定
2. **解答** — ブラウザで問題を開く + nvim で main.py / main.cpp 編集
3. **解答後** — ローカルテスト → 提出 → 結果記録 → insight記入 (任意)

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
├── flake.nix                   # NixOS flake (minimal/full/x1nano)
├── profiles/
│   ├── minimal/                # ベース: CLIツール + ダッシュボード
│   └── full/                   # GUI: Sway + Neovim + Firefox + fcitx5
├── hosts/
│   ├── minimal/                # 汎用minimalデプロイ用ホストラッパー
│   ├── full/                   # 汎用fullデプロイ用ホストラッパー
│   └── x1nano/               # X1 Carbon固有 (ハードウェア, 指紋認証, TLP)
├── modules/
│   ├── sway.nix                # Sway WM設定 (キーバインド、入力、起動)
│   └── nvim/                   # Neovim設定 (nixvim)
├── home/                       # 共有home-managerモジュール (shell, git, starship)
├── dashboard/
│   ├── dashboard.py            # GTK4 + WebKit6 レンダラー
│   ├── fetch_stats.py          # AtCoder/kenkoooo APIデータ取得
│   ├── dashboard.html          # CSSレイアウト
│   └── js/                     # モジュラーJS (difficulty-log, streak, skill-graph等)
└── tools/                      # CLIツール (cp-go, cp-submit, cp-new等)
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
