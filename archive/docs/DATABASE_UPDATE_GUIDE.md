# データベーススキーマ更新手順

## 1. auth_user_id カラムの追加

### 手順:
1. Supabaseダッシュボードにログイン
2. 左メニューから「SQL Editor」を選択
3. `sql/add_auth_user_id_column.sql` の内容をコピー&ペースト
4. 「RUN」ボタンをクリックして実行

### 実行するSQL:
```sql
-- users テーブルに auth_user_id カラムを追加
-- Supabase Auth との連携用

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- auth_user_id にインデックスを追加（検索性能向上のため）
CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users(auth_user_id);
```

## 2. 認証システムの更新

SQL実行後、以下のファイルの一時的修正を元に戻す必要があります：

### `barcode_battler_auth.py` の修正箇所:

1. **sign_up関数**: 
   - `auth_user_id` フィールドを有効化
   
2. **sign_in関数**: 
   - `auth_user_id` による検索を有効化
   - 既存ユーザーとの紐付け機能を有効化

## 3. 確認方法

```sql
-- カラムが正しく追加されたか確認
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND table_schema = 'public'
ORDER BY ordinal_position;
```

## 4. 注意事項

- 既存のユーザーデータには `auth_user_id` が NULL になります
- 初回ログイン時に自動的に `auth_user_id` が設定される仕組みになっています
- カラム追加後は一時的なコメントアウトを解除してください