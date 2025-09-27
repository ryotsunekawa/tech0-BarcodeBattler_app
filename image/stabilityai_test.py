import base64
import os
import requests


#.envを使う
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def get_secret_or_env(name: str) -> str:
    """環境変数または secrets.toml から値を取得。見つからなければエラー表示して停止。"""
    value = os.getenv(name)
    
    return value

##前提情報※promptはサンプル（OPEN AIで作成したものを埋め込む予定）
engine_id = "stable-diffusion-xl-1024-v1-0"
api_host = os.getenv('API_HOST', 'https://api.stability.ai')
stability_api_key = get_secret_or_env("STABILITY_API_KEY")
sd_prompt = """Create a cute chibi character inspired by the product "Attack ZERO Perfect Stick 76 sticks" personified with the image of Hokkaido. The character should have a comical and deformed style, resembling a retro card battle game illustration. It should feature thick outlines, vibrant and flashy colors, and an aura of abilities and attributes."""
prompt = """{sd_prompt}"""
os.makedirs("./test_image_ai/out", exist_ok=True)

#API Keyの確認
if stability_api_key is None:
    raise Exception("Missing Stability API key.")

response = requests.post(
    f"{api_host}/v1/generation/{engine_id}/text-to-image",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {stability_api_key}"
    },
    json={
         "style_preset": "anime",
        "text_prompts": [
        {
            "text": f"{prompt}"
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
