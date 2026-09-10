import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def record_part1_15s():
    video_dir = "/Users/felipe/.gemini/antigravity-ide/brain/12065b10-d1e4-4fee-8ca8-4cd2bb88ed8f/scratch/video_recordings_part1_15s"
    os.makedirs(video_dir, exist_ok=True)
    
    output_mp4 = "/Users/felipe/Downloads/video_pos_ia_parte1_15s.mp4"
    artifact_mp4 = "/Users/felipe/.gemini/antigravity-ide/brain/12065b10-d1e4-4fee-8ca8-4cd2bb88ed8f/video_pos_ia_parte1_15s.mp4"

    print("Iniciando grabación PARTE 1: Primeros 15 Segundos (Full HD 1080x1920)...")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 540, "height": 960},
            device_scale_factor=2,
            record_video_dir=video_dir,
            record_video_size={"width": 1080, "height": 1920}
        )
        page = context.new_page()

        # [00s-05s] Portal Clientes / Selección de Empresa
        print("[00s-05s] Portal Clientes...")
        page.goto("http://127.0.0.1:8083/clientes", wait_until="networkidle")
        time.sleep(5.0)
        
        # [05s-15s] Terminal Punto de Venta & Selección de Productos al Carrito
        print("[05s-15s] Entrando a la Terminal POS y seleccionando productos...")
        page.goto("http://127.0.0.1:8083/pos", wait_until="networkidle")
        time.sleep(2.0)

        print("[07s-10s] Clic en Aceite Multigrado 10W40 (4L)...")
        page.click("#prod-1")
        time.sleep(2.0)

        print("[10s-15s] Clic en Filtro de Aire Industrial XL...")
        page.click("#prod-2")
        time.sleep(4.0)

        video_path = page.video.path()
        context.close()
        browser.close()

    elapsed = time.time() - start_time
    print(f"PARTE 1 completada en {elapsed:.2f} segundos.")
    print(f"Video WebM grabado: {video_path}")
    
    # Convertir a MP4 Full HD (1080x1920, 30 FPS, Bitrate 10M, -crf 18)
    cmd = f"ffmpeg -y -i '{video_path}' -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -b:v 10M -r 30 '{output_mp4}'"
    subprocess.run(cmd, shell=True, check=True)
    
    # Copiar a artifacts
    subprocess.run(f"cp '{output_mp4}' '{artifact_mp4}'", shell=True, check=True)
    print(f"Parte 1 (15s) generada exitosamente en: {output_mp4}")

if __name__ == "__main__":
    record_part1_15s()
