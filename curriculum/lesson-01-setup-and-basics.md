# レッスン1: 環境セットアップとDatadog基礎

## 📋 レッスン概要

このレッスンでは、Datadogハンズオン環境をセットアップし、Datadogの基本的な概念とUIの使い方を学びます。

**所要時間:** 60分
**難易度:** 初級
**前提知識:** Docker/Docker Composeの基礎、基本的なLinuxコマンド

## 🎯 学習目標

このレッスンを完了すると、以下ができるようになります：

- [ ] Datadogの主要機能を説明できる
- [ ] デモ環境をセットアップできる
- [ ] DatadogアカウントとAPI Keyを設定できる
- [ ] Datadogの基本的なUIナビゲーションができる
- [ ] データが正しく送信されていることを確認できる

## 📚 学習内容

### 1. Datadogとは？

Datadogは、クラウドスケールのアプリケーション向けの監視・セキュリティプラットフォームです。

#### 主要機能

1. **APM（Application Performance Monitoring）**
   - アプリケーションのパフォーマンス監視
   - 分散トレーシング
   - サービス依存関係の可視化

2. **Infrastructure Monitoring**
   - サーバー、コンテナ、クラウドリソースの監視
   - 400以上のインテグレーション
   - リアルタイムメトリクス

3. **Log Management**
   - ログの収集・検索・分析
   - トレースとの相関
   - ログベースメトリクス

4. **RUM（Real User Monitoring）**
   - フロントエンドのユーザー体験監視
   - セッション再生
   - Core Web Vitals

5. **Synthetic Monitoring**
   - APIとブラウザテストの自動化
   - グローバルな可用性監視

6. **Security Monitoring**
   - 脅威検出
   - コンプライアンス監視

#### Datadogのアーキテクチャ

```
[アプリケーション/インフラ]
         ↓
   [Datadog Agent]
         ↓
   [Datadog Cloud]
         ↓
  [ダッシュボード/アラート]
```

**Datadog Agent**: サーバーやコンテナ上で動作し、メトリクス、ログ、トレースを収集
**Datadog Cloud**: データを集約・分析・可視化
**UI**: ブラウザから監視データにアクセス

---

### 2. 環境セットアップ

#### 2.1 必要な環境

- **Docker Desktop**: v20.10以上
- **メモリ**: 最低4GB、推奨8GB以上
- **ディスク**: 5GB以上の空き容量
- **OS**: macOS, Windows, Linux

#### 2.2 リポジトリのクローン

すでにこのリポジトリをお持ちの場合はスキップしてください。

```bash
git clone https://github.com/your-username/datadog-demo.git
cd datadog-demo
```

#### 2.3 Datadogアカウントの作成

1. [Datadog公式サイト](https://www.datadoghq.com/)にアクセス
2. 「Try Datadog Free」をクリック
3. アカウント情報を入力して登録
4. 14日間の無料トライアルが開始

**重要:** メールアドレスの確認を忘れずに！

#### 2.4 API Keyの取得

1. Datadogにログイン
2. 左下のユーザー名 → **Organization Settings** をクリック
3. 左メニューから **API Keys** を選択
4. **New Key** をクリック（または既存のキーをコピー）
5. キー名を入力（例: "datadog-demo"）
6. **Create Key** をクリック
7. **API Key をコピー**（重要: 後で再表示できません）

#### 2.5 RUM設定（オプション）

フロントエンド監視を行う場合：

1. 左メニューから **UX Monitoring** → **RUM Applications** を選択
2. **New Application** をクリック
3. Application Type: **JS** を選択
4. Application Name: "datadog-demo-frontend" を入力
5. **Create New RUM Application** をクリック
6. **Application ID** と **Client Token** をコピー

#### 2.6 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# エディタで開く（VScodeの例）
code .env
```

`.env`ファイルを編集：

```env
# 必須: Datadog API Key
DD_API_KEY=your_actual_api_key_here

# 必須: Datadog Site（通常は datadoghq.com）
DD_SITE=datadoghq.com

# 推奨設定
DD_ENV=dev
DD_SERVICE=datadog-demo
DD_VERSION=1.0.0

# RUM設定（オプション）
REACT_APP_DD_RUM_APPLICATION_ID=your_rum_app_id
REACT_APP_DD_RUM_CLIENT_TOKEN=your_rum_client_token
REACT_APP_DD_RUM_SITE=datadoghq.com
```

**重要なサイト設定:**
- 米国: `datadoghq.com`（デフォルト）
- 欧州: `datadoghq.eu`
- 米国3: `us3.datadoghq.com`
- 米国5: `us5.datadoghq.com`
- アジア太平洋: `ap1.datadoghq.com`

#### 2.7 環境の起動

```bash
# すべてのコンテナを起動
docker-compose up -d

# ログを確認（Ctrl+Cで終了）
docker-compose logs -f

# 別のターミナルでコンテナの状態を確認
docker-compose ps
```

**期待される出力:**
```
NAME                STATUS              PORTS
datadog-agent       Up                  0.0.0.0:8126->8126/tcp
postgres            Up                  0.0.0.0:5432->5432/tcp
redis               Up                  0.0.0.0:6379->6379/tcp
backend             Up                  0.0.0.0:5000->5000/tcp
frontend            Up                  0.0.0.0:3000->3000/tcp
nginx               Up                  0.0.0.0:80->80/tcp
```

すべてのコンテナが "Up" 状態であることを確認してください。

#### 2.8 アプリケーションへのアクセス

ブラウザで以下にアクセス：

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/health
- **Nginx**: http://localhost:80

Frontendにアクセスして、ユーザー一覧や統計情報が表示されることを確認してください。

---

### 3. Datadog UIの基本ナビゲーション

#### 3.1 ダッシュボードにログイン

1. https://app.datadoghq.com/ にアクセス
2. 作成したアカウントでログイン

#### 3.2 主要メニューの確認

左サイドバーの主要メニュー：

| メニュー | 説明 |
|--------|------|
| **Dashboards** | カスタムダッシュボード |
| **Infrastructure** | インフラ監視（ホスト、コンテナなど） |
| **APM** | アプリケーションパフォーマンス監視 |
| **Logs** | ログ管理 |
| **UX Monitoring** | RUM、セッション再生 |
| **Monitors** | アラート設定 |
| **Integrations** | 連携サービス設定 |

#### 3.3 データ受信の確認

**Infrastructure List:**
1. **Infrastructure** → **Containers** を開く
2. 起動した6つのコンテナが表示されることを確認
3. コンテナ名をクリックして詳細を確認

**APM Services:**
1. **APM** → **Services** を開く
2. `backend-api` サービスが表示されることを確認
   - 初回は数分かかる場合があります
3. サービス名をクリックして詳細を確認

**Logs:**
1. **Logs** → **Explorer** を開く
2. 各コンテナのログが表示されることを確認
3. フィルター: `service:backend-api` を試す

---

### 4. トラフィック生成とデータ確認

#### 4.1 トラフィック生成

```bash
# トラフィック生成スクリプトを実行
python scripts/generate_traffic.py

# または複数回実行
python scripts/generate_traffic.py 3
```

スクリプトが以下を実行します：
- ユーザー一覧の取得
- 個別ユーザー取得（キャッシュテスト）
- 注文一覧の取得
- 遅いエンドポイントの呼び出し
- エラーエンドポイントの呼び出し
- カスタムメトリクスの送信

#### 4.2 APMでトレースを確認

1. **APM** → **Traces** を開く
2. 最近のトレースが表示されることを確認
3. 任意のトレースをクリック
4. **フレームグラフ** で処理時間を確認
   - Flask処理
   - PostgreSQL クエリ
   - Redis 操作

#### 4.3 Infrastructure でメトリクスを確認

1. **Infrastructure** → **Containers** を開く
2. `backend` コンテナをクリック
3. **Metrics** タブで以下を確認：
   - CPU使用率
   - メモリ使用量
   - ネットワークI/O

#### 4.4 Logs でログを確認

1. **Logs** → **Explorer** を開く
2. フィルター: `service:backend-api status:info`
3. ログエントリをクリックして詳細を確認
4. **View in APM** でトレースに移動できることを確認

---

### 5. 実習課題

#### 課題1: 基本操作（15分）

1. Webアプリで以下の操作を実施：
   - 「ユーザー」タブをクリックしてユーザー一覧を表示
   - 任意のユーザーの「詳細」ボタンをクリック
   - 「注文」タブに切り替え
   - 「遅いエンドポイント」ボタンをクリック
   - 「エラー発生」ボタンを数回クリック

2. Datadogで以下を確認：
   - APM → Services で `backend-api` のリクエスト数が増加
   - APM → Traces で各操作のトレースを確認
   - Logs で INFO, WARNING, ERROR レベルのログを確認

#### 課題2: データ探索（15分）

1. **Infrastructure List**
   - 各コンテナのCPU、メモリ使用率を確認
   - 最もリソースを使用しているコンテナを特定

2. **APM Service Map**
   - APM → Service Map を開く
   - サービス間の依存関係を確認
   - backend-api → postgres, redis の接続を確認

3. **Metrics Explorer**
   - Metrics → Explorer を開く
   - メトリクス `docker.cpu.usage` を検索
   - コンテナごとにグラフ化

#### 課題3: トラブルシューティング（10分）

意図的にエラーを発生させ、Datadogで調査：

1. Webアプリで「エラー発生」ボタンを5回クリック
2. APM → Services → backend-api → **Errors** タブを開く
3. エラー率とエラーの種類を確認
4. 任意のエラートレースをクリックして詳細を確認
5. スタックトレースからエラー原因を特定

---

### 6. 確認問題

#### 問1: 基礎知識
Datadogの主要な4つの機能を挙げてください。

<details>
<summary>解答例</summary>

1. APM（Application Performance Monitoring）
2. Infrastructure Monitoring
3. Log Management
4. RUM（Real User Monitoring）

その他にも Synthetic Monitoring, Security Monitoring などがあります。
</details>

#### 問2: Datadog Agent
Datadog Agentの役割を説明してください。

<details>
<summary>解答例</summary>

Datadog Agentは、監視対象のホストやコンテナ上で動作し、以下を収集してDatadog Cloudに送信します：
- メトリクス（CPU、メモリ、ネットワークなど）
- ログ
- APMトレース
- プロセス情報
</details>

#### 問3: トレース分析
APM のトレースから、どのような情報を得られますか？

<details>
<summary>解答例</summary>

- リクエストの処理時間（全体およびスパン単位）
- サービス間の呼び出し関係
- データベースクエリの実行時間
- エラーの発生箇所
- ボトルネックの特定
- 依存サービスのパフォーマンス
</details>

#### 問4: 実践
`/api/slow` エンドポイントが遅い理由をAPMで特定してください。

<details>
<summary>解答例</summary>

1. APM → Traces で `/api/slow` のトレースを開く
2. フレームグラフで `time.sleep()` による意図的な遅延を確認
3. `delay_seconds` タグで遅延時間を確認

実際の環境では、データベースクエリ、外部API呼び出し、複雑な処理などがボトルネックになることが多い。
</details>

---

### 7. トラブルシューティング

#### コンテナが起動しない

**症状:** `docker-compose ps` で "Exited" 状態のコンテナがある

**対処法:**
```bash
# ログを確認
docker-compose logs [service-name]

# よくあるエラー
# 1. ポートが既に使用されている
#    → 使用中のプロセスを停止するか、docker-compose.ymlのポートを変更

# 2. メモリ不足
#    → Docker Desktopのメモリ設定を増やす（推奨: 8GB）

# 完全リセット
docker-compose down -v
docker-compose up -d
```

#### Datadogにデータが表示されない

**確認項目:**

1. **API Keyが正しいか**
   ```bash
   cat .env | grep DD_API_KEY
   ```

2. **Datadog Agentが動作しているか**
   ```bash
   docker-compose logs datadog-agent
   # "Datadog Agent is running" というメッセージを確認
   ```

3. **ネットワーク接続**
   ```bash
   # Agent コンテナ内から確認
   docker-compose exec datadog-agent agent status
   ```

4. **サイト設定が正しいか**
   - `.env` の `DD_SITE` がアカウントのリージョンと一致しているか確認

#### Frontend が表示されない

**対処法:**
```bash
# Frontend コンテナのログを確認
docker-compose logs frontend

# Reactの起動には数分かかる場合があります
# "webpack compiled successfully" が表示されるまで待つ

# ブラウザのキャッシュをクリア
# Shift + Ctrl + R (Windows/Linux)
# Shift + Cmd + R (Mac)
```

---

### 8. 次のステップ

おめでとうございます！レッスン1を完了しました！

次のレッスンでは、APMを詳しく学びます：

**[レッスン2: APM（Application Performance Monitoring）入門](./lesson-02-apm-basics.md)**

#### 予習

次のレッスンの前に、以下を確認しておくと理解が深まります：

- [ ] APM → Service Map でサービス依存関係を確認
- [ ] いくつかのトレースを開いてフレームグラフを見てみる
- [ ] backend/app.py のコードを読んでトレーシングの実装を確認

#### 環境の停止・再開

```bash
# 停止（データは保持）
docker-compose stop

# 再開
docker-compose start

# 完全停止・削除
docker-compose down -v
```

---

## 📚 参考資料

- [Datadog Getting Started](https://docs.datadoghq.com/ja/getting_started/)
- [Datadog Agent Documentation](https://docs.datadoghq.com/ja/agent/)
- [Datadog UI Guide](https://docs.datadoghq.com/ja/getting_started/dashboards/)

## 💡 まとめ

このレッスンで学んだこと：

✅ Datadogの主要機能の概要
✅ デモ環境のセットアップ
✅ Datadog Agent の役割
✅ 基本的なUIナビゲーション
✅ データ収集の確認方法

次のレッスンでは、APMを使った詳細なパフォーマンス分析を学びます！
