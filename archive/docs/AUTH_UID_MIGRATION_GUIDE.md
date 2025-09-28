# Auth UID統一移行ガイド

## 概要
現在のシステムでは、Supabase AuthenticationのUIDとデータベースのusersテーブルのuser_idが別々になっています。
これを統一することで、より安全で効率的なデータ管理が可能になります。

## 現在の構造
```
Supabase Auth: user_a_auth_uid, user_b_auth_uid, ...
DB users: user_1_db_id, user_2_db_id, ...
```

## 修正後の構造
```
Supabase Auth: user_a_auth_uid, user_b_auth_uid, ...
DB users: user_a_auth_uid, user_b_auth_uid, ... (同一)
```

## 移行手順

### 1. データベース移行の実行

**⚠️ 重要: 実行前に必ずデータをバックアップしてください**

1. Supabaseダッシュボードにアクセス
2. SQL Editorを開く
3. `sql/migrate_to_auth_uid.sql`の内容を実行

### 2. 既存データの手動移行

現在のusersテーブルのデータを新しい構造に移行する必要があります。

#### 手順A: 既存ユーザーのAuth登録

既存のメールアドレスでSupabase Authにユーザーを作成し、そのUIDを使用してusersテーブルに再挿入します。

```sql
-- 例: 既存データを新しい構造に移行
-- 1. まずSupabase Authでユーザーを作成
-- 2. 作成されたUIDを使用してデータを移行

INSERT INTO users (user_id, mail_address, user_name, location, created_at)
VALUES 
('auth_uid_from_supabase_auth', 'tanaka@example.com', '田中太郎', '東京都', NOW());
```

#### 手順B: 操作ログの移行

user_operationsテーブルのuser_idも新しいAuth UIDに更新する必要があります。

### 3. アプリケーションコードの更新

移行後は以下のファイルを使用してください：

- `auth_uid_unified_app.py`: Auth UID統一後の認証システム

### 4. RLSポリシーの更新

移行後のRLSポリシーでは、`auth.uid()`と`user_id`が直接比較できます：

```sql
-- 従来（文字列変換が必要）
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- 修正後（直接比較）
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = user_id);
```

## メリット

### 1. セキュリティの向上
- Auth UIDとDB UIDの一致により、データの整合性が保証される
- RLSポリシーがより直感的で安全になる

### 2. パフォーマンスの向上
- 文字列変換（::text）が不要になり、クエリが高速化
- インデックスの効率性が向上

### 3. 開発効率の向上
- 認証とデータの紐付けが簡単になる
- バグの発生リスクが減少

## 注意事項

### 移行時の注意点

1. **データバックアップ**: 移行前に必ずすべてのデータをバックアップ
2. **ダウンタイム**: 移行中はアプリケーションが一時的に利用不可
3. **テスト環境**: 本番環境での実行前にテスト環境で十分検証

### 既存ユーザーへの対応

既存ユーザーには以下の対応が必要です：

1. **再登録**: 新しいシステムでアカウントを再作成
2. **データ移行**: 必要に応じて既存データを新しいアカウントに移行

## 実装例

### 新規ユーザー登録
```python
def sign_up(self, email: str, password: str, user_name: str):
    # 1. Auth登録
    auth_response = self.supabase.auth.sign_up({
        "email": email,
        "password": password
    })
    
    # 2. プロフィール作成（AuthのUIDを使用）
    if auth_response.user:
        profile_data = {
            "user_id": auth_response.user.id,  # AuthのUIDをそのまま使用
            "mail_address": email,
            "user_name": user_name
        }
        self.supabase.table('users').insert(profile_data).execute()
```

### キャラクター保存
```python
def save_character(self, character_data: dict):
    current_user = self.supabase.auth.get_user()
    if current_user.user:
        character_data["user_id"] = current_user.user.id  # AuthのUIDを直接使用
        return self.supabase.table('user_operations').insert(character_data).execute()
```

## 移行後の検証

移行完了後、以下を確認してください：

1. **データ整合性**: すべてのuser_idがAuth UIDと一致しているか
2. **RLSポリシー**: 適切にアクセス制御が機能しているか
3. **アプリケーション**: すべての機能が正常に動作するか

## ロールバック手順

問題が発生した場合のロールバック：

```sql
-- バックアップテーブルから復元
DROP TABLE users;
DROP TABLE user_operations;

ALTER TABLE users_backup RENAME TO users;
ALTER TABLE user_operations_backup RENAME TO user_operations;

-- 外部キー制約の復元
ALTER TABLE user_operations 
ADD CONSTRAINT user_operations_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(user_id);
```

## サポート

移行に関する質問や問題が発生した場合は、開発チームにお問い合わせください。