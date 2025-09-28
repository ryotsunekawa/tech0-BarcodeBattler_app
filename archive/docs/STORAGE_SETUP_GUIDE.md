"""
Supabase Storage設定ガイド

DB連携図鑑機能を動作させるために必要なStorage設定手順
"""

## 🛠️ Supabase Storage設定手順

### 1. Supabaseダッシュボードにアクセス
- https://supabase.com/dashboard
- プロジェクトを選択

### 2. Storageに移動
- 左サイドバーから「Storage」をクリック

### 3. バケットの作成
- 「Create Bucket」ボタンをクリック
- バケット名: `character-images`
- Public bucket: ✅ チェック（公開アクセス許可）
- 「Create Bucket」をクリック

### 4. バケットポリシーの確認
作成後、以下のポリシーが自動設定されているか確認：

**SELECT Policy (読み取り):**
```sql
CREATE POLICY "Public Access" ON storage.objects FOR SELECT TO public USING (bucket_id = 'character-images');
```

**INSERT Policy (書き込み - 認証ユーザーのみ):**
```sql
CREATE POLICY "Authenticated users can upload" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'character-images');
```

### 5. 設定確認方法
- Storage > character-images バケット内に移動
- 「Settings」タブをクリック
- Public access が有効になっていることを確認

## ✅ 設定完了後の確認項目

1. **バケット作成完了**
   - `character-images` バケットが存在する
   - Public access が有効

2. **アクセス権限**
   - 認証ユーザーがファイルアップロード可能
   - 全ユーザーがファイル閲覧可能

3. **URL構造確認**
   ```
   https://[project-id].supabase.co/storage/v1/object/public/character-images/[file-path]
   ```

## 🚨 トラブルシューティング

### バケットが作成できない場合
- プロジェクトの権限を確認
- 別の名前でバケットを作成してコード内のbucket_nameを変更

### 画像がアップロードできない場合
- ユーザーが認証済みか確認
- Storage > Policies でINSERTポリシーが設定されているか確認

### 画像が表示されない場合
- Public accessが有効か確認
- URLが正しく構築されているか確認
- ブラウザの開発者ツールでネットワークエラーを確認

## 📋 次のステップ

設定完了後：
1. `login_db_ready.py` を実行
2. 認証システムでログイン
3. バーコードスキャンでキャラクター生成
4. 「図鑑に保存する」をテスト
5. 図鑑画面で保存されたキャラクター確認