# Supabase認証設定の確認・修正ガイド

## 問題: "Invalid login credentials" エラー

### 原因
1. **メール確認が必要**: 新規登録後、メール確認が完了していない
2. **認証設定**: Supabaseのメール確認設定が有効になっている
3. **パスワード不一致**: 登録時とログイン時のパスワードが異なる

### 解決方法

#### 1. Supabaseダッシュボードでメール確認を無効化

1. Supabaseダッシュボードにログイン
2. 左メニューから「Authentication」を選択
3. 「Settings」タブをクリック
4. 「Email Auth」セクションで以下を設定:
   - **「Enable email confirmations」をOFF**に設定
   - **「Enable secure email change」をOFF**に設定（推奨）

#### 2. テスト用設定

```sql
-- SQL Editorで実行（オプション）
-- 既存ユーザーのemail_confirmedを強制的にtrueに設定
UPDATE auth.users 
SET email_confirmed_at = NOW(), 
    confirmed_at = NOW() 
WHERE email_confirmed_at IS NULL;
```

#### 3. 実行手順

1. Supabaseダッシュボードで設定変更
2. 既存のテストユーザーを削除
3. 新規登録を再実行
4. ログインテスト

### 注意事項

- 本番環境ではメール確認を有効にしてください
- テスト環境では無効化して開発を効率化
- 設定変更後は既存ユーザーの再登録が必要な場合があります