import os
import csv
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import random
import json

# 環境変数を読み込み
load_dotenv()

def create_dummy_data():
    """
    ダミーデータを生成してSupabaseに挿入する
    """
    
    # Supabaseクライアント初期化
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(supabase_url, supabase_anon_key)
    
    print("🚀 ダミーデータ作成を開始します")
    print("=" * 50)
    
    # ダミーユーザーデータ
    dummy_users = [
        {
            "mail_address": "tanaka@example.com",
            "user_name": "田中太郎",
            "location": "東京都"
        },
        {
            "mail_address": "sato@example.com",
            "user_name": "佐藤花子",
            "location": "大阪府"
        },
        {
            "mail_address": "yamada@example.com", 
            "user_name": "山田一郎",
            "location": "愛知県"
        },
        {
            "mail_address": "suzuki@example.com",
            "user_name": "鈴木美咲",
            "location": "福岡県"
        },
        {
            "mail_address": "watanabe@example.com",
            "user_name": "渡辺健司",
            "location": "北海道"
        }
    ]
    
    # ダミー商品データ（バーコード例）
    dummy_products = [
        {
            "code_number": "4901480072968",
            "item_name": "コクヨS&T キャンパスノート（特殊罫） ノ-201WN",
            "character_name": "ノートマスター",
            "character_parameter": {
                "attack": 45,
                "defense": 80,
                "speed": 35,
                "magic": 90,
                "element": "知識",
                "rarity": "レア",
                "skills": ["記憶強化", "集中力アップ", "整理術"]
            }
        },
        {
            "code_number": "4902370517859",
            "item_name": "ペプシコーラ 500ml",
            "character_name": "ブリズファイター",
            "character_parameter": {
                "attack": 75,
                "defense": 40,
                "speed": 85,
                "magic": 30,
                "element": "炭酸",
                "rarity": "コモン",
                "skills": ["瞬発力", "リフレッシュ", "エナジーバースト"]
            }
        },
        {
            "code_number": "4987176014443",
            "item_name": "明治チョコレート効果カカオ72%",
            "character_name": "ダークカカオナイト",
            "character_parameter": {
                "attack": 60,
                "defense": 70,
                "speed": 50,
                "magic": 85,
                "element": "苦味",
                "rarity": "エピック",
                "skills": ["集中力", "抗酸化", "リラックス"]
            }
        },
        {
            "code_number": "4901301013717",
            "item_name": "キリン午後の紅茶 ストレートティー",
            "character_name": "ティーマジシャン",
            "character_parameter": {
                "attack": 40,
                "defense": 60,
                "speed": 70,
                "magic": 80,
                "element": "紅茶",
                "rarity": "レア",
                "skills": ["癒し", "優雅", "アフタヌーンパワー"]
            }
        },
        {
            "code_number": "4549741511278",
            "item_name": "セブンプレミアム おにぎり 鮭",
            "character_name": "サーモンファイター",
            "character_parameter": {
                "attack": 65,
                "defense": 75,
                "speed": 55,
                "magic": 45,
                "element": "和食",
                "rarity": "アンコモン",
                "skills": ["満腹感", "栄養補給", "日本の心"]
            }
        }
    ]
    
    try:
        # 1. ユーザーデータを挿入
        print("👥 ユーザーデータを挿入中...")
        
        users_result = supabase.table('users').insert(dummy_users).execute()
        inserted_users = users_result.data
        
        print(f"✅ {len(inserted_users)}人のユーザーを挿入しました")
        for user in inserted_users:
            print(f"   - {user['user_name']} ({user['mail_address']})")
        
        # 2. 操作ログデータを挿入
        print("\n📦 操作ログデータを挿入中...")
        
        operations_data = []
        base_time = datetime.now() - timedelta(days=30)  # 30日前から開始
        
        for i, product in enumerate(dummy_products):
            # ランダムなユーザーを選択
            user = random.choice(inserted_users)
            
            # ランダムな時間を生成（過去30日間）
            random_time = base_time + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            operation = {
                "user_id": user['user_id'],
                "code_number": product['code_number'],
                "item_name": product['item_name'],
                "character_img_url": f"https://example.com/characters/{product['character_name'].lower()}.png",
                "character_name": product['character_name'],
                "character_parameter": product['character_parameter'],
                "created_at": random_time.isoformat()
            }
            operations_data.append(operation)
        
        # 追加の操作ログ（同じユーザーが複数回使用）
        for _ in range(5):
            user = random.choice(inserted_users)
            product = random.choice(dummy_products)
            
            random_time = base_time + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            operation = {
                "user_id": user['user_id'],
                "code_number": product['code_number'],
                "item_name": product['item_name'],
                "character_img_url": f"https://example.com/characters/{product['character_name'].lower()}.png",
                "character_name": product['character_name'],
                "character_parameter": product['character_parameter'],
                "created_at": random_time.isoformat()
            }
            operations_data.append(operation)
        
        operations_result = supabase.table('user_operations').insert(operations_data).execute()
        inserted_operations = operations_result.data
        
        print(f"✅ {len(inserted_operations)}件の操作ログを挿入しました")
        
        # 3. CSVファイルを作成
        print("\n📄 CSVファイルを作成中...")
        
        # usersテーブル用CSV
        with open('dummy_users.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'mail_address', 'user_name', 'location', 'created_at'])
            writer.writeheader()
            writer.writerows(inserted_users)
        
        # user_operationsテーブル用CSV
        with open('dummy_operations.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'user_id', 'code_number', 'item_name', 'character_img_url', 'character_name', 'character_parameter', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for op in inserted_operations:
                # JSONデータを文字列に変換
                op_copy = op.copy()
                op_copy['character_parameter'] = json.dumps(op_copy['character_parameter'], ensure_ascii=False)
                writer.writerow(op_copy)
        
        print("✅ CSVファイルを作成しました:")
        print("   - dummy_users.csv")
        print("   - dummy_operations.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def verify_data():
    """
    挿入されたデータを確認
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(supabase_url, supabase_anon_key)
    
    print("\n🔍 データ確認を実行中...")
    
    try:
        # ユーザー数確認
        users_result = supabase.table('users').select('*').execute()
        users_count = len(users_result.data)
        print(f"👥 ユーザー数: {users_count}人")
        
        # 操作ログ数確認
        operations_result = supabase.table('user_operations').select('*').execute()
        operations_count = len(operations_result.data)
        print(f"📦 操作ログ数: {operations_count}件")
        
        # 最新の操作ログを表示
        if operations_result.data:
            latest_op = operations_result.data[0]
            print(f"\n📋 最新の操作ログ例:")
            print(f"   商品名: {latest_op['item_name']}")
            print(f"   キャラ名: {latest_op['character_name']}")
            print(f"   作成日時: {latest_op['created_at']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")
        return False

if __name__ == "__main__":
    print("🎲 ダミーデータ作成スクリプトを開始します")
    print("=" * 50)
    
    success = create_dummy_data()
    
    if success:
        verify_data()
        print("\n🎉 ダミーデータの作成と確認が完了しました！")
        print("   Supabase Table Editorで確認してみてください。")
    else:
        print("\n❌ ダミーデータの作成に失敗しました。")