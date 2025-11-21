# OpenTelemetry (OTel) 完全ガイド

## 目次

1. [OpenTelemetryとは](#opentelemetryとは)
2. [歴史と背景](#歴史と背景)
3. [OTelの意義と目的](#otelの意義と目的)
4. [OpenTelemetryの仕様](#opentelemetryの仕様)
5. [DataDogとOpenTelemetryの関係](#datadogとopentelemetryの関係)
6. [OTel vs Datadog Agent比較](#otel-vs-datadog-agent比較)
7. [DatadogでのOTel活用方法](#datadogでのotel活用方法)
8. [移行戦略とベストプラクティス](#移行戦略とベストプラクティス)

---

## OpenTelemetryとは

**OpenTelemetry (OTel)** は、クラウドネイティブアプリケーションのテレメトリデータ（トレース、メトリクス、ログ）を収集、処理、エクスポートするための**ベンダー中立的なオープンソース標準**です。

### コアコンセプト

```
┌─────────────────────────────────────────────────────────────┐
│            OpenTelemetry の3つの柱                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Traces     │  │   Metrics    │  │    Logs      │      │
│  │              │  │              │  │              │      │
│  │ 分散システム  │  │ 時系列の     │  │ 構造化       │      │
│  │ のリクエスト  │  │ 数値データ   │  │ イベント     │      │
│  │ フロー       │  │              │  │ データ       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### キーコンポーネント

1. **API**: テレメトリデータを生成するためのインターフェース
2. **SDK**: APIの実装と設定
3. **Instrumentation Libraries**: 自動計装ライブラリ
4. **Collector**: テレメトリデータの収集・処理・エクスポート
5. **Protocol (OTLP)**: 標準通信プロトコル

---

## 歴史と背景

### タイムライン

```
2016
  │
  ├─ OpenTracing 誕生
  │   - CNCF プロジェクトとして開始
  │   - 分散トレーシングのAPI標準化
  │   - Jaeger, Zipkin などが実装
  │
2017
  │
  ├─ OpenCensus 誕生
  │   - Google が開発
  │   - トレーシング + メトリクスの統合
  │   - より包括的なアプローチ
  │
2019
  │
  ├─ OpenTelemetry 誕生
  │   - OpenTracing と OpenCensus が統合
  │   - CNCF Sandbox プロジェクトとして開始
  │   - 業界全体の統一標準を目指す
  │
2021
  │
  ├─ Tracing 仕様が GA (Generally Available)
  │   - 本番環境での使用が推奨される
  │
2022
  │
  ├─ Metrics 仕様が GA
  │
2023
  │
  ├─ Logs 仕様が安定化
  │   - 3つの柱すべてが成熟
  │
2024
  │
  └─ 広く採用される
      - AWS, Google Cloud, Azure がネイティブサポート
      - Datadog, New Relic, Dynatrace などが統合
      - Kubernetes エコシステムの標準に
```

### なぜ統合が必要だったか？

#### OpenTracing の課題

- **トレーシング専用**: メトリクスやログは対象外
- **実装の断片化**: 各ベンダーが独自の実装
- **コンテキスト伝播の非標準化**: 相互運用性の問題

#### OpenCensus の課題

- **Googleの色が強い**: コミュニティの分散
- **OpenTracingとの競合**: エコシステムの分断

#### OpenTelemetry による解決

```
統合前:
┌──────────────┐    ┌──────────────┐
│ OpenTracing  │    │ OpenCensus   │
├──────────────┤    ├──────────────┤
│ - Traces     │    │ - Traces     │
│              │    │ - Metrics    │
│              │    │              │
│ 多数の実装    │    │ Google主導   │
└──────────────┘    └──────────────┘
        ↓                   ↓
        └─────────┬─────────┘
                  ↓
        ┌──────────────────┐
        │ OpenTelemetry    │
        ├──────────────────┤
        │ - Traces         │
        │ - Metrics        │
        │ - Logs           │
        │                  │
        │ 統一された仕様    │
        │ ベンダー中立     │
        │ CNCF 管理        │
        └──────────────────┘
```

---

## OTelの意義と目的

### 1. ベンダーロックインの回避

**問題:**
```
従来のアプローチ:
Application → [Datadog Agent] → Datadog Platform
              (ベンダー固有)      (ロックイン)

変更が困難:
- エージェントの置き換えが必要
- コードの書き直しが必要
- データフォーマットの変換が必要
```

**OTel による解決:**
```
OpenTelemetry アプローチ:
Application → [OTel Collector] → [任意のバックエンド]
              (標準化)            - Datadog
                                  - Prometheus
                                  - Jaeger
                                  - New Relic
                                  - など

利点:
- バックエンド変更が容易
- 複数のバックエンドに同時送信可能
- アプリケーションコードは変更不要
```

### 2. 標準化による相互運用性

#### 統一されたAPI

```go
// OpenTelemetry の統一されたAPI (Go例)
import "go.opentelemetry.io/otel"

// トレーサーの取得（実装に依存しない）
tracer := otel.Tracer("my-service")

// スパンの作成（標準化されたAPI）
ctx, span := tracer.Start(ctx, "operation-name")
defer span.End()

// 属性の追加（標準化されたセマンティック規約）
span.SetAttributes(
    attribute.String("http.method", "GET"),
    attribute.String("http.url", "/api/users"),
    attribute.Int("http.status_code", 200),
)
```

#### セマンティック規約 (Semantic Conventions)

OpenTelemetry は共通の属性名を定義:

```yaml
HTTP リクエスト:
  http.method: GET, POST, PUT, DELETE
  http.url: リクエストURL
  http.status_code: HTTPステータスコード
  http.user_agent: ユーザーエージェント

Database:
  db.system: postgresql, mysql, redis
  db.name: データベース名
  db.statement: SQLクエリ
  db.operation: SELECT, INSERT, UPDATE

RPC/gRPC:
  rpc.system: grpc
  rpc.service: サービス名
  rpc.method: メソッド名
  rpc.grpc.status_code: gRPCステータスコード
```

これにより、異なるベンダー間でも一貫したクエリが可能:

```
# どのバックエンドでも同じクエリ
http.method:GET AND http.status_code:500
```

### 3. コミュニティとエコシステム

#### CNCF プロジェクトとしての位置づけ

```
CNCF Graduated Projects (最高ランク):
├─ Kubernetes
├─ Prometheus
├─ Envoy
└─ OpenTelemetry (進行中)

支援企業:
- Google, Microsoft, AWS, Alibaba
- Datadog, New Relic, Dynatrace
- Splunk, Lightstep, Honeycomb
- など100社以上
```

#### 幅広い言語サポート

```
公式サポート言語:
├─ Go
├─ Java
├─ Python
├─ JavaScript/TypeScript
├─ .NET (C#)
├─ Ruby
├─ PHP
├─ Rust
├─ C++
└─ Erlang/Elixir
```

---

## OpenTelemetryの仕様

### アーキテクチャ全体図

```
┌───────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Application Code                                       │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │                                                         │  │
│  │  import { trace, metrics, logs } from '@opentelemetry'  │  │
│  │                                                         │  │
│  │  // Manual Instrumentation                             │  │
│  │  const span = tracer.startSpan('operation')            │  │
│  │  meter.createCounter('requests').add(1)                │  │
│  │  logger.info('Event occurred')                         │  │
│  │                                                         │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                       │
│  ┌─────────────────────▼───────────────────────────────────┐  │
│  │  Auto-Instrumentation Libraries                         │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  - HTTP Client/Server                                   │  │
│  │  - Database drivers (PostgreSQL, MySQL, MongoDB)        │  │
│  │  - RPC frameworks (gRPC)                                │  │
│  │  - Message queues (Kafka, RabbitMQ)                     │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                       │
│  ┌─────────────────────▼───────────────────────────────────┐  │
│  │  OpenTelemetry SDK                                      │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  - TracerProvider                                       │  │
│  │  - MeterProvider                                        │  │
│  │  - LoggerProvider                                       │  │
│  │  - Context Propagation                                  │  │
│  │  - Resource Detection                                   │  │
│  │  - Sampling                                             │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                       │
└────────────────────────┼───────────────────────────────────────┘
                         │
                         │ OTLP (OpenTelemetry Protocol)
                         │ - gRPC or HTTP/JSON
                         │
┌────────────────────────▼───────────────────────────────────────┐
│             OpenTelemetry Collector (Optional)                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │  Receivers   │   │  Processors  │   │  Exporters   │       │
│  ├──────────────┤   ├──────────────┤   ├──────────────┤       │
│  │ - OTLP       │──▶│ - Batch      │──▶│ - Datadog    │       │
│  │ - Jaeger     │   │ - Sampling   │   │ - Prometheus │       │
│  │ - Zipkin     │   │ - Attributes │   │ - Jaeger     │       │
│  │ - Prometheus │   │ - Filtering  │   │ - OTLP       │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   Observability Backends       │
        ├────────────────────────────────┤
        │ - Datadog                      │
        │ - Prometheus + Grafana         │
        │ - Jaeger                       │
        │ - AWS X-Ray                    │
        │ - Google Cloud Trace           │
        │ - Azure Monitor                │
        └────────────────────────────────┘
```

### OTLP (OpenTelemetry Protocol)

#### プロトコル仕様

```
OTLP は2つのエンコーディングをサポート:

1. gRPC (推奨)
   - Protocol Buffers
   - 高効率、低レイテンシ
   - ストリーミング対応

2. HTTP/JSON
   - RESTful API
   - ファイアウォールフレンドリー
   - デバッグが容易
```

#### OTLP リクエスト例

**gRPC エンドポイント:**
```
Service: opentelemetry.proto.collector.trace.v1.TraceService
Method: Export

Endpoint: grpc://localhost:4317
```

**HTTP エンドポイント:**
```http
POST /v1/traces HTTP/1.1
Host: localhost:4318
Content-Type: application/json

{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "my-service"}},
          {"key": "service.version", "value": {"stringValue": "1.0.0"}}
        ]
      },
      "scopeSpans": [
        {
          "scope": {
            "name": "my-instrumentation",
            "version": "1.0.0"
          },
          "spans": [
            {
              "traceId": "5B8EFFF798038103D269B633813FC60C",
              "spanId": "EEE19B7EC3C1B174",
              "name": "GET /api/users",
              "kind": "SPAN_KIND_SERVER",
              "startTimeUnixNano": 1544712660000000000,
              "endTimeUnixNano": 1544712661000000000,
              "attributes": [
                {"key": "http.method", "value": {"stringValue": "GET"}},
                {"key": "http.status_code", "value": {"intValue": 200}}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Context Propagation (コンテキスト伝播)

#### W3C Trace Context 標準

OpenTelemetry は W3C Trace Context を採用:

```http
Request Headers:
┌─────────────────────────────────────────────────────────────┐
│ traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
│              │  │                                │            │
│              │  └─ Trace ID (128bit)            │            │
│              │                                   │            │
│              └─ Version (00)                     │            │
│                                                  │            │
│                                    Span ID (64bit)            │
│                                                               │
│                                                 Trace Flags ──┘
│                                                 (01 = sampled)
│
│ tracestate: dd=s:1;o:rum;t.dm:-4;t.usr.id:12345
│             (ベンダー固有の情報)
└─────────────────────────────────────────────────────────────┘
```

#### マルチベンダー対応

```
traceparent (標準):
  - すべてのベンダーが理解できる基本情報

tracestate (拡張):
  - 各ベンダーが独自情報を追加
  - 複数のベンダーが共存可能

例:
tracestate: datadog=s:1,newrelic=123456,custom=abc
            └─────┬──────┘ └────┬────┘ └───┬───┘
               Datadog       New Relic    Custom
```

### Resource (リソース) の概念

リソースは、テレメトリを生成するエンティティの属性:

```yaml
リソース属性の例:

サービス情報:
  service.name: "backend-api"
  service.version: "1.2.3"
  service.namespace: "production"
  service.instance.id: "pod-123abc"

ホスト情報:
  host.name: "worker-node-1"
  host.type: "n1-standard-4"
  os.type: "linux"
  os.version: "5.10.0"

コンテナ情報:
  container.name: "backend"
  container.id: "abc123..."
  container.image.name: "myapp:1.2.3"

クラウド情報:
  cloud.provider: "gcp"
  cloud.region: "us-central1"
  cloud.availability_zone: "us-central1-a"

Kubernetes:
  k8s.cluster.name: "production-cluster"
  k8s.namespace.name: "default"
  k8s.pod.name: "backend-5d4c7b9f8-xk9zd"
  k8s.deployment.name: "backend"
```

---

## DataDogとOpenTelemetryの関係

### Datadogの OTel サポート戦略

Datadog は OpenTelemetry を**積極的にサポート**しており、以下の方針を取っています:

```
Datadog の方針:
┌─────────────────────────────────────────────────────────┐
│  "OpenTelemetry First, Datadog Native Also"            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. OTel データの完全サポート                            │
│     - OTLP Ingest の提供                                │
│     - セマンティック規約の尊重                          │
│                                                          │
│  2. Datadog ネイティブの継続サポート                    │
│     - ddtrace (独自SDK) の継続開発                      │
│     - Datadog Agent の最適化                            │
│                                                          │
│  3. ハイブリッドアプローチの推奨                         │
│     - 状況に応じた使い分け                              │
│     - 段階的な移行をサポート                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Datadog でのデータ取り込み方法

#### オプション1: OTel Collector → Datadog Exporter

```
Application (OTel SDK)
  ↓ OTLP
OpenTelemetry Collector
  ├─ Datadog Exporter
  ↓
Datadog Agent (optional)
  ↓
Datadog Platform
```

**設定例:**

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  datadog:
    api:
      key: ${DD_API_KEY}
      site: datadoghq.com

    # ホスト名のマッピング
    hostname: my-host

    # タグの追加
    tags:
      - env:production
      - team:backend

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
```

#### オプション2: Datadog Agent で OTLP 受信

```
Application (OTel SDK)
  ↓ OTLP
Datadog Agent (OTLP receiver 有効)
  ↓
Datadog Platform
```

**設定例:**

```yaml
# datadog.yaml
otlp_config:
  receiver:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # トレース設定
  traces:
    span_name_remappings:
      # OTel スパン名を Datadog 形式にマッピング
      http.request: http.server.request

    # サンプリング
    probabilistic_sampler:
      sampling_percentage: 100

  # メトリクス設定
  metrics:
    enabled: true
    # ヒストグラムのパーセンタイル
    histograms:
      mode: distributions
      send_aggregation_metrics: true
```

#### オプション3: ddtrace (Datadog ネイティブ)

```
Application (ddtrace)
  ↓ Datadog Protocol
Datadog Agent
  ↓
Datadog Platform
```

**Python での例:**

```python
from ddtrace import tracer, patch_all

# 自動インスツルメンテーション
patch_all()

# マニュアルトレース
with tracer.trace("custom.operation") as span:
    span.set_tag("user.id", "12345")
    do_something()
```

### OTel vs ddtrace 比較表

| 項目 | OpenTelemetry | Datadog ddtrace |
|------|---------------|-----------------|
| **標準化** | ✅ ベンダー中立 | ❌ Datadog 固有 |
| **移植性** | ✅ バックエンド変更容易 | ❌ Datadog 専用 |
| **機能の豊富さ** | ⚠️ 基本的な機能 | ✅ Datadog 独自機能フル活用 |
| **パフォーマンス** | ⚠️ 標準的 | ✅ Datadog に最適化 |
| **自動計装** | ✅ 多数のライブラリ | ✅ Datadog 最適化 |
| **学習コスト** | ⚠️ やや高い | ✅ Datadog ドキュメント充実 |
| **コミュニティ** | ✅ CNCF、大規模 | ⚠️ Datadog 中心 |
| **統合管理** | ✅ マルチベンダー対応 | ❌ Datadog のみ |

### Datadog 独自機能との関係

Datadog は OTel では提供されない独自機能を持っています:

```
Datadog 独自機能:

1. Continuous Profiler
   - CPU、メモリのコード レベル プロファイリング
   - OTel にはまだ相当機能なし

2. Dynamic Instrumentation
   - コード変更なしで動的にログ/トレース追加
   - Datadog 独自技術

3. Application Security Management (ASM)
   - ランタイムセキュリティ検知
   - OTel スコープ外

4. Database Monitoring (DBM)
   - クエリレベルの詳細分析
   - 正規化とサンプリング

5. RUM (Real User Monitoring)
   - ブラウザSDK
   - OTel Browser は開発中

これらを活用したい場合は、ddtrace の使用を推奨
```

---

## OTel vs Datadog Agent比較

### アーキテクチャの違い

```
┌────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  設計思想: 柔軟性とプラグアビリティ                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Receivers (入力プラグイン)                          │  │
│  │  - OTLP, Jaeger, Zipkin, Prometheus, etc.           │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Processors (処理プラグイン)                         │  │
│  │  - Batch, Sampling, Attributes, Filtering            │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Exporters (出力プラグイン)                          │  │
│  │  - OTLP, Datadog, Prometheus, Jaeger, etc.          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  利点:                                                      │
│  + 複数バックエンドに同時送信可能                          │
│  + カスタムプロセッサーの追加が容易                        │
│  + ベンダー中立                                            │
│                                                             │
│  欠点:                                                      │
│  - Datadog 固有機能の一部が使えない                        │
│  - 設定が複雑になりがち                                    │
│                                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                Datadog Agent                               │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  設計思想: Datadog への最適化と統合                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  APM (Trace Agent)                                   │  │
│  │  - ddtrace からのトレース受信                         │  │
│  │  - OTLP サポート (v7.35+)                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DogStatsD                                           │  │
│  │  - メトリクス収集 (UDP/UDS)                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Log Agent                                           │  │
│  │  - ファイル、コンテナログ収集                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Checks & Integrations                               │  │
│  │  - 600+ インテグレーション                            │  │
│  │  - PostgreSQL, Redis, Nginx, etc.                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Process Agent                                       │  │
│  │  - プロセス監視                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Security Agent                                      │  │
│  │  - Runtime Security, CWS                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  利点:                                                      │
│  + Datadog の全機能を活用可能                              │
│  + 最適化されたパフォーマンス                              │
│  + 統合された管理                                          │
│  + 600+ インテグレーション                                 │
│                                                             │
│  欠点:                                                      │
│  - Datadog 専用                                            │
│  - 他のバックエンドへの送信は不可                          │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 併用パターン

```
パターン1: OTel Collector + Datadog Agent

Application (OTel SDK)
  ↓ OTLP (traces, metrics)
OTel Collector
  ├─ Datadog Exporter → Datadog Agent
  └─ Prometheus Exporter → Prometheus

Datadog Agent
  ├─ Integrations (PostgreSQL, Redis, etc.)
  ├─ Logs collection
  ├─ Process monitoring
  └─ Security monitoring
  ↓
Datadog Platform

利点: OTel の柔軟性 + Datadog の統合機能


パターン2: Datadog Agent のみ (OTLP サポート)

Application (OTel SDK)
  ↓ OTLP
Datadog Agent (OTLP receiver 有効)
  ├─ すべての Datadog 機能
  ↓
Datadog Platform

利点: シンプルな構成、Datadog 機能フル活用


パターン3: 完全 OTel

Application (OTel SDK)
  ↓ OTLP
OTel Collector
  ├─ Datadog Exporter → Datadog
  ├─ Prometheus Exporter → Prometheus
  └─ Jaeger Exporter → Jaeger

利点: 完全なベンダー中立性
欠点: Datadog 固有機能は使えない
```

---

## DatadogでのOTel活用方法

### 実装例1: Python アプリケーション

#### OTel SDK を使用した計装

```python
# requirements.txt
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation-flask
opentelemetry-instrumentation-requests
opentelemetry-exporter-otlp

# app.py
from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# リソースの設定
resource = Resource.create({
    "service.name": "python-backend",
    "service.version": "1.0.0",
    "deployment.environment": "production",
})

# TracerProvider の初期化
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# OTLP Exporter の設定 (Datadog Agent へ送信)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://datadog-agent:4317",  # Datadog Agent の OTLP endpoint
    insecure=True
)

# BatchSpanProcessor の追加
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# 自動計装
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# マニュアル計装
tracer = trace.get_tracer(__name__)

@app.route('/api/users')
def get_users():
    with tracer.start_as_current_span("get_users") as span:
        span.set_attribute("custom.attribute", "value")

        # データベース処理など
        users = fetch_users_from_db()

        span.set_attribute("user.count", len(users))
        return {"users": users}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 実装例2: Node.js アプリケーション

```javascript
// package.json dependencies
{
  "@opentelemetry/api": "^1.7.0",
  "@opentelemetry/sdk-node": "^0.45.0",
  "@opentelemetry/auto-instrumentations-node": "^0.40.0",
  "@opentelemetry/exporter-trace-otlp-grpc": "^0.45.0",
  "@opentelemetry/resources": "^1.18.0",
  "@opentelemetry/semantic-conventions": "^1.18.0"
}

// tracing.js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

// リソースの定義
const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: 'nodejs-backend',
  [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
  [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'production',
});

// OTLP Exporter の設定
const traceExporter = new OTLPTraceExporter({
  url: 'grpc://datadog-agent:4317',
});

// SDK の初期化
const sdk = new NodeSDK({
  resource: resource,
  traceExporter: traceExporter,
  instrumentations: [
    getNodeAutoInstrumentations({
      // 細かい設定
      '@opentelemetry/instrumentation-http': {
        requestHook: (span, request) => {
          span.setAttribute('custom.header', request.headers['x-custom']);
        },
      },
    }),
  ],
});

// SDK の開始
sdk.start();

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('Tracing terminated'))
    .catch((error) => console.log('Error terminating tracing', error))
    .finally(() => process.exit(0));
});

// app.js
require('./tracing'); // 最初にインポート

const express = require('express');
const { trace } = require('@opentelemetry/api');

const app = express();
const tracer = trace.getTracer('express-app');

app.get('/api/users', async (req, res) => {
  const span = tracer.startSpan('fetch_users');

  try {
    // ビジネスロジック
    const users = await fetchUsers();

    span.setAttribute('user.count', users.length);
    span.setStatus({ code: 0 }); // OK

    res.json({ users });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: 2, message: error.message }); // ERROR
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### Datadog Agent 設定

```yaml
# docker-compose.yml
services:
  datadog-agent:
    image: gcr.io/datadoghq/agent:7
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_SITE=datadoghq.com

      # OTLP サポートを有効化
      - DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_GRPC_ENDPOINT=0.0.0.0:4317
      - DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_HTTP_ENDPOINT=0.0.0.0:4318

      # APM 設定
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true

    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "8126:8126"  # Datadog APM
```

---

## 移行戦略とベストプラクティス

### 段階的移行アプローチ

```
Phase 1: 調査と計画 (1-2週間)
├─ 現在のインスツルメンテーションを監査
├─ OTel 互換性を確認
├─ PoC (Proof of Concept) の実施
└─ 移行計画の策定

Phase 2: パイロットサービス (2-4週間)
├─ 低リスクのサービスを選択
├─ OTel SDK への移行
├─ Datadog Agent の OTLP サポート有効化
├─ 並行稼働でデータ比較
└─ パフォーマンステスト

Phase 3: 段階的ロールアウト (2-3ヶ月)
├─ サービスごとに順次移行
├─ カナリアデプロイメント
├─ モニタリングとアラート調整
└─ ドキュメント更新

Phase 4: 最適化 (継続的)
├─ サンプリング戦略の調整
├─ カスタム属性の追加
├─ パフォーマンスチューニング
└─ チームトレーニング
```

### ベストプラクティス

#### 1. セマンティック規約の遵守

```python
# ❌ 悪い例: カスタム属性名
span.set_attribute("method", "GET")
span.set_attribute("url", "/api/users")
span.set_attribute("status", 200)

# ✅ 良い例: OTel セマンティック規約
from opentelemetry.semconv.trace import SpanAttributes

span.set_attribute(SpanAttributes.HTTP_METHOD, "GET")
span.set_attribute(SpanAttributes.HTTP_URL, "/api/users")
span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
```

#### 2. リソース属性の適切な設定

```python
# 重要なリソース属性
resource = Resource.create({
    # 必須
    "service.name": "my-service",
    "service.version": "1.2.3",

    # 推奨
    "deployment.environment": "production",
    "service.namespace": "ecommerce",
    "service.instance.id": os.getenv("HOSTNAME"),

    # クラウド環境
    "cloud.provider": "gcp",
    "cloud.region": "us-central1",

    # Kubernetes
    "k8s.namespace.name": "default",
    "k8s.pod.name": os.getenv("POD_NAME"),
    "k8s.deployment.name": "backend",
})
```

#### 3. サンプリング戦略

```python
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    TraceIdRatioBased,
)

# 本番環境: 10% サンプリング
sampler = ParentBased(
    root=TraceIdRatioBased(0.1)  # 10%
)

provider = TracerProvider(
    resource=resource,
    sampler=sampler
)
```

#### 4. エラーハンドリング

```python
from opentelemetry.trace import Status, StatusCode

@tracer.start_as_current_span("risky_operation")
def risky_operation():
    span = trace.get_current_span()

    try:
        result = dangerous_call()
        span.set_status(Status(StatusCode.OK))
        return result
    except ValueError as e:
        # 例外を記録
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
```

### Datadog UI での OTel データ確認

OTel から送信されたデータは、Datadog UI で通常のトレースと同様に表示されます:

```
Datadog APM UI:
┌──────────────────────────────────────────────────────────┐
│ Service: python-backend (OTel)                           │
├──────────────────────────────────────────────────────────┤
│ Trace: 4bf92f3577b34da6a3ce929d0e0e4736                  │
│                                                           │
│ ┌─ GET /api/users                    245ms              │
│ │  Resource: python-backend                             │
│ │  Tags:                                                │
│ │    - service.name: python-backend                     │
│ │    - http.method: GET                                 │
│ │    - http.status_code: 200                            │
│ │    - otel.library.name: opentelemetry                 │
│ │                                                        │
│ │  ├─ SELECT * FROM users             45ms              │
│ │  │  Resource: postgresql                              │
│ │  │  Tags:                                             │
│ │  │    - db.system: postgresql                         │
│ │  │    - db.statement: SELECT * FROM users             │
│ │                                                        │
│ │  └─ GET user:123                    2ms               │
│ │     Resource: redis                                   │
│ │     Tags:                                             │
│ │       - db.system: redis                              │
│ │       - db.operation: GET                             │
└──────────────────────────────────────────────────────────┘

注: OTel タグは Datadog のタグシステムに自動マッピングされます
```

---

## まとめ

### OpenTelemetry を選ぶべき場合

✅ **以下の場合は OTel を推奨:**

- マルチクラウド/ハイブリッドクラウド環境
- 複数の監視バックエンドを使用
- ベンダーロックインを避けたい
- 将来的なバックエンド変更の可能性
- Kubernetes ネイティブな環境
- CNCF エコシステムに準拠したい

### Datadog ネイティブを選ぶべき場合

✅ **以下の場合は ddtrace を推奨:**

- Datadog のみを使用
- Datadog 独自機能をフル活用したい
  - Continuous Profiler
  - Dynamic Instrumentation
  - Application Security Management
  - Database Monitoring
- 最高のパフォーマンスが必要
- 素早く始めたい

### ハイブリッドアプローチ

多くの組織では、**両方を併用**することで最大の価値を得ています:

```
推奨構成:
├─ マイクロサービス (新規): OpenTelemetry
│  └─ 将来の柔軟性を確保
├─ レガシーアプリ: Datadog ddtrace
│  └─ 既存の計装を維持
└─ インフラ・統合: Datadog Agent
   └─ 600+ インテグレーションを活用
```

OpenTelemetry は、可観測性の**未来の標準**として位置づけられており、Datadog も積極的にサポートしています。適切なツールを選択し、段階的に移行することで、両方の利点を享受できます。
