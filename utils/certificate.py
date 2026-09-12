import os
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import datetime
import textwrap

def normalize_text(text):
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
        font_name = ImageFont.truetype(font_path, 54)
        font_label = ImageFont.truetype(font_path, 20)
        font_value = ImageFont.truetype(font_path, 28)
        font_id = ImageFont.truetype(font_path, 18)
    except IOError:
        font_name = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_id = ImageFont.load_default()

    img_w, img_h = img.size
    text_color = (13, 27, 42) # Deep navy blue
    gold_color = (212, 175, 55) # Metallic gold
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    
    # Draw centered text helper
    def draw_centered_text(x, y, text, font, fill, max_width=None):
        if max_width:
            # Dynamic font shrinking and wrapping
            current_font = font
            size = current_font.size
            
            # First try shrinking
            while size > 16:
                bbox = draw.textbbox((0, 0), text, font=current_font)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    break
                size -= 2
                try:
                    current_font = ImageFont.truetype(font_path, size)
                except:
                    break
                    
            # If still too wide, wrap to 2 lines
            bbox = draw.textbbox((0, 0), text, font=current_font)
            w = bbox[2] - bbox[0]
            if w > max_width:
                # Wrap text
                avg_char_width = w / len(text) if len(text) > 0 else 1
                max_chars = int(max_width / avg_char_width)
                wrapped_text = textwrap.wrap(text, width=max_chars)
                
                # Draw multiline
                line_y = y
                for line in wrapped_text[:2]: # Max 2 lines
                    l_bbox = draw.textbbox((0, 0), line, font=current_font)
                    lw = l_bbox[2] - l_bbox[0]
                    lh = l_bbox[3] - l_bbox[1]
                    draw.text((x - lw / 2, line_y), line, fill=fill, font=current_font)
                    line_y += lh + 5
                return
            else:
                draw.text((x - w / 2, y), text, fill=fill, font=current_font)
        else:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            draw.text((x - w / 2, y), text, fill=fill, font=font)

    # 1. NAME
    draw_centered_text(img_w / 2, img_h * 0.44, name, font_name, gold_color)
    
    # 2. 3-COLUMN LAYOUT
    safe_left = 100
    safe_right = img_w - 100
    container_width = safe_right - safe_left
    col_width = container_width / 3
    
    col1_center = safe_left + col_width * 0.5
    col2_center = safe_left + col_width * 1.5
    col3_center = safe_left + col_width * 2.5
    
    # ZONE 2: Information section (Raised to avoid the shield in ZONE 3)
    base_y = img_h * 0.54
    val_y = base_y + 35
    
    # Labels
    draw_centered_text(col1_center, base_y, "MAVZU", font_label, gold_color)
    draw_centered_text(col2_center, base_y, "NATIJA", font_label, gold_color)
    draw_centered_text(col3_center, base_y, "SANA", font_label, gold_color)
    
    # Values
    draw_centered_text(col1_center, val_y, topic, font_value, text_color, max_width=col_width - 20)
    draw_centered_text(col2_center, val_y, f"{score} ta to'g'ri", font_value, text_color, max_width=col_width - 20)
    draw_centered_text(col3_center, val_y, date_str, font_value, text_color, max_width=col_width - 20)
    
    # Separators (Thin Gold lines between columns)
    sep_y1 = base_y
    sep_y2 = val_y + 40
    sep_x1 = safe_left + col_width
    sep_x2 = safe_left + col_width * 2
    
    draw.line([(sep_x1, sep_y1), (sep_x1, sep_y2)], fill=gold_color, width=2)
    draw.line([(sep_x2, sep_y1), (sep_x2, sep_y2)], fill=gold_color, width=2)
    
    # ZONE 5: ID at the bottom right corner
    bbox_id = draw.textbbox((0, 0), f"ID: #{cert_id:04d}", font=font_id)
    w_id = bbox_id[2] - bbox_id[0]
    draw.text((img_w - w_id - 40, img_h - 40), f"ID: #{cert_id:04d}", fill=gold_color, font=font_id)
    
    img.save(output_path)
    return output_path
