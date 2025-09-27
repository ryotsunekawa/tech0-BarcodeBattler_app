-- セキュリティ設定確認用SQL
-- Supabase SQL Editorで実行して現在の設定を確認

-- 1. Storage ポリシー一覧
SELECT 
    schemaname, 
    tablename, 
    policyname, 
    cmd as operation,
    CASE 
        WHEN policyname LIKE '%Demo%' THEN '🔴 デモ用（危険）'
        WHEN policyname LIKE '%Authenticated%' THEN '🟢 セキュア'
        WHEN policyname LIKE '%own%' THEN '🟢 セキュア'
        ELSE '⚪ その他'
    END as security_level
FROM pg_policies 
WHERE tablename = 'objects' AND schemaname = 'storage'
ORDER BY security_level DESC, policyname;

-- 2. バケット設定確認
SELECT 
    id,
    name,
    public as is_public,
    file_size_limit,
    allowed_mime_types,
    CASE 
        WHEN public = true THEN '⚠️ パブリック'
        ELSE '🔒 プライベート'
    END as access_type
FROM storage.buckets 
WHERE name = 'character-images';

-- 3. 現在の認証状態確認
SELECT 
    auth.uid() as current_user_id,
    auth.role() as current_role,
    CASE 
        WHEN auth.uid() IS NULL THEN '❌ 未認証'
        ELSE '✅ 認証済み'
    END as auth_status;