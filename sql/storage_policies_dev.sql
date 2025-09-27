-- 開発用の簡略化されたStorage設定
-- SQL Editor で実行してください

-- 1. character-imagesバケットを作成
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'character-images',
    'character-images', 
    true,
    52428800, -- 50MB
    '{"image/jpeg","image/png","image/gif","image/webp"}'
)
ON CONFLICT (id) DO NOTHING;

-- 2. 開発用の簡単なRLSポリシー（本番前に変更）

-- 認証済みユーザーは画像アップロード可能
CREATE POLICY "Dev: Users can upload character images" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'character-images' AND 
    auth.role() = 'authenticated'
);

-- 認証済みユーザーは自分の画像のみ読取可能
CREATE POLICY "Dev: Users can view own character images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- 開発者のみ全画像アクセス可能（メールアドレス直接指定）
CREATE POLICY "Dev: Developer can view all character images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'character-images' AND 
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE auth.users.id = auth.uid() 
        AND auth.users.email IN (
            'gp02m@example.com',     -- あなたのメールアドレスに変更してください
            'developer@company.com'   -- 必要に応じて追加
        )
    )
);

-- ユーザーは自分の画像のみ更新・削除可能
CREATE POLICY "Dev: Users can update own character images" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Dev: Users can delete own character images" ON storage.objects
FOR DELETE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- 3. user_operationsテーブルの開発用ポリシー

-- ユーザーは自分の操作ログのみ閲覧可能
CREATE POLICY "Dev: Users can view own operations" ON user_operations
FOR SELECT USING (auth.uid()::text = user_id::text);

-- 開発者は全操作ログ閲覧可能
CREATE POLICY "Dev: Developer can view all operations" ON user_operations
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM auth.users 
        WHERE auth.users.id = auth.uid() 
        AND auth.users.email IN (
            'gp02m@example.com',     -- あなたのメールアドレスに変更してください
            'developer@company.com'   -- 必要に応じて追加
        )
    )
);

-- 4. 確認クエリ
SELECT * FROM storage.buckets WHERE name = 'character-images';
SELECT policyname, cmd FROM pg_policies 
WHERE schemaname = 'storage' AND tablename = 'objects'
AND policyname LIKE 'Dev:%';