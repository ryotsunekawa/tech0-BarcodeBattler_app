"""
pyzbar DLL 依存関係テストとフィックス
"""

import os
import sys
import ctypes
from pathlib import Path

def check_dll_dependencies():
    """DLLの依存関係をチェック"""
    print("=== DLL依存関係チェック ===")
    
    # pyzbar のパスを取得
    try:
        import pyzbar
        pyzbar_path = Path(pyzbar.__file__).parent
        print(f"pyzbar パス: {pyzbar_path}")
        
        # DLLファイルの確認
        libzbar_dll = pyzbar_path / "libzbar-64.dll"
        libiconv_dll = pyzbar_path / "libiconv.dll"
        
        print(f"libzbar-64.dll 存在: {libzbar_dll.exists()}")
        print(f"libiconv.dll 存在: {libiconv_dll.exists()}")
        
        if libzbar_dll.exists():
            print(f"libzbar-64.dll サイズ: {libzbar_dll.stat().st_size} bytes")
        if libiconv_dll.exists():
            print(f"libiconv.dll サイズ: {libiconv_dll.stat().st_size} bytes")
            
        # DLLを直接ロードしてテスト
        print("\n=== DLL直接ロードテスト ===")
        try:
            # まずlibiconv.dllをロード
            libiconv_handle = ctypes.CDLL(str(libiconv_dll))
            print("✅ libiconv.dll ロード成功")
            
            # 次にlibzbar-64.dllをロード
            libzbar_handle = ctypes.CDLL(str(libzbar_dll))
            print("✅ libzbar-64.dll ロード成功")
            
        except OSError as e:
            print(f"❌ DLL直接ロードエラー: {e}")
            return False
            
    except Exception as e:
        print(f"❌ pyzbar パス取得エラー: {e}")
        return False
    
    return True

def add_pyzbar_to_path():
    """pyzbarのDLLパスをPATHに追加"""
    try:
        import pyzbar
        pyzbar_path = str(Path(pyzbar.__file__).parent)
        
        if pyzbar_path not in os.environ['PATH']:
            os.environ['PATH'] = pyzbar_path + os.pathsep + os.environ['PATH']
            print(f"✅ PATH に pyzbar ディレクトリを追加: {pyzbar_path}")
        else:
            print(f"ℹ️ pyzbar ディレクトリは既にPATHに含まれています: {pyzbar_path}")
            
    except Exception as e:
        print(f"❌ PATH追加エラー: {e}")

def test_pyzbar_import():
    """pyzbar のインポートテスト"""
    print("\n=== pyzbar インポートテスト ===")
    
    try:
        from pyzbar import pyzbar as pyzbar_decode
        print("✅ pyzbar.pyzbar インポート成功")
        
        # decode 関数のテスト
        decode_func = pyzbar_decode.decode
        print("✅ decode 関数取得成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ ImportError: {e}")
    except OSError as e:
        print(f"❌ OSError: {e}")
    except Exception as e:
        print(f"❌ その他のエラー ({type(e).__name__}): {e}")
        
    return False

def main():
    print("=== pyzbar DLL 問題解決テスト ===\n")
    
    # 1. DLL依存関係チェック
    dll_ok = check_dll_dependencies()
    
    # 2. PATHにpyzbarディレクトリを追加
    add_pyzbar_to_path()
    
    # 3. pyzbar インポートテスト
    if dll_ok:
        success = test_pyzbar_import()
        if success:
            print("\n🎉 pyzbar の問題が解決されました！")
        else:
            print("\n❌ まだ問題があります。追加の対策が必要です。")
    else:
        print("\n❌ DLLの基本的な問題があります。")

if __name__ == "__main__":
    main()