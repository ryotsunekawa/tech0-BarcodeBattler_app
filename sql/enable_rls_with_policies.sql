-- RLS (Row Level Security) を再有効化して適切なポリシーを設定

-- 1. RLSを再有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_operations ENABLE ROW LEVEL SECURITY;

-- 2. 基本的なRLSポリシーを設定

-- ユーザーテーブル用ポリシー
-- 認証されたユーザーは自分のレコードのみアクセス可能
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own profile" ON users  
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- 操作ログテーブル用ポリシー  
-- 認証されたユーザーは自分の操作ログのみアクセス可能
CREATE POLICY "Users can view own operations" ON user_operations
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own operations" ON user_operations
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own operations" ON user_operations
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- 3. 開発中の一時的な管理者アクセス（オプション）
-- 注意: 本番環境では削除してください

-- 管理者用ポリシー（全データ閲覧可能）
CREATE POLICY "Admin full access users" ON users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE auth.users.id = auth.uid() 
            AND auth.users.email = 'admin@yourdomain.com'  -- 管理者メールに変更
        )
    );

CREATE POLICY "Admin full access operations" ON user_operations  
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM auth.users
            WHERE auth.users.id = auth.uid()
            AND auth.users.email = 'admin@yourdomain.com'  -- 管理者メールに変更
        )
    );

-- 4. 確認用クエリ
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'user_operations');

-- 5. RLS状態確認
SELECT schemaname, tablename, rowsecurity, forcerowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'user_operations');