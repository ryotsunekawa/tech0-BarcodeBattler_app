from __future__ import annotations
import os, io, re, json, base64, zipfile, random
from typing import Dict, List, Tuple
from supabase import create_client, AuthApiError #supabaseを使う

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

#画像生成APIを使う準備
engine_id = "stable-diffusion-xl-1024-v1-0"
stability_api_host = os.getenv('API_HOST', 'https://api.stability.ai')
stability_api_key = get_secret_or_env("STABILITY_API_KEY")
#API Keyの確認
if stability_api_key is None:
    raise Exception("Missing Stability API key.")

#SUPABASEを使うための情報
API_URL = get_secret_or_env("SUPABASE_URL")
API_KEY = get_secret_or_env("SUPABASE_KEY")
supabase = create_client(API_URL, API_KEY)

# JANCODEAPI呼び出し
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

    # 2. OpenAIでプロンプト生成
    region = st.session_state.todoufuken
    if not region:
        st.error("都道府県を入力してください")
        return  None, None, None

    prompt_for_gpt = f"""
    以下の商品情報をもとに、アニメ風キャラクターをStable Diffusionで生成するための
    使える英語のテキストプロンプトを作成してください。
    
    キャラクターは商品「{product_json['itemName']}」を擬人化したもので、
    地域「{region}」のイメージを反映させます。
    
    キャラクターはデフォルメ強めのコミカルな「ちびキャラ（SDキャラ）」風で、
    レトロなカードバトルゲーム風イラストとして表現してください。
    太めのアウトライン、カラフルで派手な色彩、能力値や属性を感じさせる雰囲気を持たせてください。
    
    以下の要素を必ず英語プロンプトに含めてください：
    - **性格**：キャラクターの性格を具体的に描写（例：勇敢で元気、清潔感がある、戦闘好きなど）
    - **服装**：RPGキャラクター風の衣装。商品名を連想させるデザインを取り入れる
    - **小物・持ち物**：商品名をモチーフにしたデフォルメ武器・防具を装備
    - **姿勢**：戦闘ポーズ（カードバトルゲーム風の構え）
    - **背景**：地域の特徴（自然や建物など）を取り入れた、カードゲーム用イラスト風背景
    - **演出**：戦闘力や特殊技を発動しそうなエフェクト（光、オーラ、数字的な力を感じさせる演出）
    
    また、このキャラクターに合う短く覚えやすいキャラクター名も作成してください。
    キャラクター名はカタカナで8文字以内でお願いします。
    
    
    商品情報：
    - 商品名: {product_json['itemName']}
    - メーカー: {product_json['makerName']}
    - 商品画像URL: {product_json['itemImageUrl']}
    
    ※結果は以下の形式で出力してください：
    Prompt: <ここに英語のプロンプト>
    Character Name: <ここにキャラクター名>
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはアニメ風キャラクター化用プロンプト作成の専門家です。"},
            {"role": "user", "content": prompt_for_gpt + "\n\n必ず以下の形式で出力してください:\nPrompt: <英語のプロンプト>\nCharacter Name: <カタカナ8文字以内>"}
        ],
        max_tokens=200
    )

    generated_text = response.choices[0].message.content.strip()
    lines = generated_text.splitlines()
    sd_prompt = ""
    character_name = ""
    collecting_prompt = False
    for line in lines:
        lower_line = line.lower().strip()
        if lower_line.startswith("prompt:"):
            # Prompt: の行から収集開始
            sd_prompt = line.split(":", 1)[1].strip()
            collecting_prompt = True
        elif lower_line.startswith("character name:"):
            character_name = line.split(":", 1)[1].strip()
            collecting_prompt = False
        elif collecting_prompt:
            # Prompt: の続き（改行で複数行ある場合）
            sd_prompt += " " + line.strip()    

    if not sd_prompt:
        st.write("=== lines ===")
        st.write(lines)
        st.error("OpenAIでプロンプト生成に失敗しました")
        return  None, None, None

    # 3. Stability AIで画像生成
    stability_prompt = f"""{sd_prompt}"""
    response = requests.post(
        f"{stability_api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {stability_api_key}"
        },
        json={
             "style_preset": "anime",
            "text_prompts": [
            {
                "text": f"{stability_prompt}"
            }
        ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        st.error(f"APIエラーが発生しました。ステータスコード: {response.status_code}\n内容: {response.text}")
        return None, None, None

    data = response.json()
    image_base64 = data["artifacts"][0]["base64"]
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_bytes))
    st.markdown(f'''キャラクター名： :blue[{character_name}]''')
    st.image(image, use_container_width=True)
    st.write(f"キャラ詳細")
    st.write(f"{sd_prompt}")
    st.write(f"居住地：{region}")

    return sd_prompt, character_name,image

                
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


