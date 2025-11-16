# Datadog ハンズオン手順書

このハンズオンでは、Datadogの主要な機能を実際に体験しながら学びます。

## 📋 目次

1. [環境セットアップ](#1-環境セットアップ)
2. [APM（Application Performance Monitoring）](#2-apmapplication-performance-monitoring)
3. [インフラ監視](#3-インフラ監視)
4. [ログ管理](#4-ログ管理)
5. [RUM（Real User Monitoring）](#5-rumreal-user-monitoring)
6. [カスタムメトリクス](#6-カスタムメトリクス)
7. [ダッシュボード作成](#7-ダッシュボード作成)
8. [アラート設定](#8-アラート設定)

---

## 1. 環境セットアップ

### 1.1 Datadog API キーの取得

1. [Datadog](https://www.datadoghq.com/)にサインアップ（無料トライアルOK）
2. Organization Settings → API Keys に移動
3. 新しいAPI Keyを作成（または既存のキーをコピー）

### 1.2 RUM設定（オプション）

フロントエンド監視を行う場合：

1. UX Monitoring → RUM Applications に移動
2. 新しいアプリケーションを作成
3. Application IDとClient Tokenをコピー

### 1.3 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集
nano .env
```

必須項目：
```env
DD_API_KEY=your_api_key_here
```

オプション（RUM使用時）：
```env
REACT_APP_DD_RUM_APPLICATION_ID=your_rum_app_id
REACT_APP_DD_RUM_CLIENT_TOKEN=your_rum_client_token
```

### 1.4 環境の起動

```bash
# すべてのコンテナを起動
docker-compose up -d

# ログを確認（すべてのサービスが正常に起動することを確認）
docker-compose logs -f

# 各サービスの起動を確認
docker-compose ps
```

✅ **確認ポイント:**
- すべてのコンテナが "Up" 状態
- エラーログがないこと

### 1.5 アプリケーションへのアクセス

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/health
- Nginx: http://localhost:80

---

## 2. APM（Application Performance Monitoring）

### 2.1 サービスマップの確認

1. Datadogで [APM → Service Map](https://app.datadoghq.com/apm/map) を開く
2. `backend-api` サービスを探す
3. サービス間の依存関係を確認

**学習ポイント:**
- マイクロサービス間の通信フロー
- 各サービスのヘルスステータス

### 2.2 トレースの確認

```bash
# トラフィックを生成
python scripts/generate_traffic.py
```

1. [APM → Traces](https://app.datadoghq.com/apm/traces) を開く
2. フィルターで `service:backend-api` を選択
3. 任意のトレースをクリックして詳細を確認

**学習ポイント:**
- リクエストのフローグラフ（フレームグラフ）
- 各スパンの実行時間
- データベースクエリやRedis呼び出しの可視化

### 2.3 パフォーマンス分析

1. Webアプリで「遅いエンドポイント」ボタンをクリック
2. APM → Services → backend-api → Resources を開く
3. `/api/slow` エンドポイントのパフォーマンスを確認

**分析項目:**
- 平均レスポンスタイム
- P50、P75、P95、P99 パーセンタイル
- スループット

### 2.4 エラートラッキング

1. Webアプリで「エラー発生」ボタンを数回クリック
2. APM → Services → backend-api → Errors タブを開く
3. エラーの詳細を確認

**確認項目:**
- エラー率
- エラーの種類（ZeroDivisionError、KeyError、ValueError）
- スタックトレース

---

## 3. インフラ監視

### 3.1 コンテナ監視

1. [Infrastructure → Containers](https://app.datadoghq.com/containers) を開く
2. 各コンテナのメトリクスを確認

**確認項目:**
- CPU使用率
- メモリ使用量
- ネットワークI/O
- ディスクI/O

### 3.2 PostgreSQL監視

1. [Infrastructure → Integrations](https://app.datadoghq.com/infrastructure) で "postgres" を検索
2. PostgreSQLダッシュボードを開く

**確認項目:**
- 接続数
- クエリ実行時間
- データベースサイズ
- トランザクション数

### 3.3 Redis監視

1. Integrationsで "redis" を検索
2. Redisダッシュボードを開く

**確認項目:**
- メモリ使用量
- キャッシュヒット率
- 接続数
- コマンド実行数

### 3.4 Nginx監視

1. Integrationsで "nginx" を検索
2. Nginxダッシュボードを開く

**確認項目:**
- リクエスト数
- レスポンスタイム
- エラー率（4xx、5xx）
- アクティブな接続数

---

## 4. ログ管理

### 4.1 ログエクスプローラー

1. [Logs → Explorer](https://app.datadoghq.com/logs) を開く
2. 各サービスのログを確認

**フィルター例:**
```
service:backend-api
service:nginx
service:postgres
```

### 4.2 ログとトレースの相関

1. ログエクスプローラーでバックエンドのログを表示
2. 任意のログエントリをクリック
3. "View in APM" をクリックしてトレースに移動

**学習ポイント:**
- ログとトレースが自動的に相関付けられている
- `trace_id` と `span_id` による関連付け

### 4.3 ログパターン分析

1. Logs → Patterns を開く
2. 自動検出されたログパターンを確認

**活用例:**
- 頻出するエラーパターンの特定
- 異常なログパターンの検出

### 4.4 ログメトリクス

1. Logs → Configuration → Generate Metrics を開く
2. 新しいログベースメトリクスを作成

**例: エラーログのカウント**
- Query: `status:error service:backend-api`
- Metric name: `custom.logs.error.count`
- Group by: `service`, `env`

---

## 5. RUM（Real User Monitoring）

> **注意:** RUM機能を使用するには、.envファイルでRUM設定が必要です

### 5.1 セッション再生

1. [UX Monitoring → Sessions](https://app.datadoghq.com/rum/sessions) を開く
2. Webアプリを操作してセッションを生成
3. セッション再生で実際のユーザー操作を確認

### 5.2 パフォーマンス監視

1. RUM → Performance を開く
2. ページロードパフォーマンスを確認

**確認項目:**
- Largest Contentful Paint (LCP)
- First Input Delay (FID)
- Cumulative Layout Shift (CLS)
- Core Web Vitals

### 5.3 エラートラッキング

1. Webアプリで「エラー発生」ボタンをクリック
2. RUM → Errors を開く
3. フロントエンドエラーを確認

### 5.4 ユーザーアクション

1. RUM → User Actions を開く
2. ボタンクリックやページ遷移を確認

**分析項目:**
- 最も使用されている機能
- ユーザーフロー
- アクションごとのパフォーマンス

---

## 6. カスタムメトリクス

### 6.1 カスタムメトリクスの送信

1. Webアプリで「カスタムメトリクス」ボタンをクリック
2. [Metrics → Explorer](https://app.datadoghq.com/metric/explorer) を開く
3. `custom.frontend.button_click` メトリクスを検索

### 6.2 ビジネスメトリクスの確認

既に組み込まれているビジネスメトリクス：

- `users.count` - ユーザー数
- `orders.count` - 注文数
- `orders.total_amount` - 注文合計金額
- `cache.hit` / `cache.miss` - キャッシュヒット/ミス

**確認方法:**
```bash
# トラフィックを生成
python scripts/generate_traffic.py

# Metrics Explorerで確認
```

### 6.3 メトリクス分析

1. Metrics → Explorer で任意のメトリクスを選択
2. グラフ化して傾向を分析
3. タグでグループ化（例: `service`, `env`）

---

## 7. ダッシュボード作成

### 7.1 新しいダッシュボードの作成

1. [Dashboards → New Dashboard](https://app.datadoghq.com/dashboard/lists) を開く
2. 「Datadog Demo Dashboard」という名前で作成

### 7.2 ウィジェットの追加

以下のウィジェットを追加してみましょう：

#### a) APMサービスパフォーマンス

- Widget Type: Timeseries
- Metric: `trace.flask.request.duration`
- Group by: `resource_name`

#### b) エラー率

- Widget Type: Query Value
- Metric: `trace.flask.request.errors`
- Formula: `(errors / requests) * 100`

#### c) データベースパフォーマンス

- Widget Type: Timeseries
- Metric: `postgresql.connections`
- Metric: `postgresql.queries`

#### d) Redisキャッシュヒット率

- Widget Type: Timeseries
- Metric: `redis.stats.keyspace_hits`
- Metric: `redis.stats.keyspace_misses`
- Formula: `(hits / (hits + misses)) * 100`

#### e) ビジネスメトリクス

- Widget Type: Query Value
- Metrics:
  - `users.count`
  - `orders.count`
  - `orders.total_amount`

### 7.3 ダッシュボードのカスタマイズ

- タイムレンジの設定
- グラフの色やスタイルの変更
- ウィジェットの配置調整

---

## 8. アラート設定

### 8.1 APMモニターの作成

1. [Monitors → New Monitor](https://app.datadoghq.com/monitors/create) → APM を選択
2. 設定例：

**モニター名:** 高エラー率アラート

**条件:**
- Service: `backend-api`
- Resource: `*`
- Threshold: エラー率 > 10%
- Evaluation window: 5分

**通知メッセージ:**
```
⚠️ Backend APIのエラー率が高くなっています

エラー率: {{value}}%
サービス: {{service.name}}
環境: {{env}}

@slack-alerts
```

### 8.2 メトリクスモニターの作成

**モニター名:** 高CPU使用率アラート

**条件:**
- Metric: `docker.cpu.usage`
- Container: `backend`
- Alert threshold: > 80%
- Warning threshold: > 60%

### 8.3 ログモニターの作成

**モニター名:** エラーログ急増アラート

**条件:**
- Query: `status:error service:backend-api`
- Alert threshold: > 10 errors in 5 minutes
- Warning threshold: > 5 errors in 5 minutes

### 8.4 アノマリー検出

1. New Monitor → Anomaly を選択
2. 設定例：

**メトリクス:** `orders.total_amount`

**条件:**
- アルゴリズム: Agile
- 感度: Medium
- 評価期間: 15分

---

## 🎯 実践演習

### 演習1: パフォーマンス調査

1. トラフィックを継続的に生成
   ```bash
   python scripts/generate_traffic.py 10
   ```

2. 最も遅いエンドポイントを特定
3. ボトルネックを分析（DB? Redis? ビジネスロジック?）
4. APMのフレームグラフで詳細を確認

### 演習2: エラー分析

1. エラーエンドポイントを複数回呼び出し
2. エラーの種類と頻度を分析
3. エラーログとトレースを相関付けて原因を特定
4. エラー率のグラフを作成

### 演習3: インフラ最適化

1. 各コンテナのリソース使用状況を確認
2. ボトルネックとなっているサービスを特定
3. Redis キャッシュヒット率を確認
4. 最適化の提案をまとめる

### 演習4: カスタムダッシュボード作成

以下を含む総合ダッシュボードを作成：

- システム全体のヘルスチェック
- APMサービスパフォーマンス
- インフラメトリクス
- ビジネスメトリクス
- エラー率とログ

---

## 🔧 トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs [service-name]

# コンテナを再起動
docker-compose restart [service-name]

# 完全リセット
docker-compose down -v
docker-compose up -d
```

### Datadogにデータが表示されない

1. API Keyが正しく設定されているか確認
2. Datadog Agentのログを確認
   ```bash
   docker-compose logs datadog-agent
   ```
3. ネットワーク接続を確認

### RUMが動作しない

1. Application IDとClient Tokenが正しいか確認
2. ブラウザのコンソールでエラーを確認
3. Datadogのドメインがブロックされていないか確認

---

## 📚 参考資料

- [Datadog APM ドキュメント](https://docs.datadoghq.com/ja/tracing/)
- [Datadog インフラ監視](https://docs.datadoghq.com/ja/infrastructure/)
- [Datadog ログ管理](https://docs.datadoghq.com/ja/logs/)
- [Datadog RUM](https://docs.datadoghq.com/ja/real_user_monitoring/)
- [Datadog ダッシュボード](https://docs.datadoghq.com/ja/dashboards/)
- [Datadog モニター](https://docs.datadoghq.com/ja/monitors/)

---

## ✅ チェックリスト

ハンズオン完了の確認：

- [ ] 環境が正常に起動した
- [ ] APMでトレースを確認できた
- [ ] サービスマップで依存関係を確認できた
- [ ] インフラメトリクス（PostgreSQL、Redis、Nginx）を確認できた
- [ ] ログとトレースの相関を確認できた
- [ ] RUM（オプション）でユーザー操作を確認できた
- [ ] カスタムメトリクスを送信できた
- [ ] ダッシュボードを作成できた
- [ ] アラートを設定できた

**おめでとうございます！Datadogハンズオンを完了しました！** 🎉
