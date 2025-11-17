# レッスン6: カスタムメトリクスとダッシュボード

## 📋 レッスン概要

**所要時間:** 90分 | **難易度:** 中級 | **前提:** レッスン1-5完了

## 🎯 学習目標

- [ ] カスタムメトリクスの種類を理解できる
- [ ] メトリクスを送信できる
- [ ] 効果的なダッシュボードを設計できる
- [ ] ビジネスメトリクスを監視できる
- [ ] SLI/SLOを設定できる

## 📚 主要トピック

### 1. メトリクスの種類

#### Count（カウンター）
イベントの発生回数：
```python
from datadog import statsd

statsd.increment('page.views', tags=['page:home'])
```

**使用例:**
- ページビュー数
- API呼び出し回数
- エラー発生回数

#### Gauge（ゲージ）
ある時点の値：
```python
statsd.gauge('users.active', 1234, tags=['env:prod'])
```

**使用例:**
- アクティブユーザー数
- CPU使用率
- キュー長

#### Histogram（ヒストグラム）
値の分布を測定：
```python
statsd.histogram('request.duration', 0.234, tags=['endpoint:api'])
```

**使用例:**
- レスポンスタイム
- ファイルサイズ
- データベースクエリ時間

#### Rate
単位時間あたりの変化：
```python
statsd.increment('requests.count')
# Datadogが自動的にrate計算
```

---

### 2. カスタムメトリクスの送信

#### バックエンド（Python）
```python
from datadog import statsd

# ビジネスメトリクス
statsd.gauge('business.revenue', 12345.67, tags=['currency:usd'])
statsd.increment('business.orders', tags=['status:completed'])
statsd.histogram('business.order_value', order_amount)
```

#### フロントエンド（JavaScript）
```javascript
import { datadogRum } from '@datadog/browser-rum';

datadogRum.addAction('custom_metric', {
  metric_name: 'button_click',
  metric_value: 1
});
```

#### 実習: カスタムメトリクスの送信
1. Webアプリで「カスタムメトリクス」ボタンをクリック
2. Metrics → Explorer で確認
3. メトリクス名: `custom.frontend.button_click`
4. グラフ化して推移を確認

---

### 3. ダッシュボードの基本

```
Dashboards → New Dashboard
```

#### ウィジェットの種類

| ウィジェット | 用途 |
|-------------|------|
| **Timeseries** | 時系列データ |
| **Query Value** | 単一の値 |
| **Table** | 表形式 |
| **Heatmap** | 分布の可視化 |
| **Top List** | トップN |
| **Change** | 前期比較 |

#### 実習: 最初のダッシュボード
1. "System Overview" ダッシュボード作成
2. 以下のウィジェット追加：
   - CPU使用率（Timeseries）
   - アクティブコンテナ数（Query Value）
   - サービスごとのリクエスト数（Top List）

---

### 4. 効果的なダッシュボード設計

#### ベストプラクティス

**1. 目的別にダッシュボードを分ける**
- エグゼクティブダッシュボード（経営層向け）
- オペレーションダッシュボード（運用チーム向け）
- トラブルシューティングダッシュボード

**2. ゴールデンシグナル**
- **Latency**: レスポンスタイム
- **Traffic**: リクエスト数
- **Errors**: エラー率
- **Saturation**: リソース使用率

**3. レイアウト**
- 最重要メトリクスを上部に
- 関連するメトリクスをグループ化
- 一画面に収める（スクロール不要）

#### 実習: APMダッシュボード作成

**"Backend Performance Dashboard"**

1. **Row 1: 概要**
   - リクエスト数（Query Value）
   - 平均レイテンシ（Query Value）
   - エラー率（Query Value）

2. **Row 2: トラフィック**
   - エンドポイント別リクエスト数（Timeseries）
   - リクエスト数トップ5（Top List）

3. **Row 3: パフォーマンス**
   - レイテンシ P50/P95/P99（Timeseries）
   - エンドポイント別レイテンシ（Heatmap）

4. **Row 4: エラー**
   - エラー数（Timeseries）
   - エラーの種類（Table）

---

### 5. ビジネスメトリクス

#### デモアプリの既存ビジネスメトリクス

```python
# backend/app.py に実装済み
statsd.gauge('users.count', user_count)
statsd.gauge('orders.count', order_count)
statsd.gauge('orders.total_amount', total_amount)
statsd.increment('cache.hit', tags=['resource:user'])
statsd.increment('cache.miss', tags=['resource:user'])
```

#### 実習: ビジネスダッシュボード

**"Business Metrics Dashboard"**

1. **KPI Row**
   - 総ユーザー数
   - 総注文数
   - 総売上

2. **トレンド Row**
   - 注文数の推移（Timeseries）
   - 売上の推移（Timeseries）

3. **効率 Row**
   - キャッシュヒット率（Query Value + Timeseries）

---

### 6. SLI/SLO設定

```
Service Management → SLOs → New SLO
```

#### SLI (Service Level Indicator)
サービスレベルを測定する指標：
- 可用性（Availability）
- レイテンシ（Latency）
- エラー率（Error Rate）

#### SLO (Service Level Objective)
目標とする水準：
- 可用性 99.9%
- P95レイテンシ < 200ms
- エラー率 < 0.1%

#### 実習: SLO作成

**例: APIの可用性SLO**

1. **Metric-based SLO**
   - Good events: `sum:trace.flask.request.hits{!status:error}`
   - Total events: `sum:trace.flask.request.hits{*}`
   - Target: 99.5%
   - Time window: 30 days

2. **Monitor-based SLO**
   - 既存のモニターを使用
   - Target: 99.9%

3. **エラーバジェット**
   - 許容されるエラー時間を自動計算
   - バジェット消費率を監視

---

### 7. テンプレート変数

```
Dashboard Settings → Template Variables
```

**動的フィルタリング:**
```
$env = dev, staging, prod
$service = backend-api, frontend
$host = *
```

**使用例:**
```
sum:trace.flask.request.hits{env:$env, service:$service}
```

ドロップダウンで環境やサービスを切り替え可能

---

### 8. 実習課題

#### 課題1: 総合ダッシュボード作成（45分）

**"Production Monitoring Dashboard"** を作成：

1. **システムヘルス**
   - 全サービスのステータス
   - コンテナの健全性
   - エラー率

2. **パフォーマンス**
   - APMメトリクス
   - データベースパフォーマンス
   - キャッシュ効率

3. **ビジネス**
   - KPI
   - トランザクション数
   - ユーザー活動

#### 課題2: アラート付きダッシュボード（30分）
1. 重要メトリクスにアラート設定
2. ダッシュボードにアラート状態を表示
3. エラーバジェットの可視化

---

## 📚 参考資料

- [Metrics Documentation](https://docs.datadoghq.com/ja/metrics/)
- [Dashboards](https://docs.datadoghq.com/ja/dashboards/)
- [SLOs](https://docs.datadoghq.com/ja/service_management/service_level_objectives/)
- [Custom Metrics](https://docs.datadoghq.com/ja/metrics/custom_metrics/)
