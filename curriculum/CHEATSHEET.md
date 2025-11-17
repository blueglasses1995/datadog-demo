# Datadog ハンズオン チートシート

クイックリファレンス - よく使うコマンド、クエリ、トラブルシューティング

---

## 🐳 Docker コマンド

### 環境の起動・停止

```bash
# 起動
docker-compose up -d

# 停止（データ保持）
docker-compose stop

# 停止 + 削除（データも削除）
docker-compose down -v

# 再起動
docker-compose restart

# 特定のサービスのみ再起動
docker-compose restart backend
```

### ログの確認

```bash
# 全サービスのログ（リアルタイム）
docker-compose logs -f

# 特定のサービス
docker-compose logs -f backend

# 最新100行
docker-compose logs --tail=100 backend

# タイムスタンプ付き
docker-compose logs -f -t backend
```

### コンテナの状態確認

```bash
# コンテナ一覧
docker-compose ps

# 詳細情報
docker-compose ps -a

# リソース使用状況
docker stats

# コンテナ内でコマンド実行
docker-compose exec backend bash
docker-compose exec postgres psql -U demo_user -d demo_db
```

### トラブルシューティング

```bash
# 完全リセット
docker-compose down -v
docker system prune -a  # 注意: すべてのDockerリソース削除
docker-compose up -d

# ビルドキャッシュなしで再構築
docker-compose build --no-cache
docker-compose up -d

# ボリュームの確認
docker volume ls
docker volume inspect datadog-demo_postgres_data
```

---

## 📊 Datadog クエリ

### APM クエリ

```
# サービスでフィルタ
service:backend-api

# 特定のエンドポイント
resource_name:"GET /api/users"

# エラーのみ
service:backend-api error:true

# レイテンシが高いトレース
service:backend-api @duration:>1s

# 複数条件
service:backend-api AND resource_name:"GET /api/users" AND status:ok
```

### ログクエリ

```
# サービスでフィルタ
service:backend-api

# ステータスでフィルタ
status:error
status:(error OR warning)

# タグでフィルタ
@http.status_code:500
@http.method:POST

# 全文検索
"database connection failed"

# 時間範囲
service:backend-api @timestamp:[now-1h TO now]

# 複合条件
service:backend-api AND status:error AND @http.url_details.path:/api/users
```

### メトリクスクエリ

```
# 基本
avg:system.cpu.user{*}

# タグでフィルタ
avg:docker.cpu.usage{container_name:backend}

# 集計
sum:trace.flask.request.hits{service:backend-api}
avg:trace.flask.request.duration{service:backend-api}
max:postgresql.connections{*}

# グループ化
avg:docker.cpu.usage{*} by {container_name}
sum:trace.flask.request.hits{*} by {resource_name}

# 算術演算
( sum:trace.flask.request.errors{*} / sum:trace.flask.request.hits{*} ) * 100
```

---

## 🔧 よく使うAPI呼び出し

### cURLコマンド

```bash
# ヘルスチェック
curl http://localhost/health
curl http://localhost:5000/health

# ユーザー一覧
curl http://localhost/api/users

# 特定ユーザー
curl http://localhost/api/users/1

# 注文一覧
curl http://localhost/api/orders

# 統計情報
curl http://localhost/api/stats

# 遅いエンドポイント
curl http://localhost/api/slow

# エラー発生
curl http://localhost/api/error

# カスタムメトリクス送信
curl -X POST http://localhost/api/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "test.metric",
    "metric_value": 123,
    "metric_type": "gauge",
    "tags": ["env:dev"]
  }'

# キャッシュクリア
curl -X POST http://localhost/api/cache/clear
```

### 負荷生成

```bash
# トラフィック生成スクリプト
python scripts/generate_traffic.py

# 複数回実行
python scripts/generate_traffic.py 5

# 並列リクエスト（Apache Bench）
ab -n 100 -c 10 http://localhost/api/users

# 並列リクエスト（curl）
for i in {1..10}; do
  curl http://localhost/api/users &
done
wait
```

---

## 🐍 Python コード スニペット

### Datadog APM トレーシング

```python
from ddtrace import tracer

# カスタムスパンの作成
@tracer.wrap(service="my-service", resource="my-function")
def my_function():
    pass

# コンテキストマネージャー
def process_data():
    with tracer.trace("process_data", service="backend") as span:
        span.set_tag("user_id", 123)
        span.set_tag("data_size", len(data))
        # 処理

# エラーの記録
try:
    risky_operation()
except Exception as e:
    span.set_tag("error", True)
    span.set_tag("error.message", str(e))
    raise
```

### カスタムメトリクス

```python
from datadog import statsd

# Gauge: 現在の値
statsd.gauge('my.gauge', 42, tags=['env:prod'])

# Increment: カウンター
statsd.increment('page.views', tags=['page:home'])

# Decrement
statsd.decrement('queue.size')

# Histogram: 分布
statsd.histogram('request.duration', 0.245, tags=['endpoint:api'])

# Set: ユニーク数
statsd.set('unique.users', user_id, tags=['env:prod'])

# Timing: 処理時間
with statsd.timed('database.query'):
    execute_query()
```

### ログ記録

```python
import logging
from ddtrace import tracer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 通常のログ
logger.info("User logged in", extra={'user_id': 123})

# エラーログ
logger.error("Failed to process", exc_info=True)

# トレースIDを含むログ（DD_LOGS_INJECTION=trueが必要）
logger.info("Processing request")  # 自動的にtrace_id, span_idが追加される
```

---

## ⚛️ React/JavaScript スニペット

### Datadog RUM 初期化

```javascript
import { datadogRum } from '@datadog/browser-rum';

datadogRum.init({
  applicationId: 'YOUR_APP_ID',
  clientToken: 'YOUR_CLIENT_TOKEN',
  site: 'datadoghq.com',
  service: 'my-frontend',
  env: 'prod',
  version: '1.0.0',
  sessionSampleRate: 100,
  sessionReplaySampleRate: 100,
  trackUserInteractions: true,
  trackResources: true,
  trackLongTasks: true,
  defaultPrivacyLevel: 'mask-user-input',
});
```

### カスタムアクション

```javascript
import { datadogRum } from '@datadog/browser-rum';

// ユーザーアクション記録
datadogRum.addAction('button_click', {
  button_name: 'checkout',
  item_count: 3,
  total_price: 99.99
});

// エラー記録
datadogRum.addError(error, {
  user_id: user.id,
  action: 'payment_processing'
});

// ユーザー識別
datadogRum.setUser({
  id: '123',
  name: 'John Doe',
  email: 'john@example.com',
  plan: 'premium'
});
```

### カスタムログ

```javascript
import { datadogLogs } from '@datadog/browser-logs';

// Info
datadogLogs.logger.info('Button clicked', {
  button_name: 'submit',
  form_data: { /* ... */ }
});

// Error
datadogLogs.logger.error('API call failed', {
  endpoint: '/api/users',
  status_code: 500
});
```

---

## 📈 ダッシュボードクエリ

### よく使うウィジェット設定

#### CPU使用率（Timeseries）
```
avg:docker.cpu.usage{*} by {container_name}
```

#### エラー率（Query Value）
```
( sum:trace.flask.request.errors{service:backend-api}.as_count() /
  sum:trace.flask.request.hits{service:backend-api}.as_count() ) * 100
```

#### P95レイテンシ（Timeseries）
```
p95:trace.flask.request.duration{service:backend-api} by {resource_name}
```

#### リクエスト数（Top List）
```
sum:trace.flask.request.hits{service:backend-api} by {resource_name}
```

#### キャッシュヒット率（Query Value）
```
( sum:cache.hit{*}.as_count() /
  (sum:cache.hit{*}.as_count() + sum:cache.miss{*}.as_count()) ) * 100
```

---

## 🚨 モニター設定

### APM エラー率モニター

```
Metric: trace.flask.request.errors
Type: Metric Monitor
Query: sum(last_5m):sum:trace.flask.request.errors{service:backend-api}.as_count() / sum:trace.flask.request.hits{service:backend-api}.as_count() > 0.05
Alert threshold: 0.05 (5%)
Warning threshold: 0.02 (2%)
```

### レイテンシモニター

```
Metric: trace.flask.request.duration
Type: APM Monitor
Aggregation: p95
Alert threshold: > 1000ms
Warning threshold: > 500ms
Evaluation window: 5 minutes
```

### ログベースモニター

```
Query: logs("service:backend-api status:error").index("*").rollup("count").last("5m")
Alert threshold: > 20
Warning threshold: > 10
```

### コンテナヘルスモニター

```
Metric: docker.containers.running
Type: Metric Monitor
Query: max(last_5m):avg:docker.containers.running{image_name:backend} < 1
Notify on: Container down
```

---

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. コンテナが起動しない

```bash
# ログ確認
docker-compose logs [service-name]

# よくある原因
# - ポートが既に使用されている
netstat -an | grep 5000  # macOS/Linux
# 使用中のプロセスを停止または docker-compose.yml のポートを変更

# - メモリ不足
docker stats
# Docker Desktop のメモリ設定を増やす

# 完全リセット
docker-compose down -v
docker-compose up -d
```

#### 2. Datadogにデータが表示されない

```bash
# 1. API Key確認
cat .env | grep DD_API_KEY

# 2. Agent ステータス確認
docker-compose logs datadog-agent | grep -i "running"

# 3. Agent内部ステータス
docker-compose exec datadog-agent agent status

# 4. ネットワーク確認
docker-compose exec datadog-agent curl https://api.datadoghq.com
```

#### 3. トレースが表示されない

```bash
# 1. APM 有効確認
docker-compose logs datadog-agent | grep -i apm

# 2. Backend 設定確認
docker-compose logs backend | grep -i ddtrace

# 3. ポート確認
docker-compose exec backend curl http://datadog-agent:8126

# 4. 環境変数確認
docker-compose exec backend env | grep DD_
```

#### 4. RUMデータが表示されない

```javascript
// ブラウザコンソールで確認
// RUM初期化確認
console.log(datadogRum)

// エラー確認
// Chrome DevTools → Network → Filter: datadoghq
```

#### 5. パフォーマンス問題

```bash
# コンテナリソース確認
docker stats

# データベース接続数
docker-compose exec postgres psql -U demo_user -d demo_db -c "SELECT count(*) FROM pg_stat_activity;"

# Redisメモリ
docker-compose exec redis redis-cli INFO memory
```

---

## 📚 環境変数リファレンス

### 必須環境変数

```env
# Datadog API Key（必須）
DD_API_KEY=your_api_key_here

# Datadog Site
DD_SITE=datadoghq.com  # US1
# DD_SITE=datadoghq.eu  # EU
# DD_SITE=us3.datadoghq.com  # US3
# DD_SITE=ap1.datadoghq.com  # AP1

# Environment（推奨）
DD_ENV=dev
DD_SERVICE=datadog-demo
DD_VERSION=1.0.0
```

### APM 関連

```env
# APM有効化
DD_APM_ENABLED=true
DD_APM_NON_LOCAL_TRAFFIC=true

# トレース設定
DD_TRACE_SAMPLE_RATE=1  # 100%サンプリング
DD_TRACE_DEBUG=false

# プロファイリング
DD_PROFILING_ENABLED=false
```

### ログ関連

```env
# ログ収集
DD_LOGS_ENABLED=true
DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true

# ログとトレースの相関
DD_LOGS_INJECTION=true
```

### RUM 関連

```env
# RUM Application ID
REACT_APP_DD_RUM_APPLICATION_ID=your_rum_app_id

# RUM Client Token
REACT_APP_DD_RUM_CLIENT_TOKEN=your_rum_client_token

# RUM Site
REACT_APP_DD_RUM_SITE=datadoghq.com

# RUM Service
REACT_APP_DD_RUM_SERVICE=frontend
REACT_APP_DD_RUM_ENV=dev
```

---

## 🎯 ベストプラクティス

### タグ付けの規則

```python
# 推奨タグ
- env: dev/staging/prod
- service: backend-api/frontend
- version: 1.0.0
- team: platform/data
- project: datadog-demo

# カスタムタグ
statsd.increment('api.call', tags=[
    'endpoint:/api/users',
    'method:GET',
    'status:200',
    'user_tier:premium'
])
```

### メトリクス命名規則

```
# 形式: <namespace>.<noun>.<verb>
business.revenue.total
business.users.active
api.requests.count
api.response.duration
cache.hits.count
database.queries.duration
```

### ダッシュボード構成

```
1. Executive Summary
   - SLO status
   - Key business metrics
   - Overall health

2. Service Health
   - Request rate
   - Error rate
   - Latency

3. Infrastructure
   - CPU, Memory
   - Network, Disk
   - Container status

4. Dependencies
   - Database metrics
   - Cache metrics
   - External APIs

5. Business Metrics
   - KPIs
   - User activity
   - Revenue
```

---

## 🔗 便利なリンク

### Datadog UI

```
# ダッシュボード
https://app.datadoghq.com/dashboard/lists

# APM Services
https://app.datadoghq.com/apm/services

# Infrastructure List
https://app.datadoghq.com/infrastructure

# Log Explorer
https://app.datadoghq.com/logs

# Metrics Explorer
https://app.datadoghq.com/metric/explorer

# Monitors
https://app.datadoghq.com/monitors/manage

# Integrations
https://app.datadoghq.com/integrations

# API Keys
https://app.datadoghq.com/organization-settings/api-keys
```

### ドキュメント

```
# 日本語ドキュメント
https://docs.datadoghq.com/ja/

# APM
https://docs.datadoghq.com/ja/tracing/

# Infrastructure
https://docs.datadoghq.com/ja/infrastructure/

# Logs
https://docs.datadoghq.com/ja/logs/

# RUM
https://docs.datadoghq.com/ja/real_user_monitoring/

# API Reference
https://docs.datadoghq.com/ja/api/
```

---

## 💡 クイックTips

### パフォーマンス最適化

```python
# ❌ 悪い例: N+1クエリ
for user in users:
    orders = get_orders(user.id)  # N回のクエリ

# ✅ 良い例: 一括取得
user_ids = [user.id for user in users]
orders = get_orders_batch(user_ids)  # 1回のクエリ
```

### エラーハンドリング

```python
from ddtrace import tracer

try:
    result = risky_operation()
except Exception as e:
    # スパンにエラー情報を追加
    span = tracer.current_span()
    if span:
        span.set_tag('error', True)
        span.set_tag('error.type', type(e).__name__)
        span.set_tag('error.message', str(e))
        span.set_tag('error.stack', traceback.format_exc())

    logger.error("Operation failed", exc_info=True)
    raise
```

### 効率的なログ記録

```python
# ❌ 悪い例
logger.info(f"Processing {len(items)} items: {items}")  # itemsが大きいとログが肥大化

# ✅ 良い例
logger.info("Processing items", extra={
    'item_count': len(items),
    'item_ids': [item.id for item in items]  # IDのみ
})
```

---

このチートシートをブックマークして、いつでも参照できるようにしてください！ 🚀
