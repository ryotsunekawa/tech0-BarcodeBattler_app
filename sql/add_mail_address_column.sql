-- 既存usersテーブル（CSV形式）にSupabase認証連携カラムを追加
-- SQL EditorでSupabaseに実行してください

-- 現在のusersテーブル構造（CSV確認済み）:
-- user_id (UUID), mail_address (TEXT), user_name (TEXT), location (TEXT), created_at (TIMESTAMP)

-- Supabase認証システムとの連携用カラム追加
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_user_id UUID UNIQUE;

-- mail_addressにUNIQUE制約追加（認証用）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name LIKE '%mail_address%' 
        AND table_name = 'users'
        AND constraint_type = 'UNIQUE'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_mail_address_unique UNIQUE (mail_address);
    END IF;
END $$;

-- インデックス追加（検索性能向上）
CREATE INDEX IF NOT EXISTS idx_users_mail_address ON users(mail_address);
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);

-- 確認用クエリ
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;