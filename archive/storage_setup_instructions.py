"""
Supabase Storage設定手順

1. Supabaseダッシュボード > Storage に移動
2. "Create a new bucket" をクリック
3. バケット設定:
   - Bucket name: character-images
   - Public bucket: ON (公開アクセス可能)
   - File size limit: 50MB (必要に応じて調整)
   - Allowed MIME types: image/jpeg, image/png, image/gif, image/webp

4. RLS (Row Level Security) ポリシー設定:
   - 画像アップロード: 認証済みユーザーのみ
   - 画像読取: 誰でも可能（公開）

SQL Editor で実行するポリシー:

-- Storageオブジェクト用のRLSポリシー
-- 認証済みユーザーは画像アップロード可能
INSERT INTO storage.buckets (id, name, public) VALUES ('character-images', 'character-images', true);

-- アップロードポリシー（認証済みユーザーのみ）
CREATE POLICY "Authenticated users can upload character images" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'character-images' AND 
    auth.role() = 'authenticated'
);

-- 読取ポリシー（誰でも可能）
CREATE POLICY "Public read access for character images" ON storage.objects
FOR SELECT USING (bucket_id = 'character-images');

-- 更新・削除ポリシー（所有者のみ）
CREATE POLICY "Users can update own character images" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete own character images" ON storage.objects
FOR DELETE USING (
    bucket_id = 'character-images' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);
"""