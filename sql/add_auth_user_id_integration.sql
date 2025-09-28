-- 段階的なAuth UID統合SQL
-- 既存のuser_idを維持しつつ、auth_user_idで認証と紐付ける

-- 1. 一時的にRLSを無効化
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_operations DISABLE ROW LEVEL SECURITY;

-- 2. auth_user_idカラムを追加（既に存在する場合はスキップ）
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- 3. auth_user_idにUNIQUE制約を追加（重複防止）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'users_auth_user_id_unique'
        AND table_name = 'users'
        AND constraint_type = 'UNIQUE'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_auth_user_id_unique UNIQUE (auth_user_id);
    END IF;
END $$;

-- 4. インデックス追加（検索性能向上）
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);

-- 5. RLSポリシーを更新
-- 既存ポリシーを削除
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Users can insert own profile" ON users;
DROP POLICY IF EXISTS "Users can view own operations" ON user_operations;
DROP POLICY IF EXISTS "Users can insert own operations" ON user_operations;
DROP POLICY IF EXISTS "Users can update own operations" ON user_operations;

-- 新しいポリシー（auth_user_idベース）
CREATE POLICY "Auth users can view own profile" ON users
    FOR SELECT USING (
        auth.uid() = auth_user_id OR 
        auth.uid()::text = user_id::text  -- 既存データとの互換性
    );

CREATE POLICY "Auth users can update own profile" ON users  
    FOR UPDATE USING (
        auth.uid() = auth_user_id OR 
        auth.uid()::text = user_id::text
    );

CREATE POLICY "Auth users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = auth_user_id);

-- user_operationsテーブル用ポリシー
-- まず既存のuser_idから対応するauth_user_idを取得する関数ポリシー
CREATE POLICY "Auth users can view own operations" ON user_operations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.user_id = user_operations.user_id 
            AND users.auth_user_id = auth.uid()
        ) OR 
        auth.uid()::text = user_id::text  -- 既存データとの互換性
    );

CREATE POLICY "Auth users can insert own operations" ON user_operations
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.user_id = user_operations.user_id 
            AND users.auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Auth users can update own operations" ON user_operations
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.user_id = user_operations.user_id 
            AND users.auth_user_id = auth.uid()
        )
    );

-- 6. RLSを再有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_operations ENABLE ROW LEVEL SECURITY;

-- 7. 確認クエリ
SELECT 
    'Updated users table structure:' as info,
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 8. 既存データの確認
SELECT 
    COUNT(*) as total_users,
    COUNT(auth_user_id) as users_with_auth_id,
    COUNT(*) - COUNT(auth_user_id) as users_without_auth_id
FROM users;