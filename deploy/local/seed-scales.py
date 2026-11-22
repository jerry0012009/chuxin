"""Initialize the questionnaire library on the isolated local Compose backend."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "scale-imports" / "scripts"))
import restore_scales as scales


def seed():
    token = scales.login()
    surveys_path = "/api/scale-assessments/surveys"
    curated = {f"huaxinyun-{code}" for code in scales.HISTORICAL_ORDER}
    original = {
        f"huaxinyun-{path.stem.removeprefix('survey_')}"
        for path in scales.HUAXINYUN_ORIGINAL_DIR.glob("survey_*.json")
    }
    if len(curated) != 90 or len(original) != 66:
        raise RuntimeError("Incomplete questionnaire sources: expected 90 curated and 66 original")

    existing = scales.api_request("GET", surveys_path, token)
    expected = curated | original
    if existing:
        if expected.issubset({survey["code"] for survey in existing}):
            print("Questionnaire library already present; leaving it unchanged.")
            return
        raise RuntimeError("Local questionnaire library is partial; refusing to overwrite existing data")

    scales.import_json_scales(token)
    scales.import_script_only_scales(token)
    scales.configure_library(token)
    scales.import_huaxinyun_original_scales(token)

    surveys = scales.api_request("GET", surveys_path, token)
    published = {survey["code"] for survey in surveys if survey["status"] == "published"}
    self_tests = {survey["code"] for survey in surveys if survey["self_test_enabled"]}
    if published != expected or self_tests != curated:
        raise RuntimeError("Questionnaire verification failed: expected 156 published and 90 self-tests")
    print(f"Questionnaire library ready: {len(published)} published, {len(self_tests)} self-tests.")


if __name__ == "__main__":
    seed()
