#!/usr/bin/env python3
"""
Datadog ハンズオン用トラフィック生成スクリプト

このスクリプトは、デモアプリケーションに対して様々なリクエストを送信し、
Datadogで監視できるトラフィックを生成します。
"""

import requests
import time
import random
import sys
from typing import List, Dict, Any

# 基本URL
BASE_URL = "http://localhost:80/api"

class TrafficGenerator:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'errors': 0
        }

    def make_request(self, method: str, endpoint: str, description: str, **kwargs) -> bool:
        """HTTPリクエストを送信"""
        url = f"{self.base_url}{endpoint}"
        self.stats['total_requests'] += 1

        try:
            print(f"📡 {description}... ", end='', flush=True)
            response = self.session.request(method, url, timeout=10, **kwargs)

            if response.status_code < 400:
                self.stats['successful_requests'] += 1
                print(f"✅ ({response.status_code})")
                return True
            else:
                self.stats['failed_requests'] += 1
                print(f"⚠️  ({response.status_code})")
                return False

        except requests.exceptions.RequestException as e:
            self.stats['errors'] += 1
            print(f"❌ エラー: {str(e)}")
            return False

    def test_user_endpoints(self):
        """ユーザー関連エンドポイントをテスト"""
        print("\n👥 ユーザーエンドポイントのテスト")
        print("=" * 60)

        # ユーザー一覧を取得
        self.make_request('GET', '/users', 'ユーザー一覧を取得')
        time.sleep(0.5)

        # 個別ユーザーを取得（キャッシュテスト）
        user_ids = [1, 2, 3, 4, 5]
        for user_id in random.sample(user_ids, 3):
            self.make_request('GET', f'/users/{user_id}', f'ユーザー {user_id} を取得（初回：DB）')
            time.sleep(0.3)

            # 同じユーザーを再取得（キャッシュヒット）
            self.make_request('GET', f'/users/{user_id}', f'ユーザー {user_id} を取得（2回目：キャッシュ）')
            time.sleep(0.3)

    def test_order_endpoints(self):
        """注文関連エンドポイントをテスト"""
        print("\n📦 注文エンドポイントのテスト")
        print("=" * 60)

        # 注文一覧を取得
        self.make_request('GET', '/orders', '注文一覧を取得')
        time.sleep(0.5)

    def test_stats_endpoint(self):
        """統計エンドポイントをテスト"""
        print("\n📊 統計エンドポイントのテスト")
        print("=" * 60)

        self.make_request('GET', '/stats', 'システム統計を取得')
        time.sleep(0.5)

    def test_slow_endpoint(self):
        """遅いエンドポイントをテスト（APMパフォーマンス監視）"""
        print("\n⏱️  パフォーマンステスト（遅いエンドポイント）")
        print("=" * 60)

        for i in range(3):
            self.make_request('GET', '/slow', f'遅いエンドポイント {i+1}/3')
            time.sleep(1)

    def test_error_endpoint(self):
        """エラーエンドポイントをテスト（エラートラッキング）"""
        print("\n⚠️  エラートラッキングテスト")
        print("=" * 60)

        for i in range(3):
            self.make_request('GET', '/error', f'意図的なエラー {i+1}/3')
            time.sleep(0.5)

    def test_custom_metrics(self):
        """カスタムメトリクスを送信"""
        print("\n📈 カスタムメトリクステスト")
        print("=" * 60)

        metrics = [
            {
                'metric_name': 'demo.custom.gauge',
                'metric_value': random.uniform(10, 100),
                'metric_type': 'gauge',
                'tags': ['test:traffic_generator', 'type:gauge']
            },
            {
                'metric_name': 'demo.custom.counter',
                'metric_value': random.randint(1, 10),
                'metric_type': 'increment',
                'tags': ['test:traffic_generator', 'type:counter']
            },
            {
                'metric_name': 'demo.custom.histogram',
                'metric_value': random.uniform(0, 1000),
                'metric_type': 'histogram',
                'tags': ['test:traffic_generator', 'type:histogram']
            }
        ]

        for metric in metrics:
            self.make_request(
                'POST',
                '/metrics',
                f"カスタムメトリクス送信: {metric['metric_name']}",
                json=metric
            )
            time.sleep(0.3)

    def test_cache_operations(self):
        """キャッシュ操作をテスト"""
        print("\n🗑️  キャッシュ操作テスト")
        print("=" * 60)

        # キャッシュをクリア
        self.make_request('POST', '/cache/clear', 'キャッシュをクリア')
        time.sleep(0.5)

    def run_full_test(self, iterations: int = 1):
        """全テストを実行"""
        print("\n" + "=" * 60)
        print("🚀 Datadog ハンズオン - トラフィック生成スクリプト")
        print("=" * 60)

        for iteration in range(iterations):
            if iterations > 1:
                print(f"\n\n🔄 反復 {iteration + 1}/{iterations}")
                print("=" * 60)

            # 各種エンドポイントをテスト
            self.test_user_endpoints()
            self.test_order_endpoints()
            self.test_stats_endpoint()
            self.test_slow_endpoint()
            self.test_error_endpoint()
            self.test_custom_metrics()
            self.test_cache_operations()

            if iteration < iterations - 1:
                wait_time = 5
                print(f"\n⏳ {wait_time}秒待機中...")
                time.sleep(wait_time)

    def print_stats(self):
        """統計情報を表示"""
        print("\n\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        print(f"総リクエスト数:     {self.stats['total_requests']}")
        print(f"成功:              {self.stats['successful_requests']} ✅")
        print(f"失敗 (4xx/5xx):    {self.stats['failed_requests']} ⚠️")
        print(f"エラー:            {self.stats['errors']} ❌")

        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            print(f"成功率:            {success_rate:.1f}%")

        print("=" * 60)
        print("\n💡 Datadogダッシュボードで確認:")
        print("   - APM: https://app.datadoghq.com/apm/services")
        print("   - Logs: https://app.datadoghq.com/logs")
        print("   - Infrastructure: https://app.datadoghq.com/infrastructure")
        print("   - Metrics: https://app.datadoghq.com/metric/explorer")
        print("=" * 60 + "\n")

def main():
    """メイン関数"""
    # コマンドライン引数で反復回数を指定可能
    iterations = 1
    if len(sys.argv) > 1:
        try:
            iterations = int(sys.argv[1])
            if iterations < 1:
                iterations = 1
        except ValueError:
            print("⚠️  引数は正の整数である必要があります。デフォルト値（1）を使用します。")

    generator = TrafficGenerator()

    try:
        generator.run_full_test(iterations=iterations)
    except KeyboardInterrupt:
        print("\n\n⚠️  ユーザーによって中断されました")
    finally:
        generator.print_stats()

if __name__ == "__main__":
    main()
