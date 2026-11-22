#!/usr/bin/env python3
"""Restore Chuxin scale library from tracked JSON and script-only scales."""
import json
import os
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
JSON_DIR = ROOT / "scale-imports" / "json"
HUAXINYUN_ORIGINAL_DIR = ROOT / "scale-imports" / "huaxinyun-original" / "json"
SCRIPT_DIR = ROOT / "scale-imports" / "scripts"
BASE_URL = os.environ.get("CHUXIN_BASE_URL", "http://localhost:18080")

SCRIPT_ONLY = [
    "p66_scs.py",
    "p67_gse.py",
    "p68_gq6.py",
    "p69_ffmq.py",
    "p70_fmps.py",
    "p72_bpns.py",
    "p73_tas20.py",
    "p74_hfs.py",
    "p75_mlq.py",
    "p76_lsas.py",
    "p77_itis.py",
    "p78_ams.py",
    "p79_agq.py",
    "p80_auth.py",
    "p87_ras.py",
    "p88_tscs.py",
    "p89_djgls.py",
    "p90_ptmr.py",
]

HISTORICAL_ORDER = [
    "sd3-dark-triad",
    "mcsds-social-desirability",
    "npi16-narcissism",
    "gad7-anxiety",
    "pss10-stress",
    "bpaq-aggression",
    "bis11-impulsiveness",
    "tipi-personality",
    "lsrp-psychopathy",
    "hsns-narcissism",
    "vast-sadistic",
    "wds-workplace-deviance",
    "cwbc-counterproductive-work",
    "ojs-organizational-justice",
    "mds-moral-disengagement",
    "els-ethical-leadership",
    "panas-affect",
    "grit-s-short-grit",
    "eq-emotional-intelligence",
    "fs-flourishing",
    "oci-r-ocd",
    "rrs-rumination",
    "lies-deception",
    "bfs-bullshitting",
    "ncs6-cognition",
    "lotr-optimism",
    "webexec-executive",
    "cfq-cognition",
    "pcl5-ptsd",
    "asrs-adhd",
    "aq-autism",
    "ucla-loneliness",
    "audit-alcohol",
    "dast10-drugs",
    "k6-distress",
    "brs-resilience",
    "uppsp-impulsivity",
    "spsrq-sensitivity",
    "cpss14-stress",
    "cssrs-suicide-risk",
    "edds-eating-disorder",
    "icu-callous-unemotional",
    "ius27-intolerance-uncertainty",
    "bfi-big-five",
    "crime-delinquency",
    "atq-adult-temperament",
    "ipip-neo120",
    "hexaco-60",
    "loc-control",
    "ei-emotional-intelligence",
    "dissociation",
    "self-monitoring",
    "bidr-impression-management",
    "bidr-self-deception",
    "sensation-seeking",
    "ocd-perfectionism",
    "ipip-ocd-order",
    "ipip-self-consciousness",
    "hypomanic-traits",
    "catpd-personality-disorder",
    "ipc-interpersonal",
    "iri-c",
    "ecr",
    "erq",
    "brief-cope",
    "scs-self-compassion",
    "gse-self-efficacy",
    "gq6-gratitude",
    "ffmq-mindfulness",
    "fmps-perfectionism",
    "pwb-42",
    "bpns-basic-needs",
    "tas20-alexithymia",
    "hfs-forgiveness",
    "mlq-meaning-life",
    "lsas-social-anxiety",
    "itis-growth-mindset",
    "ams-academic-motivation",
    "agq-achievement-goals",
    "authenticity",
    "hsq",
    "bas2",
    "sassv",
    "das",
    "mbiss",
    "its",
    "ras-assertiveness",
    "tscs-self-control",
    "djgls-loneliness",
    "ptmr-prosocial",
]


def login():
    token = os.environ.get("CHUXIN_ACCESS_TOKEN")
    if token:
        return token
    username = os.environ.get("CHUXIN_ADMIN_USERNAME", "admin")
    password = os.environ.get("CHUXIN_ADMIN_PASSWORD", "123456")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"usernameOrEmail": username, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["accessToken"]


def api_request(method, path, token, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers=headers,
        timeout=120,
        **kwargs,
    )
    response.raise_for_status()
    return response.json().get("data")


def import_json_scales(token):
    content = []
    for path in sorted(JSON_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            content.append(json.load(f))
    result = api_request(
        "POST",
        "/api/scale-assessments/import/huaxinyun",
        token,
        json={
            "content": content,
            "dry_run": False,
            "publish": True,
            "overwrite": True,
            "skip_invalid": False,
        },
    )
    print(
        "JSON import:",
        f"total={result['total']}",
        f"imported={result['imported']}",
        f"updated={result['updated']}",
        f"failed={result['failed']}",
    )


def import_script_only_scales(token):
    env = os.environ.copy()
    env["CHUXIN_BASE_URL"] = BASE_URL
    env["CHUXIN_ACCESS_TOKEN"] = token
    for filename in SCRIPT_ONLY:
        path = SCRIPT_DIR / filename
        print(f"Script import: {filename}")
        subprocess.run(["python3", str(path)], cwd=str(ROOT), env=env, check=True)


def import_huaxinyun_original_scales(token):
    content = []
    for path in sorted(HUAXINYUN_ORIGINAL_DIR.glob("survey_*.json")):
        with path.open(encoding="utf-8") as f:
            content.append(json.load(f))
    if not content:
        print("Huaxinyun original import: skipped, no JSON files found")
        return
    result = api_request(
        "POST",
        "/api/scale-assessments/import/huaxinyun",
        token,
        json={
            "content": content,
            "dry_run": False,
            "publish": True,
            "overwrite": True,
            "skip_invalid": False,
        },
    )
    print(
        "Huaxinyun original import:",
        f"total={result['total']}",
        f"imported={result['imported']}",
        f"updated={result['updated']}",
        f"failed={result['failed']}",
    )


def configure_library(token):
    surveys = api_request("GET", "/api/scale-assessments/surveys", token)
    by_code = {survey["code"]: survey for survey in surveys}
    orders = []
    for index, source_id in enumerate(HISTORICAL_ORDER, 1):
        code = f"huaxinyun-{source_id}"
        survey = by_code.get(code)
        if not survey:
            raise RuntimeError(f"Missing imported survey: {code}")
        api_request(
            "PUT",
            f"/api/scale-assessments/surveys/{survey['id']}",
            token,
            json={
                "title": survey["title"],
                "code": survey["code"],
                "description": survey.get("description"),
                "cover_url": survey.get("cover_url"),
                "survey_type": survey.get("survey_type"),
                "status": survey.get("status", "published"),
                "self_test_enabled": True,
                "sort_order": index,
            },
        )
        orders.append({"id": survey["id"], "sort_order": index})
    api_request("PUT", "/api/scale-assessments/surveys/reorder", token, json={"orders": orders})
    free_surveys = api_request("GET", "/api/scale-assessments/free-surveys", token)
    print(f"Configured {len(orders)} scale surveys; free surveys={len(free_surveys)}")


def main():
    token = login()
    import_json_scales(token)
    import_script_only_scales(token)
    configure_library(token)
    import_huaxinyun_original_scales(token)


if __name__ == "__main__":
    main()
