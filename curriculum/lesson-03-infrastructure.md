# レッスン3: インフラストラクチャ監視

## 📋 レッスン概要

**所要時間:** 90分 | **難易度:** 初級 | **前提:** レッスン1-2完了

## 🎯 学習目標

- [ ] コンテナ監視の基礎を理解できる
- [ ] データベース監視（PostgreSQL）を実践できる
- [ ] キャッシュ監視（Redis）を実践できる
- [ ] Webサーバー監視（Nginx）を実践できる
- [ ] インテグレーションを設定・活用できる

## 📚 主要トピック

### 1. コンテナ監視

#### Container List の確認
```
Infrastructure → Containers
```

**監視項目:**
- CPU使用率
- メモリ使用量
- ネットワークI/O
- ディスクI/O
- コンテナステータス

#### 実習
1. 最もCPUを使用しているコンテナを特定
2. メモリ使用量が増加傾向のコンテナを確認
3. Live Containers ビューでリアルタイム監視

---

### 2. PostgreSQL 監視

#### ダッシュボード
```
Integrations → Postgres → Dashboard
```

**主要メトリクス:**

| メトリクス | 説明 |
|----------|------|
| `postgresql.connections` | 接続数 |
| `postgresql.database.size` | DB サイズ |
| `postgresql.bgwriter.checkpoints_timed` | チェックポイント |
| `postgresql.queries_per_second` | クエリ数/秒 |

#### 実習: DBパフォーマンス分析
1. 接続数の推移を確認
2. 遅いクエリをAPMと相関して分析
3. データベースサイズの増加傾向を確認

---

### 3. Redis 監視

#### ダッシュボード
```
Integrations → Redis → Dashboard
```

**主要メトリクス:**
- `redis.mem.used`: メモリ使用量
- `redis.net.commands`: コマンド実行数
- `redis.stats.keyspace_hits`: キャッシュヒット数
- `redis.stats.keyspace_misses`: キャッシュミス数

#### キャッシュヒット率の計算
```
ヒット率 = hits / (hits + misses) × 100
```

**目標:** 80%以上

#### 実習: キャッシュ効率分析
1. キャッシュヒット率を計算
2. ユーザー詳細APIでキャッシュ動作を確認
3. キャッシュクリア前後の比較

---

### 4. Nginx 監視

#### ダッシュボード
```
Integrations → Nginx → Dashboard
```

**主要メトリクス:**
- `nginx.net.connections`: 接続数
- `nginx.net.request_per_s`: リクエスト数
- アクセスログ（JSON形式）
- エラーログ

#### 実習: Webサーバー分析
1. リクエスト数の推移
2. レスポンスタイム分布
3. 4xx/5xxエラーの分析
4. アクセスログからトップパスを確認

---

### 5. Host Map の活用

```
Infrastructure → Host Map
```

**視覚化:**
- ホスト/コンテナを六角形で表示
- 色: 選択したメトリクスの値
- サイズ: リソース量

**使用例:**
- CPU使用率が高いホストを一目で確認
- メモリ使用量の比較
- アラート発生中のホストの特定

---

### 6. インテグレーション設定

#### Autodiscovery
Docker Composeのlabelsで自動設定：

```yaml
labels:
  com.datadoghq.ad.check_names: '["postgres"]'
  com.datadoghq.ad.init_configs: '[{}]'
  com.datadoghq.ad.instances: '[{"host":"%%host%%","port":5432}]'
```

#### 手動設定
`datadog/conf.d/postgres.d/conf.yaml`

```yaml
init_config:
instances:
  - host: postgres
    port: 5432
    username: demo_user
    password: demo_password
```

---

### 7. 実習課題

#### 課題1: リソース最適化提案（30分）
1. 各コンテナのCPU/メモリ使用率を分析
2. オーバープロビジョニングされているコンテナを特定
3. リソース配分の最適化案を作成

#### 課題2: キャッシュ戦略の評価（20分）
1. Redisキャッシュヒット率を計算
2. キャッシュされるべきだがされていないデータを特定
3. キャッシュ戦略の改善案を提案

#### 課題3: データベース健全性チェック（20分）
1. PostgreSQL接続数の推移を確認
2. データベースサイズの増加率を計算
3. 遅いクエリをAPMで特定
4. インデックス最適化の提案

---

## 📚 参考資料

- [Infrastructure Monitoring](https://docs.datadoghq.com/ja/infrastructure/)
- [Integrations](https://docs.datadoghq.com/ja/integrations/)
- [PostgreSQL Integration](https://docs.datadoghq.com/ja/integrations/postgres/)
- [Redis Integration](https://docs.datadoghq.com/ja/integrations/redisdb/)
- [Nginx Integration](https://docs.datadoghq.com/ja/integrations/nginx/)
