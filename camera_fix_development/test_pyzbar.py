"""
pyzbar の動作テストスクリプト
DLL の問題を詳しく調査します
"""

import sys
import os

print("=== Python環境情報 ===")
print(f"Python実行ファイル: {sys.executable}")
print(f"Pythonバージョン: {sys.version}")
print(f"現在の作業ディレクトリ: {os.getcwd()}")

print("\n=== ライブラリのインポートテスト ===")

# OpenCV のテスト
try:
    import cv2
    print("✅ OpenCV インポート成功")
    print(f"   OpenCVバージョン: {cv2.__version__}")
except Exception as e:
    print(f"❌ OpenCV インポートエラー: {e}")

# PIL のテスト
try:
    from PIL import Image
    print("✅ PIL インポート成功")
except Exception as e:
    print(f"❌ PIL インポートエラー: {e}")

# pyzbar のテスト（詳細エラー情報付き）
print("\n=== pyzbar詳細テスト ===")
try:
    import pyzbar
    print("✅ pyzbar モジュールインポート成功")
    print(f"   pyzbarのパス: {pyzbar.__file__}")
    
    # pyzbar.pyzbar のインポートテスト
    try:
        from pyzbar import pyzbar as pyzbar_decode
        print("✅ pyzbar.pyzbar インポート成功")
        
        # decode 関数のテスト
        try:
            decode_func = pyzbar_decode.decode
            print("✅ decode 関数取得成功")
        except Exception as e:
            print(f"❌ decode 関数取得エラー: {e}")
            
    except ImportError as e:
        print(f"❌ pyzbar.pyzbar インポートエラー: {e}")
        print("   詳細:", str(e))
    except OSError as e:
        print(f"❌ pyzbar.pyzbar OSエラー: {e}")
        print("   詳細:", str(e))
    except Exception as e:
        print(f"❌ pyzbar.pyzbar その他のエラー: {type(e).__name__}: {e}")

except Exception as e:
    print(f"❌ pyzbar モジュールインポートエラー: {type(e).__name__}: {e}")

print("\n=== システム環境情報 ===")
print("PATH変数:")
for path in os.environ.get('PATH', '').split(os.pathsep):
    if path.strip():
        print(f"  {path}")

# Windows特有のDLL検索パスをチェック
if sys.platform == 'win32':
    print("\n=== Windows DLL情報 ===")
    try:
        import ctypes
        from ctypes import wintypes
        
        # システムディレクトリの確認
        system_dir = ctypes.windll.kernel32.GetSystemDirectoryW(None, 0)
        system_path = ctypes.create_unicode_buffer(system_dir)
        ctypes.windll.kernel32.GetSystemDirectoryW(system_path, system_dir)
        print(f"Systemディレクトリ: {system_path.value}")
        
    except Exception as e:
        print(f"DLL情報取得エラー: {e}")

print("\n=== pyzbar関連ファイル検索 ===")
# pyzbar関連ファイルを検索
try:
    import site
    for site_dir in site.getsitepackages():
        pyzbar_dir = os.path.join(site_dir, 'pyzbar')
        if os.path.exists(pyzbar_dir):
            print(f"pyzbarディレクトリ発見: {pyzbar_dir}")
            for root, dirs, files in os.walk(pyzbar_dir):
                for file in files:
                    if file.endswith(('.dll', '.pyd', '.so')):
                        print(f"  DLL/バイナリファイル: {os.path.join(root, file)}")
except Exception as e:
    print(f"ファイル検索エラー: {e}")