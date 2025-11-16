# Datadog ハンズオン環境

マイクロサービスアーキテクチャとインフラ監視を学ぶためのDatadog実践デモ環境です。

## 🎯 この環境で学べること

### APM (Application Performance Monitoring)
- アプリケーションのパフォーマンス監視
- 分散トレーシング
- サービス間のリクエストフロー可視化

### インフラ監視
- Nginxのメトリクスとログ
- PostgreSQLのパフォーマンス監視
- Redisのメトリクス監視
- コンテナメトリクス

### ログ管理
- 統合ログ収集
- ログとトレースの相関
- ログ検索・分析

### RUM (Real User Monitoring)
- フロントエンドのユーザー体験監視
- ページパフォーマンス
- エラートラッキング

### カスタムメトリクス
- ビジネスメトリクスの送信
- カスタムダッシュボード作成

## 🏗️ アーキテクチャ

```
Internet
   ↓
[Nginx] ← Datadog Agent (ログ・メトリクス)
   ↓
   ├→ [Frontend (React)] ← RUM
   └→ [Backend API (Flask)] ← APM
         ↓
         ├→ [PostgreSQL] ← DB監視
         └→ [Redis] ← キャッシュ監視
```

## 📋 前提条件

- Docker & Docker Compose
- Datadog アカウント（無料トライアルOK）
- Datadog API キー

## 🚀 クイックスタート

### 1. Datadog API キーの設定

```bash
# .env ファイルを作成
cp .env.example .env

# .env を編集してAPI キーを設定
# DD_API_KEY=your_datadog_api_key_here
```

### 2. 環境の起動

```bash
# すべてのサービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

### 3. アプリケーションにアクセス

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Nginx: http://localhost:80

### 4. Datadogダッシュボードで確認

- APM: https://app.datadoghq.com/apm/services
- Infrastructure: https://app.datadoghq.com/infrastructure
- Logs: https://app.datadoghq.com/logs
- RUM: https://app.datadoghq.com/rum

## 🧪 トラフィック生成

デモ用のトラフィックを生成してDatadogでデータを確認できます：

```bash
# サンプルトラフィックを生成
python scripts/generate_traffic.py
```

## 📚 ハンズオン手順

詳細なハンズオン手順は [docs/HANDSON.md](docs/HANDSON.md) を参照してください。

## 🛠️ サービス構成

| サービス | ポート | 説明 |
|---------|--------|------|
| Nginx | 80 | リバースプロキシ |
| Frontend | 3000 | React アプリケーション |
| Backend | 5000 | Flask API |
| PostgreSQL | 5432 | データベース |
| Redis | 6379 | キャッシュ |
| Datadog Agent | 8126 (APM) | 監視エージェント |

## 🔍 監視ポイント

### アプリケーション
- `/api/users` - ユーザー一覧取得（DB接続）
- `/api/users/<id>` - ユーザー詳細（キャッシュ利用）
- `/api/orders` - 注文一覧（複数サービス連携）
- `/api/slow` - 意図的に遅いエンドポイント
- `/api/error` - エラー生成エンドポイント

### インフラ
- Nginx アクセスログ・エラーログ
- PostgreSQL 接続数・クエリパフォーマンス
- Redis メモリ使用量・ヒット率
- コンテナ CPU・メモリ使用量

## 🎓 学習トピック

1. **基礎**: APMの設定とトレース確認
2. **応用**: 分散トレーシングとサービスマップ
3. **発展**: カスタムメトリクスとダッシュボード作成
4. **インフラ**: Nginxログ分析とメトリクス監視
5. **統合**: ログとトレースの相関分析
6. **アラート**: 異常検知とアラート設定

## 🧹 クリーンアップ

```bash
# すべてのコンテナを停止・削除
docker-compose down -v
```

## 📖 参考資料

- [Datadog APM ドキュメント](https://docs.datadoghq.com/ja/tracing/)
- [Datadog インフラ監視](https://docs.datadoghq.com/ja/infrastructure/)
- [Datadog ログ管理](https://docs.datadoghq.com/ja/logs/)
- [Datadog RUM](https://docs.datadoghq.com/ja/real_user_monitoring/)

## 📝 ライセンス

MIT

## 🤝 コントリビューション

プルリクエスト歓迎！バグ報告や機能提案はIssueでお願いします。
