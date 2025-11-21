# Datadog 技術アーキテクチャ詳細ドキュメント

## 目次

1. [システム概要](#システム概要)
2. [APM (Application Performance Monitoring) 技術的原理](#apm-技術的原理)
3. [ログ収集・転送の仕組み](#ログ収集転送の仕組み)
4. [メトリクス収集・集約の詳細](#メトリクス収集集約の詳細)
5. [RUM (Real User Monitoring) 技術的実装](#rum-技術的実装)
6. [データフロー全体図](#データフロー全体図)
7. [パフォーマンスとスケーラビリティ](#パフォーマンスとスケーラビリティ)

---

## システム概要

### アーキテクチャ全体像

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet/User                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Nginx (Port 80) │
                    │  - Access logs    │
                    │  - Error logs     │
                    │  - Metrics        │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐  ┌──────▼──────┐     │
     │  Frontend   │  │   Backend   │     │
     │  (React)    │  │   (Flask)   │     │
     │             │  │             │     │
     │  RUM SDK    │  │  ddtrace    │     │
     │  ↓          │  │  ↓          │     │
     │  Browser    │  │  APM Tracer │     │
     └─────┬───────┘  └──────┬──────┘     │
           │                 │             │
           │         ┌───────┼─────────────┘
           │         │       │
           │    ┌────▼───┐  ┌▼──────┐
           │    │ Postgres│  │ Redis │
           │    │   DB    │  │ Cache │
           │    └────┬────┘  └┬──────┘
           │         │        │
           │         │        │
     ┌─────▼─────────▼────────▼──────┐
     │      Datadog Agent             │
     │  ┌──────────────────────────┐  │
     │  │ APM Receiver :8126       │  │
     │  │ DogStatsD    :8125       │  │
     │  │ Log Collector            │  │
     │  │ System Metrics           │  │
     │  └──────────┬───────────────┘  │
     └─────────────┼──────────────────┘
                   │
            ┌──────▼───────┐
            │   Datadog    │
            │   Platform   │
            │  (Cloud SaaS)│
            └──────────────┘
```

### コンポーネント一覧

| コンポーネント | 役割 | データ送信先 | プロトコル |
|------------|------|------------|----------|
| Nginx | リバースプロキシ、アクセスログ | Datadog Agent | ファイル監視 |
| Frontend (React) | ユーザーインターフェース、RUM | Datadog RUM Intake | HTTPS |
| Backend (Flask) | ビジネスロジック、API | Datadog Agent | HTTP/msgpack |
| PostgreSQL | データベース | Datadog Agent | メトリクスクエリ |
| Redis | キャッシュ | Datadog Agent | Redis INFO |
| Datadog Agent | 統合監視エージェント | Datadog Platform | HTTPS/gRPC |

---

## APM 技術的原理

### 1. 分散トレーシングの基本概念

#### トレースとスパンの構造

```
Trace (1つのリクエスト全体)
│
├─ Span: nginx.request (HTTP Request)
│  ├─ duration: 245ms
│  ├─ resource: GET /api/users
│  └─ tags: {http.status_code: 200}
│
├─ Span: flask.request (Backend Processing)
│  ├─ duration: 230ms
│  ├─ parent: nginx.request
│  │
│  ├─ Span: postgres.query (Database Query)
│  │  ├─ duration: 45ms
│  │  ├─ resource: SELECT * FROM users
│  │  └─ tags: {db.name: demo_db}
│  │
│  └─ Span: redis.command (Cache Check)
│     ├─ duration: 2ms
│     ├─ resource: GET user:123
│     └─ tags: {redis.command: GET}
```

#### トレースコンテキストの伝播

Datadogは **W3C Trace Context** および独自の **Datadog Trace Context** をサポートしています。

**HTTPヘッダーでのコンテキスト伝播:**

```
Request Headers:
┌─────────────────────────────────────────────────────┐
│ x-datadog-trace-id: 1234567890123456789             │
│ x-datadog-parent-id: 9876543210987654               │
│ x-datadog-sampling-priority: 1                      │
│ x-datadog-origin: rum                               │
│ x-datadog-tags: _dd.p.tid=0000000000000001          │
└─────────────────────────────────────────────────────┘

これらのヘッダーにより、フロントエンド → バックエンド → データベース
まで一貫したトレースIDで追跡が可能
```

### 2. Python (Flask) での APM 実装

#### ddtrace の動作原理

`ddtrace` は **モンキーパッチング** により、ライブラリの関数を自動的にラップしてトレーシングを追加します。

**実装例 (backend/app.py):**

```python
from ddtrace import tracer
from ddtrace.contrib.flask import TraceMiddleware

# Flaskアプリにトレーシングミドルウェアを追加
traced_app = TraceMiddleware(app, tracer, service="backend-api")

@app.route('/api/users', methods=['GET'])
def get_users():
    # 自動的にスパンが作成される (TraceMiddleware)
    with tracer.trace("get_users", service="backend-api") as span:
        span.set_tag("endpoint", "/api/users")

        # データベースクエリ (自動インスツルメンテーション)
        conn = get_db_connection()  # psycopg2 自動トレース
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")  # SQL クエリが自動記録
        users = cur.fetchall()

        return jsonify({"users": users})
```

#### 自動インスツルメンテーションの仕組み

ddtraceは以下のライブラリを自動的にインスツルメント化:

- **Flask/Django**: HTTPリクエスト/レスポンス
- **psycopg2**: PostgreSQL クエリ
- **redis-py**: Redis コマンド
- **requests**: HTTP クライアント
- **SQLAlchemy**: ORM クエリ

**技術的な動作:**

```python
# ddtrace の内部動作 (簡略化)
import psycopg2

# オリジナルの execute メソッドを保存
original_execute = psycopg2.cursor.execute

def traced_execute(self, query, params=None):
    # スパンを開始
    with tracer.trace("postgres.query") as span:
        span.set_tag("sql.query", query)
        span.set_tag("db.type", "postgres")

        # オリジナルのメソッドを実行
        result = original_execute(self, query, params)

        return result

# メソッドを置き換え (モンキーパッチ)
psycopg2.cursor.execute = traced_execute
```

### 3. トレースサンプリング戦略

#### サンプリングの種類

**1. Head-based Sampling (ヘッドベースサンプリング)**

リクエストの開始時点でサンプリングを決定します。

```python
# 環境変数での設定
DD_TRACE_SAMPLE_RATE=1.0  # 100% サンプリング (開発環境)
DD_TRACE_SAMPLE_RATE=0.1  # 10% サンプリング (本番環境)
```

**2. Priority Sampling (優先度サンプリング)**

トレースの重要度に応じて動的にサンプリング率を調整:

- **Priority 2**: ユーザーが手動で保持を要求
- **Priority 1**: 自動サンプラーが保持を決定
- **Priority 0**: 自動サンプラーが破棄を決定
- **Priority -1**: ユーザーが手動で破棄を要求

**3. Error Sampling (エラーサンプリング)**

エラーを含むトレースは常に保持されます。

```python
@app.route('/api/error')
def error_endpoint():
    with tracer.trace("error_endpoint") as span:
        try:
            result = 1 / 0
        except Exception as e:
            span.set_tag("error", True)
            span.set_tag("error.type", type(e).__name__)
            span.set_tag("error.msg", str(e))
            # このトレースは自動的に保持される
            raise
```

### 4. トレースエージェントへの送信

#### データフロー

```
Application (ddtrace)
      ↓
[Trace Buffer] (メモリ内バッファ)
      ↓ (定期的にフラッシュ: 1秒ごと)
[HTTP/msgpack] → Datadog Agent :8126
      ↓
[Agent Buffer & Aggregation]
      ↓ (10秒ごとにバッチ送信)
[HTTPS/Protocol Buffers] → Datadog Platform
```

#### 通信プロトコル

**1. Application → Agent (HTTP + msgpack)**

```http
POST /v0.4/traces HTTP/1.1
Host: datadog-agent:8126
Content-Type: application/msgpack
Content-Encoding: gzip

[バイナリ msgpack データ]
```

**msgpack形式の利点:**
- JSONより40-50%小さいデータサイズ
- シリアライズ/デシリアライズが高速
- 型情報を保持

**2. Agent → Datadog Platform (HTTPS + Protocol Buffers)**

```
Agent は複数のトレースを集約し、10秒ごとにバッチ送信:
- 圧縮: gzip / zstd
- 暗号化: TLS 1.2+
- エンドポイント: https://trace.agent.datadoghq.com
```

### 5. サービスマップの自動生成

トレース情報から自動的にサービス間の依存関係を抽出:

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  nginx   │────▶│ backend  │────▶│ postgres │
│          │     │   API    │     │    DB    │
└──────────┘     └────┬─────┘     └──────────┘
                      │
                      ▼
                 ┌──────────┐
                 │  redis   │
                 │  cache   │
                 └──────────┘

各矢印には以下の情報が付与:
- リクエスト数/秒
- 平均レイテンシ
- エラー率
- スループット
```

---

## ログ収集・転送の仕組み

### 1. ログ収集アーキテクチャ

```
┌───────────────────────────────────────────────────────────────┐
│                     Application Layer                          │
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Nginx     │  │   Backend   │  │  Frontend   │           │
│  │  Container  │  │  Container  │  │  Container  │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                    │
│    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐            │
│    │ stdout  │      │ stdout  │      │ stdout  │            │
│    │ stderr  │      │ JSON    │      │ JSON    │            │
│    │ files   │      │ logs    │      │ logs    │            │
│    └────┬────┘      └────┬────┘      └────┬────┘            │
│         │                │                │                    │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼────────────────────┐
│                    Docker Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /var/lib/docker/containers/[container-id]/[container-id]-json.log │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  {"log": "...", "stream": "stdout", "time": "..."}      │  │
│  │  {"log": "...", "stream": "stderr", "time": "..."}      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Datadog Agent                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Log Collection Pipeline                                 │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  1. [File Tailer] ─▶ ファイル監視 & 読み込み            │  │
│  │                                                          │  │
│  │  2. [Parser] ─▶ JSON / 正規表現パース                   │  │
│  │                                                          │  │
│  │  3. [Processor] ─▶ 属性追加 / フィルタリング            │  │
│  │     - source, service, host タグ追加                    │  │
│  │     - センシティブ情報マスキング                        │  │
│  │     - ログレベル抽出                                    │  │
│  │                                                          │  │
│  │  4. [Enrichment] ─▶ トレースIDとの相関                  │  │
│  │     - dd.trace_id をログに注入                          │  │
│  │     - dd.span_id をログに注入                           │  │
│  │                                                          │  │
│  │  5. [Buffer] ─▶ メモリバッファ (最大 10MB)              │  │
│  │                                                          │  │
│  │  6. [Batcher] ─▶ バッチ送信 (最大 1000 logs / batch)    │  │
│  │                                                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  HTTPS POST    │
                    │  (gzip圧縮)    │
                    └───────┬────────┘
                            │
               ┌────────────▼────────────┐
               │  Datadog Log Intake     │
               │  logs.datadoghq.com     │
               └─────────────────────────┘
```

### 2. ログ収集の設定方法

#### Docker ラベルによる自動設定

**docker-compose.yml での設定例:**

```yaml
services:
  backend:
    image: my-backend:latest
    labels:
      com.datadoghq.ad.logs: '[
        {
          "source": "python",
          "service": "backend-api",
          "log_processing_rules": [
            {
              "type": "exclude_at_match",
              "name": "exclude_healthcheck",
              "pattern": "GET /health"
            },
            {
              "type": "mask_sequences",
              "name": "mask_api_keys",
              "replace_placeholder": "[REDACTED]",
              "pattern": "api_key=\\w+"
            }
          ]
        }
      ]'
```

#### Datadog Agent のログ収集設定

**環境変数:**

```bash
DD_LOGS_ENABLED=true                          # ログ収集を有効化
DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true     # 全コンテナのログを収集
DD_LOGS_CONFIG_AUTO_MULTI_LINE_DETECTION=true # 複数行ログ自動検出
```

**Agent 設定ファイル (datadog.yaml):**

```yaml
logs_enabled: true
logs_config:
  container_collect_all: true
  processing_rules:
    - type: exclude_at_match
      name: exclude_debug_logs
      pattern: .*DEBUG.*
```

### 3. ログとトレースの相関

#### JSON ログフォーマットでの実装

**backend/app.py での設定:**

```python
from pythonjsonlogger import jsonlogger
from ddtrace import tracer

# JSON形式のロガーを設定
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
logHandler.setFormatter(formatter)

# ログ出力時に自動的にトレースIDが追加される
logger.info("User request processed")

# 出力例:
# {
#   "asctime": "2024-01-15 10:30:45",
#   "name": "backend-api",
#   "levelname": "INFO",
#   "message": "User request processed",
#   "dd.trace_id": "1234567890123456789",
#   "dd.span_id": "9876543210987654",
#   "dd.service": "backend-api",
#   "dd.env": "dev",
#   "dd.version": "1.0.0"
# }
```

#### トレースIDの自動注入

ddtraceライブラリは、ログ出力時に自動的にトレースコンテキストを注入します:

```python
# 環境変数で有効化
DD_LOGS_INJECTION=true

# これにより、tracer のコンテキストがログに自動追加される
```

**Datadog UI での相関表示:**

```
トレースビュー:
┌─────────────────────────────────────┐
│ Trace: 1234567890123456789          │
├─────────────────────────────────────┤
│ nginx.request     245ms             │
│   flask.request   230ms             │
│     postgres.query 45ms             │
│                                     │
│ [Logs] タブ:                        │
│  - 10:30:45 INFO User request...   │
│  - 10:30:45 DEBUG DB query...      │
│  - 10:30:46 ERROR Cache miss...    │
└─────────────────────────────────────┘
```

### 4. ログ処理パイプライン

#### ログ処理ルールの適用順序

```
Raw Log
  ↓
[1. Source Detection] - ログのソースを特定
  ↓
[2. Service Extraction] - サービス名を抽出
  ↓
[3. Status Remapping] - ログレベルを正規化
  ↓
[4. Multi-line Aggregation] - 複数行ログを統合
  ↓
[5. Parsing] - JSON / 正規表現でパース
  ↓
[6. Attribute Extraction] - 属性を抽出
  ↓
[7. Trace ID Correlation] - トレースIDと相関
  ↓
[8. Sensitive Data Scanner] - 機密情報をマスク
  ↓
[9. Exclusion Filters] - 不要なログを除外
  ↓
Processed Log → Datadog Platform
```

#### パイプラインの例

**Nginx アクセスログのパース:**

```
Raw Log:
192.168.1.100 - - [15/Jan/2024:10:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234

↓ [Parsing with grok pattern]

Parsed Attributes:
{
  "http.client_ip": "192.168.1.100",
  "http.method": "GET",
  "http.url": "/api/users",
  "http.status_code": 200,
  "network.bytes_written": 1234,
  "timestamp": "2024-01-15T10:30:45Z"
}
```

### 5. ログの送信と配信保証

#### 送信バッファとリトライメカニズム

```
┌─────────────────────────────────────┐
│  Datadog Agent Log Buffer           │
├─────────────────────────────────────┤
│                                     │
│  [In-Memory Buffer]                 │
│  - Max Size: 10MB                   │
│  - Max Age: 5 seconds               │
│                                     │
│  ↓ (バッファが満杯 or タイムアウト)  │
│                                     │
│  [Batch Sender]                     │
│  - Max logs per batch: 1000         │
│  - Compression: gzip                │
│                                     │
│  ↓ (送信失敗時)                      │
│                                     │
│  [Retry Queue]                      │
│  - Exponential backoff              │
│  - Max retries: 5                   │
│  - Retry intervals:                 │
│    1s → 2s → 4s → 8s → 16s          │
│                                     │
└─────────────────────────────────────┘
```

#### 送信プロトコル

```http
POST /v1/input HTTP/1.1
Host: http-intake.logs.datadoghq.com
Content-Type: application/json
Content-Encoding: gzip
DD-API-KEY: [API_KEY]

[
  {
    "ddsource": "python",
    "ddtags": "env:dev,service:backend-api",
    "hostname": "backend-container",
    "message": "User request processed",
    "timestamp": 1705315845000,
    "dd.trace_id": "1234567890123456789"
  }
]
```

---

## メトリクス収集・集約の詳細

### 1. メトリクス収集アーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Backend API   │  │    Nginx        │  │   PostgreSQL    │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  │
│  │                 │  │                 │  │                 │  │
│  │ DogStatsD       │  │ nginx_status    │  │ pg_stat_*       │  │
│  │ Client          │  │ module          │  │ views           │  │
│  │   ↓             │  │   ↓             │  │   ↓             │  │
│  │ statsd.gauge()  │  │ HTTP /status    │  │ SQL queries     │  │
│  │ statsd.count()  │  │                 │  │                 │  │
│  │ statsd.histo()  │  │                 │  │                 │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │             │
└───────────┼────────────────────┼────────────────────┼─────────────┘
            │                    │                    │
            │ UDP :8125          │ HTTP polling       │ TCP query
            │                    │ (10s interval)     │ (10s interval)
            │                    │                    │
┌───────────▼────────────────────▼────────────────────▼─────────────┐
│                    Datadog Agent :8125 / :8126                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  DogStatsD Server (UDP receiver)                           │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  [1. UDP Socket] → メトリクス受信 (non-blocking)           │  │
│  │                                                             │  │
│  │  [2. Parser] → メトリクスフォーマット解析                  │  │
│  │      Format: metric.name:value|type|@sample|#tags          │  │
│  │                                                             │  │
│  │  [3. Aggregator] → 10秒間隔で集約                          │  │
│  │      - Counter: 合計値                                     │  │
│  │      - Gauge: 最新値                                       │  │
│  │      - Histogram: 統計値 (min/max/avg/p50/p95/p99)        │  │
│  │      - Rate: 変化率                                        │  │
│  │                                                             │  │
│  │  [4. Tagger] → タグ追加                                    │  │
│  │      - host, container_id, env, service                    │  │
│  │                                                             │  │
│  │  [5. Buffer] → メモリバッファ (最大 10,000 metrics)        │  │
│  │                                                             │  │
│  └─────────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
│  ┌─────────────────────────▼───────────────────────────────────┐  │
│  │  Checks & Integrations (ポーリング型収集)                  │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  [Nginx Check]                                             │  │
│  │    └─ HTTP GET http://nginx/nginx_status                   │  │
│  │       └─ nginx.net.connections, nginx.net.requests/s       │  │
│  │                                                             │  │
│  │  [PostgreSQL Check]                                        │  │
│  │    └─ SQL: SELECT * FROM pg_stat_database                  │  │
│  │       └─ postgresql.connections, postgresql.locks          │  │
│  │                                                             │  │
│  │  [Redis Check]                                             │  │
│  │    └─ Redis: INFO command                                  │  │
│  │       └─ redis.mem.used, redis.net.commands/s              │  │
│  │                                                             │  │
│  │  [Docker Check]                                            │  │
│  │    └─ Docker API: /containers/json                         │  │
│  │       └─ docker.cpu.usage, docker.mem.usage                │  │
│  │                                                             │  │
│  └─────────────────────────┬───────────────────────────────────┘  │
│                            │                                       │
└────────────────────────────┼───────────────────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Serialization   │
                    │  Protocol Buffers│
                    │  + gzip          │
                    └────────┬─────────┘
                             │
                ┌────────────▼─────────────┐
                │  HTTPS POST (batch)      │
                │  metrics.datadoghq.com   │
                └──────────────────────────┘
```

### 2. メトリクスタイプの詳細

#### 1. Counter (カウンター)

リクエスト数、エラー数など、累積値を記録するメトリクス。

**使用例:**

```python
from datadog import statsd

# リクエスト数をカウント
statsd.increment('api.requests', tags=['endpoint:users', 'method:GET'])

# エラー数をカウント
statsd.increment('api.errors', tags=['error_type:500'])

# 複数回カウント
statsd.increment('cache.hits', value=10)
```

**Agent での集約:**

```
Time Window: 10 seconds

Received:
  t=0s:  api.requests:1
  t=2s:  api.requests:1
  t=5s:  api.requests:1
  t=8s:  api.requests:1

Aggregated (sent to Datadog):
  api.requests: 4 (rate: 0.4 requests/second)
```

#### 2. Gauge (ゲージ)

現在の値を記録するメトリクス。CPU使用率、メモリ使用量など。

**使用例:**

```python
# ユーザー数を記録
statsd.gauge('users.count', 1250, tags=['database:postgres'])

# キャッシュサイズを記録
statsd.gauge('cache.size', 1024, tags=['cache:redis'])
```

**Agent での集約:**

```
Time Window: 10 seconds

Received:
  t=0s:  cache.size:1000
  t=3s:  cache.size:1200
  t=7s:  cache.size:1100

Aggregated (sent to Datadog):
  cache.size: 1100 (最新値のみ送信)
```

#### 3. Histogram (ヒストグラム)

値の分布を記録するメトリクス。レイテンシ、リクエストサイズなど。

**使用例:**

```python
import time

start = time.time()
# 処理実行
response = make_api_call()
duration = time.time() - start

# レイテンシを記録
statsd.histogram('api.response_time', duration, tags=['endpoint:users'])
```

**Agent での集約:**

```
Time Window: 10 seconds

Received:
  api.response_time:0.123
  api.response_time:0.245
  api.response_time:0.156
  api.response_time:0.089
  api.response_time:0.312

Aggregated (sent to Datadog):
  api.response_time.avg: 0.185
  api.response_time.max: 0.312
  api.response_time.min: 0.089
  api.response_time.median: 0.156
  api.response_time.95percentile: 0.312
  api.response_time.99percentile: 0.312
  api.response_time.count: 5
  api.response_time.sum: 0.925
```

#### 4. Distribution (ディストリビューション)

グローバルに集約される高精度なヒストグラム。

**使用例:**

```python
# レイテンシをグローバルに記録
statsd.distribution('request.duration', duration, tags=['region:us-east-1'])
```

**特徴:**
- サーバー側で集約 (Agent 集約なし)
- 複数のホスト/リージョンをまたいだ統計
- パーセンタイル計算が高精度

### 3. DogStatsD プロトコル

#### メトリクスフォーマット

```
metric.name:value|type|@sample_rate|#tag1:value1,tag2:value2
```

**例:**

```
# Counter
page.views:1|c|#page:home,user:logged_in

# Gauge
memory.usage:1024|g|#host:backend-01

# Histogram
request.duration:0.234|h|@0.5|#endpoint:api,method:GET

# Distribution
request.size:2048|d|#service:nginx
```

#### UDP 通信の特性

**メリット:**
- 低オーバーヘッド (TCPハンドシェイク不要)
- アプリケーションのブロッキングなし
- 高スループット

**デメリット:**
- 配信保証なし (パケットロスの可能性)
- ネットワーク輻輳時にメトリクスが失われる可能性

**対策:**
```python
# サンプリングによる負荷軽減
statsd.increment('high_volume.metric', sample_rate=0.1)
# → 10回に1回だけ送信し、Datadogが自動的に10倍に補正
```

### 4. インテグレーションによるメトリクス収集

#### PostgreSQL インテグレーション

**docker-compose.yml でのラベル設定:**

```yaml
services:
  postgres:
    labels:
      com.datadoghq.ad.check_names: '["postgres"]'
      com.datadoghq.ad.init_configs: '[{}]'
      com.datadoghq.ad.instances: '[
        {
          "host": "%%host%%",
          "port": 5432,
          "username": "demo_user",
          "password": "demo_password",
          "dbname": "demo_db",
          "relations": [
            {"relation_name": "users", "schemas": ["public"]},
            {"relation_name": "orders", "schemas": ["public"]}
          ]
        }
      ]'
```

**収集されるメトリクス:**

```
postgresql.connections             # 接続数
postgresql.database.size           # データベースサイズ
postgresql.locks                   # ロック数
postgresql.bgwriter.checkpoints    # チェックポイント
postgresql.table.rows              # テーブル行数
postgresql.table.size              # テーブルサイズ
postgresql.index.size              # インデックスサイズ
postgresql.query.count             # クエリ実行数
```

#### Redis インテグレーション

**収集されるメトリクス:**

```
redis.mem.used                     # メモリ使用量
redis.mem.fragmentation_ratio      # メモリ断片化率
redis.net.commands                 # コマンド実行数/秒
redis.net.clients                  # 接続クライアント数
redis.keys                         # キー総数
redis.expires                      # TTL付きキー数
redis.evicted_keys                 # 退去されたキー数
redis.cpu.sys                      # システムCPU時間
```

#### Nginx インテグレーション

**nginx.conf での設定:**

```nginx
server {
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

**収集されるメトリクス:**

```
nginx.net.connections              # 接続数
nginx.net.conn_opened_per_s        # 新規接続数/秒
nginx.net.conn_dropped_per_s       # 切断された接続数/秒
nginx.net.request_per_s            # リクエスト数/秒
nginx.net.reading                  # リクエスト読み込み中の接続
nginx.net.writing                  # レスポンス書き込み中の接続
nginx.net.waiting                  # アイドル接続
```

### 5. メトリクス集約とロールアップ

#### 時系列データの保存とロールアップ

```
Raw Data (10秒解像度)
  ↓
[1 hour retention] → 保存期間: 15時間
  ↓
[1 minute rollup] → 1分間隔に集約
  ↓
[1 hour rollup] → 1時間間隔に集約
  ↓
[Retention: 15 months] → 長期保存
```

**ロールアップの計算方法:**

```
1分間のロールアップ (6 data points, 10秒間隔):

Counter:
  sum([1, 2, 1, 3, 2, 1]) = 10

Gauge:
  avg([100, 102, 105, 103, 101, 100]) = 101.83

Histogram:
  全データポイントを統合して再計算
  p95([0.1, 0.2, 0.15, 0.3, 0.12, 0.18]) = 0.27
```

---

## RUM (Real User Monitoring) 技術的実装

### 1. RUM アーキテクチャ

```
┌────────────────────────────────────────────────────────────────┐
│                        User Browser                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React Application (frontend)                           │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  [1. RUM SDK Initialization]                            │  │
│  │      import { datadogRum } from '@datadog/browser-rum'  │  │
│  │                                                          │  │
│  │      datadogRum.init({                                  │  │
│  │        applicationId: 'xxx',                            │  │
│  │        clientToken: 'yyy',                              │  │
│  │        site: 'datadoghq.com',                           │  │
│  │        service: 'frontend',                             │  │
│  │        env: 'dev',                                      │  │
│  │        version: '1.0.0',                                │  │
│  │        sessionSampleRate: 100,                          │  │
│  │        sessionReplaySampleRate: 100,                    │  │
│  │        trackUserInteractions: true,                     │  │
│  │        trackResources: true,                            │  │
│  │        trackLongTasks: true                             │  │
│  │      })                                                 │  │
│  │                                                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  [2. Auto-Instrumentation]                              │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Page Views                                         │ │  │
│  │  │  - URL changes                                     │ │  │
│  │  │  - Navigation timing                               │ │  │
│  │  │  - First Contentful Paint (FCP)                    │ │  │
│  │  │  - Largest Contentful Paint (LCP)                  │ │  │
│  │  │  - First Input Delay (FID)                         │ │  │
│  │  │  - Cumulative Layout Shift (CLS)                   │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Resources                                          │ │  │
│  │  │  - XHR / Fetch requests                            │ │  │
│  │  │  - Images, CSS, JS files                           │ │  │
│  │  │  - Load time, size                                 │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Errors                                             │ │  │
│  │  │  - JavaScript errors                               │ │  │
│  │  │  - Network errors                                  │ │  │
│  │  │  - Console errors                                  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ User Actions                                       │ │  │
│  │  │  - Clicks                                          │ │  │
│  │  │  - Form submissions                                │ │  │
│  │  │  - Custom actions                                  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Long Tasks                                         │ │  │
│  │  │  - JavaScript blocking > 50ms                      │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │  [3. Data Collection & Buffering]                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  In-Memory Buffer:                                      │  │
│  │  - Events queued until batch size reached               │  │
│  │  - Max batch: 50 events or 30 seconds                   │  │
│  │  - Compression: JSON → gzip                             │  │
│  │                                                          │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │  HTTPS POST        │
                  │  (gzip compressed) │
                  └─────────┬──────────┘
                            │
            ┌───────────────▼───────────────┐
            │  Datadog RUM Intake           │
            │  rum.browser-intake-          │
            │  datadoghq.com                │
            │                               │
            │  ┌─────────────────────────┐  │
            │  │ Session Replay Storage  │  │
            │  │ (video recording)       │  │
            │  └─────────────────────────┘  │
            └───────────────────────────────┘
```

### 2. RUM SDK の実装

#### 初期化 (frontend/src/index.js)

```javascript
import { datadogRum } from '@datadog/browser-rum';

datadogRum.init({
    // 必須設定
    applicationId: process.env.REACT_APP_DD_RUM_APPLICATION_ID,
    clientToken: process.env.REACT_APP_DD_RUM_CLIENT_TOKEN,
    site: process.env.REACT_APP_DD_RUM_SITE || 'datadoghq.com',

    // サービス情報
    service: 'frontend',
    env: process.env.REACT_APP_DD_RUM_ENV || 'dev',
    version: '1.0.0',

    // セッションサンプリング
    sessionSampleRate: 100,  // 100% のセッションを収集
    sessionReplaySampleRate: 100,  // 100% セッションリプレイ記録

    // パフォーマンス追跡
    trackUserInteractions: true,  // クリック、スクロールなど
    trackResources: true,         // XHR/Fetch、画像、CSS/JS
    trackLongTasks: true,         // 50ms以上のJavaScript実行

    // ネットワーク追跡
    allowedTracingUrls: [
        { match: 'http://localhost:80/api', propagatorTypes: ['datadog'] },
        { match: /https:\/\/.*\.example\.com/, propagatorTypes: ['datadog'] }
    ],

    // プライバシー設定
    defaultPrivacyLevel: 'mask-user-input',  // ユーザー入力をマスク

    // エラー追跡
    trackSessionAcrossSubdomains: true,
    useSecureSessionCookie: true,
    useCrossSiteSessionCookie: true,

    // 詳細設定
    beforeSend: (event, context) => {
        // イベント送信前のカスタム処理
        if (event.type === 'error' && event.error.message.includes('test')) {
            return false;  // テストエラーを除外
        }
        return true;
    }
});

// ユーザー情報の設定
datadogRum.setUser({
    id: '12345',
    name: 'John Doe',
    email: 'john.doe@example.com',
    plan: 'premium'
});

// グローバルコンテキストの追加
datadogRum.setGlobalContextProperty('region', 'us-east-1');
datadogRum.setGlobalContextProperty('feature_flags', {
    new_dashboard: true,
    beta_features: false
});
```

#### カスタムアクションの追跡

```javascript
import { datadogRum } from '@datadog/browser-rum';

// カスタムアクションを記録
function handleCheckout(cart) {
    datadogRum.addAction('checkout', {
        cart_total: cart.total,
        item_count: cart.items.length,
        payment_method: 'credit_card'
    });
}

// カスタムエラーを記録
function handlePaymentError(error) {
    datadogRum.addError(error, {
        payment_method: 'credit_card',
        amount: 99.99,
        error_code: error.code
    });
}

// カスタムタイミングを記録
function measureFeatureLoad() {
    const startTime = performance.now();

    loadFeature().then(() => {
        const duration = performance.now() - startTime;
        datadogRum.addTiming('feature_load_time', duration);
    });
}
```

### 3. Performance API との統合

RUM SDK は **Navigation Timing API** と **Performance Observer API** を使用してパフォーマンスメトリクスを収集します。

#### Navigation Timing

```javascript
// ブラウザのナビゲーションタイミング
const perfData = performance.getEntriesByType('navigation')[0];

{
  "view.loading_time": 1234,           // 総ロード時間
  "view.dom_content_loaded": 890,      // DOM Content Loaded
  "view.dom_interactive": 850,         // DOM Interactive
  "view.dom_complete": 1200,           // DOM Complete
  "view.load_event": 1234,             // Load Event

  // ネットワーク
  "view.dns_time": 45,                 // DNS解決時間
  "view.tcp_time": 78,                 // TCP接続時間
  "view.ssl_time": 120,                // SSL/TLSハンドシェイク
  "view.ttfb": 234,                    // Time to First Byte
  "view.download_time": 456,           // コンテンツダウンロード時間

  // レンダリング
  "view.first_paint": 678,             // First Paint
  "view.first_contentful_paint": 720,  // First Contentful Paint
  "view.largest_contentful_paint": 1100 // Largest Contentful Paint
}
```

#### Core Web Vitals

```javascript
// Largest Contentful Paint (LCP)
// - 最大のコンテンツが表示されるまでの時間
// - 目標: 2.5秒以下
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime);
}).observe({ type: 'largest-contentful-paint', buffered: true });

// First Input Delay (FID)
// - ユーザーの最初の操作に対する応答時間
// - 目標: 100ms以下
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  entries.forEach((entry) => {
    console.log('FID:', entry.processingStart - entry.startTime);
  });
}).observe({ type: 'first-input', buffered: true });

// Cumulative Layout Shift (CLS)
// - レイアウトの累積的なずれ
// - 目標: 0.1以下
let clsScore = 0;
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsScore += entry.value;
    }
  }
  console.log('CLS:', clsScore);
}).observe({ type: 'layout-shift', buffered: true });
```

### 4. フロントエンド ↔ バックエンド トレース相関

#### トレースコンテキストの伝播

RUM SDK は XHR/Fetch リクエストに自動的にトレースヘッダーを追加します。

```javascript
// フロントエンドでのリクエスト
fetch('http://localhost:80/api/users')
  .then(response => response.json());

// 自動的に追加されるヘッダー:
{
  "x-datadog-trace-id": "1234567890123456789",
  "x-datadog-parent-id": "9876543210987654",
  "x-datadog-origin": "rum",
  "x-datadog-sampling-priority": "1"
}
```

**バックエンドでの受信 (Flask):**

```python
from ddtrace import tracer
from flask import request

@app.route('/api/users')
def get_users():
    # ddtrace が自動的にトレースコンテキストを抽出
    # RUM trace_id がバックエンドトレースに引き継がれる

    span = tracer.current_span()
    trace_id = span.trace_id  # フロントエンドと同じ trace_id

    logger.info(f"Request from RUM, trace_id: {trace_id}")

    return jsonify({"users": users})
```

**Datadog UI での表示:**

```
RUM Session View:
┌────────────────────────────────────────┐
│ User Session: john.doe@example.com     │
├────────────────────────────────────────┤
│ Page View: /users                      │
│  ↓                                     │
│ XHR: GET /api/users (245ms)            │
│  - Frontend: 15ms                      │
│  - Backend: 230ms ← [View in APM]     │
│    ↓                                   │
│    └─ postgres.query: 45ms             │
└────────────────────────────────────────┘
```

### 5. Session Replay の仕組み

#### DOM スナップショットとイベント記録

Session Replay は DOM の変更をキャプチャし、動画のように再生可能な形式で記録します。

**記録される情報:**

```javascript
{
  "type": "full_snapshot",
  "timestamp": 1705315845000,
  "data": {
    "node": {
      "type": 0,
      "childNodes": [
        {
          "type": 1,
          "tagName": "html",
          "attributes": {},
          "childNodes": [
            {
              "type": 1,
              "tagName": "body",
              "attributes": {"class": "dark-mode"},
              "childNodes": [...]
            }
          ]
        }
      ]
    }
  }
}

// その後の変更は差分として記録
{
  "type": "incremental_snapshot",
  "timestamp": 1705315846000,
  "data": {
    "source": 2,  // Mutation
    "adds": [],
    "removes": [],
    "texts": [
      {
        "id": 123,
        "value": "New text content"
      }
    ],
    "attributes": [
      {
        "id": 456,
        "attributes": {
          "class": "active"
        }
      }
    ]
  }
}
```

#### プライバシー保護

```javascript
datadogRum.init({
    defaultPrivacyLevel: 'mask-user-input',  // デフォルト設定
    // ...
});

// HTML要素でのプライバシー制御
<input type="text" data-dd-privacy="mask" />        <!-- 完全にマスク -->
<div data-dd-privacy="allow">Safe content</div>     <!-- 許可 -->
<div data-dd-privacy="hidden">Sensitive data</div>  <!-- 非表示 -->
```

**マスキングの例:**

```
元のHTML:
<input type="password" value="mypassword123" />
<div>Credit card: 4111-1111-1111-1111</div>

記録されるデータ:
<input type="password" value="***" />
<div>Credit card: ***</div>
```

### 6. RUM データの送信と保存

#### バッチ送信メカニズム

```
Browser Buffer
├─ Event Queue (max 50 events or 30 seconds)
│   ├─ View event
│   ├─ Resource event
│   ├─ Action event
│   └─ Error event
│
└─ Batch Sender
    ↓
    [HTTPS POST] → Datadog RUM Intake

    Payload:
    {
      "application": {
        "id": "xxx"
      },
      "session": {
        "id": "session-123",
        "type": "user"
      },
      "view": {
        "id": "view-456",
        "url": "http://example.com/users",
        "referrer": "http://example.com/home"
      },
      "events": [
        {
          "type": "view",
          "date": 1705315845000,
          "view": {
            "loading_time": 1234,
            "first_contentful_paint": 720,
            "largest_contentful_paint": 1100
          }
        }
      ]
    }
```

---

## データフロー全体図

### エンドツーエンドのデータフロー

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│  ┌────────────┐                                                  │
│  │ RUM SDK    │ ────HTTPS────▶ Datadog RUM Intake               │
│  └────────────┘                                                  │
└────────────┬────────────────────────────────────────────────────┘
             │ HTTP Request
             │ (w/ trace headers)
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Nginx                                                           │
│  ├─ Access Log ────────────────┐                                │
│  └─ Metrics (connections) ─────┤                                │
└────────────┬───────────────────┼─────────────────────────────────┘
             │                   │
             ▼                   │
┌─────────────────────────────────────────────────────────────────┐
│  Backend (Flask)                │                                │
│  ├─ APM Traces ─────────────────┤                                │
│  ├─ DogStatsD Metrics ──────────┤                                │
│  └─ JSON Logs ──────────────────┤                                │
└────────────┬────────────────────┼─────────────────────────────────┘
             │                    │
      ┌──────┴─────┐              │
      ▼            ▼              │
┌──────────┐  ┌──────────┐       │
│ Postgres │  │  Redis   │       │
│          │  │          │       │
│ Metrics ─┤  │ Metrics ─┤       │
│ Logs ────┤  │ Logs ────┤       │
└──────┬───┘  └────┬─────┘       │
       │           │              │
       └───────┬───┘              │
               │                  │
┌──────────────▼──────────────────▼───────────────────────────────┐
│  Datadog Agent                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  APM Traces      :8126  ──▶ trace.agent.datadoghq.com    │  │
│  │  DogStatsD       :8125  ──▶ metrics.datadoghq.com        │  │
│  │  Logs            file   ──▶ logs.datadoghq.com           │  │
│  │  Integrations    checks ──▶ metrics.datadoghq.com        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Datadog Platform (Cloud)                     │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │   APM        │   Metrics    │   Logs       │    RUM       │  │
│  │   Backend    │   Backend    │   Backend    │   Backend    │  │
│  └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘  │
│         │              │              │              │           │
│         └──────────────┴──────────────┴──────────────┘           │
│                        │                                         │
│  ┌─────────────────────▼──────────────────────────────────────┐  │
│  │  Query Engine & Correlation                                │  │
│  │  - Traces ↔ Logs (trace_id)                                │  │
│  │  - Traces ↔ RUM (trace_id)                                 │  │
│  │  - Metrics ↔ Tags (service, env, host)                     │  │
│  └─────────────────────┬──────────────────────────────────────┘  │
│                        ▼                                         │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Datadog UI (Dashboards, Monitors, Alerts)              │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## パフォーマンスとスケーラビリティ

### 1. Datadog Agent のリソース使用量

#### 推奨リソース配分

```yaml
Minimum:
  CPU: 0.5 cores
  Memory: 512 MB

Recommended (本番環境):
  CPU: 1-2 cores
  Memory: 1-2 GB

High Volume (大規模環境):
  CPU: 4+ cores
  Memory: 4+ GB
```

#### Agent のチューニング

```yaml
# datadog.yaml
apm_config:
  max_traces_per_second: 100      # トレース制限
  max_memory: 500000000           # 最大メモリ (500MB)
  max_cpu_percent: 50             # 最大CPU使用率

logs_config:
  open_files_limit: 100           # 同時監視ファイル数

dogstatsd_config:
  buffer_size: 8192               # UDPバッファサイズ
  queue_size: 1024                # キューサイズ
```

### 2. サンプリング戦略

#### 本番環境での推奨設定

```python
# Backend APM
DD_TRACE_SAMPLE_RATE=0.1  # 10% サンプリング

# RUM
sessionSampleRate: 10      # 10% のセッションを記録
sessionReplaySampleRate: 1 # 1% セッションリプレイ

# DogStatsD
statsd.increment('metric', sample_rate=0.1)  # 10% サンプリング
```

### 3. データ保持期間

```
APM Traces:
  - 保持期間: 15日間
  - 統計データ: 15ヶ月

Logs:
  - デフォルト: 15日間
  - 拡張可能: 最大15ヶ月 (プランによる)

Metrics:
  - フル解像度 (10秒): 15時間
  - 1分ロールアップ: 15ヶ月

RUM:
  - セッション: 30日間
  - Session Replay: 30日間
```

---

## まとめ

このドキュメントでは、Datadogの技術アーキテクチャの詳細を解説しました:

1. **APM**: 分散トレーシング、自動インスツルメンテーション、トレースコンテキスト伝播
2. **ログ**: ファイル監視、パース、トレース相関、バッチ送信
3. **メトリクス**: DogStatsD、インテグレーション、集約、ロールアップ
4. **RUM**: ブラウザSDK、Performance API、Session Replay、フロントエンド/バックエンド相関

これらの技術を組み合わせることで、フルスタックの可観測性を実現できます。
