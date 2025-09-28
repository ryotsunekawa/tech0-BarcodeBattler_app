import os, io, re, json, base64, zipfile, random
from PIL import Image #画像ファイルを使用する（画像生成時）
import streamlit as st #streamlitを使う
# from pyzbar.pyzbar import decode # pyzbarエラー回避のためコメントアウト
from supabase import create_client, AuthApiError #supabaseを使う
#open aiを使う
from openai import OpenAI
from openai import RateLimitError, APIStatusError

#stabilityで使う
from io import BytesIO
from PIL import Image
import requests
import uuid



# .env ファイルを読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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

#SUPABASEを使うための情報
API_URL = get_secret_or_env("SUPABASE_URL")
API_KEY = get_secret_or_env("SUPABASE_ANON_KEY")  # 修正: SUPABASE_KEYからSUPABASE_ANON_KEYに変更
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


# 段階的Auth統合用のヘルパー関数
def get_or_create_user_profile(auth_user_id: str, email: str):
    """
    ユーザープロフィールを取得、または既存ユーザーのauth_user_idを更新
    """
    try:
        # 1. auth_user_idで検索
        response = supabase.table('users').select('*').eq('auth_user_id', auth_user_id).execute()
        if response.data:
            return response.data[0]
        
        # 2. auth_user_idが設定されていない既存ユーザーをmail_addressで検索
        response = supabase.table('users').select('*').eq('mail_address', email).execute()
        if response.data:
            # 既存ユーザーのauth_user_idを更新
            user_record = response.data[0]
            updated_response = supabase.table('users').update({
                "auth_user_id": auth_user_id
            }).eq('user_id', user_record['user_id']).execute()
            
            return updated_response.data[0] if updated_response.data else user_record
        
        # 3. どちらでも見つからない場合はNoneを返す
        return None
        
    except Exception as e:
        st.error(f"プロフィール取得エラー: {str(e)}")
        return None

def create_new_user_profile(auth_user_id: str, email: str, full_name: str = ""):
    """
    新規ユーザーのプロフィールを作成
    """
    try:
        profile_data = {
            "auth_user_id": auth_user_id,  # AuthのUIDを設定
            "mail_address": email,
            "user_name": full_name or email.split('@')[0],  # 名前がなければメールのローカル部分を使用
            "location": ""  # 初期値は空
        }
        
        response = supabase.table('users').insert(profile_data).execute()
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"プロフィール作成エラー: {str(e)}")
        return None

def save_character_to_db(character_data: dict):
    """
    キャラクターをデータベースに保存
    現在のユーザーのuser_id（DB）を使用
    """
    if 'user_profile' not in st.session_state or not st.session_state.user_profile:
        st.error("ユーザープロフィールが見つかりません")
        return False
    
    try:
        # 現在のユーザーのDB user_idを追加
        character_data["user_id"] = st.session_state.user_profile["user_id"]
        
        response = supabase.table('user_operations').insert(character_data).execute()
        
        if response.data:
            st.success("キャラクターをデータベースに保存しました！")
            return True
        else:
            st.error("キャラクター保存に失敗しました")
            return False
            
    except Exception as e:
        st.error(f"キャラクター保存エラー: {str(e)}")
        return False

def get_user_characters():
    """
    現在のユーザーのキャラクター一覧を取得
    """
    if 'user_profile' not in st.session_state or not st.session_state.user_profile:
        return []
    
    try:
        user_id = st.session_state.user_profile["user_id"]
        response = supabase.table('user_operations').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"キャラクター取得エラー: {str(e)}")
        return []


# 画像生成する関数
def generate_character_image():
    # 1. 商品情報取得（テスト用のダミーデータ）
    barcode = st.session_state.get('current_barcode', "4901301446596")
    
    # 簡単な商品名マッピング（実際のAPIの代わり）
    item_mapping = {
        "4901301446596": "アタックZERO パーフェクトスティック",
        "4901480072968": "コクヨ キャンパスノート",
        "4902370517859": "ペプシコーラ 500ml",
        "1234567890123": "テスト商品",
    }
    
    item_name = item_mapping.get(barcode, f"商品番号{barcode}")
    
    product_json = {
        "codeNumber": barcode,
        "codeType": "JAN",
        "itemName": item_name,
        "itemUrl": f"https://www.jancodelookup.com/code/{barcode}/",
        "itemImageUrl": f"https://image.jancodelookup.com/{barcode}.jpg",
        "brandName": "",
        "makerName": "テストメーカー",
        "makerNameKana": "テストメーカー",
        "ProductDetails": []
    }

    # 2. OpenAIでプロンプト生成
    region = st.session_state.get('todoufuken', '東京都')
    if not region:
        st.error("都道府県を選択してください")
        return None, None, None

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
        
        st.success(f"🎉 新キャラを獲得！")
        st.markdown(f'''キャラクター名： :blue[{character_name}]''')
        st.image(image, use_container_width=True)
        st.write(f"キャラ詳細")
        st.write(f"{sd_prompt}")
        st.write(f"居住地：{region}")

        return sd_prompt, character_name, image
        
    except Exception as e:
        st.error(f"キャラクター生成エラー: {str(e)}")
        return None, None, None


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
    st.header("令和版バーコードバトラー（Auth統合版・pyzbarフリー）",divider="gray")
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
                    
                    # プロフィール取得または作成
                    profile = get_or_create_user_profile(user.id, email)
                    if not profile:
                        # 新規ユーザーの場合、プロフィールを作成
                        full_name = user.user_metadata.get("full_name", "")
                        profile = create_new_user_profile(user.id, email, full_name)
                    
                    if profile:
                        st.session_state.user_profile = profile
                        st.session_state.full_name = profile.get("user_name", user.email)
                        st.success("ログインに成功しました")
                        st.rerun()
                    else:
                        st.error("プロフィール設定に失敗しました")
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
                    # 新規ユーザーのプロフィールを作成
                    profile = create_new_user_profile(response.user.id, new_email, new_name)
                    if profile:
                        st.success("アカウントとプロフィールが作成されました。ログインしてください。")
                    else:
                        st.warning("アカウントは作成されましたが、プロフィール作成に失敗しました。ログイン時に再作成されます。")
                else:
                    st.success("アカウントが作成されました。メールを確認してください。※登録済みの場合はメールが送信されません。")

            except AuthApiError as e:
                # e.code があれば取得
                code = getattr(e, "code", None)
                message = str(e)
                status = getattr(e, "status_code", None)  # or whatever属性があれば

                st.write("error message:", message)
                st.write("error code property:", code)
                st.write("status code:", status)
            
                if "already" in str(code):
                    st.error("このメールアドレスはすでに登録済みです。")
                elif "validation" in str(code):
                   st.error("メールアドレスの書き方不適切です。")
                else:
                    st.error("その他のエラー: " + message)
            


#メイン画面

def main_app():
    # プロフィール情報があればそれを、なければ email を表示
    if 'user_profile' in st.session_state and st.session_state.user_profile:
        name_to_display = st.session_state.user_profile.get("user_name", st.session_state.user.email)
        # ユーザー情報をサイドバーに表示
        st.sidebar.success(f"👋 {name_to_display}さん")
        st.sidebar.write(f"📧 {st.session_state.user_profile.get('mail_address')}")
        if st.session_state.user_profile.get('location'):
            st.sidebar.write(f"📍 {st.session_state.user_profile.get('location')}")
        
        # デバッグ情報
        with st.sidebar.expander("🔧 デバッグ情報"):
            st.write(f"Auth UID: {st.session_state.user.id[:8]}...")
            st.write(f"DB user_id: {st.session_state.user_profile['user_id']}")
            auth_linked = "✅" if st.session_state.user_profile.get('auth_user_id') else "❌"
            st.write(f"Auth連携: {auth_linked}")
    else:
        name_to_display = st.session_state.user.email
    
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
        st.title("📷 バーコードスキャン（手入力版）")
        
        # pyzbarの代わりに手動入力機能を提供
        st.info("📝 カメラ機能は現在無効になっています。バーコード番号を直接入力してください。")
        
        # サンプルバーコード
        st.write("**テスト用バーコード例:**")
        sample_codes = [
            ("4901301446596", "アタックZERO パーフェクトスティック"),
            ("4901480072968", "コクヨ キャンパスノート"),  
            ("4902370517859", "ペプシコーラ 500ml"),
            ("1234567890123", "テスト商品")
        ]
        
        for code, name in sample_codes:
            if st.button(f"{code} - {name}"):
                st.session_state.current_barcode = code
                st.success(f"選択されました: {code}")

        # 数字入力
        digits_input = st.text_input(
            "バーコード番号を入力してください",
            value=st.session_state.get('current_barcode', '')
        )
        
        if st.button("✅ バーコード確定") and digits_input:
            st.session_state.current_barcode = digits_input
            st.success(f"バーコード設定: {digits_input}")

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
                if st.session_state.get('current_barcode'):
                    prompt, name, image = generate_character_image()
                    if prompt and name and image:
                        # 保存ボタンを表示
                        col_save1, col_save2 = st.columns(2)
                        with col_save1:
                            if st.button("💾 保存する", type="primary"):
                                # キャラクターデータをデータベースに保存
                                character_data = {
                                    "code_number": st.session_state.generated_character['barcode'],
                                    "item_name": st.session_state.generated_character['item_name'],
                                    "character_name": st.session_state.generated_character['name'],
                                    "character_img_url": f"generated_{uuid.uuid4()}.png",  # 実際の画像URLに置き換え
                                    "character_parameter": {
                                        "prompt": st.session_state.generated_character['prompt'],
                                        "region": st.session_state.generated_character['region'],
                                        "power": random.randint(50, 100),
                                        "attack": random.randint(30, 90),
                                        "defense": random.randint(20, 80),
                                        "speed": random.randint(40, 95)
                                    }
                                }
                                
                                if save_character_to_db(character_data):
                                    # セッション状態の文字配列にも追加（表示用）
                                    st.session_state.characters.append({
                                        'name': name,
                                        'barcode': st.session_state.current_barcode,
                                        'type': 'JAN',
                                        'region': selected_pref,
                                        'power': character_data['character_parameter']['power']
                                    })
                                    st.success("図鑑に登録されました！")
                        with col_save2:
                            if st.button("🚫 保存しない"):
                                st.info("保存をキャンセルしました")
                else:
                    st.warning("まずバーコードを入力してください")

        st.markdown("---")
        if st.button("⬅️ メイン画面へ戻る"):
            go_to("main")

    # --- 図鑑画面 ---
    elif st.session_state.page == "zukan":
        st.title("📖 図鑑")
        
        # データベースからキャラクター一覧を取得
        db_characters = get_user_characters()
        
        if db_characters:
            st.write(f"**登録済みキャラクター数**: {len(db_characters)}体")
            for idx, char in enumerate(db_characters, start=1):
                with st.expander(f"{idx}. {char.get('character_name', '無名キャラ')} - {char.get('item_name', '不明アイテム')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if char.get('character_img_url'):
                            # 実際の画像URLがある場合は表示
                            try:
                                st.image(char['character_img_url'], width=200)
                            except:
                                st.write("🖼️ 画像を表示できませんでした")
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
                                    elif key == 'region':
                                        st.write(f"**出身地**: {value}")
                        
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
        page_title="令和版バーコードバトラー（Auth統合版・pyzbarフリー）",
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