import os
import time
import subprocess
from playwright.sync_api import sync_playwright

def record_full_flow_video():
    video_dir = "/Users/felipe/.gemini/antigravity-ide/brain/12065b10-d1e4-4fee-8ca8-4cd2bb88ed8f/scratch/video_recordings_full_flow"
    os.makedirs(video_dir, exist_ok=True)
    
    output_60s = "/Users/felipe/Downloads/video_pos_ia_completo_60s.mp4"
    artifact_60s = "/Users/felipe/.gemini/antigravity-ide/brain/12065b10-d1e4-4fee-8ca8-4cd2bb88ed8f/video_pos_ia_completo_60s.mp4"
    output_45s = "/Users/felipe/Downloads/video_pos_ia_resto_45s.mp4"
    artifact_45s = "/Users/felipe/.gemini/antigravity-ide/brain/12065b10-d1e4-4fee-8ca8-4cd2bb88ed8f/video_pos_ia_resto_45s.mp4"

    print("Iniciando grabación FULL HD 1080x1920 con Login real, Selección de Empresa Ferretería y POS 4 Fases...")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
            record_video_dir=video_dir,
            record_video_size={"width": 1080, "height": 1920}
        )
        page = context.new_page()

        # ====================================================
        # FASE 0 [00s - 05s]: IMAGEN 1 -> LOGIN (admin / admin123)
        # ====================================================
        print("[00s-05s] Imagen 1: Login con admin y admin123...")
        page.goto("http://127.0.0.1:8083/clientes", wait_until="networkidle")
        time.sleep(4.0)

        # ====================================================
        # FASE 1 [05s - 15s]: IMAGEN 2 -> SELECCIÓN DE EMPRESA & FERRETERÍA
        # ====================================================
        print("[05s-15s] Imagen 2: Selección de Empresa -> Clic en Ferretería Don Manolo...")
        page.goto("http://127.0.0.1:8083/clientes?logged_in=true", wait_until="networkidle")
        time.sleep(3.5)

        print("Ingresando a Ferretería Don Manolo...")
        page.click("form[action='/pos'] button")
        page.wait_for_load_state("networkidle")
        time.sleep(2.5)

        # ====================================================
        # FASE 2 [15s - 30s]: INGRESO DE PRODUCTO & VENTAS CON BOLETA SII
        # ====================================================
        print("[15s-30s] En el POS de Ferretería: Pestaña 1 Ingreso de Mercadería...")
        page.click("#btn-registrar-ingreso")
        time.sleep(3.0)

        print("Cambiando a Pestaña 2: Ventas & Boleta SII...")
        page.click("#tab-btn-ventas")
        time.sleep(2.0)
        page.click("#prod-1")
        time.sleep(1.5)
        page.click("#prod-2")
        time.sleep(2.0)
        page.click("#checkout-btn")
        time.sleep(6.5)

        # ====================================================
        # FASE 3 [30s - 45s]: REVISIÓN DE INVENTARIO
        # ====================================================
        print("[30s-45s] Pestaña 3: Revisión de Inventario (Kardex Ferretería)...")
        page.click("#tab-btn-inventario")
        time.sleep(15.0)

        # ====================================================
        # FASE 4 [45s - 60s]: ALERTA & INFORME PREDICTIVO IA
        # ====================================================
        print("[45s-60s] Navegando al Informe Predictivo de Stock por IA...")
        page.goto("http://127.0.0.1:8083/informe-quiebre-stock-ia", wait_until="networkidle")
        time.sleep(5.0)

        page.evaluate("window.scrollBy({top: 250, behavior: 'smooth'});")
        time.sleep(4.0)

        print("Presionando Orden de Compra IA...")
        if page.is_visible(".cta-reel-btn"):
            page.click(".cta-reel-btn")
            time.sleep(6.0)
        else:
            time.sleep(6.0)

        video_path = page.video.path()
        context.close()
        browser.close()

    elapsed = time.time() - start_time
    print(f"Grabación completa finalizada en {elapsed:.2f} s.")
    print(f"Video WebM grabado: {video_path}")
    
    # Convertir a MP4 Full HD (1080x1920, 30 FPS, Bitrate 10M, -crf 18)
    cmd = f"ffmpeg -y -i '{video_path}' -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -b:v 10M -r 30 '{output_60s}'"
    subprocess.run(cmd, shell=True, check=True)
    subprocess.run(f"cp '{output_60s}' '{artifact_60s}'", shell=True, check=True)

    # Extraer también el tramo de los otros 45 segundos (de los 15s al final)
    cmd_cut = f"ffmpeg -y -ss 00:00:15 -i '{output_60s}' -c copy '{output_45s}'"
    subprocess.run(cmd_cut, shell=True, check=True)
    subprocess.run(f"cp '{output_45s}' '{artifact_45s}'", shell=True, check=True)

    print(f"Video completo de 60s generado en: {output_60s}")
    print(f"Video de los otros 45s generado en: {output_45s}")

if __name__ == "__main__":
    record_full_flow_video()
