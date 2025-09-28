# login(1).py ベース Auth統合版 セットアップガイド

## 📋 概要

元のlogin(1).pyファイルをベースに、段階的Auth UID統合機能を追加したバージョンです。
同じSupabaseデータベースを使用しながら、独立したディレクトリで実行できます。

## 🚀 セットアップ手順

### 1. 必要な環境準備

```bash
# 新しいディレクトリに移動
cd "c:\Users\gp02m\Tech0\Supabase_try0.1\login_based_integration"

# 仮想環境作成（オプション）
python -m venv venv
.\venv\Scripts\activate

# パッケージインストール
pip install -r requirements.txt
```

### 2. 環境変数設定

`.env`ファイルを編集して、APIキーを設定：

```env
# OpenAI API Key（必須）
OPENAI_API_KEY=sk-your-openai-api-key

# Stability AI API Key（必須）  
STABILITY_API_KEY=sk-your-stability-api-key

# その他は設定済み
```

### 3. データベース準備

**重要**: まず元のディレクトリでデータベース更新を実行してください：

```sql
-- 元ディレクトリのsql/add_auth_user_id_integration.sqlを実行
-- Supabase SQL Editorで実行
```

### 4. アプリケーション起動

```bash
# アプリケーション起動
streamlit run login_auth_integrated.py --server.port 8514
```

## 🔧 機能説明

### 元のlogin(1).pyから引き継いだ機能

- ✅ バーコードスキャン機能
- ✅ OpenAI + Stability AIによるキャラクター生成
- ✅ 都道府県選択
- ✅ 図鑑表示機能
- ✅ ユーザー認証システム

### 新たに追加された統合機能

- ✅ **段階的Auth UID統合**: 既存ユーザーとの互換性を保持
- ✅ **データベース連携**: キャラクターをSupabaseに保存
- ✅ **プロフィール管理**: auth_user_idによる適切な紐付け
- ✅ **セキュリティ向上**: RLS対応によるデータ保護

## 🎯 動作フロー

### 1. 新規ユーザー
```
1. アカウント作成 → Supabase Auth + usersテーブルにプロフィール作成
2. ログイン → 認証情報とプロフィールを取得
3. キャラ生成 → DB保存（user_id使用）
4. 図鑑表示 → DBから取得して表示
```

### 2. 既存ユーザー
```
1. ログイン → mail_addressで既存ユーザー検索
2. auth_user_id自動更新 → 認証との紐付け完了
3. 既存データアクセス → 過去のキャラクターも表示
4. 新規キャラ作成 → 統合されたシステムで保存
```

## 🔍 テスト項目

### 基本機能テスト
- [ ] 新規ユーザー登録
- [ ] ログイン・ログアウト
- [ ] バーコードスキャン
- [ ] キャラクター生成（OpenAI + Stability AI）
- [ ] キャラクター保存
- [ ] 図鑑表示

### 統合機能テスト  
- [ ] 既存ユーザー（CSV）でのログイン
- [ ] auth_user_idの自動設定
- [ ] 既存キャラクターの表示
- [ ] 新規キャラクター保存
- [ ] 他ユーザーデータへのアクセス不可確認

## 🔧 設定ファイル

### .env設定例
```env
SUPABASE_URL=https://lkhbqezbsjojrlmhnuev.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=sk-your-openai-key  
STABILITY_API_KEY=sk-your-stability-key
```

### 起動コマンド
```bash
streamlit run login_auth_integrated.py --server.port 8514
```

## ⚡ 主な違い（元のlogin(1).pyとの比較）

| 項目 | 元のlogin(1).py | Auth統合版 |
|------|-----------------|------------|
| 認証 | 基本的なSupabase Auth | Auth UID統合 |
| データ保存 | セッション状態のみ | データベース永続化 |
| ユーザー管理 | 認証情報のみ | プロフィール + 既存ユーザー対応 |
| セキュリティ | 基本レベル | RLS対応 |
| 図鑑機能 | セッション内のみ | DB連携で永続化 |

## 🚨 注意事項

### セキュリティ
- API キーを`.env`ファイルで管理
- `.env`ファイルをGitにコミットしない
- 本番環境では適切な環境変数管理

### 互換性
- 元のSupabaseデータベースと完全互換
- 既存ユーザーデータを保護
- 段階的な移行をサポート

### パフォーマンス
- 画像生成にはOpenAI + Stability AIのAPIが必要
- API使用料が発生する可能性があります

## 📞 トラブルシューティング

### よくある問題

#### 1. pyzbarのDLLエラー
```bash
# 解決方法: 依存関係を再インストール
pip uninstall pyzbar
pip install pyzbar
```

#### 2. OpenAI APIエラー
```
原因: APIキーが未設定または無効
解決: .envファイルでOPENAI_API_KEYを正しく設定
```

#### 3. Stability API エラー
```  
原因: APIキーが未設定または残高不足
解決: .envファイルでSTABILITY_API_KEYを正しく設定
```

#### 4. データベースアクセスエラー
```
原因: データベース更新SQLが未実行
解決: sql/add_auth_user_id_integration.sqlを実行
```

## 🎉 使用方法

1. **起動**: `streamlit run login_auth_integrated.py --server.port 8514`
2. **アカウント**: 新規登録またはログイン
3. **スキャン**: バーコードを撮影または手入力
4. **生成**: 都道府県を選択してキャラクター生成
5. **保存**: 気に入ったキャラクターをデータベースに保存
6. **図鑑**: 保存したキャラクターを確認

この統合版により、元のlogin(1).pyの機能を保持しながら、データベース連携と認証統合の恩恵を受けることができます。