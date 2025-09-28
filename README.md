# 令和版バーコードバトラー - 完全統合版

AIを活用したバーコードスキャンキャラクター生成アプリケーション

## � クイックスタート

### 必要な環境
- Python 3.8+
- Streamlit
- Supabase アカウント
- OpenAI API キー
- Stability AI API キー

### インストール手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd Supabase_try0.1
```

2. **仮想環境の作成と有効化**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

3. **依存パッケージのインストール**
```bash
pip install -r requirements.txt
```

4. **環境変数の設定**
`.env.example`を参考に`.env`ファイルを作成し、以下を設定：
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
STABILITY_API_KEY=your_stability_ai_api_key
```

5. **アプリケーションの起動**
```bash
cd login_based_integration
streamlit run login_full_auth_unified.py --server.port 8517
```

## 📁 プロジェクト構成

```
├── login_based_integration/          # メインアプリケーション
│   ├── login_full_auth_unified.py   # 統合版メインアプリ
│   ├── sql_full_auth_uid_integration.sql  # データベース設定
│   ├── RLS_FIX_QUERIES.sql         # RLSポリシー修正クエリ
│   ├── FULL_AUTH_UNIFIED_GUIDE.md  # 実装ガイド
│   ├── UPDATE_MEMO_画像保存機能.md   # 更新履歴
│   └── requirements.txt            # パッケージ要件
├── .env.example                     # 環境変数テンプレート
├── requirements.txt                 # ルートパッケージ要件
└── archive/                         # 過去のコード・ドキュメント
```

## 🎮 機能概要

### コア機能
- **バーコードスキャン** - 手動入力によるバーコード読み取り
- **AIキャラクター生成** - OpenAI + Stability AIによる自動キャラクター生成
- **ユーザー認証** - Supabase Authを使用した完全統合認証
- **キャラクター図鑑** - 生成したキャラクターの保存・表示
- **画像ストレージ** - Supabase Storageによる画像管理

### 技術特徴
- **完全Auth UID統合** - Supabase Authentication UIDとDatabase user_idの完全統一
- **RLS無効化** - シンプルで確実なデータアクセス
- **日本語対応** - ファイル名の安全な処理とUIの日本語化
- **レスポンシブUI** - Streamlitによる直感的なWebインターフェース

## 🛠 開発情報

### データベース構成
- **users テーブル** - ユーザープロフィール情報
- **user_operations テーブル** - キャラクター生成履歴
- **character-images バケット** - キャラクター画像ストレージ

### API統合
- **OpenAI GPT-3.5-turbo** - キャラクター設定生成
- **Stability AI SDXL** - 画像生成
- **Supabase** - 認証・データベース・ストレージ

## 📋 使い方

1. **アカウント作成/ログイン**
2. **バーコード入力** - 商品のJANコードを入力
3. **地域選択** - キャラクターの出身地を選択
4. **キャラクター生成** - AIが自動でキャラクターを生成
5. **図鑑保存** - 気に入ったキャラクターを図鑑に保存

## 🔧 トラブルシューティング

### よくある問題
- **画像アップロードエラー** → `RLS_FIX_QUERIES.sql`を実行
- **認証エラー** → `.env`ファイルの設定を確認
- **依存関係エラー** → `pip install -r requirements.txt`を再実行

### デバッグモード
アプリケーション内の「🔍 詳細情報」セクションで技術的な詳細を確認できます。

## 📚 ドキュメント

詳細なドキュメントは以下を参照：
- `login_based_integration/FULL_AUTH_UNIFIED_GUIDE.md` - 実装ガイド
- `login_based_integration/UPDATE_MEMO_画像保存機能.md` - 更新履歴
- `archive/docs/` - 過去の開発ドキュメント

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🔗 関連リンク

- [Supabase Documentation](https://supabase.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Stability AI API](https://platform.stability.ai/docs)
- [Streamlit Documentation](https://docs.streamlit.io)

## 📝 ファイル移動時の注意

- **ルートディレクトリでの実行が必要**: `.env` ファイルへのアクセスのため
- **サブディレクトリから実行する場合**: 
  ```bash
  # productionディレクトリから実行する場合の例
  cd production
  streamlit run secure_image_management.py --server.fileWatcherType none
  ```
  ただし、`.env` ファイルが見つからないエラーが発生する可能性あり

## 🎯 推奨使用パターン

1. **開発・テスト**: ルートディレクトリから `image_management_system.py` を実行
2. **本番使用**: SQL設定完了後、`production/secure_image_management.py` を実行
3. **機能確認**: 各機能を個別に `simple_barcode_scanner.py` 等で確認