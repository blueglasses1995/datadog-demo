import os
import time
import random
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from ddtrace import tracer
from ddtrace.contrib.flask import TraceMiddleware
from datadog import initialize, statsd
from pythonjsonlogger import jsonlogger

# Datadog初期化
initialize(
    statsd_host=os.getenv('DD_AGENT_HOST', 'datadog-agent'),
    statsd_port=8125
)

# ロギング設定（JSON形式でログとトレースを相関）
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Flaskアプリケーション初期化
app = Flask(__name__)
CORS(app)

# Datadog APMトレーシング設定
traced_app = TraceMiddleware(app, tracer, service="backend-api")

# データベース接続設定
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'demo_db'),
    'user': os.getenv('POSTGRES_USER', 'demo_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'demo_password'),
}

# Redis接続
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

def get_db_connection():
    """データベース接続を取得"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    logger.info("Health check called")
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/users', methods=['GET'])
def get_users():
    """ユーザー一覧を取得（DB接続）"""
    with tracer.trace("get_users", service="backend-api") as span:
        span.set_tag("endpoint", "/api/users")

        logger.info("Fetching all users from database")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users ORDER BY id")
            users = cur.fetchall()
            cur.close()
            conn.close()

            # カスタムメトリクス: ユーザー数
            statsd.gauge('users.count', len(users), tags=['endpoint:users'])

            logger.info(f"Successfully fetched {len(users)} users")
            return jsonify({"users": users, "count": len(users)})

        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}", exc_info=True)
            span.set_tag("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """特定ユーザーを取得（Redisキャッシュ利用）"""
    with tracer.trace("get_user", service="backend-api") as span:
        span.set_tag("user_id", user_id)

        # キャッシュチェック
        cache_key = f"user:{user_id}"
        cached_user = redis_client.get(cache_key)

        if cached_user:
            logger.info(f"Cache hit for user {user_id}")
            statsd.increment('cache.hit', tags=['resource:user'])
            span.set_tag("cache", "hit")
            return jsonify({"user": eval(cached_user), "from_cache": True})

        logger.info(f"Cache miss for user {user_id}, fetching from database")
        statsd.increment('cache.miss', tags=['resource:user'])
        span.set_tag("cache", "miss")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                # キャッシュに保存（60秒）
                redis_client.setex(cache_key, 60, str(dict(user)))
                logger.info(f"User {user_id} cached")
                return jsonify({"user": user, "from_cache": False})
            else:
                logger.warning(f"User {user_id} not found")
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}", exc_info=True)
            span.set_tag("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """注文一覧を取得（複数サービス連携のシミュレーション）"""
    with tracer.trace("get_orders", service="backend-api") as span:
        logger.info("Fetching orders with user information")

        try:
            # 注文データ取得
            with tracer.trace("database.query.orders"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT o.id, o.user_id, o.product_name, o.amount, o.created_at,
                           u.name as user_name, u.email as user_email
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    ORDER BY o.created_at DESC
                    LIMIT 50
                """)
                orders = cur.fetchall()
                cur.close()
                conn.close()

            # カスタムメトリクス: 注文数と合計金額
            total_amount = sum(float(order['amount']) for order in orders)
            statsd.gauge('orders.count', len(orders), tags=['endpoint:orders'])
            statsd.gauge('orders.total_amount', total_amount, tags=['endpoint:orders'])

            logger.info(f"Fetched {len(orders)} orders, total amount: {total_amount}")
            return jsonify({
                "orders": orders,
                "count": len(orders),
                "total_amount": total_amount
            })

        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
            span.set_tag("error", True)
            return jsonify({"error": str(e)}), 500

@app.route('/api/slow', methods=['GET'])
def slow_endpoint():
    """意図的に遅いエンドポイント（パフォーマンス監視デモ用）"""
    with tracer.trace("slow_endpoint", service="backend-api") as span:
        delay = random.uniform(1.0, 3.0)
        span.set_tag("delay_seconds", delay)

        logger.warning(f"Slow endpoint called, delaying {delay:.2f} seconds")

        # 意図的な遅延
        time.sleep(delay)

        # カスタムメトリクス
        statsd.histogram('endpoint.slow.delay', delay, tags=['endpoint:slow'])

        return jsonify({
            "message": "This endpoint is intentionally slow",
            "delay_seconds": delay
        })

@app.route('/api/error', methods=['GET'])
def error_endpoint():
    """意図的にエラーを発生させるエンドポイント（エラートラッキングデモ用）"""
    logger.error("Error endpoint called - intentional error")

    # カスタムメトリクス
    statsd.increment('endpoint.error.called', tags=['endpoint:error'])

    # ランダムなエラーを発生
    error_type = random.choice(['division', 'key', 'value'])

    if error_type == 'division':
        # ZeroDivisionError
        result = 1 / 0
    elif error_type == 'key':
        # KeyError
        data = {}
        value = data['nonexistent_key']
    else:
        # ValueError
        raise ValueError("Intentional error for testing purposes")

@app.route('/api/metrics', methods=['POST'])
def send_custom_metrics():
    """カスタムメトリクスを送信"""
    data = request.json

    with tracer.trace("send_custom_metrics", service="backend-api"):
        metric_name = data.get('metric_name')
        metric_value = data.get('metric_value')
        metric_type = data.get('metric_type', 'gauge')  # gauge, count, histogram
        tags = data.get('tags', [])

        logger.info(f"Sending custom metric: {metric_name}={metric_value}, type={metric_type}")

        if metric_type == 'gauge':
            statsd.gauge(metric_name, metric_value, tags=tags)
        elif metric_type == 'increment':
            statsd.increment(metric_name, value=metric_value, tags=tags)
        elif metric_type == 'histogram':
            statsd.histogram(metric_name, metric_value, tags=tags)
        else:
            return jsonify({"error": "Invalid metric type"}), 400

        return jsonify({
            "message": "Custom metric sent successfully",
            "metric": metric_name,
            "value": metric_value,
            "type": metric_type
        })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """キャッシュをクリア"""
    with tracer.trace("clear_cache", service="backend-api"):
        logger.info("Clearing Redis cache")

        try:
            # user:* キーを削除
            keys = redis_client.keys("user:*")
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys")
                return jsonify({"message": f"Cleared {len(keys)} cache entries"})
            else:
                return jsonify({"message": "No cache entries to clear"})
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """システム統計情報を取得"""
    with tracer.trace("get_stats", service="backend-api"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # ユーザー数
            cur.execute("SELECT COUNT(*) as count FROM users")
            user_count = cur.fetchone()['count']

            # 注文数
            cur.execute("SELECT COUNT(*) as count FROM orders")
            order_count = cur.fetchone()['count']

            # 合計注文金額
            cur.execute("SELECT SUM(amount) as total FROM orders")
            total_amount = cur.fetchone()['total'] or 0

            cur.close()
            conn.close()

            # Redisキャッシュ情報
            cache_keys = len(redis_client.keys("user:*"))

            stats = {
                "users": user_count,
                "orders": order_count,
                "total_amount": float(total_amount),
                "cache_entries": cache_keys,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Stats retrieved: {stats}")
            return jsonify(stats)

        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
