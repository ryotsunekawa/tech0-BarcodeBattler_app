-- 本番用セキュアStorageポリシー
-- 認証されたユーザーのみアクセス可能

-- 1. デモ用ポリシーを削除
DROP POLICY IF EXISTS "Demo: Anyone can upload to character-images" ON storage.objects;
DROP POLICY IF EXISTS "Demo: Anyone can view character-images" ON storage.objects;
DROP POLICY IF EXISTS "Demo: Anyone can update character-images" ON storage.objects;
DROP POLICY IF EXISTS "Demo: Anyone can delete character-images" ON storage.objects;

-- 2. セキュアなポリシーを作成

-- 認証済みユーザーのみアップロード可能
CREATE POLICY "Authenticated users can upload character images" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'character-images' AND 
    auth.role() = 'authenticated'
);

-- ユーザーは自分がアップロードした画像のみ閲覧可能
-- ファイルパスにユーザーIDを含める形式: /user_id/filename.jpg
CREATE POLICY "Users can view own character images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- ユーザーは自分がアップロードした画像のみ更新可能
CREATE POLICY "Users can update own character images" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (string_to_array(name, '/'))[1]
)
WITH CHECK (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- ユーザーは自分がアップロードした画像のみ削除可能
CREATE POLICY "Users can delete own character images" ON storage.objects
FOR DELETE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- 3. 管理者権限（管理者は全ての画像にアクセス可能）
-- 事前にadmin_usersテーブルが必要

CREATE POLICY "Admin can view all character images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'character-images' AND 
    EXISTS (
        SELECT 1 FROM admin_users au
        JOIN auth.users u ON au.email = u.email
        WHERE u.id = auth.uid() 
        AND au.is_active = true
        AND au.role IN ('admin', 'super_admin')
    )
);

CREATE POLICY "Admin can update all character images" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'character-images' AND 
    EXISTS (
        SELECT 1 FROM admin_users au
        JOIN auth.users u ON au.email = u.email
        WHERE u.id = auth.uid() 
        AND au.is_active = true
        AND au.role IN ('admin', 'super_admin')
    )
)
WITH CHECK (bucket_id = 'character-images');

CREATE POLICY "Admin can delete all character images" ON storage.objects
FOR DELETE USING (
    bucket_id = 'character-images' AND 
    EXISTS (
        SELECT 1 FROM admin_users au
        JOIN auth.users u ON au.email = u.email
        WHERE u.id = auth.uid() 
        AND au.is_active = true
        AND au.role IN ('admin', 'super_admin')
    )
);

-- 4. 確認クエリ
SELECT schemaname, tablename, policyname, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' AND schemaname = 'storage'
ORDER BY policyname;