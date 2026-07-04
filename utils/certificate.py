import os
from PIL import Image, ImageDraw, ImageFont
import datetime

def generate_certificate(name, topic, score):
    template_path = os.path.join(os.path.dirname(__file__), "..", "template.jpg")
    output_path = os.path.join(os.path.dirname(__file__), "..", f"cert_{name}.jpg")
    
    # Agar template bo'lmasa, vaqtincha oq fon yaratamiz
    if not os.path.exists(template_path):
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Soddaroq chegara
        draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=5)
    else:
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
    try:
        # Default shriftni ishlatamiz yoki tizimdagi arial.ttf
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    # Matnlarni markazlashtirib yozish (oddiyroq usul)
    text_color = (0, 0, 0)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    draw.text((100, 150), f"Sertifikat", fill=text_color, font=font_large)
    draw.text((100, 250), f"Ism: {name}", fill=text_color, font=font_medium)
    draw.text((100, 320), f"Mavzu: {topic}", fill=text_color, font=font_medium)
    draw.text((100, 390), f"Natija: {score} ta to'g'ri", fill=text_color, font=font_medium)
    draw.text((100, 460), f"Sana: {date_str}", fill=text_color, font=font_medium)
    
    img.save(output_path)
    return output_path
