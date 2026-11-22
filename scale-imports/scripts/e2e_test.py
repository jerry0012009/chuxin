"""
E2E test for all 28 imported scales.
Tests: start → answer → submit → score → report for each scale.
Also tests multiple answer patterns (low/mid/high) for key scales.
"""
import json, sys, os, requests, random, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import BASE_URL, get_token, TOKEN_FILE

# ─── Auth ───────────────────────────────────────────────────────────
def auth_headers():
    token = get_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def api(method, path, payload=None, retry=True):
    headers = auth_headers()
    url = f"{BASE_URL}{path}"
    if method == "GET":
        resp = requests.get(url, headers=headers)
    else:
        resp = requests.post(url, headers=headers, json=payload or {})
    if resp.status_code == 401 and retry:
        # force re-login
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        headers = auth_headers()
        if method == "GET":
            resp = requests.get(url, headers=headers)
        else:
            resp = requests.post(url, headers=headers, json=payload or {})
    resp.raise_for_status()
    return resp.json().get("data", resp.json())

# ─── All 28 scale codes ─────────────────────────────────────────────
SCALE_CODES = [
    "huaxinyun-sd3-dark-triad",
    "huaxinyun-mcsds-social-desirability",
    "huaxinyun-npi16-narcissism",
    "huaxinyun-gad7-anxiety",
    "huaxinyun-pss10-stress",
    "huaxinyun-bpaq-aggression",
    "huaxinyun-bis11-impulsiveness",
    "huaxinyun-tipi-personality",
    "huaxinyun-lsrp-psychopathy",
    "huaxinyun-hsns-narcissism",
    "huaxinyun-vast-sadistic",
    "huaxinyun-wds-workplace-deviance",
    "huaxinyun-cwbc-counterproductive-work",
    "huaxinyun-ojs-organizational-justice",
    "huaxinyun-mds-moral-disengagement",
    "huaxinyun-els-ethical-leadership",
    "huaxinyun-panas-affect",
    "huaxinyun-grit-s-short-grit",
    "huaxinyun-eq-emotional-intelligence",
    "huaxinyun-fs-flourishing",
    "huaxinyun-oci-r-ocd",
    "huaxinyun-rrs-rumination",
    "huaxinyun-lies-deception",
    "huaxinyun-bfs-bullshitting",
    "huaxinyun-ncs6-cognition",
    "huaxinyun-lotr-optimism",
    "huaxinyun-webexec-executive",
    "huaxinyun-cfq-cognition",
]

# ─── Answer strategies ──────────────────────────────────────────────
def pick_answer_first_option(questions):
    """Pick the first option for every question (simplest baseline)."""
    answers = []
    for q in questions:
        opts = q.get("options", [])
        if opts:
            answers.append({"questionId": q["id"], "myAnswer": opts[0]["id"]})
        else:
            answers.append({"questionId": q["id"], "myAnswer": ""})
    return answers

def pick_answer_last_option(questions):
    """Pick the last option for every question (tests high-score path)."""
    answers = []
    for q in questions:
        opts = q.get("options", [])
        if opts:
            answers.append({"questionId": q["id"], "myAnswer": opts[-1]["id"]})
        else:
            answers.append({"questionId": q["id"], "myAnswer": ""})
    return answers

def pick_answer_middle_option(questions):
    """Pick the middle option for every question (tests moderate path)."""
    answers = []
    for q in questions:
        opts = q.get("options", [])
        if opts:
            mid = len(opts) // 2
            answers.append({"questionId": q["id"], "myAnswer": opts[mid]["id"]})
        else:
            answers.append({"questionId": q["id"], "myAnswer": ""})
    return answers

STRATEGIES = {
    "first": pick_answer_first_option,
    "middle": pick_answer_middle_option,
    "last": pick_answer_last_option,
}

# ─── Test one scale ─────────────────────────────────────────────────
def test_scale(code, strategy_name="middle"):
    """Test a single scale: start → answer → submit → verify report."""
    strategy = STRATEGIES[strategy_name]
    result = {
        "code": code,
        "strategy": strategy_name,
        "started": False,
        "submitted": False,
        "reported": False,
        "dims_scored": 0,
        "dims_with_conclusion": 0,
        "warning_level": "none",
        "errors": [],
        "warnings": [],
    }
    
    try:
        # Step 1: Start free assessment
        data = api("POST", f"/api/scale-assessments/free/{code}/start")
        record_id = data.get("recordId") or data.get("id")
        if not record_id:
            result["errors"].append(f"start: no recordId in response: {list(data.keys())}")
            return result
        result["started"] = True
        
        # Get questions from the record detail
        questions = data.get("questions") or data.get("survey", {}).get("questions") or []
        if not questions:
            # Try fetching the record detail
            detail = api("GET", f"/api/scale-assessments/records/{record_id}")
            questions = detail.get("questions") or detail.get("survey", {}).get("questions") or []
        if not questions:
            result["errors"].append(f"start: no questions found (keys={list(data.keys())})")
            return result
        
        result["question_count"] = len(questions)
        
        # Step 2: Build answers
        answers = strategy(questions)
        
        # Step 3: Submit
        submit_data = api("POST", f"/api/scale-assessments/records/{record_id}/submit",
                         {"answers": answers})
        result["submitted"] = True
        
        # Step 4: Get report
        report = api("GET", f"/api/scale-assessments/records/{record_id}/report")
        result["reported"] = True
        
        # Verify dimensions
        dims = report.get("dimensions") or report.get("dimensionReports") or []
        result["dims_scored"] = len(dims)
        
        for dim in dims:
            if dim.get("conclusion"):
                result["dims_with_conclusion"] += 1
            if dim.get("warningLevel") and dim["warningLevel"] != "none":
                result["warning_level"] = dim["warningLevel"]
            # Check rawScore is a number
            raw = dim.get("rawScore")
            if raw is None or raw == "":
                result["warnings"].append(f"dim '{dim.get('name')}': rawScore is empty")
        
        # Check total score exists
        total = report.get("totalScore")
        if total is None:
            result["warnings"].append("totalScore is null")
        
        # Check overall warning
        overall_warn = report.get("warningLevel") or report.get("warning_level")
        if overall_warn:
            result["warning_level"] = overall_warn
        
        result["total_score"] = total
        result["status"] = report.get("status")
        
    except requests.exceptions.HTTPError as e:
        result["errors"].append(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        result["errors"].append(f"{type(e).__name__}: {str(e)[:200]}")
    
    return result

# ─── Main ───────────────────────────────────────────────────────────
def run_all_tests():
    """Run E2E tests on all 28 scales with middle-option strategy."""
    print(f"{'='*70}")
    print(f"  E2E Scale Import Test — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Testing {len(SCALE_CODES)} scales")
    print(f"{'='*70}\n")
    
    passed = []
    failed = []
    warnings_list = []
    
    for i, code in enumerate(SCALE_CODES, 1):
        short = code.replace("huaxinyun-", "")
        print(f"[{i:2d}/{len(SCALE_CODES)}] {short}...", end=" ", flush=True)
        
        result = test_scale(code, "middle")
        
        if result["errors"]:
            print(f"❌ FAIL — {result['errors'][0]}")
            failed.append(result)
        elif result["dims_scored"] == 0:
            print(f"❌ FAIL — no dimensions scored")
            failed.append(result)
        elif result["dims_with_conclusion"] == 0:
            print(f"⚠️  WARN — dimensions scored but no conclusions triggered")
            warnings_list.append(result)
            passed.append(result)
        else:
            warn_tag = f" [warn={result['warning_level']}]" if result["warning_level"] != "none" else ""
            print(f"✅ PASS — {result['dims_scored']} dims, {result['dims_with_conclusion']} conclusions{warn_tag}")
            passed.append(result)
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.3)
    
    # ─── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  RESULTS: {len(passed)} passed, {len(failed)} failed, {len(warnings_list)} with warnings")
    print(f"{'='*70}")
    
    if failed:
        print(f"\n❌ FAILURES:")
        for r in failed:
            print(f"  - {r['code']}: {r['errors']}")
    
    if warnings_list:
        print(f"\n⚠️  WARNINGS:")
        for r in warnings_list:
            print(f"  - {r['code']}: {r['warnings']}")
    
    # ─── Detailed output ────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  DETAILED RESULTS")
    print(f"{'='*70}")
    for r in passed + failed:
        short = r["code"].replace("huaxinyun-", "")
        status = "✅" if not r["errors"] else "❌"
        score = r.get("total_score", "N/A")
        dims = r.get("dims_scored", 0)
        conc = r.get("dims_with_conclusion", 0)
        warn = r.get("warning_level", "none")
        print(f"  {status} {short:35s} | score={str(score):8s} | dims={dims} | conclusions={conc} | warn={warn}")
    
    return len(failed) == 0

def run_extreme_tests():
    """Test a few key scales with first/last options to verify scoring range."""
    print(f"\n{'='*70}")
    print(f"  EXTREME SCORE TESTS (first vs last option)")
    print(f"{'='*70}\n")
    
    test_scales = [
        "huaxinyun-gad7-anxiety",
        "huaxinyun-pss10-stress", 
        "huaxinyun-oci-r-ocd",
        "huaxinyun-panas-affect",
        "huaxinyun-sd3-dark-triad",
    ]
    
    for code in test_scales:
        short = code.replace("huaxinyun-", "")
        for strategy in ["first", "last"]:
            result = test_scale(code, strategy)
            score = result.get("total_score", "N/A")
            warn = result.get("warning_level", "none")
            dims = result.get("dims_scored", 0)
            errs = result["errors"]
            status = "✅" if not errs else "❌"
            print(f"  {status} {short:25s} [{strategy:5s}] | score={str(score):8s} | dims={dims} | warn={warn}")
            if errs:
                print(f"       errors: {errs}")
            time.sleep(0.3)

if __name__ == "__main__":
    success = run_all_tests()
    run_extreme_tests()
    sys.exit(0 if success else 1)
