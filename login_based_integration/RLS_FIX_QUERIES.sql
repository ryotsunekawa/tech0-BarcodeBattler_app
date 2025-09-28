-- 🔧 RLS問題修正用SQLクエリ集

-- ==========================================
-- 1. 緊急時：RLSを完全無効化（すぐにテストしたい場合）
-- ==========================================

-- user_operationsテーブルのRLSを無効化
ALTER TABLE user_operations DISABLE ROW LEVEL SECURITY;

-- usersテーブルのRLSも無効化（必要に応じて）
ALTER TABLE users DISABLE ROW LEVEL SECURITY;


-- ==========================================
-- 2. セキュリティ保持：適切なRLSポリシー設定
-- ==========================================

-- まず既存のポリシーをすべて削除
DROP POLICY IF EXISTS "Users can insert their own character data" ON user_operations;
DROP POLICY IF EXISTS "Users can view their own character data" ON user_operations;
DROP POLICY IF EXISTS "Users can update their own character data" ON user_operations;
DROP POLICY IF EXISTS "Users can delete their own character data" ON user_operations;
DROP POLICY IF EXISTS "Enable insert for users based on user_id" ON user_operations;
DROP POLICY IF EXISTS "Enable read access for all users" ON user_operations;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON user_operations;

-- RLSを有効化
ALTER TABLE user_operations ENABLE ROW LEVEL SECURITY;

-- 新しいポリシーを作成（Auth UID統一版対応）
CREATE POLICY "Enable insert for authenticated users" 
ON user_operations FOR INSERT 
TO authenticated
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Enable select for own data" 
ON user_operations FOR SELECT 
TO authenticated
USING (auth.uid()::text = user_id);

CREATE POLICY "Enable update for own data" 
ON user_operations FOR UPDATE 
TO authenticated
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Enable delete for own data" 
ON user_operations FOR DELETE 
TO authenticated
USING (auth.uid()::text = user_id);


-- ==========================================
-- 3. usersテーブルのRLSポリシー（必要に応じて）
-- ==========================================

-- 既存のポリシー削除
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can insert own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;

-- RLS有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 新しいポリシー作成
CREATE POLICY "Enable insert for authenticated users" 
ON users FOR INSERT 
TO authenticated
WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Enable select for own profile" 
ON users FOR SELECT 
TO authenticated
USING (auth.uid()::text = user_id);

CREATE POLICY "Enable update for own profile" 
ON users FOR UPDATE 
TO authenticated
USING (auth.uid()::text = user_id)
WITH CHECK (auth.uid()::text = user_id);


-- ==========================================
-- 4. デバッグ用：現在のポリシー確認
-- ==========================================

-- user_operationsテーブルのポリシー一覧表示
SELECT 
    schemaname,
    tablename, 
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'user_operations';

-- usersテーブルのポリシー一覧表示
SELECT 
    schemaname,
    tablename, 
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'users';


-- ==========================================
-- 5. テーブル情報確認
-- ==========================================

-- RLS有効状態確認
SELECT 
    schemaname, 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE tablename IN ('users', 'user_operations');

-- テーブル構造確認
\d users
\d user_operations


-- ==========================================
-- 使用手順:
-- 1. まず「1. 緊急時」のクエリでRLSを無効化してテスト
-- 2. 動作確認後、「2. セキュリティ保持」で適切なポリシー設定
-- 3. 「4. デバッグ用」でポリシーが正しく設定されているか確認
-- ==========================================