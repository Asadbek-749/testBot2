import os
from PIL import Image, ImageDraw, ImageFont
import datetime

def generate_certificate(name, topic, score):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, "template.jpg")
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
        font_huge = ImageFont.truetype(font_path, 70)
        font_large = ImageFont.truetype(font_path, 40)
        font_medium = ImageFont.truetype(font_path, 30)
    except IOError:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    img_w, img_h = img.size
    text_color = (13, 27, 42) # Deep navy blue
    gold_color = (212, 175, 55) # Metallic gold
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    
    # Helper for centered text
    def draw_centered_text(y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((img_w - w) / 2, y), text, fill=fill, font=font)

    # Placing text beautifully on the image
    draw_centered_text(img_h * 0.40, name, font_huge, gold_color)
    draw_centered_text(img_h * 0.55, f"Mavzu: {topic}", font_large, text_color)
    draw_centered_text(img_h * 0.65, f"Natija: {score} ta to'g'ri", font_large, text_color)
    draw_centered_text(img_h * 0.75, f"Sana: {date_str}", font_medium, text_color)
    
    img.save(output_path)
    return output_path
