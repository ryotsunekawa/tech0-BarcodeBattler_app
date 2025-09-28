# メール確認問題の解決ガイド

## 問題: 確認メールが届かない

### 考えられる原因と解決方法

#### 1. Supabaseのメール設定が無効
**確認方法:**
- Supabaseダッシュボード > Authentication > Settings
- "Email Auth" セクションを確認

**設定項目:**
- ✅ **Enable email confirmations** → ONにする
- ✅ **Enable secure email change** → ONにする（推奨）
- ✅ **SMTP Settings** → 適切なメールプロバイダを設定

#### 2. SMTPプロバイダ未設定
**デフォルトの制限:**
- Supabaseの無料プランでは1時間に30通まで
- カスタムSMTPプロバイダーが推奨

**推奨プロバイダ:**
- SendGrid
- Mailgun
- AWS SES
- Resend

#### 3. 開発・テスト用の対処法

**A. メール確認を一時的に無効化**
```
Supabase Dashboard > Authentication > Settings
→ "Enable email confirmations" を OFF
```

**B. 開発用テストアプリを使用**
```bash
streamlit run auth_test_dev.py
```

**C. 手動でユーザーを確認状態にする（SQL）**
```sql
-- 特定ユーザーのメール確認を手動で有効化
UPDATE auth.users 
SET email_confirmed_at = NOW(), 
    confirmed_at = NOW() 
WHERE email = 'your-email@example.com';
```

## 本番環境での推奨設定

### 1. カスタムSMTPプロバイダーの設定
```
Supabase Dashboard > Settings > Auth > SMTP Settings
```

### 2. メールテンプレートのカスタマイズ
```
Supabase Dashboard > Authentication > Email Templates
```

### 3. ドメイン認証の設定
- SPF レコード設定
- DKIM 認証設定
- カスタムドメインの使用

## トラブルシューティング手順

1. **Supabase Authログを確認**
   - Dashboard > Logs > Auth logs

2. **メール送信ログを確認**
   - SMTPプロバイダーのダッシュボード確認

3. **迷惑メールフォルダを確認**
   - Gmail, Outlook等の迷惑メールフォルダ

4. **メールアドレスの形式確認**
   - 正しい形式かどうか確認

5. **開発用テストアプリで動作確認**
   ```bash
   streamlit run auth_test_dev.py
   ```

## 緊急対応（開発中）

メール確認機能を一時的に無効化して開発を継続:

1. Supabaseダッシュボードでメール確認を無効化
2. 既存ユーザーを削除
3. 新規登録を再実行
4. 正常にログインできることを確認