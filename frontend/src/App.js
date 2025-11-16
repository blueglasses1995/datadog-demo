import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { datadogRum } from '@datadog/browser-rum';
import { datadogLogs } from '@datadog/browser-logs';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('users');

  // ユーザー一覧を取得
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);

    datadogRum.addAction('fetch_users');
    datadogLogs.logger.info('Fetching users list');

    try {
      const response = await axios.get(`${API_URL}/users`);
      setUsers(response.data.users);
      datadogLogs.logger.info(`Successfully fetched ${response.data.count} users`);
    } catch (err) {
      setError('ユーザー情報の取得に失敗しました: ' + err.message);
      datadogLogs.logger.error('Failed to fetch users', { error: err.message });
      datadogRum.addError(err);
    } finally {
      setLoading(false);
    }
  };

  // ユーザー詳細を取得（キャッシュテスト用）
  const fetchUserDetail = async (userId) => {
    datadogRum.addAction('fetch_user_detail', { userId });
    datadogLogs.logger.info(`Fetching user detail for ID: ${userId}`);

    try {
      const response = await axios.get(`${API_URL}/users/${userId}`);
      const fromCache = response.data.from_cache ? 'キャッシュ' : 'DB';
      alert(`ユーザー: ${response.data.user.name}\nデータソース: ${fromCache}`);
      datadogLogs.logger.info(`User ${userId} fetched from ${fromCache}`);
    } catch (err) {
      alert('ユーザー詳細の取得に失敗しました');
      datadogLogs.logger.error(`Failed to fetch user ${userId}`, { error: err.message });
      datadogRum.addError(err);
    }
  };

  // 注文一覧を取得
  const fetchOrders = async () => {
    setLoading(true);
    setError(null);

    datadogRum.addAction('fetch_orders');
    datadogLogs.logger.info('Fetching orders list');

    try {
      const response = await axios.get(`${API_URL}/orders`);
      setOrders(response.data.orders);
      datadogLogs.logger.info(`Successfully fetched ${response.data.count} orders`);
    } catch (err) {
      setError('注文情報の取得に失敗しました: ' + err.message);
      datadogLogs.logger.error('Failed to fetch orders', { error: err.message });
      datadogRum.addError(err);
    } finally {
      setLoading(false);
    }
  };

  // 統計情報を取得
  const fetchStats = async () => {
    datadogRum.addAction('fetch_stats');
    datadogLogs.logger.info('Fetching stats');

    try {
      const response = await axios.get(`${API_URL}/stats`);
      setStats(response.data);
      datadogLogs.logger.info('Successfully fetched stats');
    } catch (err) {
      datadogLogs.logger.error('Failed to fetch stats', { error: err.message });
      datadogRum.addError(err);
    }
  };

  // 遅いエンドポイントを呼び出し（パフォーマンステスト用）
  const testSlowEndpoint = async () => {
    datadogRum.addAction('test_slow_endpoint');
    datadogLogs.logger.warn('Testing slow endpoint');

    try {
      const startTime = Date.now();
      await axios.get(`${API_URL}/slow`);
      const duration = Date.now() - startTime;
      alert(`遅いエンドポイントのレスポンス時間: ${duration}ms`);
      datadogLogs.logger.info(`Slow endpoint responded in ${duration}ms`);
    } catch (err) {
      alert('エラーが発生しました');
      datadogRum.addError(err);
    }
  };

  // エラーを発生させる（エラートラッキングテスト用）
  const testErrorEndpoint = async () => {
    datadogRum.addAction('test_error_endpoint');
    datadogLogs.logger.warn('Testing error endpoint');

    try {
      await axios.get(`${API_URL}/error`);
    } catch (err) {
      alert('意図的なエラーが発生しました（Datadogでトラッキング中）');
      datadogLogs.logger.error('Intentional error from error endpoint', { error: err.message });
      datadogRum.addError(err);
    }
  };

  // キャッシュをクリア
  const clearCache = async () => {
    datadogRum.addAction('clear_cache');
    datadogLogs.logger.info('Clearing cache');

    try {
      const response = await axios.post(`${API_URL}/cache/clear`);
      alert(response.data.message);
      datadogLogs.logger.info('Cache cleared successfully');
    } catch (err) {
      alert('キャッシュのクリアに失敗しました');
      datadogRum.addError(err);
    }
  };

  // カスタムメトリクスを送信
  const sendCustomMetric = async () => {
    const metricValue = Math.random() * 100;

    datadogRum.addAction('send_custom_metric', { value: metricValue });
    datadogLogs.logger.info(`Sending custom metric: ${metricValue}`);

    try {
      await axios.post(`${API_URL}/metrics`, {
        metric_name: 'custom.frontend.button_click',
        metric_value: metricValue,
        metric_type: 'gauge',
        tags: ['source:frontend', 'action:button_click']
      });
      alert(`カスタムメトリクスを送信しました: ${metricValue.toFixed(2)}`);
      datadogLogs.logger.info('Custom metric sent successfully');
    } catch (err) {
      alert('メトリクスの送信に失敗しました');
      datadogRum.addError(err);
    }
  };

  // 初回ロード時に統計情報を取得
  useEffect(() => {
    fetchStats();
  }, []);

  // タブ切り替え時にデータを取得
  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'orders') {
      fetchOrders();
    }
  }, [activeTab]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>📊 Datadog ハンズオン デモ</h1>
        <p>マイクロサービス監視 & インフラ監視</p>
      </header>

      <div className="container">
        {/* 統計情報 */}
        {stats && (
          <div className="stats-panel">
            <h2>📈 システム統計</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{stats.users}</div>
                <div className="stat-label">ユーザー数</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.orders}</div>
                <div className="stat-label">注文数</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">¥{stats.total_amount.toLocaleString()}</div>
                <div className="stat-label">合計金額</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.cache_entries}</div>
                <div className="stat-label">キャッシュ数</div>
              </div>
            </div>
          </div>
        )}

        {/* テストボタン */}
        <div className="test-panel">
          <h2>🧪 Datadog機能テスト</h2>
          <div className="button-grid">
            <button onClick={testSlowEndpoint} className="btn btn-warning">
              ⏱️ 遅いエンドポイント
            </button>
            <button onClick={testErrorEndpoint} className="btn btn-danger">
              ⚠️ エラー発生
            </button>
            <button onClick={sendCustomMetric} className="btn btn-info">
              📊 カスタムメトリクス
            </button>
            <button onClick={clearCache} className="btn btn-secondary">
              🗑️ キャッシュクリア
            </button>
          </div>
        </div>

        {/* タブナビゲーション */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            👥 ユーザー
          </button>
          <button
            className={`tab ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            📦 注文
          </button>
        </div>

        {/* エラー表示 */}
        {error && <div className="error-message">{error}</div>}

        {/* ローディング */}
        {loading && <div className="loading">読み込み中...</div>}

        {/* ユーザー一覧 */}
        {activeTab === 'users' && !loading && (
          <div className="data-panel">
            <h2>👥 ユーザー一覧</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>名前</th>
                    <th>メールアドレス</th>
                    <th>登録日</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id}>
                      <td>{user.id}</td>
                      <td>{user.name}</td>
                      <td>{user.email}</td>
                      <td>{new Date(user.created_at).toLocaleDateString('ja-JP')}</td>
                      <td>
                        <button
                          onClick={() => fetchUserDetail(user.id)}
                          className="btn btn-sm"
                        >
                          詳細（キャッシュテスト）
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 注文一覧 */}
        {activeTab === 'orders' && !loading && (
          <div className="data-panel">
            <h2>📦 注文一覧</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>ユーザー</th>
                    <th>商品名</th>
                    <th>金額</th>
                    <th>注文日</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map(order => (
                    <tr key={order.id}>
                      <td>{order.id}</td>
                      <td>{order.user_name}</td>
                      <td>{order.product_name}</td>
                      <td>¥{parseFloat(order.amount).toLocaleString()}</td>
                      <td>{new Date(order.created_at).toLocaleDateString('ja-JP')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <footer className="App-footer">
        <p>Datadog Monitoring Demo - マイクロサービス & インフラ監視</p>
      </footer>
    </div>
  );
}

export default App;
