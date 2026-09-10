import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips

SPEC_FILE = Path("/Users/felipe/Downloads/video_specs_diario_oficial_sin_voz.json")
OUTPUT_DIR = Path("/Users/felipe/proyectos/quantuschile.cl/do/output_videos")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

ARTIFACT_DIR = Path("/Users/felipe/.gemini/antigravity-ide/brain/d6504e83-a3d8-439d-a40e-4dfb5e8ccf90")
RESOLUTION = (1080, 1920)
FPS = 30

# Mapa de imágenes reales generadas por IA para el Video 1
VIDEO_1_IMAGES = {
    1: ARTIFACT_DIR / "diario_oficial_video1_scene1_1786390818006.png",
    2: ARTIFACT_DIR / "video1_scene2_document_1786394298637.png",
    3: ARTIFACT_DIR / "video1_scene3_noticeboard_1786394323281.png",
    4: ARTIFACT_DIR / "video1_scene4_clock_1786394368887.png",
    5: ARTIFACT_DIR / "video1_scene5_pensive_1786394440511.png",
    6: ARTIFACT_DIR / "video1_scene6_notification_1786394495937.png"
}

def crop_center_to_916(image_path: Path) -> Path:
    """Adapta y recorta la imagen generada (1024x1024 o 1:1) al formato vertical 1080x1920 (9:16)."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    
    # Redimensionar para cubrir 1080x1920 mantendiendo aspecto
    target_w, target_h = RESOLUTION
    aspect_target = target_w / target_h
    aspect_img = w / h
    
    if aspect_img > aspect_target:
        # Imagen más ancha: escalar según alto
        new_h = target_h
        new_w = int(w * (target_h / h))
    else:
        # Imagen más alta: escalar según ancho
        new_w = target_w
        new_h = int(h * (target_w / w))
        
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Recortar al centro exacto (1080, 1920)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))
    
    out_path = ARTIFACT_DIR / f"cropped_{image_path.name}"
    img_cropped.save(out_path, "PNG")
    return out_path

def crear_ken_burns_clip(image_path: Path, duration: float) -> ImageClip:
    """Aplica movimiento y zoom Ken Burns progresivo sobre la imagen real sin textos superpuestos."""
    cropped_path = crop_center_to_916(image_path)
    base_clip = ImageClip(str(cropped_path)).with_duration(duration)
    return base_clip.resized(lambda t: 1.0 + 0.05 * (t / duration))

def renderizar_video_1():
    data = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    video_spec = data["videos"][0]  # video_1_hook_miedo
    video_id = video_spec["id"]
    
    print(f"\n==========================================")
    print(f"🎬 RENDERIZANDO VIDEO CLEAN (SIN SUBTÍTULOS): {video_spec['title']} ({video_id})")
    print(f"==========================================")
    
    scene_clips = []
    for escena in video_spec["scenes"]:
        scene_id = escena["scene_id"]
        duration = escena["duration"]
        
        img_ia_path = VIDEO_1_IMAGES[scene_id]
        print(f"  -> Procesando Escena {scene_id} con imagen IA: {img_ia_path.name}")
        
        # Generar clip limpio solo con Ken Burns (sin subtítulos)
        final_scene_clip = crear_ken_burns_clip(img_ia_path, duration)
        scene_clips.append(final_scene_clip)
        
    video_final = concatenate_videoclips(scene_clips, method="compose")
    output_path = OUTPUT_DIR / f"{video_id}_clean_no_text.mp4"
    
    print(f"🚀 Exportando video limpio (sin texto/subtítulos) en 1080x1920 (9:16) a: {output_path}...")
    video_final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="fast",
        threads=4
    )
    print(f"✅ VIDEO 1 LIMPIO (SIN SUBTÍTULOS) RENDERIZADO CON ÉXITO: {output_path}\n")

if __name__ == "__main__":
    renderizar_video_1()
