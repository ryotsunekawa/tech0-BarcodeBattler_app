import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# 環境変数を読み込み
load_dotenv()

def check_current_data():
    """
    現在のSupabaseデータを確認する
    """
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(supabase_url, supabase_anon_key)
    
    print("🔍 現在のデータベース状況を確認します")
    print("=" * 50)
    
    try:
        # ユーザーデータ確認
        users_result = supabase.table('users').select('*').execute()
        users = users_result.data
        
        print(f"👥 現在のユーザー数: {len(users)}人")
        print("\n📋 ユーザー一覧:")
        for user in users:
            print(f"   - {user['user_name']} ({user['mail_address']}) [{user['location']}]")
        
        # 操作ログデータ確認
        operations_result = supabase.table('user_operations').select('*, users(user_name)').execute()
        operations = operations_result.data
        
        print(f"\n📦 操作ログ数: {len(operations)}件")
        print("\n📋 操作ログ一覧:")
        for i, op in enumerate(operations, 1):
            user_name = op.get('users', {}).get('user_name', '不明')
            character_params = op.get('character_parameter', {})
            
            print(f"\n   {i}. {op['item_name']}")
            print(f"      ユーザー: {user_name}")
            print(f"      キャラ名: {op['character_name']}")
            print(f"      バーコード: {op['code_number']}")
            
            if isinstance(character_params, dict):
                print(f"      攻撃力: {character_params.get('attack', 'N/A')}")
                print(f"      防御力: {character_params.get('defense', 'N/A')}")
                print(f"      素早さ: {character_params.get('speed', 'N/A')}")
                print(f"      魔力: {character_params.get('magic', 'N/A')}")
                print(f"      属性: {character_params.get('element', 'N/A')}")
                print(f"      レアリティ: {character_params.get('rarity', 'N/A')}")
            
            print(f"      作成日時: {op['created_at']}")
        
        # CSVファイルも作成
        create_csv_from_current_data(users, operations)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def create_csv_from_current_data(users, operations):
    """
    現在のデータからCSVファイルを作成
    """
    import csv
    
    print("\n📄 CSVファイルを作成中...")
    
    try:
        # usersテーブル用CSV
        with open('current_users.csv', 'w', newline='', encoding='utf-8') as f:
            if users:
                fieldnames = users[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(users)
        
        # user_operationsテーブル用CSV
        with open('current_operations.csv', 'w', newline='', encoding='utf-8') as f:
            if operations:
                # usersの関連データを除外したデータを作成
                clean_operations = []
                for op in operations:
                    clean_op = {k: v for k, v in op.items() if k != 'users'}
                    # JSONデータを文字列に変換
                    if 'character_parameter' in clean_op:
                        clean_op['character_parameter'] = json.dumps(clean_op['character_parameter'], ensure_ascii=False)
                    clean_operations.append(clean_op)
                
                if clean_operations:
                    fieldnames = clean_operations[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(clean_operations)
        
        print("✅ CSVファイルを作成しました:")
        print("   - current_users.csv")
        print("   - current_operations.csv")
        
    except Exception as e:
        print(f"❌ CSV作成エラー: {e}")

if __name__ == "__main__":
    success = check_current_data()
    
    if success:
        print("\n🎉 データ確認が完了しました！")
        print("   Supabase Table Editorでも確認してみてください。")
    else:
        print("\n❌ データ確認に失敗しました。")