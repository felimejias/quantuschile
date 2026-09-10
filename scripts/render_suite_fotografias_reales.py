import json
import os
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips

SPEC_FILE = Path("/Users/felipe/Downloads/video_specs_diario_oficial_sin_voz.json")
OUTPUT_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/output_videos")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

ARTIFACT_DIR = Path("/Users/felipe/.gemini/antigravity-ide/brain/d6504e83-a3d8-439d-a40e-4dfb5e8ccf90")
STOCK_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/stock_images")
STOCK_DIR.mkdir(exist_ok=True, parents=True)
TEMP_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/temp_assets")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

RESOLUTION = (1080, 1920)
FPS = 30

# Fotografías de Stock reales en Alta Definición por escena
STOCK_URLS = {
    # Video 1: POV te demandaron y no lo sabes
    "video_1_hook_miedo": {
        1: ARTIFACT_DIR / "diario_oficial_video1_scene1_1786390818006.png",  # Imagen IA real
        2: ARTIFACT_DIR / "video1_scene2_document_1786394298637.png",        # Imagen IA real
        3: ARTIFACT_DIR / "video1_scene3_noticeboard_1786394323281.png",     # Imagen IA real
        4: ARTIFACT_DIR / "video1_scene4_clock_1786394368887.png",           # Imagen IA real
        5: ARTIFACT_DIR / "video1_scene5_pensive_1786394440511.png",         # Imagen IA real
        6: ARTIFACT_DIR / "video1_scene6_notification_1786394495937.png"     # Imagen IA real
    },
    # Video 2: 3 cosas que se publican y nadie revisa
    "video_2_lista_educativa": {
        1: ARTIFACT_DIR / "video2_scene1_brand_bg_1786402056538.png",        # Imagen IA real
        2: ARTIFACT_DIR / "video2_scene2_pyme_owner_1786402104877.png",      # Imagen IA real
        3: ARTIFACT_DIR / "video2_scene3_memories_box_1786402150377.png",    # Imagen IA real
        4: ARTIFACT_DIR / "video2_scene4_meeting_room_1786402201750.png",    # Imagen IA real
        5: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"  # Imagen IA real
    },
    # Video 3: La herencia que se enteraron tarde
    "video_3_storytime": {
        1: ARTIFACT_DIR / "video3_scene1_family_1786402315615.png",        # Imagen IA real
        2: ARTIFACT_DIR / "video3_scene2_calendar_1786402379746.png",      # Imagen IA real
        3: "https://images.unsplash.com/photo-1512428559087-560fa5ceab42?w=1080&q=80", # Hands holding phone searching
        4: "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=1080&q=80", # Family sitting zusammen sunset
        5: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"
    },
    # Video 4: Te traduzco una publicación tipo
    "video_4_educativo_documento": {
        1: "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=1080&q=80", # Legal document form close up
        2: "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80", # Legal gavel & documents
        3: "https://images.unsplash.com/photo-1501139083538-0139583c060f?w=1080&q=80", # Clock warning time passing
        4: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=1080&q=80", # Young professional relieved phone
        5: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"
    },
    # Video 5: Un día en la vida del radar
    "video_5_dia_del_radar": {
        1: "https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?w=1080&q=80", # Smartphone push notification 9:03
        2: "https://images.unsplash.com/photo-1555774698-0b77e0d5fac6?w=1080&q=80", # Phone screen notification app 11:47
        3: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1080&q=80", # Dashboard analytics cards 3:15
        4: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1080&q=80", # Person relaxed coffee home evening
        5: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"
    },
    # Video 6: Sabías esto sobre las marcas?
    "video_6_encuesta_interactiva": {
        1: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1080&q=80", # Woman entrepreneur workshop
        2: "https://images.unsplash.com/photo-1600508774634-4e11d34730e2?w=1080&q=80", # Two similar design logos concept
        3: ARTIFACT_DIR / "video2_scene1_brand_bg_1786402056538.png",                 # Brand background for sticker
        4: ARTIFACT_DIR / "video2_scene5_quantus_closing_1786402255002.png"
    }
}

def obtener_imagen_escena(video_id: str, scene_id: int) -> Path:
    """Descarga o recupera la fotografía real de stock/IA para la escena."""
    item = STOCK_URLS.get(video_id, {}).get(scene_id)
    
    if isinstance(item, Path) and item.exists():
        return item
        
    if isinstance(item, str) and item.startswith("http"):
        dest_path = STOCK_DIR / f"{video_id}_scene{scene_id}.jpg"
        if not dest_path.exists():
            print(f"  ⬇️ Descargando foto real de stock para Escena {scene_id}...")
            req = urllib.request.Request(item, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
                f.write(resp.read())
        return dest_path
        
    # Fallback si no hay URL/Path
    fallback_path = STOCK_DIR / f"{video_id}_scene{scene_id}_fallback.jpg"
    if not fallback_path.exists():
        img = Image.new("RGB", RESOLUTION, color="#0F172A")
        img.save(fallback_path)
    return fallback_path

def crop_center_to_916(image_path: Path) -> Path:
    """Recorta y adapta la fotografía real al formato vertical 1080x1920 (9:16)."""
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
    img_cropped.save(out_path, "JPEG" if image_path.suffix.lower() in ('.jpg', '.jpeg') else "PNG")
    return out_path

def crear_ken_burns_clip(image_path: Path, duration: float) -> ImageClip:
    """Aplica movimiento panorámico y zoom continuo Ken Burns (SIN SUBTÍTULOS)."""
    cropped_path = crop_center_to_916(image_path)
    base_clip = ImageClip(str(cropped_path)).with_duration(duration)
    return base_clip.resized(lambda t: 1.0 + 0.05 * (t / duration))

def generar_todos_los_videos_con_imagenes_reales():
    data = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    
    for idx, video_spec in enumerate(data["videos"], 1):
        video_id = video_spec["id"]
        
        print(f"\n==========================================")
        print(f"🎬 RENDERIZANDO VIDEO {idx}/6 CON FOTOGRAFÍAS REALES (SIN SUBTÍTULOS): {video_spec['title']} ({video_id})")
        print(f"==========================================")
        
        scene_clips = []
        for escena in video_spec["scenes"]:
            scene_id = escena["scene_id"]
            duration = escena["duration"]
            
            # Obtener fotografía real (Stock / IA real)
            img_real_path = obtener_imagen_escena(video_id, scene_id)
            print(f"  -> Escena {scene_id}: Procesando fotografía real ({img_real_path.name})")
            
            # Clip limpio en movimiento Ken Burns sin subtítulos
            kb_clip = crear_ken_burns_clip(img_real_path, duration)
            scene_clips.append(kb_clip)
            
        video_final = concatenate_videoclips(scene_clips, method="compose")
        output_path = OUTPUT_DIR / f"{video_id}_fotografias_reales_clean.mp4"
        
        print(f"🚀 Exportando video final en 1080x1920 (9:16) a: {output_path}...")
        video_final.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="fast",
            threads=4
        )
        print(f"✅ VIDEO {idx} CON FOTOGRAFÍAS REALES FINALIZADO CON ÉXITO: {output_path}")

if __name__ == "__main__":
    generar_todos_los_videos_con_imagenes_reales()
