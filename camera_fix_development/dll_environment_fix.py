"""
DLL問題を環境変数で解決するテスト
pyzbarを削除せずに解決を試みます
"""

import os
import sys
from pathlib import Path

def setup_dll_environment():
    """DLL環境を設定"""
    try:
        import pyzbar
        pyzbar_path = Path(pyzbar.__file__).parent
        
        # 複数の方法でDLLパスを追加
        dll_path = str(pyzbar_path)
        
        # 1. PATH環境変数に追加
        current_path = os.environ.get('PATH', '')
        if dll_path not in current_path:
            os.environ['PATH'] = dll_path + os.pathsep + current_path
            print(f"✅ PATHに追加: {dll_path}")
        
        # 2. DLL検索パスに追加（Windows固有）
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(dll_path)
                print(f"✅ DLLディレクトリ設定: {dll_path}")
            except Exception as e:
                print(f"❌ DLLディレクトリ設定エラー: {e}")
        
        # 3. 作業ディレクトリを一時的に変更
        original_cwd = os.getcwd()
        try:
            os.chdir(dll_path)
            print(f"✅ 作業ディレクトリ変更: {dll_path}")
            
            # pyzbarのインポートテスト
            from pyzbar import pyzbar as pyzbar_decode
            print("🎉 pyzbar インポート成功！")
            
            # 元のディレクトリに戻す
            os.chdir(original_cwd)
            return True
            
        except Exception as e:
            os.chdir(original_cwd)
            print(f"❌ インポートテストエラー: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 環境設定エラー: {e}")
        return False

if __name__ == "__main__":
    print("=== DLL環境設定テスト ===")
    success = setup_dll_environment()
    
    if success:
        print("\n🎉 解決策が見つかりました！")
    else:
        print("\n❌ この方法では解決できませんでした。")