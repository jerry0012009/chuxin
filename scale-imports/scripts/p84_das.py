"""P84: DAS 死亡焦虑量表 (Death Anxiety Scale)
Templer (1970), 中文版
15 items, 是/否计分. Single dimension: 死亡焦虑.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "das"
IMPORT_CODE = "huaxinyun-das"

OPT_YN = [("是", 1), ("否", 0)]
OPT_YN_REV = [("否", 0), ("是", 1)]

# Reverse-scored items: 2, 4, 5, 8, 10, 12, 14
QUESTIONS_RAW = [
    (1,  "我非常害怕死亡。", False),
    (2,  "我很少想到死亡。", True),
    (3,  "当别人谈论死亡时，我会感到不安。", False),
    (4,  "想到自己的死亡并不会让我感到焦虑。", True),
    (5,  "我不会因想到自己将不久于人世而感到烦恼。", True),
    (6,  "我经常因为想到死亡而感到特别紧张。", False),
    (7,  "我在深夜想到死亡时会感到恐惧。", False),
    (8,  "面对死亡的形象并不会使我感到不安。", True),
    (9,  "我害怕在痛苦中死去。", False),
    (10, "关于死亡的话题并不会让我感到困扰。", True),
    (11, "我非常害怕患上绝症。", False),
    (12, "我很少被死亡的念头所困扰。", True),
    (13, "当我听到有人去世的消息时，我会感到不安。", False),
    (14, "我很少对死亡感到恐惧。", True),
    (15, "当我知道自己终有一死时，我并不感到担忧。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_YN_REV if is_rev else OPT_YN
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    formula = q_range(1, 15) + " / 15"
    return [
        dimension("死亡焦虑", "death_anxiety", 1, formula, "", [
            result_rule("hx_wd_y_1 <= 0.3", "死亡焦虑水平较低",
                "您对死亡的恐惧和焦虑程度较低，能够较为平静地面对与死亡相关的话题和思考。", "none"),
            result_rule("hx_wd_y_1 > 0.3 && hx_wd_y_1 <= 0.6", "死亡焦虑水平中等",
                "您存在一定程度的死亡焦虑，在特定情境下可能会因死亡相关话题感到不安。这是正常的心理现象。", "none"),
            result_rule("hx_wd_y_1 > 0.6", "死亡焦虑水平较高",
                "您对死亡存在较强的恐惧和焦虑，这可能会在日常生活中造成困扰。建议通过正念练习或心理咨询来缓解死亡焦虑。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="死亡焦虑量表(DAS)",
        description="本量表帮助了解您对死亡的态度和感受。共15题，请根据实际情况选择「是」或「否」，大约需要3分钟完成。",
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
