import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# 環境変数を読み込み
load_dotenv()

def test_postgresql_connection():
    """
    PostgreSQL接続をテストする（修正版）
    """
    
    # Supabaseの接続情報を取得
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not supabase_url or not db_password:
        print("❌ 環境変数が設定されていません")
        return False
    
    # URLからホスト名を抽出
    parsed_url = urlparse(supabase_url)
    host = parsed_url.hostname.replace("https://", "").replace("http://", "")
    
    # 接続設定のバリエーション
    connection_configs = [
        {
            "name": "標準接続",
            "config": {
                "host": host,
                "database": "postgres",
                "user": "postgres",
                "password": db_password,
                "port": 5432,
                "connect_timeout": 30
            }
        },
        {
            "name": "SSL接続",
            "config": {
                "host": host,
                "database": "postgres", 
                "user": "postgres",
                "password": db_password,
                "port": 5432,
                "sslmode": "require",
                "connect_timeout": 30
            }
        },
        {
            "name": "接続プール経由",
            "config": {
                "host": f"db.{host}",  # 接続プール用ホスト
                "database": "postgres",
                "user": "postgres",
                "password": db_password,
                "port": 6543,  # 接続プール用ポート
                "sslmode": "require",
                "connect_timeout": 30
            }
        }
    ]
    
    for conn_config in connection_configs:
        print(f"\n🔌 {conn_config['name']}を試行中...")
        try:
            conn = psycopg2.connect(**conn_config['config'])
            cursor = conn.cursor()
            
            # 接続テスト
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ 接続成功！")
            print(f"   PostgreSQLバージョン: {version[:50]}...")
            
            cursor.close()
            conn.close()
            
            print(f"✅ {conn_config['name']}が正常に動作しました！")
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ {conn_config['name']}: {str(e)[:100]}...")
        except Exception as e:
            print(f"❌ {conn_config['name']}: 予期しないエラー - {str(e)[:100]}...")
    
    print("\n💡 解決策:")
    print("1. Supabaseダッシュボード > Settings > Database で接続情報を確認")
    print("2. ファイアウォール設定でポート5432/6543を許可")
    print("3. 代わりにSupabase Python SDKを使用（推奨）")
    
    return False

def get_supabase_connection_string():
    """
    Supabaseから正しい接続文字列を取得する手順を表示
    """
    print("\n📋 正しい接続文字列の取得手順:")
    print("=" * 50)
    print("1. Supabaseダッシュボード > Settings > Database")
    print("2. 'Connection string' セクションを確認")
    print("3. 以下の形式の文字列をコピー:")
    print("   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
    print("4. または Connection pooling:")
    print("   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres")
    print("\n注意: [PASSWORD]と[PROJECT-REF]は実際の値に置き換えてください")

if __name__ == "__main__":
    print("🧪 PostgreSQL接続テストを開始します")
    print("=" * 50)
    
    success = test_postgresql_connection()
    
    if not success:
        get_supabase_connection_string()
        print("\n💡 推奨: 直接PostgreSQL接続の代わりにSupabase SDKを使用してください")