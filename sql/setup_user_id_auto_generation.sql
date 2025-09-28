-- usersテーブルのuser_id自動生成設定

-- 方法1: UUIDを使用（現在の実装）
-- user_idをUUID型にして、デフォルト値で自動生成
ALTER TABLE users 
ALTER COLUMN user_id SET DEFAULT gen_random_uuid();

-- 方法2: シーケンス番号を使用（連番）
-- CREATE SEQUENCE IF NOT EXISTS user_id_seq;
-- ALTER TABLE users 
-- ALTER COLUMN user_id SET DEFAULT nextval('user_id_seq');

-- 現在のテーブル構造確認
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;