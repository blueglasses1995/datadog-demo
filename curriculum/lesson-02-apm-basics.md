# レッスン2: APM（Application Performance Monitoring）入門

## 📋 レッスン概要

このレッスンでは、Datadog APMを使ったアプリケーションパフォーマンス監視の基礎を学びます。

**所要時間:** 90分
**難易度:** 初級
**前提知識:** レッスン1完了、HTTP/REST APIの基本理解

## 🎯 学習目標

- [ ] APMの基礎概念（トレース、スパン、サービス）を理解できる
- [ ] サービスマップを読み解ける
- [ ] トレースを分析してパフォーマンス問題を特定できる
- [ ] リソースとエンドポイントのパフォーマンスを監視できる
- [ ] エラーをトラッキングして原因を特定できる

## 📚 学習内容

### 1. APMの基礎概念

#### 1.1 トレース（Trace）とは

**トレース** = 1つのリクエストの完全なジャーニー

```
ユーザーリクエスト
    ↓
[Nginx] → トレース開始
    ↓
[Backend API] → スパン
    ↓
[PostgreSQL] → スパン
    ↓
[Redis] → スパン
    ↓
レスポンス → トレース完了
```

#### 1.2 スパン（Span）とは

**スパン** = トレース内の個別の処理単位

スパンに含まれる情報：
- オペレーション名（例: `flask.request`, `postgres.query`）
- 開始時刻と期間
- タグ（メタデータ）
- エラー情報（該当する場合）

#### 1.3 サービス（Service）とは

**サービス** = 独立した機能を提供するコンポーネント

このデモ環境のサービス：
- `backend-api`: Flask APIサーバー
- `postgres`: データベース
- `redis`: キャッシュ
- `nginx`: リバースプロキシ

---

### 2. サービスマップの活用

#### 2.1 サービスマップを開く

1. **APM** → **Service Map** に移動
2. デモ環境のサービス構成を確認

#### 2.2 サービスマップの読み方

**ノード（円）:**
- **サイズ**: リクエスト数に比例
- **色**: ヘルスステータス
  - 緑: 正常
  - 黄: 警告
  - 赤: エラー

**エッジ（矢印）:**
- サービス間の依存関係
- 矢印の太さ = 通信量

#### 2.3 実習: サービスマップの探索

**タスク:**
1. `backend-api` ノードをクリック
2. 依存サービス（postgres, redis）を確認
3. 右パネルで以下を確認：
   - リクエスト数
   - レイテンシ（平均、P50、P75、P95、P99）
   - エラー率

**質問:**
- backend-apiは何個のサービスに依存していますか？
- 最もレイテンシが高いサービスは？

---

### 3. トレースの詳細分析

#### 3.1 トレースリストの表示

1. **APM** → **Traces** に移動
2. フィルター: `service:backend-api`
3. 時間範囲を調整（直近15分など）

#### 3.2 トレースの開き方

1. 任意のトレースをクリック
2. **フレームグラフ（Flame Graph）** が表示される

#### 3.3 フレームグラフの読み方

**横軸:** 時間（処理期間）
**縦軸:** スパンの階層

```
[========== flask.request ==========]  ← ルートスパン
  [== postgres.query ==]               ← DBクエリ
  [= redis.command =]                  ← Redis操作
```

**色の意味:**
- 青系: アプリケーション処理
- 紫系: データベース
- オレンジ系: キャッシュ
- 赤系: エラー

#### 3.4 実習: パフォーマンスボトルネックの特定

**手順:**

1. **遅いエンドポイントを呼び出し**
   ```bash
   # Webアプリで「遅いエンドポイント」ボタンを5回クリック
   # または
   curl http://localhost/api/slow
   ```

2. **トレースを検索**
   - APM → Traces
   - フィルター: `resource_name:/api/slow`

3. **フレームグラフを分析**
   - どのスパンが最も時間を消費している？
   - ボトルネックはどこ？

4. **タグを確認**
   - `delay_seconds` タグで遅延時間を確認
   - `http.status_code` でステータスコードを確認

---

### 4. リソースとエンドポイントの監視

#### 4.1 Service Overview

1. **APM** → **Services** → **backend-api** をクリック

**表示される情報:**
- **リクエスト数** (Requests)
- **レイテンシ** (Latency)
- **エラー率** (Error Rate)
- **Apdex スコア** (ユーザー満足度指標)

#### 4.2 Resources タブ

**Resources** = APIエンドポイント

1. **Resources** タブをクリック
2. エンドポイント一覧を確認：
   - `GET /api/users`
   - `GET /api/users/:id`
   - `GET /api/orders`
   - `GET /api/slow`
   - `GET /api/error`

**並び替え:**
- **Total Time**: 最も時間を消費しているエンドポイント
- **Avg Latency**: 平均レイテンシが高いエンドポイント
- **Requests**: リクエスト数が多いエンドポイント

#### 4.3 実習: リソース分析

**タスク1: 最も遅いエンドポイントを特定**

1. Resources タブで **Avg Latency** でソート
2. 最も遅いエンドポイントは？
3. そのエンドポイント名をクリックして詳細を確認

**タスク2: エンドポイント詳細の確認**

エンドポイント詳細ページで以下を確認：
- レイテンシ分布（ヒストグラム）
- パーセンタイル（P50, P75, P95, P99）
- 時系列グラフ
- トップスパン（どの処理が時間を消費しているか）

---

### 5. エラートラッキング

#### 5.1 エラーの発生

```bash
# Webアプリで「エラー発生」ボタンを10回クリック
# または
for i in {1..10}; do curl http://localhost/api/error; done
```

#### 5.2 Errors タブの確認

1. **APM** → **Services** → **backend-api**
2. **Errors** タブをクリック

**表示される情報:**
- エラー率のグラフ
- エラーの種類（Exception Type）
- エラーメッセージ

#### 5.3 エラーの詳細分析

1. エラーの種類をクリック（例: `ZeroDivisionError`）
2. **スタックトレース** を確認
3. どのコード行でエラーが発生しているか特定

**トレースへのリンク:**
- "View a Sample Trace" をクリック
- エラーが発生した時のリクエスト全体を確認

#### 5.4 実習: エラーの根本原因分析

**シナリオ:** `ZeroDivisionError` が発生している

**手順:**
1. Errors タブで `ZeroDivisionError` を確認
2. スタックトレースから `backend/app.py` の該当行を特定
3. コードを確認:
   ```python
   # app.py の /api/error エンドポイント
   if error_type == 'division':
       result = 1 / 0  # ← ここでエラー
   ```
4. エラーが意図的であることを確認

---

### 6. APMメトリクスとグラフ化

#### 6.1 Trace Metrics

APMは自動的にメトリクスを生成：

| メトリクス | 説明 |
|----------|------|
| `trace.flask.request.hits` | リクエスト数 |
| `trace.flask.request.duration` | レイテンシ |
| `trace.flask.request.errors` | エラー数 |
| `trace.postgres.query.duration` | DBクエリ時間 |
| `trace.redis.command.duration` | Redis操作時間 |

#### 6.2 Metrics Explorer で可視化

1. **Metrics** → **Explorer** に移動
2. メトリクス: `trace.flask.request.duration`
3. **Group by**: `resource_name`
4. グラフタイプ: **Timeseries**

**結果:** エンドポイントごとのレイテンシ推移が表示される

#### 6.3 実習: レイテンシ分析

**タスク:**
1. `trace.flask.request.duration` をグラフ化
2. `resource_name` でグループ化
3. `/api/slow` のレイテンシが他より高いことを確認
4. Percentiles (p95, p99) を追加表示

---

### 7. 分散トレーシング

#### 7.1 分散トレーシングとは

複数のサービスにまたがるリクエストを1つのトレースとして追跡：

```
[Nginx]
   ↓ trace_id: abc123
[Backend API]
   ↓ trace_id: abc123
[PostgreSQL] + [Redis]
   ↓ trace_id: abc123
Response
```

すべてのスパンが同じ `trace_id` で関連付けられている

#### 7.2 実習: 分散トレースの確認

1. `/api/orders` エンドポイントを呼び出し
   ```bash
   curl http://localhost/api/orders
   ```

2. そのトレースを開く
3. フレームグラフで以下を確認：
   - Flask処理
   - PostgreSQL クエリ（JOIN文）
   - スパンの親子関係

4. **Tags** タブで確認：
   - `trace_id`: トレースID
   - `span_id`: 各スパンのID
   - `parent_id`: 親スパンのID

---

### 8. 実習課題

#### 課題1: パフォーマンス最適化提案（30分）

1. **現状分析**
   - すべてのエンドポイントのレイテンシを確認
   - ボトルネックを特定

2. **最適化案の作成**
   - 最も遅いエンドポイントは？
   - なぜ遅いのか？（DBクエリ？外部API？処理ロジック？）
   - どう改善できるか？

3. **レポート作成**
   - 現状のレイテンシ（p50, p95, p99）
   - ボトルネックの詳細
   - 改善提案

#### 課題2: エラー調査（20分）

1. 過去1時間のエラーを調査
2. エラーの種類と頻度を集計
3. 各エラーの根本原因を特定
4. 修正方法を提案

#### 課題3: サービス依存関係の文書化（15分）

1. Service Map を参考に依存関係図を作成
2. 各サービスの役割を説明
3. クリティカルパスを特定
   - どのサービスが落ちると全体が機能しなくなるか？

---

### 9. 確認問題

#### 問1: 基礎概念
トレース、スパン、サービスの違いを説明してください。

<details>
<summary>解答</summary>

- **トレース**: 1つのリクエストの完全な処理フロー（開始から終了まで）
- **スパン**: トレース内の個別の処理単位（例: DBクエリ、Redis操作）
- **サービス**: 独立した機能を提供するコンポーネント（例: backend-api, postgres）

トレースは複数のスパンで構成され、スパンは特定のサービスで実行される。
</details>

#### 問2: パフォーマンス分析
レイテンシが高いエンドポイントを特定する3つの方法を挙げてください。

<details>
<summary>解答</summary>

1. **Resources タブ**: Avg Latency でソート
2. **Service Overview**: Latency グラフで時系列確認
3. **Metrics Explorer**: `trace.flask.request.duration` をグラフ化してエンドポイント比較
</details>

#### 問3: トレース分析
フレームグラフから何がわかりますか？

<details>
<summary>解答</summary>

- 各スパンの実行時間
- スパンの階層関係（親子関係）
- 並列実行か直列実行か
- ボトルネックの位置
- エラーの発生箇所
- 各処理の相対的な時間消費量
</details>

---

### 10. ベストプラクティス

#### APM導入のベストプラクティス

1. **重要なエンドポイントから開始**
   - ユーザー影響が大きい機能
   - ビジネスクリティカルなAPI

2. **適切なサンプリング設定**
   - 開発環境: 100%（すべてトレース）
   - 本番環境: 1-10%（トラフィックに応じて調整）

3. **カスタムスパンの追加**
   ```python
   from ddtrace import tracer

   @tracer.wrap(service="backend-api", resource="process_payment")
   def process_payment(amount):
       # 処理
       pass
   ```

4. **タグの活用**
   - ユーザーID
   - テナントID
   - バージョン
   - 環境（dev/staging/prod）

#### パフォーマンス最適化の優先順位

1. **P95, P99のレイテンシが高いエンドポイント**
   - ユーザー体験への影響が大きい

2. **リクエスト数が多いエンドポイント**
   - わずかな改善でも全体への影響が大きい

3. **エラー率が高いエンドポイント**
   - 信頼性向上が最優先

---

### 11. トラブルシューティング

#### トレースが表示されない

**確認項目:**
```bash
# Datadog Agent が APM を有効にしているか
docker-compose logs datadog-agent | grep -i apm

# Backend アプリが ddtrace を使用しているか
docker-compose logs backend | grep -i ddtrace

# ポート8126が開いているか
docker-compose exec backend curl http://datadog-agent:8126
```

#### レイテンシが異常に高い

**原因の切り分け:**
1. **アプリケーション**: フレームグラフで処理時間を確認
2. **データベース**: DBクエリのスパンを確認
3. **ネットワーク**: サービス間通信の時間を確認
4. **リソース不足**: Infrastructure でCPU/メモリを確認

---

### 12. 次のステップ

**[レッスン3: インフラストラクチャ監視](./lesson-03-infrastructure.md)**

#### 予習

- Infrastructure → Containers でリソース使用状況を確認
- Integrations で PostgreSQL, Redis のダッシュボードを確認

---

## 📚 参考資料

- [APM Documentation](https://docs.datadoghq.com/ja/tracing/)
- [Distributed Tracing](https://docs.datadoghq.com/ja/tracing/trace_collection/)
- [APM Best Practices](https://docs.datadoghq.com/ja/tracing/guide/)

## 💡 まとめ

このレッスンで学んだこと：

✅ APMの基礎概念（トレース、スパン、サービス）
✅ サービスマップの読み方
✅ トレースの詳細分析
✅ パフォーマンスボトルネックの特定方法
✅ エラートラッキングと根本原因分析

次のレッスンでは、インフラストラクチャ監視を学びます！
