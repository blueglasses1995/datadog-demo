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
    amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- サンプルデータ: ユーザー
INSERT INTO users (name, email) VALUES
    ('田中太郎', 'tanaka@example.com'),
    ('佐藤花子', 'sato@example.com'),
    ('鈴木一郎', 'suzuki@example.com'),
    ('高橋美咲', 'takahashi@example.com'),
    ('渡辺健太', 'watanabe@example.com'),
    ('伊藤彩', 'ito@example.com'),
    ('山本大輔', 'yamamoto@example.com'),
    ('中村さくら', 'nakamura@example.com'),
    ('小林健', 'kobayashi@example.com'),
    ('加藤優子', 'kato@example.com')
ON CONFLICT (email) DO NOTHING;

-- サンプルデータ: 注文
INSERT INTO orders (user_id, product_name, amount) VALUES
    (1, 'ノートパソコン', 128000.00),
    (1, 'マウス', 2500.00),
    (2, 'キーボード', 8900.00),
    (3, 'モニター', 35000.00),
    (2, 'Webカメラ', 7800.00),
    (4, 'ヘッドセット', 12000.00),
    (5, 'USBメモリ 64GB', 1800.00),
    (3, '外付けHDD 2TB', 9800.00),
    (6, 'HDMIケーブル', 1200.00),
    (7, 'スマートフォン', 89000.00),
    (4, 'タブレット', 45000.00),
    (8, 'ワイヤレスイヤホン', 15800.00),
    (9, 'スマートウォッチ', 32000.00),
    (5, 'モバイルバッテリー', 3500.00),
    (10, 'USB-Cハブ', 5600.00),
    (6, 'Bluetoothスピーカー', 7200.00),
    (7, 'デスクライト', 4800.00),
    (8, 'ゲーミングチェア', 38000.00),
    (9, 'Webデザイン書籍', 3200.00),
    (10, 'プログラミング入門書', 2800.00);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
