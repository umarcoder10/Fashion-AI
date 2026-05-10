from openai import OpenAI
from PIL import Image
import base64
import time
import os

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_outfit(image_path, style_preference):
    base64_image = image_to_base64(image_path)

    prompt = f"""
Look at this person's photo. Quickly analyze their features.
Based on their {style_preference} preference, give outfit suggestions in this EXACT format:

👤 **Your Look:** [one line description of their features]

👗 **Outfit 1:**
- Top: [specific item + color]
- Bottom: [specific item + color]
- Footwear: [specific item]
- Why it works: [one short sentence]

👗 **Outfit 2:**
- Top: [specific item + color]
- Bottom: [specific item + color]
- Footwear: [specific item]
- Why it works: [one short sentence]

💡 **Style Tips:**
- [tip 1 - one line]
- [tip 2 - one line]

Keep EVERYTHING short. Max 2 lines per point. No long paragraphs.

IMAGE_PROMPT: [short image generation prompt of the best outfit, fashion photography, white background]
"""

    for attempt in range(1):
        try:
            response = client.chat.completions.create(
                model="google/gemma-4-31b-it:free",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            full_response = response.choices[0].message.content

            if "IMAGE_PROMPT:" in full_response:
                parts = full_response.split("IMAGE_PROMPT:")
                suggestion_text = parts[0].strip()
                image_prompt = parts[1].strip()
            else:
                suggestion_text = full_response
                image_prompt = f"{style_preference} outfit fashion photography white background"

            return suggestion_text, image_prompt

        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(60)
            else:
                raise Exception("Failed after all attempts")