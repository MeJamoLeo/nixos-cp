# nixos-cp Workflow

## 精進フロー

```mermaid
flowchart TD
    START([ターミナル]) --> CPGO[cp-go]
    CPGO --> SELECT{問題選択}
    SELECT -->|WA復習あり| WA[WA Queue最優先]
    SELECT -->|スキルツリー未AC| SKILL[ベンチマーク問題]
    SELECT -->|なし| RANDOM[レート+0〜200ランダム]
    
    WA --> SETUP
    SKILL --> SETUP
    RANDOM --> SETUP
    
    SETUP[ディレクトリ作成 + テストケースDL] --> BROWSER[Firefox: 問題ページ]
    SETUP --> NVIM[nvim: main.py]
    
    NVIM --> CODE[コードを書く]
    CODE --> TEST{Space+cr テスト}
    TEST -->|FAIL| CODE
    TEST -->|PASS| SUBMIT[Space+cs 提出]
    
    SUBMIT --> CONTEST{コンテスト中?}
    CONTEST -->|Yes| CURL[curl自動提出]
    CONTEST -->|No| CLIP[クリップボード + ブラウザ提出]
    
    CURL --> RESULT
    CLIP --> RESULT[結果確認]
    
    RESULT --> TAG[fzf タグ選択]
    TAG --> INSIGHT[nvim insight記入]
    INSIGHT --> DONE([完了])
```

## コンテストフロー

```mermaid
flowchart TD
    CPNEW[cp-new abc453] --> DL[全問題 a-f DL]
    DL --> SOLVE_A[cd a && nvim main.py]
    
    SOLVE_A --> CODE_A[解く + Space+cr]
    CODE_A --> SUB_A[Space+cs 提出]
    SUB_A --> NEXT_B[cd ../b]
    
    NEXT_B --> CODE_B[解く + Space+cr]
    CODE_B --> SUB_B[Space+cs 提出]
    SUB_B --> DOTS[...]
    
    DOTS --> END_CONTEST([コンテスト終了])
    END_CONTEST --> REVISIT[各問題ディレクトリで cp-finish 再実行]
    REVISIT --> TAG[タグ + insight 記入]
    TAG --> DONE([レビュー完了])
```

## データフロー

```mermaid
flowchart LR
    subgraph AtCoder
        API_SUB[submissions API]
        API_RATE[rating API]
        API_DIFF[difficulty API]
        API_CONTEST[contests HTML]
    end
    
    subgraph NixOS
        FETCH[fetch_stats.py<br>2分ごと] --> JSON[stats.json]
        JSON --> DASH[dashboard.py<br>10秒検知]
        DASH --> WEBKIT[WebKit<br>Sway BACKGROUND]
    end
    
    subgraph JS Modules
        WEBKIT --> UTILS[utils.js]
        WEBKIT --> DIFFLOG[difficulty-log.js]
        WEBKIT --> STREAK[streak.js]
        WEBKIT --> SKILLGR[skill-graph.js]
        WEBKIT --> PANELS[panels.js]
        WEBKIT --> HYDRATE[hydrate.js]
    end
    
    API_SUB --> FETCH
    API_RATE --> FETCH
    API_DIFF --> FETCH
    API_CONTEST --> FETCH
    
    subgraph Local
        INSIGHTS[~/cp/insights/*.md]
        CONTESTS[~/cp/contests/]
    end
    
    INSIGHTS -.-> FETCH
```

## ユーザー切り替え

```mermaid
flowchart LR
    BOOT([起動]) --> LOAD[watchlist.json読み込み]
    LOAD --> SELF[自分のデータ表示]
    LOAD --> BG1[裏: friend1 フェッチ]
    LOAD --> BG2[裏: friend2 フェッチ]
    
    SELF --> KEY{Super+`}
    KEY --> F1[friend1 表示]
    F1 --> KEY2{Super+`}
    KEY2 --> F2[friend2 表示]
    F2 --> KEY3{Super+`}
    KEY3 --> SELF
```

## 予測モデル

```mermaid
flowchart TD
    subgraph Input
        WEEKLY[週diff総和]
        RATING[現在レート]
        PERFS[コンテストperf履歴]
    end
    
    subgraph Model
        EFF[滑らかな効率曲線<br>0.03 × e^{-rating/550}]
        CONV[収束レート<br>指数加重平均 decay=0.9]
        PACE[ペース目標<br>3ヶ月/6ヶ月で次の色]
    end
    
    subgraph Output
        PROJ[予測線 3本<br>楽観/維持/悲観]
        GHOST[ゴーストバー<br>今週の目標diff]
        TARGET[次の色まで<br>推定X ヶ月]
    end
    
    WEEKLY --> EFF
    RATING --> EFF
    EFF --> PROJ
    EFF --> GHOST
    EFF --> TARGET
    PERFS --> CONV
    WEEKLY --> PACE
    RATING --> PACE
    PACE --> TARGET
```
