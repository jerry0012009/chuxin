"""P57: IPIP OCD-Order - Need for Order and Cleanliness (强迫性秩序量表)
Foa et al. (1998), IPIP proxy
10 items, 5-point scale. Single dimension: 秩序与清洁.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ipip-ocd-order"
IMPORT_CODE = "huaxinyun-ipip-ocd-order"

OPT_NORMAL = [
    ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
]
OPT_REVERSE = [
    ("非常同意", 1), ("同意", 2), ("不确定", 3), ("不同意", 4), ("非常不同意", 5)
]

# 10 items: (order, text, is_reverse)
# +keyed: higher score = more need for order
# -keyed: reverse scored
QUESTIONS_RAW = [
    (1,  "我做事非常有条理。", False),               # + Am highly organized
    (2,  "我希望一切都能恰到好处。", False),          # + Want everything to be just right
    (3,  "我对杂乱无序不太在意。", True),              # - Am not bothered by disorder (R)
    (4,  "我喜欢秩序和规律。", False),                 # + Love order and regularity
    (5,  "我喜欢保持物品整齐。", False),                # + Like order
    (6,  "我注意不到周围的凌乱。", True),               # - Seldom notice messes (R)  (proxy)
    (7,  "我希望一切都完美无缺。", False),              # + Want everything to add up perfectly
    (8,  "我会确保规则得到遵守。", False),              # + See that rules are observed
    (9,  "我不会被混乱的人所困扰。", True),             # - Am not bothered by messy people (R)
    (10, "我会持续努力直到一切完美。", False),          # + Continue until everything is perfect
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # All 10 items → mean score
    formula = "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10"
    return [
        dimension("秩序与清洁", "order_cleanliness", 1, formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "秩序需求较低",
                "您对秩序和整洁的要求不高，对环境的杂乱容忍度较高，更注重灵活性和随性的生活方式。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "秩序需求中等",
                "您在秩序和灵活性之间保持平衡，能够适应不同的环境状态。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "秩序需求较高",
                "您比较注重秩序和整洁，喜欢有条理的生活和工作环境，做事倾向于追求完美。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "秩序需求很高",
                "您对秩序和整洁有很高的要求，追求一切井井有条。这种特质有助于提升工作效率，但也要注意不要过度追求完美而给自己带来压力。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="强迫性秩序量表(IPIP OCD-Order)",
        description="本问卷帮助了解您对秩序、整洁和规则的重视程度。共10题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_path}")
    print(f"   Questions: {len(scale['questions'])}")
    print(f"   Dimensions: {len(scale['dimensions'])}")

    print("\n--- Dry Run ---")
    result = import_scale(scale, dry_run=True, publish=True)
    print(f"   Importable: {result.get('importable', 0)}")
    print(f"   Publishable: {result.get('publishable', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | issues={item.get('issues')} | warnings={item.get('warnings')}")

    print("\n--- Importing ---")
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}")
    print(f"   Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | id={item.get('survey_id', 'N/A')}")

    print("\n--- DB Verify ---")
    print(verify_in_db(IMPORT_CODE))
