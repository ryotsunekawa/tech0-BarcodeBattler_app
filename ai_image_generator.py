"""
AI画像生成API統合設定ファイル

このファイルは外部のAI画像生成APIとの連携設定を管理します。
開発チームが画像生成AIを実装した際に、ここの設定を更新してください。
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Optional

# 環境変数読み込み
load_dotenv()

class AIImageGenerator:
    """外部AI画像生成API統合クラス"""
    
    def __init__(self):
        """初期化 - 各種AI APIキーを設定"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.stability_ai_key = os.getenv("STABILITY_AI_KEY") 
        self.custom_ai_api_key = os.getenv("CUSTOM_AI_API_KEY")
        self.custom_ai_endpoint = os.getenv("CUSTOM_AI_ENDPOINT")
    
    def generate_character_image(self, character_name: str, character_params: Dict) -> Optional[str]:
        """
        キャラクター画像を生成
        
        Args:
            character_name: キャラクター名
            character_params: キャラクターパラメータ
            
        Returns:
            Optional[str]: 生成された画像URL（失敗時はNone）
        """
        
        # 優先順位: カスタムAPI → OpenAI → Stability AI → プレースホルダー
        
        # 1. カスタムAI API（あなたのチームが開発中のAPI）
        if self.custom_ai_api_key and self.custom_ai_endpoint:
            try:
                return self._generate_with_custom_api(character_name, character_params)
            except Exception as e:
                print(f"カスタムAI APIエラー: {str(e)}")
        
        # 2. OpenAI DALL-E API
        if self.openai_api_key:
            try:
                return self._generate_with_openai(character_name, character_params)
            except Exception as e:
                print(f"OpenAI APIエラー: {str(e)}")
        
        # 3. Stability AI API
        if self.stability_ai_key:
            try:
                return self._generate_with_stability_ai(character_name, character_params)
            except Exception as e:
                print(f"Stability AI APIエラー: {str(e)}")
        
        # 4. フォールバック: プレースホルダー
        return self._generate_placeholder(character_name, character_params)
    
    def _generate_with_custom_api(self, character_name: str, character_params: Dict) -> str:
        """
        カスタムAI APIでキャラクター画像生成
        """
        # プロンプト生成
        prompt = self._create_character_prompt(character_name, character_params)
        
        # API リクエスト
        response = requests.post(
            f"{self.custom_ai_endpoint}/generate",
            json={
                "prompt": prompt,
                "character_name": character_name,
                "parameters": character_params,
                "style": "anime",
                "size": "512x512"
            },
            headers={
                "Authorization": f"Bearer {self.custom_ai_api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("image_url", result.get("url"))
        else:
            raise Exception(f"API応答エラー: {response.status_code}")
    
    def _generate_with_openai(self, character_name: str, character_params: Dict) -> str:
        """
        OpenAI DALL-E APIでキャラクター画像生成
        """
        prompt = self._create_character_prompt(character_name, character_params)
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            json={
                "prompt": prompt,
                "n": 1,
                "size": "512x512"
            },
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["data"][0]["url"]
        else:
            raise Exception(f"OpenAI API応答エラー: {response.status_code}")
    
    def _generate_with_stability_ai(self, character_name: str, character_params: Dict) -> str:
        """
        Stability AI APIでキャラクター画像生成
        """
        prompt = self._create_character_prompt(character_name, character_params)
        
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {self.stability_ai_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 512,
                "width": 512,
                "samples": 1,
                "steps": 30,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Base64画像をURLに変換する処理が必要（実装は省略）
            return "data:image/png;base64," + data["artifacts"][0]["base64"]
        else:
            raise Exception(f"Stability AI API応答エラー: {response.status_code}")
    
    def _create_character_prompt(self, character_name: str, character_params: Dict) -> str:
        """
        キャラクターパラメータからAI用プロンプトを生成
        """
        element = character_params.get('element', 'neutral')
        rarity = character_params.get('rarity', 'common')
        attack = character_params.get('attack', 50)
        defense = character_params.get('defense', 50)
        
        # 属性に応じた描写
        element_descriptions = {
            "知識": "scholarly, wearing glasses, surrounded by books and scrolls",
            "炭酸": "energetic, sparkling aura, dynamic pose",
            "苦味": "sophisticated, dark colors, mysterious atmosphere",
            "紅茶": "elegant, warm colors, gentle expression",
            "和食": "traditional Japanese style, serene, natural elements",
            "火": "fiery, red and orange colors, flames",
            "水": "flowing, blue tones, water elements",
            "土": "earthy, brown and green, nature-based",
            "風": "light, airy, flowing garments"
        }
        
        # レアリティに応じた品質
        rarity_descriptions = {
            "コモン": "simple design",
            "アンコモン": "detailed design with special effects",
            "レア": "elaborate design with magical aura",
            "エピック": "highly detailed with powerful energy effects",
            "レジェンダリー": "legendary quality with divine light and intricate details"
        }
        
        element_desc = element_descriptions.get(element, "neutral character")
        rarity_desc = rarity_descriptions.get(rarity, "simple design")
        
        prompt = f"A cute anime character named {character_name}, {element_desc}, {rarity_desc}, "
        prompt += f"attack power {attack}, defense {defense}, chibi style, high quality digital art"
        
        return prompt
    
    def _generate_placeholder(self, character_name: str, character_params: Dict) -> str:
        """
        プレースホルダー画像URL生成
        """
        element = character_params.get('element', 'unknown')
        color_map = {
            "知識": "blue", "炭酸": "cyan", "苦味": "brown", "紅茶": "orange", 
            "和食": "green", "火": "red", "水": "blue", "土": "brown", "風": "lightgray"
        }
        bg_color = color_map.get(element, "gray")
        
        return f"https://api.dicebear.com/7.x/avataaars/png?seed={character_name}&backgroundColor={bg_color}"

# 使用例
if __name__ == "__main__":
    generator = AIImageGenerator()
    
    # テスト用キャラクターパラメータ
    test_params = {
        "attack": 75,
        "defense": 60,
        "element": "炭酸", 
        "rarity": "レア"
    }
    
    # 画像生成テスト
    image_url = generator.generate_character_image("テストキャラ", test_params)
    print(f"生成された画像URL: {image_url}")