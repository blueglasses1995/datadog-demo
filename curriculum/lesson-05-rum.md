# レッスン5: RUM（Real User Monitoring）

## 📋 レッスン概要

**所要時間:** 90分 | **難易度:** 中級 | **前提:** レッスン1-4完了、RUM設定済み

## 🎯 学習目標

- [ ] RUMの基礎概念を理解できる
- [ ] セッション再生を活用できる
- [ ] Core Web Vitalsを監視できる
- [ ] ユーザーアクションをトラッキングできる
- [ ] フロントエンドエラーを分析できる

## 📚 主要トピック

### 1. RUM の基礎

#### RUM とは
フロントエンドのユーザー体験を実際のユーザーデータで監視：
- ページロード時間
- ユーザーアクション（クリック、入力など）
- JavaScriptエラー
- ネットワークリクエスト
- リソース読み込み

#### RUM セッション
```
UX Monitoring → Sessions
```

**セッションに含まれる情報:**
- ページビュー
- ユーザーアクション
- エラー
- リソース（JS, CSS, 画像など）
- ネットワークリクエスト

---

### 2. セッション再生

```
Sessions → 任意のセッション → Session Replay
```

**機能:**
- ユーザーの操作を動画のように再生
- DOM変更を記録
- クリック、スクロール、入力を可視化

**プライバシー設定:**
```javascript
defaultPrivacyLevel: 'mask-user-input'  // 入力内容をマスク
```

#### 実習: セッション再生
1. Webアプリを操作（ユーザー一覧 → 詳細 → 注文タブ）
2. Sessions でセッションを見つける
3. Session Replay で操作を再生
4. エラーが発生した瞬間を確認

---

### 3. Core Web Vitals

```
UX Monitoring → Performance
```

#### 主要指標

| 指標 | 説明 | 目標値 |
|------|------|--------|
| **LCP** (Largest Contentful Paint) | 最大コンテンツの描画 | < 2.5秒 |
| **FID** (First Input Delay) | 最初の入力までの遅延 | < 100ms |
| **CLS** (Cumulative Layout Shift) | レイアウトのずれ | < 0.1 |

#### パフォーマンス監視
- Page Load Time
- Time to First Byte (TTFB)
- DOM Content Loaded
- Load Event

#### 実習: パフォーマンス最適化
1. Performance Overview でLCP, FID, CLSを確認
2. 目標値と比較
3. 遅いページを特定
4. ボトルネックを分析（画像？JS？APIレスポンス？）

---

### 4. ユーザーアクション

```
UX Monitoring → User Actions
```

**自動トラッキング:**
- クリック
- タップ
- スクロール
- ページ遷移

**カスタムアクション:**
```javascript
import { datadogRum } from '@datadog/browser-rum';

datadogRum.addAction('button_click', {
  button_name: 'fetch_users',
  user_role: 'admin'
});
```

#### 実習: ユーザー行動分析
1. 最も使用されているボタンを特定
2. ユーザーフローを分析
3. 離脱ポイントを特定

---

### 5. フロントエンドエラー

```
UX Monitoring → Errors
```

**エラーの種類:**
- JavaScript エラー
- ネットワークエラー
- コンソールエラー

#### 実習: エラー分析
1. 「エラー発生」ボタンをクリック
2. RUM → Errors でエラーを確認
3. スタックトレースを確認
4. 影響を受けたユーザー数を確認
5. セッション再生でエラー発生時の状況を確認

---

### 6. APMとの統合

#### バックエンドとフロントエンドの相関

RUMとAPMを連携：
```javascript
// API リクエスト
const response = await axios.get('/api/users');
```

**Datadogで確認:**
1. RUM でユーザーアクションを確認
2. "Trace" タブでバックエンドのトレースを表示
3. フロントエンドからバックエンドまでの完全な追跡

#### エンドツーエンドの可視化
```
ユーザー操作
   ↓ (RUM)
ブラウザでAPIリクエスト
   ↓ (Trace)
Nginx
   ↓
Backend API
   ↓
PostgreSQL
```

---

### 7. 実習課題

#### 課題1: ユーザー体験最適化（30分）
1. Core Web Vitalsで課題を特定
2. ページロード時間が遅い原因を分析
3. 最適化案を作成：
   - 画像最適化
   - コード分割
   - キャッシュ活用

#### 課題2: エラー影響分析（25分）
1. 過去24時間のエラーを集計
2. エラーごとの影響ユーザー数を確認
3. 優先度を決定（影響度 × 頻度）
4. 修正計画を作成

#### 課題3: コンバージョンファネル分析（25分）
1. ユーザーフローを定義：
   - トップページ → ユーザー一覧 → 詳細 → 注文
2. 各ステップの離脱率を計算
3. ボトルネックを特定
4. 改善提案

---

## 📚 参考資料

- [RUM Documentation](https://docs.datadoghq.com/ja/real_user_monitoring/)
- [Session Replay](https://docs.datadoghq.com/ja/real_user_monitoring/session_replay/)
- [Core Web Vitals](https://web.dev/vitals/)
- [RUM Best Practices](https://docs.datadoghq.com/ja/real_user_monitoring/guide/)
