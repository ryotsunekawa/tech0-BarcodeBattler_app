# Resend SMTP設定ガイド

## 1. Resendアカウント作成

1. https://resend.com にアクセス
2. 無料アカウント作成
3. メールアドレス確認

## 2. API Key取得

1. Resendダッシュボードにログイン
2. 左メニューから「API Keys」を選択
3. 「Create API Key」をクリック
4. 名前を入力（例：supabase-auth）
5. 「Full access」を選択
6. API Keyをコピー（re_xxxxxx形式）

## 3. ドメイン設定（推奨）

### オプションA: 独自ドメインを使用
1. 「Domains」セクションでドメイン追加
2. DNS設定でSPF/DKIMレコード追加

### オプションB: Resendのデフォルトドメインを使用
- そのまま使用可能（制限あり）
- 送信者アドレスは制限される

## 4. Supabaseでの設定

### Authentication > Settings > SMTP Settings

```
SMTP Host: smtp.resend.com
SMTP Port: 587
SMTP User: resend
SMTP Pass: [Your Resend API Key]
Sender email: noreply@yourdomain.com
Sender name: Your App Name
```

## 5. .envファイルへの追加

```env
# Resend SMTP設定
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxx
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=バーコードバトラー
```

## 6. 設定後の確認

1. Supabaseで設定を保存
2. 「Enable email confirmations」をONに戻す
3. テスト用新規登録でメール送信確認

## トラブルシューティング

### メールが届かない場合
1. 迷惑メールフォルダ確認
2. Resendダッシュボードでログ確認
3. ドメイン認証状態確認

### よくある問題
- 送信者メールアドレスが認証されていない
- DNS設定が完了していない
- API Keyの権限不足