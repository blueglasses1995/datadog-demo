# レッスン7: アラートとモニタリング運用

## 📋 レッスン概要

**所要時間:** 90分 | **難易度:** 上級 | **前提:** レッスン1-6完了

## 🎯 学習目標

- [ ] モニターの種類を理解し使い分けられる
- [ ] 効果的なアラートを設計できる
- [ ] アノマリー検出を活用できる
- [ ] アラート疲れを防げる
- [ ] オンコール運用のベストプラクティスを実践できる

## 📚 主要トピック

### 1. モニターの種類

```
Monitors → New Monitor
```

#### Metric Monitor
メトリクスベースのアラート：
```
avg(last_5m):avg:docker.cpu.usage{container_name:backend} > 80
```

#### APM Monitor
APMメトリクスのアラート：
- エラー率が閾値を超えた
- レイテンシが悪化した
- リクエスト数が急増/急減した

#### Log Monitor
ログベースのアラート：
```
logs("service:backend-api status:error").index("*").rollup("count").last("5m") > 10
```

#### Composite Monitor
複数のモニターを組み合わせ：
```
Monitor A AND Monitor B
Monitor C OR Monitor D
```

#### Anomaly Monitor
機械学習で異常検出：
- 通常のパターンから逸脱を検出
- 季節性を考慮

#### Forecast Monitor
将来の予測値でアラート：
- ディスク使用量が3日後に満杯
- メモリリークの早期検出

---

### 2. 効果的なアラート設計

#### ゴールデンルール

**1. アクション可能であること**
❌ 悪い例: "CPU使用率が高い"
✅ 良い例: "Backend APIのCPU使用率が80%を5分間継続"

**2. ユーザー影響があること**
- 内部メトリクスよりユーザー体験を優先
- SLO違反を最優先

**3. 緊急性が明確であること**
- **Critical**: 即座の対応が必要
- **Warning**: 監視が必要だが緊急ではない
- **Info**: 情報提供のみ

#### 閾値の設定

**静的閾値:**
```
CPU使用率 > 80%（Warning）
CPU使用率 > 90%（Critical）
```

**動的閾値（Anomaly）:**
- 過去の傾向から自動学習
- 時間帯や曜日の変動を考慮

---

### 3. 実習: モニター作成

#### モニター1: 高エラー率アラート

```
Monitors → New Monitor → APM
```

**設定:**
- Service: `backend-api`
- Metric: Error Rate
- Alert threshold: > 5%
- Warning threshold: > 2%
- Evaluation window: 5 minutes

**通知メッセージ:**
```
⚠️ Backend APIのエラー率が上昇しています

エラー率: {{value}}%
サービス: {{service.name}}
環境: {{env}}

影響範囲を確認してください:
https://app.datadoghq.com/apm/services/backend-api

@slack-alerts @oncall
```

#### モニター2: レイテンシアラート

**設定:**
- Metric: `trace.flask.request.duration`
- Aggregation: p95
- Alert threshold: > 1000ms
- Warning threshold: > 500ms

#### モニター3: ログエラー急増

**設定:**
- Query: `service:backend-api status:error`
- Alert threshold: > 20 errors in 5 minutes
- Warning threshold: > 10 errors in 5 minutes

---

### 4. アノマリー検出

```
Monitors → New Monitor → Anomaly
```

#### アルゴリズム

**Basic**
- シンプルな統計的手法
- 高速だが精度は中程度

**Agile**
- 最近のデータを重視
- トレンドの変化に敏感

**Robust**
- 外れ値の影響を受けにくい
- 安定したメトリクスに最適

**Adaptive**
- 長期的なトレンドと短期的な変動の両方を考慮
- 季節性のあるデータに最適

#### 実習: アノマリー検出

**注文数の異常検知:**

1. Metric: `orders.count`
2. Algorithm: Agile
3. Sensitivity: Medium
4. Evaluation window: 15 minutes

**シナリオ:**
- 通常: 1時間に50-100件
- 異常: 急に200件（キャンペーン？）
- 異常: 急に10件（障害？）

---

### 5. 通知チャネル

#### Integrations

**Slack:**
```
@slack-alerts
@slack-team-backend
```

**PagerDuty:**
```
@pagerduty-critical
```

**Email:**
```
@john@example.com
```

#### 通知ポリシー

**時間帯による通知先変更:**
- 営業時間: Slack
- 夜間・休日: PagerDuty（オンコール）

**エスカレーション:**
1. 5分経過 → チームSlack
2. 15分経過 → オンコールエンジニア
3. 30分経過 → マネージャー

---

### 6. アラート疲れの防止

#### よくある問題と対策

**問題1: ノイズが多すぎる**

対策:
- 閾値を見直す
- 評価期間を延ばす
- 夜間は重要度Highのみ通知

**問題2: 誤検知が多い**

対策:
- アノマリー検出を使う
- 除外条件を追加
- メンテナンス時間を設定

**問題3: 同じアラートが繰り返し**

対策:
- 根本原因を修正
- 自動修復スクリプト
- Re-notification intervalを調整

#### Downtime設定

```
Monitors → Manage Downtime
```

**定期メンテナンス:**
- 毎週日曜日 2:00-4:00
- デプロイ中（30分）

---

### 7. オンコール運用

#### Runbook の作成

各モニターにRunbookリンクを追加：

```markdown
## 高エラー率アラート Runbook

### 1. 初動確認
- [ ] APMでエラーの種類を確認
- [ ] ログで詳細を確認
- [ ] 最近のデプロイを確認

### 2. 影響範囲の特定
- [ ] 全エンドポイントか特定エンドポイントか
- [ ] 影響ユーザー数
- [ ] ビジネスインパクト

### 3. 対応
- [ ] 既知の問題か確認
- [ ] ロールバックが必要か判断
- [ ] 関係者に連絡

### 4. 復旧後
- [ ] 根本原因分析
- [ ] 再発防止策
- [ ] ポストモーテム作成
```

#### 実習: Runbook作成
1. 各主要アラートのRunbookを作成
2. トラブルシューティング手順を文書化
3. 連絡先リストを含める

---

### 8. 実習課題

#### 課題1: アラート設計（40分）

以下のアラートを作成：

1. **サービス停止アラート**
   - コンテナが停止した
   - 即座に通知

2. **パフォーマンス劣化アラート**
   - P95レイテンシが通常の2倍
   - 10分継続で警告

3. **リソース枯渇予測アラート**
   - ディスク使用量が2日後に100%
   - 早期警告

#### 課題2: アラートテスト（30分）
1. 各アラートをテスト
2. 通知が正しく届くことを確認
3. 誤検知がないか確認
4. 閾値を調整

#### 課題3: インシデント対応訓練（20分）
1. 意図的にエラーを発生させる
2. アラート受信
3. Runbookに従って対応
4. 復旧時間を計測
5. 改善点を洗い出し

---

## 📚 参考資料

- [Monitors Documentation](https://docs.datadoghq.com/ja/monitors/)
- [Alerting Best Practices](https://docs.datadoghq.com/ja/monitors/guide/)
- [Anomaly Detection](https://docs.datadoghq.com/ja/monitors/types/anomaly/)
- [On-Call Best Practices](https://www.datadoghq.com/blog/alerting-101/)
