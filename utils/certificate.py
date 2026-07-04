import os
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import datetime

def normalize_text(text):
    # Normalize special unicode characters (like Math Alphanumerics) to standard Latin
    return unicodedata.normalize('NFKD', text)

def generate_certificate(name, topic, score, cert_id):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, "template.jpg")
    name = normalize_text(name)
    output_path = os.path.join(base_dir, f"cert_{name.replace(' ', '_')}.jpg")
    font_path = os.path.join(base_dir, "Roboto-Bold.ttf")
    
    if not os.path.exists(template_path):
        img = Image.new('RGB', (1024, 682), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 1004, 662], outline=(0, 0, 0), width=5)
    else:
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
    try:
        font_name = ImageFont.truetype(font_path, 48)
        font_topic = ImageFont.truetype(font_path, 32)
        font_score = ImageFont.truetype(font_path, 32)
        font_date = ImageFont.truetype(font_path, 24)
        font_id = ImageFont.truetype(font_path, 18)
    except IOError:
        font_name = ImageFont.load_default()
        font_topic = ImageFont.load_default()
        font_score = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_id = ImageFont.load_default()

    img_w, img_h = img.size
    text_color = (13, 27, 42) # Deep navy blue
    gold_color = (212, 175, 55) # Metallic gold
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    
    # Helper for centered text
    def draw_centered_text(y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((img_w - w) / 2, y), text, fill=fill, font=font)

    # Placing text beautifully on the clean image layout
    draw_centered_text(img_h * 0.46, name, font_name, gold_color)
    draw_centered_text(img_h * 0.60, f"Mavzu: {topic}", font_topic, text_color)
    draw_centered_text(img_h * 0.68, f"Natija: {score} ta to'g'ri", font_score, text_color)
    draw_centered_text(img_h * 0.76, f"Sana: {date_str}", font_date, text_color)
    
    # ID at the bottom right corner
    draw.text((img_w - 150, img_h - 50), f"ID: #{cert_id:04d}", fill=gold_color, font=font_id)
    
    img.save(output_path)
    return output_path
