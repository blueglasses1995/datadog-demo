# レッスン4: ログ管理とトレース相関

## 📋 レッスン概要

**所要時間:** 90分 | **難易度:** 中級 | **前提:** レッスン1-3完了

## 🎯 学習目標

- [ ] ログ収集の仕組みを理解できる
- [ ] 効率的なログ検索ができる
- [ ] ログとトレースを相関分析できる
- [ ] ログベースメトリクスを作成できる
- [ ] ログパイプラインを設定できる

## 📚 主要トピック

### 1. ログエクスプローラーの基本

#### Log Explorer の使い方
```
Logs → Explorer
```

**検索構文:**
```
service:backend-api                    # サービスでフィルタ
status:error                           # ステータスでフィルタ
@http.status_code:500                  # タグでフィルタ
service:backend-api AND status:error   # AND条件
service:backend-api OR service:nginx   # OR条件
-status:info                           # NOT条件（infoを除外）
```

#### ファセット（Facets）
- 左サイドバーの属性でフィルタリング
- `service`, `status`, `host`, `source` など

---

### 2. ログとトレースの相関

#### トレースIDの自動付与

Python/Flaskの場合：
```python
import logging
from ddtrace import tracer

# ログにトレース情報を自動付与
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
```

`.env`設定：
```env
DD_LOGS_INJECTION=true
```

#### 相関分析の実践

1. **ログからトレースへ**
   - Logs Explorer でログエントリをクリック
   - "View in APM" をクリック
   - 関連するトレースを表示

2. **トレースからログへ**
   - APM のトレースを開く
   - "Logs" タブをクリック
   - 同じ `trace_id` を持つログを表示

#### 実習: エラーの完全な調査
1. エラーエンドポイントを呼び出し
2. Logs Explorer でエラーログを検索
3. ログからトレースに移動
4. トレースの詳細を確認
5. スタックトレースで根本原因を特定

---

### 3. ログパターン分析

```
Logs → Patterns
```

**Datadogが自動検出:**
- 頻出するログパターン
- 異常なパターン
- パターンごとのログ数

**活用例:**
- 新しいエラーパターンの早期発見
- ログの傾向分析
- ノイズの多いログの特定

---

### 4. ログベースメトリクス

#### メトリクスの作成

```
Logs → Configuration → Generate Metrics
```

**例1: エラーログのカウント**
- Query: `service:backend-api status:error`
- Metric name: `custom.logs.error.count`
- Measure: Count
- Group by: `service`, `@http.status_code`

**例2: レスポンスタイムの監視**
- Query: `service:nginx`
- Metric name: `custom.nginx.response_time`
- Measure: `@duration`
- Group by: `@http.url_details.path`

#### 実習: カスタムメトリクスの作成
1. エラーログベースのメトリクス作成
2. Metrics Explorer で可視化
3. ダッシュボードに追加

---

### 5. ログパイプライン

```
Logs → Configuration → Pipelines
```

#### パイプラインとは
ログを処理・変換するルール：
1. **Grok Parser**: ログをパース
2. **Remapper**: 属性を標準化
3. **Category Processor**: カテゴリ分類
4. **Arithmetic Processor**: 計算
5. **Geo IP Parser**: IPから位置情報を抽出

#### 実習: Nginxログのパース
Nginxログ（JSON形式）を標準属性にマッピング：

```
{
  "status": "200",
  "request_time": "0.123"
}
↓
標準属性:
- http.status_code: 200
- duration: 123000000 (ナノ秒)
```

---

### 6. ログアーカイブと保持

#### アーカイブ設定
```
Logs → Configuration → Archives
```

**長期保存:**
- S3、GCS、Azure Blob にアーカイブ
- コスト削減
- コンプライアンス対応

#### インデックス設定
```
Logs → Configuration → Indexes
```

**保持期間:**
- 3日、7日、15日、30日、90日など
- 重要度に応じて設定

---

### 7. ライブテール（Live Tail）

```
Logs → Live Tail
```

**リアルタイムログストリーミング:**
- ログが即座に表示される
- デバッグに最適
- フィルタ適用可能

**使用例:**
```bash
# Backendアプリの操作
curl http://localhost/api/users

# Live Tail で即座にログ確認
# service:backend-api でフィルタ
```

---

### 8. 実習課題

#### 課題1: エラー調査（30分）
1. 過去1時間のエラーログを検索
2. エラーの種類ごとに分類
3. 各エラーのトレースを確認
4. 根本原因を特定
5. 修正提案をまとめる

#### 課題2: ログベースアラート（20分）
1. エラー率が高い場合のアラートを作成
2. 条件: 5分間で10件以上のエラー
3. 通知先を設定
4. テストしてアラートが機能することを確認

#### 課題3: ログ分析レポート（30分）
1. 最も頻繁に発生するログパターンを特定
2. エンドポイント別のアクセス数を集計
3. エラー率の時系列推移をグラフ化
4. 改善が必要な領域を特定

---

## 📚 参考資料

- [Log Management](https://docs.datadoghq.com/ja/logs/)
- [Log Pipelines](https://docs.datadoghq.com/ja/logs/log_configuration/pipelines/)
- [Log-based Metrics](https://docs.datadoghq.com/ja/logs/logs_to_metrics/)
- [Trace-Log Correlation](https://docs.datadoghq.com/ja/tracing/other_telemetry/connect_logs_and_traces/)
