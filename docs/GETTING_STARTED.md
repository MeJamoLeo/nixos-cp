# Getting Started

## 前提条件

- NixOS（flakes有効）
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

### 3. 構成を選ぶ

| 構成 | 用途 | 含まれるもの |
|------|------|-------------|
| `minimal` | 既存環境に追加 | CLIツール + ダッシュボード |
| `full` | GUI付きフル環境 | minimal + Neovim + Firefox + Sway + fcitx5 |
| `x1nano` | X1 Nano Gen2 専用 | full + nixos-hardware + 指紋認証 |

### 4. ハードウェア設定

`minimal` または `full` を使う場合、自分のマシンの設定を生成:

```bash
# ハードウェア設定を生成
sudo nixos-generate-config --show-hardware-config > hosts/minimal/hardware-configuration.nix

# hosts/minimal/configuration.nix (または hosts/full/) の imports に追加
```

`hosts/minimal/configuration.nix` を編集:
```nix
{
  imports = [
    ../../profiles/minimal/configuration.nix
    ./hardware-configuration.nix  # この行を追加
  ];
  networking.hostName = "my-machine";
}
```

### 5. ビルド

```bash
# 選んだ構成でビルド
sudo nixos-rebuild switch --flake ~/nixos-cp#minimal   # CLIのみ
sudo nixos-rebuild switch --flake ~/nixos-cp#full      # GUI付き
sudo nixos-rebuild switch --flake ~/nixos-cp#x1nano  # X1 Nano Gen2
```

### 6. AtCoderログイン

```bash
cp-login
```

1. Firefoxで https://atcoder.jp にログイン
2. F12 → Storage → Cookies → `REVEL_SESSION` の値をコピー
3. ターミナルに貼り付け

セッションは約6ヶ月有効です。

### 7. 初回データ取得

```bash
cd ~/nixos-cp/dashboard
nix-shell --run 'bash fetch_all.sh'
```

これでダッシュボードにデータが表示されます。以降は2分ごとに自動更新。

## 使い方

### 精進を始める

```bash
cp-go
# または Super+G (full/x1nano)
```

問題が自動選択され、ブラウザとnvimが開きます。
セッション内の流れ: ウォームアップ → メイン問題 → テスト → 提出 → 振り返り → 次の問題

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

### キーバインド (full/x1nano)

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
