import os
import asyncio
#import numpy as np
import re
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from collections import Counter
from anony import config
from anony.helpers import Track

try:
    from unidecode import unidecode
except ImportError:
    def unidecode(text):
        return text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_TITLE_PATH = os.path.join(BASE_DIR, "font.ttf")
FONT_INFO_PATH = os.path.join(BASE_DIR, "font2.ttf")
TEMPLATE_PATH = os.path.join(BASE_DIR, "..", "assets", "template.jpg")

def safe_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

class Thumbnail:
    def __init__(self):
        self.size = (1280, 720)
        self.font_title = safe_font(FONT_TITLE_PATH, 26)
        self.font_info = safe_font(FONT_INFO_PATH, 20)

    async def start(self):
        os.makedirs("cache", exist_ok=True)
        return True

    async def save_thumb(self, output_path: str, url: str) -> str:
        return output_path

    async def generate(self, song: Track) -> str:
        try:
            # ဘယ်သီချင်းဖွင့်ဖွင့် Default Thumbnail ပုံကိုသာ အမြဲတမ်း တိုက်ရိုက်ပြန်ပေးမည်
            if hasattr(config, "DEFAULT_THUMB") and config.DEFAULT_THUMB:
                return config.DEFAULT_THUMB
            
            return config.DEFAULT_THUMB

        except Exception as e:
            print(f"Error: {e}")
            return config.DEFAULT_THUMB
