-- RLS（Row Level Security）を一時的に無効化してダミーデータを挿入
-- Supabase SQL Editor で実行してください

-- 1. RLSを一時的に無効化
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_operations DISABLE ROW LEVEL SECURITY;

-- 2. ダミーユーザーデータ挿入
INSERT INTO users (mail_address, user_name, location) VALUES
('tanaka@example.com', '田中太郎', '東京都'),
('sato@example.com', '佐藤花子', '大阪府'),
('yamada@example.com', '山田一郎', '愛知県'),
('suzuki@example.com', '鈴木美咲', '福岡県'),
('watanabe@example.com', '渡辺健司', '北海道');

-- 3. ダミー操作ログデータ挿入
-- まず、ユーザーIDを確認
-- SELECT user_id, user_name FROM users;

-- ユーザーIDを実際の値に置き換えてください（以下は例）
INSERT INTO user_operations (user_id, code_number, item_name, character_img_url, character_name, character_parameter) VALUES
(
    (SELECT user_id FROM users WHERE mail_address = 'tanaka@example.com'),
    '4901480072968',
    'コクヨS&T キャンパスノート（特殊罫） ノ-201WN',
    'https://example.com/characters/notemaster.png',
    'ノートマスター',
    '{"attack": 45, "defense": 80, "speed": 35, "magic": 90, "element": "知識", "rarity": "レア", "skills": ["記憶強化", "集中力アップ", "整理術"]}'
),
(
    (SELECT user_id FROM users WHERE mail_address = 'sato@example.com'),
    '4902370517859',
    'ペプシコーラ 500ml',
    'https://example.com/characters/blizfighter.png',
    'ブリズファイター',
    '{"attack": 75, "defense": 40, "speed": 85, "magic": 30, "element": "炭酸", "rarity": "コモン", "skills": ["瞬発力", "リフレッシュ", "エナジーバースト"]}'
),
(
    (SELECT user_id FROM users WHERE mail_address = 'yamada@example.com'),
    '4987176014443',
    '明治チョコレート効果カカオ72%',
    'https://example.com/characters/darkcacaoknight.png',
    'ダークカカオナイト',
    '{"attack": 60, "defense": 70, "speed": 50, "magic": 85, "element": "苦味", "rarity": "エピック", "skills": ["集中力", "抗酸化", "リラックス"]}'
),
(
    (SELECT user_id FROM users WHERE mail_address = 'suzuki@example.com'),
    '4901301013717',
    'キリン午後の紅茶 ストレートティー',
    'https://example.com/characters/teamagician.png',
    'ティーマジシャン',
    '{"attack": 40, "defense": 60, "speed": 70, "magic": 80, "element": "紅茶", "rarity": "レア", "skills": ["癒し", "優雅", "アフタヌーンパワー"]}'
),
(
    (SELECT user_id FROM users WHERE mail_address = 'watanabe@example.com'),
    '4549741511278',
    'セブンプレミアム おにぎり 鮭',
    'https://example.com/characters/salmonfighter.png',
    'サーモンファイター',
    '{"attack": 65, "defense": 75, "speed": 55, "magic": 45, "element": "和食", "rarity": "アンコモン", "skills": ["満腹感", "栄養補給", "日本の心"]}'
);

-- 4. 追加の操作ログ（同じユーザーが複数回使用）
INSERT INTO user_operations (user_id, code_number, item_name, character_img_url, character_name, character_parameter) VALUES
(
    (SELECT user_id FROM users WHERE mail_address = 'tanaka@example.com'),
    '4902370517859',
    'ペプシコーラ 500ml',
    'https://example.com/characters/blizfighter.png',
    'ブリズファイター',
    '{"attack": 75, "defense": 40, "speed": 85, "magic": 30, "element": "炭酸", "rarity": "コモン", "skills": ["瞬発力", "リフレッシュ", "エナジーバースト"]}'
),
(
    (SELECT user_id FROM users WHERE mail_address = 'sato@example.com'),
    '4987176014443',
    '明治チョコレート効果カカオ72%',
    'https://example.com/characters/darkcacaoknight.png',
    'ダークカカオナイト',
    '{"attack": 60, "defense": 70, "speed": 50, "magic": 85, "element": "苦味", "rarity": "エピック", "skills": ["集中力", "抗酸化", "リラックス"]}'
);

-- 5. データ確認
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as operation_count FROM user_operations;

-- 6. 最新の操作ログを表示
SELECT 
    u.user_name,
    uo.item_name,
    uo.character_name,
    uo.created_at
FROM user_operations uo
JOIN users u ON uo.user_id = u.user_id
ORDER BY uo.created_at DESC
LIMIT 5;

-- 7. RLSを再度有効化（セキュリティのため）
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_operations ENABLE ROW LEVEL SECURITY;

-- 8. 基本的なRLSポリシー設定（例）
-- ユーザーは自分のデータのみ読み書き可能
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage own operations" ON user_operations
    FOR ALL USING (auth.uid()::text = user_id::text);