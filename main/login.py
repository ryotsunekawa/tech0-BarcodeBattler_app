import os, io, re, json, base64, zipfile, random, time
from PIL import Image #画像ファイルを使用する（バーコード読み込み時や画像生成時）
import streamlit as st #streamlitを使う
from pyzbar.pyzbar import decode # import zxingcpp から変更。(pythonでしか使用しないため)
from supabase import create_client, AuthApiError #supabaseを使う
#open aiを使う
from openai import OpenAI
from openai import RateLimitError, APIStatusError

#stabilityで使う
from io import BytesIO
from PIL import Image
import requests


#画像保存で使う
import uuid
import time
from io import BytesIO

#JANCODEで使う
from urllib.parse import urlencode



# .env ファイルを読み込む
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

#SUPABASEを使うための情報
API_URL = get_secret_or_env("SUPABASE_URL")
API_KEY = get_secret_or_env("SUPABASE_KEY")
supabase = create_client(API_URL, API_KEY)

#OPENAPIを使うための情報
OPENAPI_KEY = get_secret_or_env("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAPI_KEY)

#画像生成APIを使う準備
engine_id = "stable-diffusion-xl-1024-v1-0"
stability_api_host = os.getenv('API_HOST', 'https://api.stability.ai')
stability_api_key = get_secret_or_env("STABILITY_API_KEY")
if stability_api_key is None:
    raise Exception("Missing Stability API key.")

# JANCODE LOOKUPを使う準備①｜設定
JANCODE_APP_ID = get_secret_or_env("JANCODE_APP_ID")  # .env or st.secrets に追加しておく
JANCODE_BASE = "https://api.jancodelookup.com/"

@st.cache_data(ttl=300)  # 同じJANは5分キャッシュ
def fetch_product_by_jan(jan_code: str, hits: int = 10) -> dict:
    """jancodelookup の code 検索（前方一致）。生のJSONを返す。"""
    params = {"appId": JANCODE_APP_ID, "query": jan_code, "hits": hits, "type": "code"}
    r = requests.get(JANCODE_BASE, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

#JANCODE LOOKUPを使う準備②｜API
from urllib.parse import urlencode

JANCODE_APP_ID = get_secret_or_env("JANCODE_APP_ID")
JANCODE_BASE_URL = "https://api.jancodelookup.com/"

# JANCODEを使うための関数
def lookup_by_code(jan_code: str, hits: int = 1):
    """JANコードから商品情報を取得"""
    params = {
        "appId": JANCODE_APP_ID,
        "query": jan_code,
        "hits": hits,
        "type": "code",   # JANコード検索
    }
    url = f"{JANCODE_BASE_URL}?{urlencode(params)}"
    try:
        r = requests.get(JANCODE_BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        products = data.get("product") or []
        if not products:
            return None
        return products[0]  # 最初の1件を返す
    except Exception as e:
        st.error(f"JANコード検索エラー: {e}")
        return None

# 完全Auth UID統一版のヘルパー関数

def sanitize_filename(filename: str) -> str:
    """
    ファイル名を安全な形式に変換（日本語文字を除去し、英数字とアンダースコアのみに）
    """
    # 日本語文字を除去し、英数字・アンダースコア・ハイフンのみを残す
    import string
    safe_chars = string.ascii_letters + string.digits + '_-'
    sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # 連続するアンダースコアを単一に変換
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    # 先頭と末尾のアンダースコアを削除
    sanitized = sanitized.strip('_')
    
    # 空文字列の場合はデフォルト名を使用
    if not sanitized:
        sanitized = 'character'
    
    return sanitized


def upload_character_image_to_storage(image: Image, character_name: str, barcode: str) -> str:
    """
    キャラクター画像をSupabaseストレージにアップロードし、パブリックURLを返す
    """
    try:
        # 画像をバイト配列に変換
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # ファイル名を生成（ユニークになるように、日本語を安全な形式に変換）
        user_id = st.session_state.user.id
        timestamp = int(time.time())
        safe_character_name = sanitize_filename(character_name)
        filename = f"characters/{user_id}_{barcode}_{timestamp}_{safe_character_name}.png"
        

        
        # Supabaseストレージにアップロード
        response = supabase.storage.from_('character-images').upload(filename, img_bytes, {
            'content-type': 'image/png',
            'upsert': 'false'
        })
        
        # アップロード成功判定（エラーチェック）
        if hasattr(response, 'error') and response.error:
            st.error(f"❌ 画像アップロードに失敗しました")
            st.error(f"🔍 エラー詳細: {response.error}")
            st.error(f"📁 試行ファイル名: {filename}")
            return None
        
        # パブリックURLを取得（文字列として直接返される）
        public_url = supabase.storage.from_('character-images').get_public_url(filename)
        st.success(f"✅ 画像アップロード成功: {character_name}")
        
        return public_url
            
    except Exception as e:
        st.error(f"画像アップロードエラー: {str(e)}")
        return None

def create_user_profile_unified(auth_user_id: str, email: str, full_name: str = ""):
    """
    完全統一版：Auth UIDをそのままuser_idとして使用してプロフィール作成
    """
    try:
        profile_data = {
            "user_id": auth_user_id,  # Auth UIDをそのままuser_idとして使用
            "mail_address": email,
            "user_name": full_name or email.split('@')[0],
        }
        
        response = supabase.table('users').insert(profile_data).execute()
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"プロフィール作成エラー: {str(e)}")
        return None

def get_user_profile_unified(auth_user_id: str):
    """
    完全統一版：Auth UIDで直接プロフィール取得
    """
    try:
        response = supabase.table('users').select('*').eq('user_id', auth_user_id).execute()
        return response.data[0] if response.data else None
    except Exception:
        return None

#画像を保存する用の関数
def save_character_to_db_unified(character_data: dict, character_image: Image = None):
    """
    完全統一版：Auth UIDを直接使用してキャラクター保存（画像アップロード機能付き）
    """
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("認証情報が見つかりません")
        return False
    
    try:
        # Auth UIDを直接使用
        character_data["user_id"] = st.session_state.user.id
        

        
        # 画像をストレージにアップロード
        if character_image:
            character_name = character_data.get('character_name', 'unknown')
            barcode = character_data.get('code_number', 'unknown')
            
            with st.spinner('画像をアップロード中...'):
                image_url = upload_character_image_to_storage(character_image, character_name, barcode)
            
            if image_url:
                character_data["character_img_url"] = image_url
                st.success(f"✅ 画像アップロード完了: {character_name}")
            else:
                st.error("❌ 画像アップロードに失敗しました")
                return False
        
        # データベースに保存
        with st.spinner("📦 データベースに保存中..."):
            response = supabase.table('user_operations').insert(character_data).execute()
        
        
        if response.data:
            st.success("🎉 キャラクターを図鑑に保存しました！")
            return True
        else:
            st.error("キャラクター保存に失敗しました")
            if hasattr(response, 'error'):
                st.error(f"詳細エラー: {response.error}")
            return False
            
    except Exception as e:
        st.error(f"キャラクター保存エラー: {str(e)}")
        return False

#図鑑で表示する関数
def get_user_characters_unified():
    """
    完全統一版：Auth UIDで直接キャラクター一覧を取得
    """
    if 'user' not in st.session_state or not st.session_state.user:
        return []
    
    try:
        auth_user_id = st.session_state.user.id
        response = supabase.table('user_operations').select('*').eq('user_id', auth_user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"キャラクター取得エラー: {str(e)}")
        return []


# 画像生成する関数
def generate_character_image(product_json):
    # 1. 商品情報取得

    # 2. OpenAIでプロンプト生成
    region = st.session_state.todoufuken
    if not region:
        st.error("都道府県を選択してください")
        return  None, None, None, None, None

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
    
    try:
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
            line = line.strip()
            lower_line = line.lower()
            
            if lower_line.startswith("prompt:"):
                # Prompt: の行から収集開始
                sd_prompt = line.split(":", 1)[1].strip()
                collecting_prompt = True
            elif lower_line.startswith("character name:"):
                character_name = line.split(":", 1)[1].strip()
                collecting_prompt = False
            elif "name:" in lower_line and not character_name:
                # より柔軟なキャラクター名抽出
                character_name = line.split(":", 1)[1].strip()
                collecting_prompt = False
            elif collecting_prompt and line:
                # Prompt: の続き（改行で複数行ある場合）
                sd_prompt += " " + line
        
        # キャラクター名が見つからない場合、デフォルト名を生成
        if not character_name:
            character_name = f"キャラ{random.randint(1000, 9999)}"    

        if not sd_prompt:
            st.error("OpenAIでプロンプト生成に失敗しました")
            return None, None, None

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
        
        #キャラ出力
        data = response.json()
        image_base64 = data["artifacts"][0]["base64"]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))
        
        # セッション状態に保存
        st.session_state.generated_character = {
            'prompt': sd_prompt,
            'name': character_name,
            'image': image,
            'barcode': product_json['codeNumber'],
            'item_name': product_json['itemName'],
            'region': region
        }
        
        # 表示は呼び出し元で行う
        return sd_prompt, character_name, image
    except Exception as e:
        st.error(f"キャラクター生成エラー: {str(e)}")
        return None, None, None


# メイン画面に戻る関数
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()    


# ログイン画面
def sign_up(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out():
    supabase.auth.sign_out()
    st.session_state.clear()


def login_signup_page():
    st.header("令和版バーコードバトラー（β版）",divider="gray")
    tab1,tab2 = st.tabs(["ログイン","新規会員登録"])
    
    with tab1:
        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード",type="password",key="login_password")
        if st.button("ログインする",type="primary"):
            try:
                res = sign_in(email,password)
                user = res.user
                if user :
                    st.session_state.user = user
                    
                    # プロフィール取得（完全統一版）
                    profile = get_user_profile_unified(user.id)
                    if profile:
                        st.session_state.user_profile = profile
                        st.session_state.full_name = profile.get("user_name", user.email)
                        st.success("ログインに成功しました")
                        st.rerun()
                    else:
                        st.error("プロフィールが見つかりません。新規登録が必要かもしれません。")
                else:
                    st.error("userを取得できずにログインに失敗しました")
            except Exception as e:
                st.error(f"ログインに失敗しました: {str(e)}")
                
        st.markdown("---")
        st.button("パスワードをお忘れの方はこちら（ダミー）")

    with tab2:
        new_email = st.text_input("メールアドレス",key="signup_email")
        new_password = st.text_input("パスワード",type="password",key="signup_password")
        new_name = st.text_input("名前（任意）",key="signup_name")
        if st.button("会員登録をする",type="primary"):
            try:
                response = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password,
                    "options": {
                        "data": {
                            "full_name": new_name
                        }
                    }
                })
                
                if response.user:
                    # 完全統一版プロフィール作成
                    profile = create_user_profile_unified(response.user.id, new_email, new_name)
                    if profile:
                        st.success("アカウントとプロフィールが作成されました。ログインしてください。")
                        st.info("✨ ログインして早速始めましょう！")
                    else:
                        st.error("プロフィール作成に失敗しました。")
                else:
                    st.success("アカウントが作成されました。メールを確認してください。")

            except AuthApiError as e:
                code = getattr(e, "code", None)
                message = str(e)
                
                if "already" in str(code):
                    st.error("このメールアドレスはすでに登録済みです。")
                elif "validation" in str(code):
                   st.error("メールアドレスの書き方不適切です。")
                else:
                    st.error(f"その他のエラー: {message}")

#メイン画面

def main_app():
    # プロフィール情報表示
    if 'user_profile' in st.session_state and st.session_state.user_profile:
        name_to_display = st.session_state.user_profile.get("user_name", st.session_state.user.email)
        # ユーザー情報をサイドバーに表示
        st.sidebar.success(f"👋 {name_to_display}さん、こんにちは")
        
    
    else:
        name_to_display = st.session_state.user.email if 'user' in st.session_state else "ユーザー"
    

    if "page" not in st.session_state:
        st.session_state.page = "main"
    if "characters" not in st.session_state:
        st.session_state.characters = []

    # --- メイン画面 ---
    if st.session_state.page == "main":
        st.title("📚 バーコードキャラクター図鑑")
        st.write("遊び方を選んでください")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📷 スキャン画面へ", key="scan_btn"):
                go_to("scan")
        with col2:
            if st.button("📖 図鑑画面へ", key="zukan_btn"):
                go_to("zukan")

        # ボタンデザイン
        st.markdown(
            """
            <style>
            div.stButton > button:first-child {
                height: 180px;
                width: 100%;
                font-size: 36px;
                font-weight: bold;
                border-radius: 15px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # --- スキャン画面 ---
    elif st.session_state.page == "scan":
        st.title("📷 バーコードスキャン")
        img_file = st.camera_input("JANコードを撮影してください")

        digits, result = None, None
        if img_file:
            # アップロードした画像を Pillow で読み込む
            img = Image.open(io.BytesIO(img_file.getvalue()))
        
            #pyzbar でデコード
            results = decode(img)
        
            if results:
                # 複数バーコードがある場合は最初のものを使う
                result = results[0]
                digits = result.data.decode("utf-8")
                st.success(f"読み取ったコード: {digits} (種類: {result.type})")
            else:
                st.warning("バーコードの読み取りに失敗しました")


        # 数字入力
        col1, col2 = st.columns([3,1])
        with col1:
            digits_input = st.text_input(
                "数字を入力（読み取ったコードがあれば自動入力されます）",
                value=digits or ""
            )
        with col2:
            st.write("")  # 縦位置調整
            st.write("") 
            st.write("✅ 手入力OK")

        # 都道府県選択
        prefectures = [
            "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
            "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
            "新潟県","富山県","石川県","福井県","山梨県","長野県",
            "岐阜県","静岡県","愛知県","三重県",
            "滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
            "鳥取県","島根県","岡山県","広島県","山口県",
            "徳島県","香川県","愛媛県","高知県",
            "福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県",
            "沖縄県"
        ]
        selected_pref = st.selectbox("都道府県を選択", prefectures, index=12 ,key="todoufuken")

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            # 生成ボタン
            if st.button("✨ 生成する", use_container_width=True):
                # 1) 入力からJAN取得（カメラで読めた digits があれば digits_input に入っている想定）
                jan = (digits_input or "").strip().replace(" ", "").replace("　", "")
                if not jan:
                    st.error("JANコードを入力（またはスキャン）してください。")
                    st.stop()

                 # 2) APIで商品検索
                try:
                    with st.spinner("JANコードを確認中..."):
                        product_json = lookup_by_code(jan, hits=10)  # ← 先に貼ってある関数を使用
                except requests.HTTPError as e:
                    st.error(f"HTTPエラー: {e.response.status_code} {e.response.text[:200]}")
                    st.stop()
                except Exception as e:
                    st.error(f"取得時エラー: {e}")
                    st.stop()

                # 3) ヒットなし
                if not product_json:                    
                    # デフォルトキャラクターを表示
                    default_character = {
                        "name": "テックの妖精",
                        "image": "https://lkhbqezbsjojrlmhnuev.supabase.co/storage/v1/object/public/character-images/chatgpt_%20Image_2025_9_28_%2023_59_31.png",
                        "region": "不明",
                        "prompt": "エラーをしたときに現れる妖精。エラーをしても気にするな。"
                    }
                    
                    st.info("該当商品がデータベースに無い可能性があります！デフォルトキャラを召喚！")
                    st.image(default_character['image'], use_container_width=True)
                    
                    with st.expander("🔍 キャラ詳細"):
                        st.write(f"**名前**: {default_character['name']}")
                        st.write(f"**居住地**: {default_character['region']}")
                        st.write(f"**備考**: {default_character['prompt']}")
                    st.write("JANコードを確認して、もう一度お試しください。")

                    st.markdown("---")
                    if st.button("⬅️ メイン画面へ戻る"):
                        go_to("main")
                    
                
                    st.stop()  # ここで処理を止める（以降の生成処理には進まない）

                # 4) セッションに保存（以後の画面遷移でも使えるように）
                st.session_state["last_product_json"] = product_json
                st.success(f"🎉 JANコードの読み込み完了！")

                # 5) 生成
                with st.spinner("キャラクターを生成中..."):
                    prompt, name, image = generate_character_image(product_json)
                
                if prompt and name and image:
                    # 生成成功時は生成フラグを立てる
                    st.session_state.character_generated = True
                    st.rerun()  # ページを再読み込みして保存ボタンを表示
                

            # キャラクターが生成済みの場合、表示と保存ボタンを表示
            if st.session_state.get('character_generated') and st.session_state.get('generated_character'):
                character_info = st.session_state.generated_character
                
                st.success(f"🎉 新キャラを獲得！")
                st.markdown(f'''名前： :blue[{character_info.get('name', '名前不明')}]''')
                st.image(character_info['image'], use_container_width=True)

                with st.expander("🔍 キャラ詳細"):
                    st.write(f"**名前**: {character_info.get('name', '名前不明')}")
                    st.write(f"**居住地**: {character_info.get('region', '')}")
                    st.write(f"""**所属先**: {st.session_state['last_product_json']['makerName']}""")


                with st.expander("🔍 JANコード詳細"):
                    st.write(f"""**商品コード**: {st.session_state['last_product_json']['codeNumber']}""")
                    st.write(f"""**商品名**: {st.session_state['last_product_json']['itemName']}""") 
                    st.write(f"""**商品URL**: {st.session_state['last_product_json']['itemImageUrl']}""")     
                        
                # 保存ボタンを表示
                col_save1, col_save2 = st.columns(2)
                with col_save1:
                    if st.button("💾 保存する", type="primary"):
                        # キャラクターデータをデータベースに保存（完全統一版・画像アップロード対応）
                        character_data = {
                            "code_number": character_info['barcode'],
                            "item_name": character_info['item_name'],
                            "character_name": character_info['name'],
                            "character_parameter": {
                                "prompt": character_info['prompt'],
                                "region": character_info['region'],
                                "power": random.randint(50, 100),
                                "attack": random.randint(30, 90),
                                "defense": random.randint(20, 80),
                                "speed": random.randint(40, 95)
                            }
                        }
                        
                        # 画像も一緒に保存
                        character_image = character_info['image']
                        
                        if save_character_to_db_unified(character_data, character_image):
                            # セッション状態の文字配列にも追加（表示用）
                            st.session_state.characters.append({
                                'name': character_info['name'],
                                'barcode': character_info['barcode'],
                                'type': 'JAN',
                                'region': character_info['region'],
                                'power': character_data['character_parameter']['power']
                            })
                            st.success("🎉 図鑑に登録されました！")
                            st.info("💫 画像もSupabaseストレージに保存されました")
                            
                            # 生成フラグをリセット
                            st.session_state.character_generated = False
                            st.session_state.generated_character = None
                            
                with col_save2:
                    if st.button("🚫 保存しない"):
                        st.info("保存をキャンセルしました")
                        # 生成フラグをリセット
                        st.session_state.character_generated = False
                        st.session_state.generated_character = None
                        st.rerun()

        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")
                    
                    
    # --- 図鑑画面 ---
# --- 図鑑画面 ---
    elif st.session_state.page == "zukan":
        st.title("📖 図鑑（完全統一版）")
        
        # データベースからキャラクター一覧を取得（完全統一版）
        db_characters = get_user_characters_unified()
        
        if db_characters:
            st.write(f"**登録済みキャラクター数**: {len(db_characters)}体")
            
            for idx, char in enumerate(db_characters, start=1):
                with st.expander(f"{idx}. {char.get('character_name', '無名キャラ')} - {char.get('item_name', '不明アイテム')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if char.get('character_img_url'):
                            try:
                                st.image(char['character_img_url'], width=200, caption=char.get('character_name', '名前なし'))
                                st.caption(f"🔗 画像URL: {char['character_img_url'][:50]}...")
                            except Exception as e:
                                st.write("🖼️ 画像を表示できませんでした")
                                st.caption(f"エラー: {str(e)}")
                                st.caption(f"URL: {char.get('character_img_url', 'なし')}")
                        else:
                            st.write("🖼️ 画像なし")
                    
                    with col2:
                        st.write(f"**バーコード**: {char.get('code_number', 'N/A')}")
                        
                        if char.get('character_parameter'):
                            params = char['character_parameter']
                            if isinstance(params, dict):
                                st.write("**ステータス**:")
                                for key, value in params.items():
                                    if key in ['power', 'attack', 'defense', 'speed']:
                                        st.write(f"- {key}: {value}")
                        st.write(f"**作成日**: {char.get('created_at', 'N/A')}")
        else:
            st.info("まだキャラクターがいません。スキャンしてみましょう！")
            
        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    if st.sidebar.button("ログアウト"):
        sign_out()
        st.rerun()

#　アプリケーション全体の流れを制御する

#check_auth()はsession_stateにuserと言うキーが登録されているかの確認。

def check_auth():
    return 'user' in st.session_state

#mainとは 起動時にcheckがFalseであればlogin_signup_pageを起動し、Trueでればmain_appを起動すること。

def main():
    st.set_page_config(
        page_title="令和版バーコードバトラー（β版）",
        page_icon="📱",
        layout="wide"
    )

    if not check_auth():
        login_signup_page()
    else:
        main_app()



#__name__はpythonファイルが実行されるときに自動で設定される。
#また、直接実行されたとき、__name__は"__main__"になる。（他ファイルからインポートされた場合は）
if __name__ == "__main__":
    main()
