"""Shared utilities for scale import into chuxin."""
import json
import os
import uuid
import requests

BASE_URL = os.environ.get("CHUXIN_BASE_URL", "http://localhost:18080")
TOKEN_FILE = "/root/jry/chuxin/scale-imports/.token.json"

def get_token():
    env_token = os.environ.get("CHUXIN_ACCESS_TOKEN")
    if env_token:
        return env_token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            return data.get("accessToken")
    return login()

def login():
    username = os.environ.get("CHUXIN_ADMIN_USERNAME", "scale-importer")
    password = os.environ.get("CHUXIN_ADMIN_PASSWORD", "import123")
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "usernameOrEmail": username,
        "password": password
    })
    resp.raise_for_status()
    data = resp.json()
    token = data["accessToken"]
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"accessToken": token}, f)
    return token

def import_scale(scale_data, dry_run=False, publish=True, overwrite=True):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "content": [scale_data],
        "dry_run": dry_run,
        "publish": publish,
        "overwrite": overwrite,
        "skip_invalid": True
    }
    resp = requests.post(f"{BASE_URL}/api/scale-assessments/import/huaxinyun",
                         headers=headers, json=payload)
    if resp.status_code == 401:
        token = login()
        headers["Authorization"] = f"Bearer {token}"
        resp = requests.post(f"{BASE_URL}/api/scale-assessments/import/huaxinyun",
                             headers=headers, json=payload)
    resp.raise_for_status()
    result = resp.json()
    # Unwrap {"ok": true, "data": {...}} wrapper
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result

def verify_in_db(code):
    import subprocess
    result = subprocess.run(
        ["mysql", "-u", "root", "-p123456", "chuxin", "-e",
         f"SELECT code, title, status FROM scale_surveys WHERE code='{code}';"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def build_scale(title, description, code, questions, dimensions, survey_type="basic"):
    return {
        "id": code,  # Import service uses this as source ID, prepends "huaxinyun-"
        "title": title,
        "description": description,
        "type": survey_type,
        "questions": questions,
        "dimensions": dimensions
    }

def radio_q(order_num, text, options):
    return {
        "text": text,
        "type": "radio",
        "orderNum": order_num,
        "options": [
            {"text": label, "value": str(val), "optionNo": chr(65+i)}
            for i, (label, val) in enumerate(options)
        ]
    }

def likert_5(order_num, text):
    return radio_q(order_num, text, [
        ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
    ])

def dimension(name, code, num, raw_formula, std_formula="", results=None):
    return {
        "dimensionName": name,
        "dimensionCode": code,
        "num": num,
        "evaluateExpression": raw_formula,
        "standardScoreFormula": std_formula,
        "results": results or []
    }

def result_rule(condition, conclusion, suggestion, warning="none"):
    return {
        "evaluateExpression": condition,
        "conclusionAnalysis": conclusion,
        "suggestion": suggestion,
        "assessmentWarning": warning
    }

def q_range(start, end):
    return " + ".join(f"hx_t_{i}" for i in range(start, end+1))
