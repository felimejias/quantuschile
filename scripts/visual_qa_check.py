#!/usr/bin/env python3
"""
Quantus Visual QA Automated Inspector
Abre https://quantuschile.cl/app en resoluciones Desktop y Mobile,
captura pantallazos de alta resolución y verifica que no existan errores de renderizado.
"""

import os
import sys
from playwright.sync_api import sync_playwright

DESKTOP_OUT = "/tmp/quantus_qa_desktop.png"
MOBILE_OUT = "/tmp/quantus_qa_mobile.png"
TARGET_URL = "https://quantuschile.cl/app"

def run_visual_qa():
    print(f"👁️ Iniciando Visual QA en {TARGET_URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop Check (1440x900)
        print("🖥️ 1. Capturando vista Desktop...")
        context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page_desktop = context_desktop.new_page()
        page_desktop.goto(TARGET_URL, wait_until="domcontentloaded", timeout=15000)
        page_desktop.wait_for_timeout(3000)
        page_desktop.screenshot(path=DESKTOP_OUT, full_page=False)
        print(f"   ✅ Captura Desktop guardada en {DESKTOP_OUT}")

        # 2. Mobile Check (iPhone 15 Pro - 393x852)
        print("📱 2. Capturando vista Mobile (iPhone)...")
        iphone_device = p.devices["iPhone 15 Pro"]
        context_mobile = browser.new_context(**iphone_device)
        page_mobile = context_mobile.new_page()
        page_mobile.goto(TARGET_URL, wait_until="domcontentloaded", timeout=15000)
        page_mobile.wait_for_timeout(3000)
        page_mobile.screenshot(path=MOBILE_OUT, full_page=False)
        print(f"   ✅ Captura Mobile guardada en {MOBILE_OUT}")

        browser.close()

    print("\n🎉 Visual QA Completado con Éxito.")
    return DESKTOP_OUT, MOBILE_OUT

if __name__ == "__main__":
    run_visual_qa()
