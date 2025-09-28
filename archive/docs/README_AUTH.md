# バーコードバトラー認証システム セットアップガイド

## 🚀 セットアップ手順

### 1. データベース更新
```sql
-- Supabase SQL Editorで実行
-- ファイル: sql/add_mail_address_column.sql の内容を実行
-- ※ mail_addressカラムは既存のため、auth_user_idカラムのみ追加されます
```

### 1.1 現在のusersテーブル構造確認（推奨）
```sql
-- 既存のusersテーブル構造を確認
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
```

### 2. 必要なライブラリ確認
```bash
pip install streamlit supabase python-dotenv
```

### 3. 環境変数設定
`.env` ファイルに以下が設定されていることを確認:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
```

### 4. 認証システム起動
```bash
# メイン認証システム
streamlit run barcode_battler_auth.py

# テスト用（開発時）
streamlit run test_auth.py
```

## 🔧 主な機能

### BarcodeBattlerAuth クラス
- `sign_up(email, password, full_name)`: 新規ユーザー登録
- `sign_in(email, password)`: ログイン
- `sign_out()`: ログアウト
- `is_authenticated()`: 認証状態確認

### データベース連携
- **Supabase Auth**: パスワード管理・認証
- **usersテーブル**: ユーザー情報管理
  - `user_id`: UUID（自動生成）
  - `user_name`: ユーザー名
  - `mail_address`: メールアドレス
  - `auth_user_id`: Supabase認証ID（紐付け用）

## 🎯 将来の連携

### login.pyとの統合
1. `barcode_battler_auth.py`で認証処理
2. 認証成功後、`login.py`のメイン機能にリダイレクト
3. セッション状態（`st.session_state.user_data`）を共有

### 連携用コード例
```python
# メイン画面での認証チェック
if not auth.is_authenticated():
    st.error("ログインが必要です")
    st.stop()

# ユーザー情報取得
user_data = st.session_state.user_data
user_name = user_data['user_name']
user_id = user_data['user_id']
```

## 🔍 トラブルシューティング

### よくあるエラー
1. **"Supabase設定が見つかりません"**
   → `.env`ファイルの設定を確認

2. **"このメールアドレスは既に登録済みです"**
   → 正常な動作（重複登録防止）

3. **"メールアドレスまたはパスワードが正しくありません"**
   → 入力内容を確認、または未認証の可能性

### デバッグ用
```python
# セッション状態の確認
st.write("Session State:", st.session_state)
```