-- デモ用の一時的なStorageポリシー（開発・テスト用）
-- 本番環境では認証必須に戻してください

-- 既存のポリシーを一時的に削除
DROP POLICY IF EXISTS "Authenticated users can upload character images" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own character images" ON storage.objects;
DROP POLICY IF EXISTS "Admin can view all character images" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own character images" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own character images" ON storage.objects;

-- デモ用：誰でもアップロード・閲覧可能（開発・テスト用）
CREATE POLICY "Demo: Anyone can upload to character-images" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'character-images');

CREATE POLICY "Demo: Anyone can view character-images" ON storage.objects
FOR SELECT USING (bucket_id = 'character-images');

CREATE POLICY "Demo: Anyone can update character-images" ON storage.objects
FOR UPDATE USING (bucket_id = 'character-images')
WITH CHECK (bucket_id = 'character-images');

CREATE POLICY "Demo: Anyone can delete character-images" ON storage.objects
FOR DELETE USING (bucket_id = 'character-images');

-- 確認用
SELECT schemaname, tablename, policyname, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' AND schemaname = 'storage';