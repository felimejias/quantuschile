#!/usr/bin/env python3
"""
Test LinkedIn post with active API version discovery.
"""
import os
import sys
import json
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from marketing.linkedin_client import get_stored_token, get_user_profile

def main():
    token_info = get_stored_token()
    if not token_info or not token_info.get("access_token"):
        print("❌ No access token found.")
        return

    access_token = token_info["access_token"]
    profile = get_user_profile(access_token)
    print(f"👤 Perfil autenticado: {profile.get('name')} (sub: {profile.get('sub')})")
    
    author_urn = f"urn:li:person:{profile['sub']}"
    
    payload = {
        "author": author_urn,
        "commentary": "Radar de Remates Judiciales y Fiscales en Chile — Plataforma Quantus Chile SpA.\n\nMonitoreo continuo de causas judiciales hipotecarias, aduanas y subastas públicas con descuentos de hasta 60% sobre tasación.\n\nRevisa el radar en vivo: https://www.quantuschile.cl/remates\n\n#Inversiones #RematesChile #BienesRaices #Propiedades #LegalTech #QuantusChile",
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED"
    }

    url = "https://api.linkedin.com/rest/posts"
    
    versions_to_try = ["202604", "202603", "202602", "202601", "202512", "202511", "202510", "202509", "202508", "202507", "202506", "202505", "202504", "202503", "202502", "202501"]
    
    for ver in versions_to_try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": ver,
            "X-Restli-Protocol-Version": "2.0.0"
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"✅ ¡PUBLICACIÓN EXITOSA EN LINKEDIN con versión {ver}! HTTP {resp.status}")
                post_urn = resp.headers.get("x-restli-id") or resp.headers.get("X-Restli-Id")
                print(f"📌 Post URN en LinkedIn: {post_urn}")
                return
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode('utf-8', errors='ignore')
            print(f"⚠️ Versión {ver} -> HTTP {e.code}: {err_msg[:100]}")

if __name__ == "__main__":
    main()
