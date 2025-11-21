# 基礎編: Docker + React + Node.js ログ計装とパフォーマンス改善ハンズオン

## 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [アーキテクチャ](#アーキテクチャ)
4. [Step 1: 環境セットアップ](#step-1-環境セットアップ)
5. [Step 2: Node.js バックエンドにログを実装](#step-2-nodejs-バックエンドにログを実装)
6. [Step 3: React フロントエンドにログを実装](#step-3-react-フロントエンドにログを実装)
7. [Step 4: Datadog でログとトレースを確認](#step-4-datadog-でログとトレースを確認)
8. [Step 5: パフォーマンス問題の特定](#step-5-パフォーマンス問題の特定)
9. [Step 6: パフォーマンス改善の実装](#step-6-パフォーマンス改善の実装)
10. [Step 7: 改善効果の測定](#step-7-改善効果の測定)

---

## 概要

このハンズオンでは、Docker コンテナで動作する React + Node.js アプリケーションに対して、以下を実践します:

### 学習目標

- ✅ **構造化ログの実装**: JSON形式でのログ出力
- ✅ **トレースとログの相関**: APM トレースとログの連携
- ✅ **フロントエンドのロギング**: ブラウザからのログ送信
- ✅ **パフォーマンスボトルネックの特定**: Datadog APM での分析
- ✅ **コード改善**: N+1問題、キャッシュ戦略の実装
- ✅ **効果測定**: 改善前後のパフォーマンス比較

### 所要時間

約 **90分**

---

## 前提条件

### 必要な環境

- Docker & Docker Compose
- Node.js 18+
- Datadog アカウント
- Datadog API キー
- テキストエディタ (VS Code 推奨)

### 事前知識

- JavaScript/TypeScript の基礎
- React の基礎
- Docker の基本的な使い方
- REST API の理解

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  React App (Port 3000)                               │   │
│  │  - RUM SDK (ユーザー操作トラッキング)                 │   │
│  │  - Browser Logs (エラー、警告)                        │   │
│  │  - Performance Tracking                              │   │
│  └────────────────────┬─────────────────────────────────┘   │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                          │ HTTP/HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker Container: Node.js Backend (Port 5000)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Express.js API                                        │ │
│  │  - Winston Logger (構造化ログ)                         │ │
│  │  - dd-trace (APM計装)                                  │ │
│  │  - カスタムミドルウェア                                 │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                              │
│               ├──▶ PostgreSQL (Port 5432)                   │
│               │    - クエリログ                              │
│               │    - スロークエリ検出                        │
│               │                                              │
│               └──▶ Redis (Port 6379)                        │
│                    - キャッシュログ                          │
│                    - ヒット/ミス率                           │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Logs + Traces
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Docker Container: Datadog Agent (Port 8126)                │
├─────────────────────────────────────────────────────────────┤
│  - APM Trace Agent                                          │
│  - Log Collection                                           │
│  - DogStatsD                                                │
│  - Container Metrics                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Datadog Cloud │
              └────────────────┘
```

---

## Step 1: 環境セットアップ

### 1.1 プロジェクト構造の作成

```bash
mkdir -p logging-handson/backend
mkdir -p logging-handson/frontend
mkdir -p logging-handson/datadog
cd logging-handson
```

### 1.2 Docker Compose の作成

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Datadog Agent
  datadog-agent:
    image: gcr.io/datadoghq/agent:7
    container_name: datadog-agent
    restart: unless-stopped
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_SITE=${DD_SITE:-datadoghq.com}
      - DD_ENV=dev
      - DD_SERVICE=logging-handson
      - DD_VERSION=1.0.0

      # APM設定
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true

      # ログ収集
      - DD_LOGS_ENABLED=true
      - DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true

      # コンテナメトリクス
      - DD_CONTAINER_EXCLUDE=""

    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro

    ports:
      - "8126:8126"  # APM
      - "8125:8125/udp"  # DogStatsD

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=demo_user
      - POSTGRES_PASSWORD=demo_password
      - POSTGRES_DB=demo_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    labels:
      com.datadoghq.ad.logs: '[{"source": "postgresql", "service": "postgres"}]'

  # Redis
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    labels:
      com.datadoghq.ad.logs: '[{"source": "redis", "service": "redis"}]'

  # Node.js Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend
    restart: unless-stopped
    environment:
      - DD_AGENT_HOST=datadog-agent
      - DD_TRACE_AGENT_PORT=8126
      - DD_ENV=dev
      - DD_SERVICE=nodejs-backend
      - DD_VERSION=1.0.0
      - DD_LOGS_INJECTION=true
      - DD_TRACE_SAMPLE_RATE=1

      # Database
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_USER=demo_user
      - DATABASE_PASSWORD=demo_password
      - DATABASE_NAME=demo_db

      # Redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379

      # Node.js
      - NODE_ENV=development
      - PORT=5000

    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
      - datadog-agent
    labels:
      com.datadoghq.ad.logs: '[{"source": "nodejs", "service": "nodejs-backend"}]'

  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    restart: unless-stopped
    environment:
      - REACT_APP_API_URL=http://localhost:5000
      - REACT_APP_DD_RUM_APPLICATION_ID=${REACT_APP_DD_RUM_APPLICATION_ID}
      - REACT_APP_DD_RUM_CLIENT_TOKEN=${REACT_APP_DD_RUM_CLIENT_TOKEN}
      - REACT_APP_DD_RUM_SITE=${REACT_APP_DD_RUM_SITE:-datadoghq.com}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    labels:
      com.datadoghq.ad.logs: '[{"source": "react", "service": "frontend"}]'

volumes:
  postgres_data:
```

### 1.3 環境変数の設定

`.env`:

```bash
# Datadog
DD_API_KEY=your_datadog_api_key_here
DD_SITE=datadoghq.com

# RUM (Datadog UI から取得)
REACT_APP_DD_RUM_APPLICATION_ID=your_rum_app_id
REACT_APP_DD_RUM_CLIENT_TOKEN=your_rum_client_token
REACT_APP_DD_RUM_SITE=datadoghq.com
```

---

## Step 2: Node.js バックエンドにログを実装

### 2.1 バックエンドのプロジェクト初期化

```bash
cd backend
npm init -y
```

### 2.2 依存パッケージのインストール

`backend/package.json`:

```json
{
  "name": "nodejs-backend",
  "version": "1.0.0",
  "description": "Logging hands-on backend",
  "main": "server.js",
  "scripts": {
    "start": "node -r dd-trace/init server.js",
    "dev": "nodemon -r dd-trace/init server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.0",
    "redis": "^4.6.0",
    "winston": "^3.11.0",
    "dd-trace": "^4.20.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
```

```bash
npm install
```

### 2.3 Datadog Tracer の初期化

`backend/dd-trace/init.js`:

```javascript
const tracer = require('dd-trace').init({
  logInjection: true,  // ログにトレースIDを自動注入
  runtimeMetrics: true,  // ランタイムメトリクス
  profiling: true,  // Continuous Profiler
  appsec: false,
  env: process.env.DD_ENV || 'dev',
  service: process.env.DD_SERVICE || 'nodejs-backend',
  version: process.env.DD_VERSION || '1.0.0',
});

module.exports = tracer;
```

### 2.4 Winston Logger の設定

`backend/logger.js`:

```javascript
const winston = require('winston');
const tracer = require('dd-trace');

// カスタムフォーマット: トレースIDを含むJSON形式
const datadogFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf((info) => {
    // dd-trace からトレースコンテキストを取得
    const span = tracer.scope().active();
    if (span) {
      info.dd = {
        trace_id: span.context().toTraceId(),
        span_id: span.context().toSpanId(),
      };
    }

    // 環境変数から service/env/version を追加
    info.dd = {
      ...info.dd,
      service: process.env.DD_SERVICE || 'nodejs-backend',
      env: process.env.DD_ENV || 'dev',
      version: process.env.DD_VERSION || '1.0.0',
    };

    return JSON.stringify(info);
  })
);

// Logger インスタンスの作成
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: datadogFormat,
  transports: [
    // コンソール出力 (Docker がキャプチャ)
    new winston.transports.Console(),
  ],
});

module.exports = logger;
```

### 2.5 データベース初期化

`backend/init.sql`:

```sql
-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 注文テーブル
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_name VARCHAR(200) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- サンプルデータ挿入
INSERT INTO users (name, email) VALUES
    ('Alice Johnson', 'alice@example.com'),
    ('Bob Smith', 'bob@example.com'),
    ('Charlie Brown', 'charlie@example.com'),
    ('Diana Prince', 'diana@example.com'),
    ('Eve Adams', 'eve@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO orders (user_id, product_name, quantity, price) VALUES
    (1, 'Laptop', 1, 1200.00),
    (1, 'Mouse', 2, 25.00),
    (2, 'Keyboard', 1, 80.00),
    (3, 'Monitor', 1, 300.00),
    (4, 'Webcam', 1, 60.00),
    (5, 'Headphones', 1, 150.00);
```

### 2.6 Express サーバーの実装

`backend/server.js`:

```javascript
require('dotenv').config();
const tracer = require('./dd-trace/init');
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const redis = require('redis');
const logger = require('./logger');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// リクエストロギングミドルウェア
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;

    logger.info('HTTP Request', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration_ms: duration,
      user_agent: req.get('user-agent'),
      ip: req.ip,
    });
  });

  next();
});

// PostgreSQL 接続
const pool = new Pool({
  host: process.env.DATABASE_HOST || 'postgres',
  port: process.env.DATABASE_PORT || 5432,
  user: process.env.DATABASE_USER || 'demo_user',
  password: process.env.DATABASE_PASSWORD || 'demo_password',
  database: process.env.DATABASE_NAME || 'demo_db',
});

// Redis 接続
const redisClient = redis.createClient({
  socket: {
    host: process.env.REDIS_HOST || 'redis',
    port: process.env.REDIS_PORT || 6379,
  },
});

redisClient.on('error', (err) => {
  logger.error('Redis connection error', { error: err.message });
});

redisClient.connect();

// ==================== API エンドポイント ====================

// ヘルスチェック
app.get('/health', (req, res) => {
  logger.info('Health check called');
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// ユーザー一覧取得 (パフォーマンス問題あり - N+1クエリ)
app.get('/api/users', async (req, res) => {
  const span = tracer.scope().active();
  span?.setTag('endpoint', 'get_users');

  logger.info('Fetching all users');

  try {
    // ユーザー取得
    const usersResult = await pool.query('SELECT * FROM users ORDER BY id');
    const users = usersResult.rows;

    logger.info('Users fetched from database', { count: users.length });

    // 🚨 N+1 問題: 各ユーザーの注文を個別に取得
    for (const user of users) {
      const ordersResult = await pool.query(
        'SELECT * FROM orders WHERE user_id = $1',
        [user.id]
      );
      user.orders = ordersResult.rows;

      logger.debug('Fetched orders for user', {
        user_id: user.id,
        order_count: user.orders.length,
      });
    }

    res.json({ users, count: users.length });
  } catch (error) {
    logger.error('Error fetching users', {
      error: error.message,
      stack: error.stack,
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 特定ユーザー取得 (キャッシュなし)
app.get('/api/users/:id', async (req, res) => {
  const { id } = req.params;
  const span = tracer.scope().active();
  span?.setTag('user_id', id);

  logger.info('Fetching user by ID', { user_id: id });

  try {
    // 🚨 キャッシュを使用していない
    const userResult = await pool.query('SELECT * FROM users WHERE id = $1', [id]);

    if (userResult.rows.length === 0) {
      logger.warn('User not found', { user_id: id });
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];

    // 注文取得
    const ordersResult = await pool.query(
      'SELECT * FROM orders WHERE user_id = $1',
      [id]
    );
    user.orders = ordersResult.rows;

    logger.info('User fetched successfully', {
      user_id: id,
      order_count: user.orders.length,
    });

    res.json({ user });
  } catch (error) {
    logger.error('Error fetching user', {
      error: error.message,
      user_id: id,
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 注文一覧取得 (スロークエリ)
app.get('/api/orders', async (req, res) => {
  logger.info('Fetching all orders');

  try {
    // 🚨 インデックスがないカラムでソート
    const result = await pool.query(`
      SELECT o.*, u.name as user_name, u.email as user_email
      FROM orders o
      JOIN users u ON o.user_id = u.id
      ORDER BY o.created_at DESC
    `);

    // 🚨 不要な遅延をシミュレート
    await new Promise((resolve) => setTimeout(resolve, 500));

    logger.info('Orders fetched', { count: result.rows.length });

    res.json({ orders: result.rows, count: result.rows.length });
  } catch (error) {
    logger.error('Error fetching orders', { error: error.message });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// エラー生成エンドポイント (テスト用)
app.get('/api/error', (req, res) => {
  logger.error('Intentional error endpoint called');

  try {
    throw new Error('This is a test error');
  } catch (error) {
    logger.error('Caught intentional error', {
      error: error.message,
      stack: error.stack,
    });
    res.status(500).json({ error: 'Intentional error' });
  }
});

// サーバー起動
app.listen(PORT, () => {
  logger.info('Server started', {
    port: PORT,
    env: process.env.NODE_ENV,
    service: process.env.DD_SERVICE,
  });
});
```

### 2.7 Dockerfile

`backend/Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 5000

CMD ["npm", "start"]
```

---

## Step 3: React フロントエンドにログを実装

### 3.1 フロントエンドプロジェクトの作成

```bash
cd ../frontend
npx create-react-app . --template typescript
```

### 3.2 Datadog RUM SDK のインストール

```bash
npm install @datadog/browser-rum @datadog/browser-logs
```

### 3.3 Datadog 初期化

`frontend/src/datadog.ts`:

```typescript
import { datadogRum } from '@datadog/browser-rum';
import { datadogLogs } from '@datadog/browser-logs';

// RUM 初期化
datadogRum.init({
  applicationId: process.env.REACT_APP_DD_RUM_APPLICATION_ID || '',
  clientToken: process.env.REACT_APP_DD_RUM_CLIENT_TOKEN || '',
  site: process.env.REACT_APP_DD_RUM_SITE || 'datadoghq.com',
  service: 'frontend',
  env: 'dev',
  version: '1.0.0',

  sessionSampleRate: 100,
  sessionReplaySampleRate: 100,
  trackUserInteractions: true,
  trackResources: true,
  trackLongTasks: true,

  defaultPrivacyLevel: 'mask-user-input',

  allowedTracingUrls: [
    { match: 'http://localhost:5000', propagatorTypes: ['datadog'] },
  ],
});

// Browser Logs 初期化
datadogLogs.init({
  clientToken: process.env.REACT_APP_DD_RUM_CLIENT_TOKEN || '',
  site: process.env.REACT_APP_DD_RUM_SITE || 'datadoghq.com',
  service: 'frontend',
  env: 'dev',
  version: '1.0.0',

  forwardErrorsToLogs: true,
  forwardConsoleLogs: 'all',
  sessionSampleRate: 100,
});

// ユーザー情報の設定 (例)
datadogRum.setUser({
  id: 'demo-user-123',
  name: 'Demo User',
  email: 'demo@example.com',
});

// グローバルコンテキスト
datadogRum.setGlobalContextProperty('app.version', '1.0.0');

export { datadogRum, datadogLogs };
```

### 3.4 ユーザー一覧コンポーネント

`frontend/src/components/UserList.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import { datadogRum, datadogLogs } from '../datadog';

interface Order {
  id: number;
  product_name: string;
  quantity: number;
  price: number;
}

interface User {
  id: number;
  name: string;
  email: string;
  orders: Order[];
}

const UserList: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    // カスタムアクションを記録
    datadogRum.addAction('fetch_users_clicked');

    datadogLogs.info('Fetching users from API', {
      component: 'UserList',
      action: 'fetch',
    });

    setLoading(true);
    setError(null);

    const startTime = performance.now();

    try {
      const response = await fetch('http://localhost:5000/api/users');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setUsers(data.users);

      const duration = performance.now() - startTime;

      // カスタムタイミングを記録
      datadogRum.addTiming('fetch_users_duration', duration);

      datadogLogs.info('Users fetched successfully', {
        component: 'UserList',
        user_count: data.users.length,
        duration_ms: duration,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);

      // エラーを記録
      datadogLogs.error('Failed to fetch users', {
        component: 'UserList',
        error: errorMessage,
      });

      datadogRum.addError(err as Error, {
        component: 'UserList',
        action: 'fetch_users',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRefresh = () => {
    datadogLogs.info('User clicked refresh button', {
      component: 'UserList',
    });
    fetchUsers();
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>User List</h1>
      <button onClick={handleRefresh} style={{ marginBottom: '20px' }}>
        Refresh
      </button>

      {users.map((user) => (
        <div
          key={user.id}
          style={{
            border: '1px solid #ccc',
            padding: '15px',
            marginBottom: '10px',
            borderRadius: '5px',
          }}
        >
          <h3>{user.name}</h3>
          <p>Email: {user.email}</p>
          <h4>Orders ({user.orders.length}):</h4>
          <ul>
            {user.orders.map((order) => (
              <li key={order.id}>
                {order.product_name} - Qty: {order.quantity} - Price: $
                {order.price}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default UserList;
```

### 3.5 App.tsx の更新

`frontend/src/App.tsx`:

```typescript
import React from 'react';
import './datadog'; // Datadog 初期化
import UserList from './components/UserList';

function App() {
  return (
    <div className="App">
      <UserList />
    </div>
  );
}

export default App;
```

### 3.6 Dockerfile

`frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

---

## Step 4: Datadog でログとトレースを確認

### 4.1 環境の起動

```bash
# プロジェクトルートで実行
docker-compose up -d

# ログを確認
docker-compose logs -f backend
```

### 4.2 アプリケーションにアクセス

ブラウザで `http://localhost:3000` にアクセスし、ユーザー一覧を表示します。

### 4.3 Datadog でログを確認

1. Datadog にログイン: https://app.datadoghq.com/
2. **Logs** セクションに移動
3. 以下のクエリでフィルタ:

```
service:nodejs-backend
```

**確認すべきログ:**

```json
{
  "level": "info",
  "message": "HTTP Request",
  "method": "GET",
  "path": "/api/users",
  "status": 200,
  "duration_ms": 523,
  "dd": {
    "trace_id": "1234567890123456789",
    "span_id": "9876543210987654",
    "service": "nodejs-backend",
    "env": "dev"
  },
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### 4.4 APM トレースを確認

1. **APM > Traces** に移動
2. `service:nodejs-backend` でフィルタ
3. `/api/users` のトレースを選択

**トレースの構造:**

```
nodejs-backend.request (523ms)
  ├─ postgresql.query: SELECT * FROM users (45ms)
  ├─ postgresql.query: SELECT * FROM orders WHERE user_id = 1 (12ms)
  ├─ postgresql.query: SELECT * FROM orders WHERE user_id = 2 (11ms)
  ├─ postgresql.query: SELECT * FROM orders WHERE user_id = 3 (13ms)
  ├─ postgresql.query: SELECT * FROM orders WHERE user_id = 4 (10ms)
  └─ postgresql.query: SELECT * FROM orders WHERE user_id = 5 (14ms)
```

### 4.5 ログとトレースの相関を確認

1. トレース詳細画面で **Logs** タブをクリック
2. 同じ `trace_id` を持つログが自動的に表示される

---

## Step 5: パフォーマンス問題の特定

### 5.1 N+1 クエリ問題の発見

**APM で確認:**

1. **APM > Services** → `nodejs-backend`
2. **Endpoints** タブ → `GET /api/users`
3. レイテンシ分布を確認

**問題:**
- 平均レスポンス時間: **500ms以上**
- PostgreSQL クエリが **6回** (1回 + 5回のN+1)
- ユーザー数が増えるとさらに悪化

**ログで確認:**

```
service:nodejs-backend AND "Fetched orders for user"
```

各ユーザーごとに個別のクエリログが記録されている。

### 5.2 キャッシュ未使用の問題

**APM で確認:**

1. `/api/users/:id` エンドポイントを分析
2. 毎回データベースクエリが実行されている
3. Redis への接続はあるが使用されていない

### 5.3 スロークエリの発見

**APM で確認:**

1. `/api/orders` エンドポイントを分析
2. 不要な `setTimeout(500)` による遅延
3. インデックスのない `created_at` カラムでのソート

---

## Step 6: パフォーマンス改善の実装

### 6.1 N+1 クエリの解決

`backend/server.js` を更新:

```javascript
// 改善版: JOINで一度に取得
app.get('/api/users', async (req, res) => {
  const span = tracer.scope().active();
  span?.setTag('endpoint', 'get_users');

  logger.info('Fetching all users (optimized)');

  try {
    // 1回のクエリでユーザーと注文を取得
    const result = await pool.query(`
      SELECT
        u.id as user_id,
        u.name as user_name,
        u.email as user_email,
        u.created_at as user_created_at,
        o.id as order_id,
        o.product_name,
        o.quantity,
        o.price,
        o.created_at as order_created_at
      FROM users u
      LEFT JOIN orders o ON u.id = o.user_id
      ORDER BY u.id, o.id
    `);

    // データを整形
    const usersMap = new Map();

    for (const row of result.rows) {
      if (!usersMap.has(row.user_id)) {
        usersMap.set(row.user_id, {
          id: row.user_id,
          name: row.user_name,
          email: row.user_email,
          created_at: row.user_created_at,
          orders: [],
        });
      }

      if (row.order_id) {
        usersMap.get(row.user_id).orders.push({
          id: row.order_id,
          product_name: row.product_name,
          quantity: row.quantity,
          price: row.price,
          created_at: row.order_created_at,
        });
      }
    }

    const users = Array.from(usersMap.values());

    logger.info('Users fetched from database (optimized)', {
      count: users.length,
      optimization: 'single_query_with_join',
    });

    res.json({ users, count: users.length });
  } catch (error) {
    logger.error('Error fetching users', {
      error: error.message,
      stack: error.stack,
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### 6.2 Redis キャッシュの実装

```javascript
// 改善版: Redisキャッシュを使用
app.get('/api/users/:id', async (req, res) => {
  const { id } = req.params;
  const cacheKey = `user:${id}`;

  const span = tracer.scope().active();
  span?.setTag('user_id', id);

  logger.info('Fetching user by ID (with cache)', { user_id: id });

  try {
    // キャッシュチェック
    const cachedData = await redisClient.get(cacheKey);

    if (cachedData) {
      logger.info('Cache hit', {
        user_id: id,
        cache_key: cacheKey,
      });

      span?.setTag('cache', 'hit');

      return res.json({
        user: JSON.parse(cachedData),
        from_cache: true,
      });
    }

    logger.info('Cache miss', { user_id: id });
    span?.setTag('cache', 'miss');

    // データベースから取得
    const userResult = await pool.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );

    if (userResult.rows.length === 0) {
      logger.warn('User not found', { user_id: id });
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];

    // 注文取得
    const ordersResult = await pool.query(
      'SELECT * FROM orders WHERE user_id = $1',
      [id]
    );
    user.orders = ordersResult.rows;

    // キャッシュに保存 (60秒)
    await redisClient.setEx(cacheKey, 60, JSON.stringify(user));

    logger.info('User cached', {
      user_id: id,
      ttl_seconds: 60,
    });

    res.json({ user, from_cache: false });
  } catch (error) {
    logger.error('Error fetching user', {
      error: error.message,
      user_id: id,
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### 6.3 スロークエリの最適化

```javascript
// 改善版: 不要な遅延を削除、インデックス追加
app.get('/api/orders', async (req, res) => {
  logger.info('Fetching all orders (optimized)');

  try {
    const result = await pool.query(`
      SELECT o.*, u.name as user_name, u.email as user_email
      FROM orders o
      JOIN users u ON o.user_id = u.id
      ORDER BY o.id DESC
      LIMIT 100
    `);

    // 不要な遅延を削除
    // await new Promise((resolve) => setTimeout(resolve, 500));

    logger.info('Orders fetched (optimized)', {
      count: result.rows.length,
      optimization: 'removed_artificial_delay',
    });

    res.json({ orders: result.rows, count: result.rows.length });
  } catch (error) {
    logger.error('Error fetching orders', { error: error.message });
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

**インデックス追加 (init.sql に追加):**

```sql
-- created_at カラムにインデックス追加
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
```

---

## Step 7: 改善効果の測定

### 7.1 コンテナの再起動

```bash
docker-compose down
docker-compose up -d
```

### 7.2 負荷テストの実行

```bash
# ApacheBench でテスト
ab -n 100 -c 10 http://localhost:5000/api/users

# または curl でループ
for i in {1..50}; do
  curl http://localhost:5000/api/users
  sleep 0.1
done
```

### 7.3 Datadog での比較

**改善前:**

```
GET /api/users
- 平均レスポンス: 523ms
- p95: 750ms
- p99: 1200ms
- クエリ数: 6回 (N+1)
```

**改善後:**

```
GET /api/users
- 平均レスポンス: 65ms (87%改善 🎉)
- p95: 120ms
- p99: 200ms
- クエリ数: 1回
```

**キャッシュ効果:**

```
GET /api/users/:id (初回)
- レスポンス: 45ms
- キャッシュ: miss

GET /api/users/:id (2回目以降)
- レスポンス: 3ms (93%改善 🎉)
- キャッシュ: hit
```

### 7.4 ログでの確認

**改善前のログ:**

```json
{
  "level": "debug",
  "message": "Fetched orders for user",
  "user_id": 1,
  "order_count": 2
}
// ↑ これが5回繰り返される
```

**改善後のログ:**

```json
{
  "level": "info",
  "message": "Users fetched from database (optimized)",
  "count": 5,
  "optimization": "single_query_with_join"
}
// ↑ 1回のログのみ
```

---

## まとめ

### 学習した内容

✅ **ログ実装:**
- Winston での構造化ログ
- トレースIDの自動注入
- フロントエンドからのログ送信

✅ **パフォーマンス問題の特定:**
- N+1 クエリ問題
- キャッシュ未使用
- スロークエリ

✅ **改善手法:**
- JOIN を使った単一クエリ
- Redis キャッシュ戦略
- インデックスの活用

✅ **効果測定:**
- 87%のレスポンス改善
- 93%のキャッシュヒット効果
- Datadog での可視化

### 次のステップ

🚀 **応用編へ進む:**
次は **Kubernetes + gRPC + マルチ言語 (Python/Golang/Node.js)** ハンズオンで、より高度な分散システムのログ実装とパフォーマンス最適化を学びます！

[応用編ハンズオンへ →](./HANDSON_ADVANCED_GRPC_K8S.md)
