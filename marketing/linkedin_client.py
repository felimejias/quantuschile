import os
import json
import urllib.parse
import urllib.request
import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "data" / "linkedin_config.json"
TOKEN_PATH = Path(__file__).parent.parent / "data" / "linkedin_token.json"

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Archivo de configuración {CONFIG_PATH} no encontrado.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_authorization_url(is_local=False):
    config = load_config()
    redirect_uri = config["local_redirect_uri"] if is_local else config["redirect_uri"]
    
    state = "quantus_linkedin_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    params = {
        "response_type": "code",
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": config.get("scope", "w_member_social r_liteprofile openid profile email")
    }
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params)
    return url, state

def exchange_code_for_token(code, is_local=False):
    config = load_config()
    redirect_uri = config["local_redirect_uri"] if is_local else config["redirect_uri"]
    
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": config["client_id"],
        "client_secret": config["client_secret"]
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "QuantusMarketing/1.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            access_token = res_data.get("access_token")
            expires_in = res_data.get("expires_in", 5184000) # Default 60 days
            
            token_info = {
                "access_token": access_token,
                "expires_in": expires_in,
                "raw_response": res_data,
                "sub": res_data.get("sub"),
                "obtained_at": datetime.datetime.now().isoformat()
            }
            
            # Guardar token de forma segura
            with open(TOKEN_PATH, "w", encoding="utf-8") as tf:
                json.dump(token_info, tf, indent=2)
            os.chmod(TOKEN_PATH, 0o600)
            
            return token_info
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} de LinkedIn: {err_body or e.reason}")

def get_stored_token():
    if not TOKEN_PATH.exists():
        return None
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_user_profile(access_token):
    url = "https://api.linkedin.com/v2/userinfo"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "QuantusMarketing/1.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        try:
            url_me = "https://api.linkedin.com/v2/me"
            req_me = urllib.request.Request(url_me, headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "QuantusMarketing/1.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            with urllib.request.urlopen(req_me) as resp_me:
                return json.loads(resp_me.read().decode("utf-8"))
        except Exception:
            return {"name": "Usuario Autorizado Quantus", "sub": "urn:li:person:authorized"}

def post_share(access_token, author_urn, text, title=None, target_url=None):
    """
    Publica un post en el feed de LinkedIn utilizando la API oficial /v2/posts (versión 2024+).
    """
    url = "https://api.linkedin.com/rest/posts"
    
    payload = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED"
    }
    
    if target_url:
        payload["content"] = {
            "article": {
                "source": target_url,
                "title": title or "Noticias Quantus Chile SpA"
            }
        }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202604",
        "X-Restli-Protocol-Version": "2.0.0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    
    with urllib.request.urlopen(req) as resp:
        res_text = resp.read().decode("utf-8")
        headers = dict(resp.headers)
        post_id = headers.get("x-restli-id") or headers.get("X-Restli-Id") or "published_ok"
        return {"id": post_id, "status": resp.status, "response": res_text}
