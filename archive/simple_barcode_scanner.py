import streamlit as st
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# .envファイルを読み込み
load_dotenv()

JANCODE_API_KEY = os.environ.get("JANCODE_API_KEY")

def get_jancode_info(barcode):
    """JANCODE LOOKUP APIからバーコード情報を取得（デバッグ機能付き）"""
    if not JANCODE_API_KEY:
        return {
            "success": False, 
            "error": "JANCODE API キーが設定されていません"
        }
        
    try:
        # 正しいJANCODE LOOKUP API仕様
        api_url = "https://api.jancodelookup.com/"
        
        # 複数のリクエスト方法を試す
        request_configs = [
            # Method 1: 公式仕様通り (appIdパラメータ)
            {
                "method": "GET",
                "url": api_url,
                "headers": {
                    'User-Agent': 'SimpleBarcodeScanner/1.0',
                    'Accept': 'application/json'
                },
                "params": {
                    'appId': JANCODE_API_KEY,
                    'query': barcode,
                    'hits': 10,
                    'page': 1,
                    'type': 'jan'  # JANコード検索
                }
            },
            # Method 2: typeパラメータなし
            {
                "method": "GET",
                "url": api_url,
                "headers": {
                    'User-Agent': 'SimpleBarcodeScanner/1.0',
                    'Accept': 'application/json'
                },
                "params": {
                    'appId': JANCODE_API_KEY,
                    'query': barcode,
                    'hits': 5
                }
            },
            # Method 3: 最小パラメータ
            {
                "method": "GET",
                "url": api_url,
                "headers": {
                    'User-Agent': 'SimpleBarcodeScanner/1.0',
                    'Accept': 'application/json'
                },
                "params": {
                    'appId': JANCODE_API_KEY,
                    'query': barcode
                }
            },
            # Method 4: 別名パラメータ試行
            {
                "method": "GET",
                "url": api_url,
                "headers": {
                    'User-Agent': 'SimpleBarcodeScanner/1.0',
                    'Accept': 'application/json'
                },
                "params": {
                    'api_key': JANCODE_API_KEY,  # appIdの代わり
                    'jan': barcode,
                    'limit': 10
                }
            }
        ]
        
        debug_info = []
        
        for i, config in enumerate(request_configs):
            try:
                debug_info.append(f"\n--- 試行 {i+1} ---")
                debug_info.append(f"URL: {config['url']}")
                debug_info.append(f"パラメータ: {config['params']}")
                
                # リクエスト実行
                try:
                    if config["method"] == "GET":
                        response = requests.get(
                            config["url"],
                            headers=config["headers"],
                            params=config.get("params", {}),
                            timeout=15
                        )
                    else:  # POST (現在は使用しない)
                        response = requests.post(
                            config["url"],
                            headers=config["headers"],
                            data=config.get("data", {}),
                            timeout=15
                        )
                    
                    debug_info.append(f"✅ HTTP {response.status_code}")
                    debug_info.append(f"実際のURL: {response.url}")
                    
                    # レスポンス内容の確認
                    content_type = response.headers.get('content-type', '')
                    debug_info.append(f"Content-Type: {content_type}")
                    
                except requests.exceptions.RequestException as req_error:
                    debug_info.append(f"❌ リクエストエラー: {str(req_error)}")
                    continue
                except Exception as general_error:
                    debug_info.append(f"❌ 予期しないエラー: {str(general_error)}")
                    continue
                
                if response.status_code == 200:
                        # JSONレスポンスの場合
                        if 'application/json' in content_type:
                            try:
                                data = response.json()
                                debug_info.append(f"JSONデータ受信: {str(data)[:300]}...")
                                
                                # JANCODE LOOKUP APIのレスポンス形式に対応
                                if isinstance(data, dict) and 'product' in data and len(data['product']) > 0:
                                    # JANCODE LOOKUP APIの場合
                                    product = data['product'][0]  # 最初の商品を取得
                                    debug_info.append(f"商品データを取得: {product.get('itemName', '商品名不明')}")
                                    
                                    return {
                                        "success": True,
                                        "debug": debug_info,
                                        "data": {
                                            "barcode": product.get("codeNumber", barcode),
                                            "name": product.get("itemName", "商品名不明"),
                                            "itemModel": product.get("itemModel", ""),
                                            "brandName": product.get("brandName", ""),
                                            "maker": product.get("makerName", "メーカー不明"),
                                            "makerKana": product.get("makerNameKana", ""),
                                            "codeType": product.get("codeType", ""),
                                            "productDetails": product.get("ProductDetails", []),
                                            "jancode": product.get("codeNumber", barcode),
                                            "raw_data": product,
                                            "api_info": data.get('info', {}),
                                            "source": "JANCODE LOOKUP API"
                                        }
                                    }
                                else:
                                    debug_info.append("有効な商品データが見つかりません")
                                    debug_info.append(f"データ構造: {str(data)[:200]}...")
                                    continue
                            except json.JSONDecodeError as e:
                                debug_info.append(f"JSON解析エラー: {str(e)}")
                                debug_info.append(f"レスポンステキスト: {response.text[:500]}")
                                continue
                        else:
                            # HTMLレスポンスの場合（Webページ）
                            debug_info.append("HTMLレスポンス（APIエンドポイントではない可能性）")
                            debug_info.append(f"レスポンステキスト: {response.text[:300]}...")
                            continue
                    
                elif response.status_code in [401, 403]:
                    debug_info.append("認証エラー - APIキーまたは権限の問題")
                elif response.status_code == 404:
                    debug_info.append("エンドポイントまたは商品が見つからない")
                else:
                    debug_info.append(f"HTTPエラー: {response.status_code}")
                    debug_info.append(f"エラー内容: {response.text[:200]}...")
                        
            except requests.exceptions.Timeout:
                debug_info.append("タイムアウトエラー")
            except requests.exceptions.ConnectionError:
                debug_info.append("接続エラー")
            except requests.exceptions.RequestException as e:
                debug_info.append(f"リクエストエラー: {str(e)}")
            except Exception as e:
                debug_info.append(f"予期しないエラー: {str(e)}")
        
        # すべての試行が失敗した場合
        return {
            "success": False, 
            "error": "すべての認証方法とエンドポイントで失敗しました",
            "debug": debug_info
        }
            
    except Exception as e:
        return {
            "success": False, 
            "error": f"予期しないエラー: {str(e)}",
            "debug": [f"例外: {str(e)}"]
        }

def main():
    st.set_page_config(
        page_title="シンプルバーコードスキャナー",
        page_icon="🔍",
        layout="centered"
    )
    
    st.title("🔍 シンプルバーコードスキャナー")
    st.markdown("JANCODE LOOKUP APIを使用した商品情報検索ツール")
    
    # API設定チェック
    if JANCODE_API_KEY:
        st.sidebar.success("✅ API設定済み")
        st.sidebar.code(f"API Key: {JANCODE_API_KEY[:8]}***", language=None)
        
        # 手動URL確認
        st.sidebar.markdown("### 🔗 API情報")
        st.sidebar.markdown("""
        **JANCODE LOOKUP API:**
        [api.jancodelookup.com](https://api.jancodelookup.com/)
        
        **仕様:**
        ```
        GET https://api.jancodelookup.com/
        ?appId=[アプリID]
        &query=[キーワード]
        &hits=[取得件数]
        &type=[検索タイプ]
        ```
        """)
        
    else:
        st.sidebar.error("❌ API未設定")
        st.error("⚠️ `.env`ファイルに`JANCODE_API_KEY`を設定してください")
        st.stop()
    
    # バーコード入力
    st.subheader("📱 バーコード検索")
    
    barcode = st.text_input(
        "バーコード番号",
        placeholder="例: 4901234567890",
        help="JANコード（8桁または13桁）を入力"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        search_btn = st.button("🔍 検索", type="primary")
    
    with col2:
        clear_btn = st.button("🗑️ クリア")
    
    if clear_btn:
        st.rerun()
    
    # 検索実行
    if search_btn and barcode:
        with st.spinner("検索中..."):
            result = get_jancode_info(barcode.strip())
        
        if result["success"]:
            data = result["data"]
            
            st.success("✅ 商品情報が見つかりました！")
            
            # 商品情報表示
            with st.container():
                st.markdown("### 📦 商品詳細")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # JANCODE LOOKUP APIの全ての情報を表示
                    st.markdown(f"""
                    **バーコード:** `{data['barcode']}`  
                    **商品名:** {data['name']}  
                    **商品モデル:** {data.get('itemModel', 'なし')}  
                    **ブランド名:** {data.get('brandName', 'なし')}  
                    **メーカー:** {data['maker']}  
                    **メーカー（カナ）:** {data.get('makerKana', 'なし')}  
                    **コードタイプ:** {data.get('codeType', 'なし')}  
                    **データソース:** {data.get('source', 'なし')}  
                    """)
                
                with col2:
                    # 商品詳細情報がある場合は表示
                    product_details = data.get('productDetails', [])
                    if product_details:
                        st.markdown("**商品詳細:**")
                        for detail in product_details:
                            st.text(f"• {detail}")
                    else:
                        st.info("詳細情報なし")
                
                # API情報の表示
                if 'api_info' in data and data['api_info']:
                    api_info = data['api_info']
                    st.markdown("**検索結果情報:**")
                    st.text(f"検索結果数: {api_info.get('count', 0)}")
                    st.text(f"ページ: {api_info.get('page', 1)}/{api_info.get('pageCount', 1)}")
            
            # データ出力オプション
            st.markdown("### 💾 データ出力")
            
            # JSON表示
            with st.expander("JSON データを表示"):
                st.json(data)
            
            # デバッグ情報（成功時）
            if 'debug' in result:
                with st.expander("🔧 API接続情報"):
                    for info in result['debug']:
                        st.text(info)
            
            # 生データ表示
            if 'raw_data' in data:
                with st.expander("📋 API生データ"):
                    st.json(data['raw_data'])
            
            # CSVダウンロード
            csv_data = f"""barcode,name,maker,category,price,image_url
{data['barcode']},"{data['name']}","{data['maker']}","{data['category']}","{data['price']}","{data['image_url']}"
"""
            
            st.download_button(
                label="📥 CSV形式でダウンロード",
                data=csv_data,
                file_name=f"product_{data['barcode']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # JSON ダウンロード
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 JSON形式でダウンロード",
                data=json_data,
                file_name=f"product_{data['barcode']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        else:
            st.error(f"❌ {result['error']}")
            
            # デバッグ情報を表示
            if 'debug' in result:
                with st.expander("🔧 デバッグ情報（開発者向け）"):
                    for info in result['debug']:
                        st.text(info)
    
    # 使用例とテスト
    with st.expander("💡 使用方法とテスト"):
        st.markdown("""
        1. **バーコード入力**: JANコード（8桁または13桁）を入力
        2. **検索実行**: 🔍検索ボタンをクリック
        3. **結果確認**: 商品情報が表示されます
        4. **デバッグ**: エラー時はデバッグ情報を確認
        5. **データ出力**: CSV/JSON形式でダウンロード可能
        
        **テスト用バーコード:**
        - `4901234567890` (テストコード)
        - `4902102072854` (実在商品例)
        - `4547691316643` (実在商品例)
        
        **JANCODE LOOKUP API仕様:**
        - 正しいAPI: https://api.jancodelookup.com/
        - パラメータ: appId, query, hits, page, type
        - 認証: appId パラメータでAPIキーを送信
        
        **トラブルシューティング:**
        - デバッグ情報で「HTMLレスポンス」が表示される場合、エンドポイントが間違っています
        - 認証エラーの場合、APIキーまたは認証方法を確認
        - 404エラーの場合、商品が登録されていないかエンドポイントが無効
        """)
        
        # クイックテストボタン
        st.markdown("**クイックテスト:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("テスト1", key="test1"):
                st.session_state.test_barcode = "4901234567890"
        with col2:
            if st.button("テスト2", key="test2"):
                st.session_state.test_barcode = "4902102072854"
        with col3:
            if st.button("テスト3", key="test3"):
                st.session_state.test_barcode = "4547691316643"
        
        # テストバーコードが設定された場合
        if hasattr(st.session_state, 'test_barcode'):
            st.info(f"テストバーコード設定: {st.session_state.test_barcode}")
            st.markdown("上のバーコード入力欄にコピーして検索してください")

if __name__ == "__main__":
    main()