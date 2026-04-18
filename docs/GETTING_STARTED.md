# Getting Started

## 前提条件

- NixOS（flakes有効）
- Sway WM
- AtCoderアカウント

### NixOSのインストール

NixOSが未インストールの場合: [NixOS Manual](https://nixos.org/manual/nixos/stable/#sec-installation)

flakesを有効にする（`/etc/nixos/configuration.nix`に追加）:
```nix
nix.settings.experimental-features = [ "nix-command" "flakes" ];
```

## セットアップ

### 1. クローン

```bash
git clone https://github.com/MeJamoLeo/nixos-cp.git ~/nixos-cp
cd ~/nixos-cp
```

### 2. ユーザー名の設定

```bash
# AtCoderのユーザー名を設定
echo '["YourAtCoderUsername"]' > dashboard/watchlist.json
```

友達のダッシュボードも見たい場合:
```json
["YourUsername", "friend1", "friend2"]
```

### 3. ハードウェア設定

`hosts/x1carbon/hardware-configuration.nix` は X1 Carbon Nano 固有です。
自分のマシンの設定に置き換えてください:

```bash
# 自分のマシンのhardware-configurationを生成
sudo nixos-generate-config --show-hardware-config > hosts/x1carbon/hardware-configuration.nix
```

### 4. ビルド

```bash
sudo nixos-rebuild switch --flake ~/nixos-cp
```

これで以下がインストールされます:
- ダッシュボード（Sway背景に自動表示）
- Neovim（LSP + competitest）
- Firefox + wofi
- CLIツール（cp-go, cp-submit等）
- fcitx5 + mozc（日本語入力）
- TLP省電力

### 5. AtCoderログイン

```bash
cp-login
```

1. Firefoxで https://atcoder.jp にログイン
2. F12 → Storage → Cookies → `REVEL_SESSION` の値をコピー
3. ターミナルに貼り付け

セッションは約6ヶ月有効です。

### 6. 初回データ取得

```bash
cd ~/nixos-cp/dashboard
nix-shell --run 'bash fetch_all.sh'
```

これでダッシュボードにデータが表示されます。以降は2分ごとに自動更新。

## 使い方

### 精進を始める

```bash
cp-go
# または Super+G
```

問題が自動選択され、ブラウザとnvimが開きます。

### コンテストに参加する

```bash
cp-new abc453
cd ~/cp/contests/abc453/a
nvim main.py
```

### 提出する

nvim内で:
- `Space+cr` — テスト実行
- `Space+cs` — 保存+提出

### キーバインド

| キー | 動作 |
|------|------|
| `Super+G` | 精進セッション開始 |
| `Super+`` | ダッシュボードユーザー切り替え |
| `Super+Return` | ターミナル |
| `Super+D` | アプリランチャー(wofi) |
| `Super+B` | Firefox |
| `Super+Q` | ウィンドウ閉じる |
| `Ctrl+Space` | 日本語入力切り替え |

### ディレクトリ構成

精進を始めると、以下のディレクトリが作られます:

```
~/cp/
├── contests/           # 解答ファイル
│   └── abc453/a/main.py
├── insights/           # 振り返りメモ
│   └── abc453_a.md
└── srs.json            # 忘却曲線データ
```

## トラブルシューティング

### ダッシュボードが表示されない

```bash
# プロセス確認
pgrep -af dashboard.py

# 手動起動
cd ~/nixos-cp/dashboard && nix-shell --run 'python dashboard.py' &
```

### cp-goで「stats not found」

```bash
# データを手動取得
cd ~/nixos-cp/dashboard
nix-shell --run 'bash fetch_all.sh'
```

### AtCoderにログインできない

```bash
# cookieを再設定
cp-login
```

ブラウザでAtCoderにログインし直してからcookieをコピーしてください。

### 提出できない（practice mode）

コンテスト外ではCloudflare Turnstileのため、ブラウザでの手動提出が必要です。
`cp-submit` がクリップボードにコードをコピーし、提出ページを開きます。
Ctrl+V → 言語選択 → Submit。
