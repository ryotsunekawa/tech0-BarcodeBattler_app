from __future__ import annotations
import os, io, re, json, base64, zipfile, random
from typing import Dict, List, Tuple
import requests

#open aiを使う
from openai import OpenAI
from openai import RateLimitError, APIStatusError

#straimlitを使う
import streamlit as st

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


# JANコードAPIから取得した商品情報（例）
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

#OPENAPIを使うための情報
OPENAPI_KEY = get_secret_or_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAPI_KEY)


# プロンプト整形用テキスト
# ここで地域名も入る（例：北海道）
region = "愛知県"
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


# OpenAI APIでテキストプロンプト生成
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "あなたはアニメ風キャラクター化用プロンプト作成の専門家です。"},
        {"role": "user", "content": prompt_for_gpt}
    ],
    max_tokens=200
)

# 生成結果を取得
generated_text = response.choices[0].message.content.strip()

# ラベルで分割
lines = generated_text.splitlines()
sd_prompt = ""
character_name = ""

for line in lines:
    if line.lower().startswith("prompt:"):
        sd_prompt = line.split(":", 1)[1].strip()
    elif line.lower().startswith("character name:"):
        character_name = line.split(":", 1)[1].strip()

# 結果確認
print("=== Stable Diffusion Prompt ===")
print(sd_prompt)
print("\n=== Character Name ===")
print(character_name)



#画像生成APIを使う準備
engine_id = "stable-diffusion-xl-1024-v1-0"
stability_api_host = os.getenv('API_HOST', 'https://api.stability.ai')
stability_api_key = get_secret_or_env("STABILITY_API_KEY")
stability_prompt = f"""{sd_prompt}"""
os.makedirs("./test_image_ai/out", exist_ok=True)

#API Keyの確認
if stability_api_key is None:
    raise Exception("Missing Stability API key.")

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
#画像保存。
if response.status_code != 200:
    raise Exception("Non-200 response: " + str(response.text))

data = response.json()

for i, image in enumerate(data["artifacts"]):
    with open(f"./test_image_ai/out/v1_txt2img_{i}.png", "wb") as f:
        f.write(base64.b64decode(image["base64"]))
