"""
Supabase認証設定の無効化手順

メール確認機能を完全に無効化するためのSupabaseダッシュボード設定手順です。
"""

# Supabaseダッシュボードでの設定変更手順

## 1. Supabaseダッシュボードにアクセス
- https://supabase.com/dashboard
- プロジェクトを選択

## 2. Authentication設定に移動
- 左メニューから「Authentication」をクリック
- 「Settings」をクリック

## 3. メール確認を無効化
- 「Email Auth」セクションで以下を設定：
  * Enable email confirmations: OFF (無効化)
  * Enable secure email change: OFF (無効化)

## 4. 設定を保存
- 「Update settings」をクリック

## 5. 既存ユーザーの確認状態を修正（必要に応じて）
- Authentication > Users で該当ユーザーを確認
- email_confirmed_at が null の場合は手動で確認済みに変更可能

## 注意事項
- この設定変更により、新規登録時にメール確認なしでログイン可能になります
- 開発環境でのみ推奨される設定です
- 本番環境では適切なメール確認システムを設定してください