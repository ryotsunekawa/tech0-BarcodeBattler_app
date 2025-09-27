from __future__ import annotations
import os, io, re, json, base64, zipfile, random
from typing import Dict, List, Tuple

#open aiを使う
from openai import OpenAI
from openai import RateLimitError, APIStatusError

#straimlitを使う
import streamlit as st

#stabilityで使う
from io import BytesIO
from PIL import Image
import requests

#.envを使う
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

#APIの取得
    
def get_secret_or_env(name: str) -> str:
    """環境変数または secrets.toml から値を取得。見つからなければエラー表示して停止。"""
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets[name]
        except Exception:
            st.error(f"{name} が見つかりません。")
            st.stop()
    return value

#OPENAPIを使うための情報
OPENAPI_KEY = get_secret_or_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAPI_KEY)


def generate_character_image():
    # 1. 商品情報取得
    product_json = {
        "codeNumber": "4901301446596",
        "codeType": "JAN",
        "itemName": "アタックZERO パーフェクトスティック 76本入り",
        "itemModel": "",
        "itemUrl": "https://www.jancodelookup.com/code/4901301446596/",
        "itemImageUrl": "https://image.jancodelookup.com/4901301446596.jpg",
        "brandName": "",
        "makerName": "花王株式会社",
        "makerNameKana": "カオウ",
        "ProductDetails": []
    }

    # 2. プロンプト生成（日本語のままでOK）
    region = st.session_state.todoufuken
    if not region:
        st.error("都道府県を入力してください")
        return None, None, None

    sd_prompt = f"""
    商品「{product_json['itemName']}」情報をもとに、バーコードバトラー風に擬人化したキャラクターを描いてください。
    キャラクターはレトロなカードバトルゲーム風イラストとして表現してください。
    キャラクターには商品画像（ {product_json['itemImageUrl']} ）のイメージを反映させてください。

    以下の要素を必ず含めてください：
    - **性格**：キャラクターの性格を具体的に描写（例：勇敢で元気、清潔感がある、戦闘好きなど）
    - **服装**：RPGキャラクター風の衣装。商品名を連想させるデザインを取り入れる
    - **小物・持ち物**：商品名をモチーフにしたデフォルメ武器・防具を装備
    - **姿勢**：戦闘ポーズ（カードバトルゲーム風の構え）
    - **背景**：{region} の特徴（自然や建物、雰囲気など）を取り入れた、カードゲーム用イラスト風背景。
    - **演出**：戦闘力や特殊技を発動しそうなエフェクト（光、オーラ、数字的な力を感じさせる演出）
    - **キャラクター情報**：メーカー名（ {product_json['makerName']}）のテキストをキャラクターのどこかに入れてください。

    
    また、このキャラクターに合う短く覚えやすいキャラクター名も作成してください。
    キャラクター名はカタカナで8文字以内でお願いします。
    
    
    商品情報：
    - 商品名: {product_json['itemName']}
    - メーカー: {product_json['makerName']}
    - 商品画像URL: {product_json['itemImageUrl']}
    

    ※キャラクター名は以下の形式で出力してください：
    Character Name: <ここにキャラクター名>
    """
    
    # 3. OpenAIで画像生成
    try:
        response = client.images.generate(
            model="dall-e-3",  # DALL·E 3
            prompt=sd_prompt,
            size="1024x1024",
            response_format="b64_json"
        )
    except Exception as e:
        st.error(f"画像生成でエラーが発生しました: {str(e)}")
        return None, None, None
    
    # 4. Base64 を画像に変換（安全版）
    image_base64 = None
    if hasattr(response, "data") and len(response.data) > 0:
        image_base64 = getattr(response.data[0], "b64_json", None)
    
    if not image_base64:
        st.error("画像データが取得できませんでした。OpenAI APIの応答を確認してください。")
        st.write(response)  # デバッグ用にAPIレスポンス全体を確認
        return None, None, None
    
    # デコードして画像化
    try:
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))
    except Exception as e:
        st.error(f"画像デコードでエラーが発生しました: {str(e)}")
        return None, None, None
    
    # 5. 表示
    character_name = "仮キャラ"  # ここは必要ならOpenAIに名前も生成させる
    st.markdown(f'''キャラクター名： :blue[{character_name}]''')
    st.image(image, use_container_width=True)
    st.write("キャラ詳細")
    st.write(sd_prompt)
    st.write(f"居住地：{region}")

    return sd_prompt, character_name, image


                
#画面表示
#メイン画面

def main_app():
    st.subheader(f"つねさん、おかえりなさい！")

    tab1,tab2,tab3 = st.tabs(["キャラ生成","図鑑","バトル"])
    
    with tab1:
        scan = st.text_input("スキャン", key="login_email") #session_state.login_emailが使えるようになる。
        option = st.selectbox(
            "都道府県",
            ("北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"),
            index=None,
            placeholder="都道府県を選択",
            key="todoufuken"
        )
        if st.button("生成する"):
                    generate_character_image()  # 戻り値を受け取る
                    st.button("保存する",type="primary")
                    st.button("保存しない")

    
    with tab2:
        st.write("cominng soon")

    
    with tab3:
        st.write("cominng soon")




#mainとは 起動時にcheckがFalseであればlogin_signup_pageを起動し、Trueでればmain_appを起動すること。

def main():
        main_app()


#__name__はpythonファイルが実行されるときに自動で設定される。
#また、直接実行されたとき、__name__は"__main__"になる。（他ファイルからインポートされた場合は）
if __name__ == "__main__":
    main()


