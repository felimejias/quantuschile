import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips

SPEC_FILE = Path("/Users/felipe/Downloads/video_specs_diario_oficial_sin_voz.json")
OUTPUT_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/output_videos")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
TEMP_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/temp_assets")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

RESOLUTION = (1080, 1920)
FPS = 30

def crear_imagen_escena(prompt: str, text: str, output_path: Path, scene_num: int):
    img = Image.new("RGB", RESOLUTION, color="#0A1128")
    draw = ImageDraw.Draw(img)
    
    for y in range(0, RESOLUTION[1], 10):
        r_val = int(13 + (y / RESOLUTION[1]) * 15)
        g_val = int(27 + (y / RESOLUTION[1]) * 20)
        b_val = int(42 + (y / RESOLUTION[1]) * 35)
        draw.rectangle([0, y, RESOLUTION[0], y + 10], fill=(r_val, g_val, b_val))
    
    draw.ellipse([RESOLUTION[0] // 2 - 400, 200, RESOLUTION[0] // 2 + 400, 1000], outline="#48CAE4", width=2)
    draw.ellipse([RESOLUTION[0] // 2 - 300, 300, RESOLUTION[0] // 2 + 300, 900], outline="#1A365D", width=4)
    
    try:
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
    except Exception:
        font_small = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        
    draw.rectangle([60, 120, RESOLUTION[0] - 60, 220], fill="#1E293B", outline="#00E5FF", width=2)
    draw.text((RESOLUTION[0] // 2, 170), "QUANTUS RADAR • DIARIO OFICIAL", fill="#00E5FF", font=font_small, anchor="mm")
    
    card_box = [80, 350, RESOLUTION[0] - 80, 1200]
    draw.rectangle(card_box, fill="#0F172A", outline="#334155", width=3)
    draw.text((RESOLUTION[0] // 2, 450), f"ESCENA 0{scene_num}", fill="#48CAE4", font=font_small, anchor="mm")
    
    words = prompt.split()
    lines = []
    curr = ""
    for w in words:
        if len(curr + " " + w) < 28:
            curr += " " + w if curr else w
        else:
            lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
        
    y_text = 550
    for l in lines[:8]:
        draw.text((RESOLUTION[0] // 2, y_text), l, fill="#94A3B8", font=font_medium, anchor="mm")
        y_text += 60
        
    draw.line([140, 1100, RESOLUTION[0] - 140, 1100], fill="#00E5FF", width=3)
    draw.text((RESOLUTION[0] // 2, 1140), "NOTIFICACIÓN PREVENTIVA AUTOMÁTICA", fill="#FFFFFF", font=font_small, anchor="mm")
    
    img.save(output_path, "PNG")
    print(f"  [IMAGEN GENERADA] -> {output_path}")
    return output_path

def crear_ken_burns_clip(image_path: Path, duration: float) -> ImageClip:
    base_clip = ImageClip(str(image_path)).with_duration(duration)
    return base_clip.resized(lambda t: 1.0 + 0.05 * (t / duration))

def overlay_texto_pantalla(base_clip: ImageClip, text: str, animation: str) -> CompositeVideoClip:
    w, h = RESOLUTION
    banner_img = Image.new("RGBA", (w - 120, 320), (15, 23, 42, 235))
    b_draw = ImageDraw.Draw(banner_img)
    b_draw.rectangle([0, 0, w - 120, 320], outline="#00E5FF", width=3)
    
    try:
        font_txt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
    except Exception:
        font_txt = ImageFont.load_default()
        
    words = text.split()
    lines = []
    curr = ""
    for w_item in words:
        if len(curr + " " + w_item) < 22:
            curr += " " + w_item if curr else w_item
        else:
            lines.append(curr)
            curr = w_item
    if curr:
        lines.append(curr)
        
    y_off = 50
    for line in lines[:4]:
        b_draw.text(((w - 120) // 2 + 2, y_off + 2), line, fill=(0, 0, 0, 255), font=font_txt, anchor="mm")
        b_draw.text(((w - 120) // 2, y_off), line, fill=(255, 255, 255, 255), font=font_txt, anchor="mm")
        y_off += 60
        
    temp_banner_path = TEMP_DIR / f"banner_{abs(hash(text))}.png"
    banner_img.save(temp_banner_path, "PNG")
    
    txt_clip = ImageClip(str(temp_banner_path)).with_duration(base_clip.duration).with_position(("center", 1350))
    return CompositeVideoClip([base_clip, txt_clip], size=RESOLUTION)

def ensamblar_video(video_spec: dict, estilo_global: str, caption_style: str) -> Path:
    video_id = video_spec["id"]
    print(f"\n==========================================")
    print(f"🎬 PROCESANDO: {video_spec['title']} ({video_id})")
    print(f"==========================================")
    
    scene_clips = []
    for escena in video_spec["scenes"]:
        scene_id = escena["scene_id"]
        duration = escena["duration"]
        prompt = escena["image_prompt"]
        text = escena["on_screen_text"]
        anim = escena.get("caption_animation", "fade_in")
        
        img_path = TEMP_DIR / f"{video_id}_scene{scene_id}.png"
        crear_imagen_escena(prompt, text, img_path, scene_id)
        
        kb_clip = crear_ken_burns_clip(img_path, duration)
        final_scene_clip = overlay_texto_pantalla(kb_clip, text, anim)
        scene_clips.append(final_scene_clip)
        
    video_final = concatenate_videoclips(scene_clips, method="compose")
    output_path = OUTPUT_DIR / f"{video_id}.mp4"
    
    print(f"🚀 Renderizando video HD a 30 FPS: {output_path}...")
    video_final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="fast",
        threads=4
    )
    print(f"✅ FINALIZADO: {output_path}\n")
    return output_path

def main():
    if not SPEC_FILE.exists():
        print(f"❌ Error: Archivo de especificación no encontrado en {SPEC_FILE}")
        return
        
    data = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    estilo_global = data["default_image_style"]
    caption_style = data["default_caption_style"]

    for video_spec in data["videos"]:
        ensamblar_video(video_spec, estilo_global, caption_style)

if __name__ == "__main__":
    main()
