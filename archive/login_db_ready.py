import os, io, re, json, base64, zipfile, random, uuid
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

# ===== DB連携関数群（追加） =====

def get_user_characters():
    """現在のユーザーのキャラクター一覧を取得"""
    try:
        user_email = st.session_state.user.email if st.session_state.user else None
        if not user_email:
            return []
        
        # usersテーブルからuser_idを取得
        user_response = supabase.table('users').select('user_id').eq('mail_address', user_email).execute()
        if not user_response.data:
            return []
        
        user_id = user_response.data[0]['user_id']
        
        # charactersテーブルからユーザーのキャラクターを取得
        response = supabase.table('characters').select('''
            character_id,
            character_name,
            barcode,
            region,
            power_level,
            character_img_url,
            created_at,
            character_prompt
        ''').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"キャラクターデータの取得に失敗しました: {str(e)}")
        return []

def get_storage_image_url(img_path):
    """Supabase Storageから公開URLを取得"""
    try:
        if not img_path:
            return None
            
        # すでに完全なURLの場合はそのまま返す
        if img_path.startswith('http'):
            return img_path
        
        # Storage URLを構築
        project_url = API_URL  # SUPABASE_URL
        bucket_name = "character-images"
        storage_url = f"{project_url}/storage/v1/object/public/{bucket_name}/{img_path}"
        return storage_url
        
    except Exception as e:
        print(f"Storage URL取得エラー: {str(e)}")
        return None

def save_character_to_db(character_name, barcode, region, character_prompt, image):
    """キャラクターをデータベースとStorageに保存"""
    try:
        user_email = st.session_state.user.email if st.session_state.user else None
        if not user_email:
            return {"success": False, "error": "ユーザーが認証されていません"}
        
        # usersテーブルからuser_idを取得
        user_response = supabase.table('users').select('user_id').eq('mail_address', user_email).execute()
        if not user_response.data:
            return {"success": False, "error": "ユーザー情報が見つかりません"}
        
        user_id = user_response.data[0]['user_id']
        
        # 1. 画像をStorageに保存
        file_id = str(uuid.uuid4())
        file_name = f"user_{user_id}/{file_id}.png"
        
        # 画像をバイナリデータに変換
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Supabase Storageにアップロード
        storage_response = supabase.storage.from_("character-images").upload(
            file_name, 
            img_buffer.getvalue(),
            file_options={"content-type": "image/png"}
        )
        
        # 2. キャラクター情報をDBに保存
        character_data = {
            "user_id": user_id,
            "character_name": character_name,
            "barcode": barcode,
            "region": region,
            "power_level": random.randint(100, 999),
            "character_img_url": file_name,
            "character_prompt": character_prompt
        }
        
        db_response = supabase.table('characters').insert(character_data).execute()
        
        if db_response.data:
            return {
                "success": True, 
                "message": "キャラクターを図鑑に保存しました！",
                "character_id": db_response.data[0]['character_id']
            }
        else:
            return {"success": False, "error": "データベース保存に失敗しました"}
            
    except Exception as e:
        return {"success": False, "error": f"保存エラー: {str(e)}"}

# ===== 既存の関数群 =====

# 画像生成する関数
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
    
    #キャラ出力
    data = response.json()
    image_base64 = data["artifacts"][0]["base64"]
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_bytes))
    st.success(f"🎉 新キャラを獲得！")
    st.markdown(f'''キャラクター名： :blue[{character_name}]''')
    st.image(image, use_container_width=True)
    st.write(f"キャラ詳細")
    st.write(f"{sd_prompt}")
    st.write(f"居住地：{region}")

    return sd_prompt, character_name, image

# メイン画面に戻る関数
def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()    

# ログイン画面｜これらはcreate_clientを使うことで呼び出される関数である。
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
        email = st.text_input("メールアドレス", key="login_email") #session_state.login_emailが使えるようになる。
        password = st.text_input("パスワード",type="password",key="login_password")
        if st.button("ログインする",type="primary"):
            try:
                res = sign_in(email,password)
                user = res.user
                if user :
                    st.session_state.user = user
                    st.session_state.full_name = user.user_metadata.get("full_name", user.email)
                    st.success("ログインに成功しました")
                    st.rerun()
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
                st.success("アカウントが作成されました。メールを確認してください。※登録済みの場合はメールが送信されません。")

            except AuthApiError as e:
                # e.code があれば取得
                code = getattr(e, "code", None)
                message = str(e)
                status = getattr(e, "status_code", None)  # or whatever属性があれば

                st.write("error message:", message)
                st.write("error code property:", code)
                st.write("status code:", status)
            
                if "already" in code:
                    st.error("このメールアドレスはすでに登録済みです。")
                elif "validation" in code:
                   st.error("メールアドレスの書き方不適切です。")
                else:
                    st.error("その他のエラー: " + message)

#メイン画面
def main_app():
    # full_name があればそれを、なければ email を表示
    name_to_display = st.session_state.get("full_name", st.session_state.user.email)
    st.subheader(f"{name_to_display} さん、おかえりなさい！")

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
        
            # pyzbar でデコード
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
            number_ok = st.button("✅ 数字OK")

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
            if st.button("✨ 生成する", use_container_width=True):
                sd_prompt, character_name, image = generate_character_image()
                
                # 生成が成功した場合のみ保存オプションを表示
                if sd_prompt and character_name and image:
                    # セッションステートに生成結果を保存
                    st.session_state.generated_character = {
                        "prompt": sd_prompt,
                        "name": character_name,
                        "image": image,
                        "barcode": digits_input if digits_input else "000000000000",
                        "region": selected_pref
                    }

        # 生成されたキャラクターがあれば保存オプションを表示
        if st.session_state.get('generated_character'):
            char = st.session_state.generated_character
            st.markdown("---")
            col_save1, col_save2 = st.columns(2)
            
            with col_save1:
                if st.button("💾 図鑑に保存する", type="primary", use_container_width=True):
                    # DB保存実行
                    with st.spinner("図鑑に保存中..."):
                        result = save_character_to_db(
                            character_name=char["name"],
                            barcode=char["barcode"],
                            region=char["region"],
                            character_prompt=char["prompt"],
                            image=char["image"]
                        )
                    
                    if result["success"]:
                        st.success(f"✅ {result['message']}")
                        st.balloons()
                        # 保存後は生成済みキャラクターをクリア
                        if 'generated_character' in st.session_state:
                            del st.session_state.generated_character
                        st.rerun()
                    else:
                        st.error(f"❌ 保存失敗: {result['error']}")
            
            with col_save2:
                if st.button("🔄 再生成する", use_container_width=True):
                    # 生成済みキャラクターをクリアして再生成
                    if 'generated_character' in st.session_state:
                        del st.session_state.generated_character
                    st.rerun()

        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    # --- 図鑑画面（DB連携版） ---
    elif st.session_state.page == "zukan":
        st.title("📖 キャラクター図鑑")
        
        # キャラクターデータを取得
        characters = get_user_characters()
        
        if characters:
            st.success(f"🎉 {len(characters)}体のキャラクターを発見！")
            
            # キャラクター表示設定
            cols_per_row = 2
            for i in range(0, len(characters), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(characters):
                        char = characters[idx]
                        
                        with col:
                            # キャラクター情報を表示
                            st.markdown(f"### 🎭 {char['character_name']}")
                            
                            # 画像を表示
                            img_url = get_storage_image_url(char['character_img_url'])
                            if img_url:
                                try:
                                    st.image(img_url, use_container_width=True)
                                except Exception:
                                    st.warning("⚠️ 画像読み込みエラー")
                                    st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/300x300?text=No+Image", use_container_width=True)
                            
                            # 詳細情報
                            st.write(f"**🔢 バーコード:** `{char['barcode']}`")
                            st.write(f"**🌍 出身地:** {char['region']}")
                            st.write(f"**⚡ パワー:** {char['power_level']}")
                            st.write(f"**📅 獲得日:** {char['created_at'][:10]}")
                            
                            # 詳細表示
                            with st.expander("🔍 詳細設定"):
                                st.write(f"**キャラID:** {char['character_id']}")
                                if char.get('character_prompt'):
                                    st.write(f"**設定:** {char['character_prompt'][:100]}...")
                            
                            st.divider()
        
        else:
            st.info("🔍 まだキャラクターがいません")
            st.write("バーコードをスキャンして新しいキャラクターを獲得しよう！")
            
            # プレースホルダー画像
            st.image("https://via.placeholder.com/400x200?text=Scan+Barcode+to+Get+Characters!", 
                    use_container_width=True)
        
        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    if st.sidebar.button("ログアウト"):
        sign_out()
        st.rerun()

#　アプリケーション全体の流れを制御する
def check_auth():
    return 'user' in st.session_state

def main():
    if not check_auth():
        login_signup_page()
    else:
        main_app()

if __name__ == "__main__":
    main()