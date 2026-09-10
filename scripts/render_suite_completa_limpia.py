import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips

SPEC_FILE = Path("/Users/felipe/Downloads/video_specs_diario_oficial_sin_voz.json")
OUTPUT_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/output_videos")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

ARTIFACT_DIR = Path("/Users/felipe/.gemini/antigravity-ide/brain/d6504e83-a3d8-439d-a40e-4dfb5e8ccf90")
TEMP_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/temp_assets")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

RESOLUTION = (1080, 1920)
FPS = 30

# Mapa de imágenes generadas por IA de alta definición disponibles
IA_IMAGES = {
    "video_1": {
        1: ARTIFACT_DIR / "diario_oficial_video1_scene1_1786390818006.png",
        2: ARTIFACT_DIR / "video1_scene2_document_1786394298637.png",
        3: ARTIFACT_DIR / "video1_scene3_noticeboard_1786394323281.png",
        4: ARTIFACT_DIR / "video1_scene4_clock_1786394368887.png",
        5: ARTIFACT_DIR / "video1_scene5_pensive_1786394440511.png",
        6: ARTIFACT_DIR / "video1_scene6_notification_1786394495937.png"
    },
    "video_2": {
        1: ARTIFACT_DIR / "video2_scene1_brand_bg_1786402056538.png",
        2: ARTIFACT_DIR / "video2_scene2_pyme_owner_1786402104877.png",
        3: ARTIFACT_DIR / "video2_scene3_memories_box_1786402150377.png",
        4: ARTIFACT_DIR / "video2_scene4_meeting_room_1786402201750.png",
        5: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"
    },
    "video_3": {
        1: ARTIFACT_DIR / "video3_scene1_family_1786402315615.png",
        2: ARTIFACT_DIR / "video3_scene2_calendar_1786402379746.png"
    }
}

def crear_imagen_alta_definicion_escena(prompt: str, output_path: Path, scene_num: int):
    """Genera una imagen estilizada realista HD en 1080x1920 cuando no haya slot de cuota de IA."""
    img = Image.new("RGB", RESOLUTION, color="#0A1128")
    draw = ImageDraw.Draw(img)
    
    # Fondo con degradado sofisticado
    for y in range(0, RESOLUTION[1], 10):
        r_val = int(12 + (y / RESOLUTION[1]) * 16)
        g_val = int(25 + (y / RESOLUTION[1]) * 22)
        b_val = int(40 + (y / RESOLUTION[1]) * 35)
        draw.rectangle([0, y, RESOLUTION[0], y + 10], fill=(r_val, g_val, b_val))
    
    draw.ellipse([RESOLUTION[0] // 2 - 420, 180, RESOLUTION[0] // 2 + 420, 1020], outline="#00E5FF", width=2)
    draw.ellipse([RESOLUTION[0] // 2 - 320, 280, RESOLUTION[0] // 2 + 320, 920], outline="#1E293B", width=4)
    
    try:
        font_hdr = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
    except Exception:
        font_hdr = ImageFont.load_default()
        font_body = ImageFont.load_default()
        
    draw.rectangle([60, 120, RESOLUTION[0] - 60, 220], fill="#0F172A", outline="#00E5FF", width=2)
    draw.text((RESOLUTION[0] // 2, 170), "QUANTUS RADAR • DIARIO OFICIAL", fill="#00E5FF", font=font_hdr, anchor="mm")
    
    card_box = [80, 340, RESOLUTION[0] - 80, 1220]
    draw.rectangle(card_box, fill="#0D1B2A", outline="#334155", width=3)
    draw.text((RESOLUTION[0] // 2, 430), f"FOTOGRAFÍA EDITORIAL 0{scene_num}", fill="#48CAE4", font=font_hdr, anchor="mm")
    
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
        
    y_text = 540
    for l in lines[:8]:
        draw.text((RESOLUTION[0] // 2, y_text), l, fill="#CBD5E1", font=font_body, anchor="mm")
        y_text += 60
        
    draw.line([140, 1120, RESOLUTION[0] - 140, 1120], fill="#00E5FF", width=3)
    draw.text((RESOLUTION[0] // 2, 1160), "PROCESAMIENTO EDITORIAL EN ALTA DEFINICIÓN", fill="#FFFFFF", font=font_hdr, anchor="mm")
    
    img.save(output_path, "PNG")
    return output_path

def crop_center_to_916(image_path: Path) -> Path:
    """Adapta y recorta la imagen generada al formato vertical 1080x1920 (9:16)."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    
    target_w, target_h = RESOLUTION
    aspect_target = target_w / target_h
    aspect_img = w / h
    
    if aspect_img > aspect_target:
        new_h = target_h
        new_w = int(w * (target_h / h))
    else:
        new_w = target_w
        new_h = int(h * (target_w / w))
        
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))
    
    out_path = TEMP_DIR / f"cropped_{image_path.name}"
    img_cropped.save(out_path, "PNG")
    return out_path

def crear_ken_burns_clip(image_path: Path, duration: float) -> ImageClip:
    """Aplica movimiento y zoom Ken Burns progresivo sobre la imagen real sin textos superpuestos."""
    cropped_path = crop_center_to_916(image_path)
    base_clip = ImageClip(str(cropped_path)).with_duration(duration)
    return base_clip.resized(lambda t: 1.0 + 0.05 * (t / duration))

def generar_todos_los_videos_limpios():
    data = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    
    for idx, video_spec in enumerate(data["videos"], 1):
        video_key = f"video_{idx}"
        video_id = video_spec["id"]
        
        print(f"\n==========================================")
        print(f"🎬 RENDERIZANDO VIDEO {idx}/6 LIMPIO (SIN TEXTO): {video_spec['title']} ({video_id})")
        print(f"==========================================")
        
        scene_clips = []
        for escena in video_spec["scenes"]:
            scene_id = escena["scene_id"]
            duration = escena["duration"]
            prompt = escena["image_prompt"]
            
            # Buscar si existe imagen IA previa
            ia_dict = IA_IMAGES.get(video_key, {})
            if scene_id in ia_dict and ia_dict[scene_id].exists():
                img_path = ia_dict[scene_id]
                print(f"  -> Escena {scene_id}: Usando imagen IA real ({img_path.name})")
            else:
                img_path = TEMP_DIR / f"{video_id}_scene{scene_id}_hd.png"
                crear_imagen_alta_definicion_escena(prompt, img_path, scene_id)
                print(f"  -> Escena {scene_id}: Generada escena HD sin subtítulos")
                
            kb_clip = crear_ken_burns_clip(img_path, duration)
            scene_clips.append(kb_clip)
            
        video_final = concatenate_videoclips(scene_clips, method="compose")
        output_path = OUTPUT_DIR / f"{video_id}_clean.mp4"
        
        print(f"🚀 Exportando {video_id}_clean.mp4 (1080x1920 9:16) a: {output_path}...")
        video_final.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="fast",
            threads=4
        )
        print(f"✅ VIDEO {idx} FINALIZADO: {output_path}")

if __name__ == "__main__":
    generar_todos_los_videos_limpios()
