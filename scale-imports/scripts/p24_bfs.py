"""P2-24: BFS - Bullshitting Frequency Scale (Jastrzębski et al., 2022)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bfs-bullshitting"
IMPORT_CODE = "huaxinyun-bfs-bullshitting"

# BFS: 12 items, 5-point (1=never to 5=all the time)
# Persuasive bullshitting (items 1-8), Evasive bullshitting (items 9-12)
# Mean per subscale. Norms: overall ~2.57.

QUESTIONS = [
    # Persuasive Bullshitting (1-8)
    (1, "我会在不真正了解某个话题的情况下发表自己的看法。"),
    (2, "我会用听起来很专业但自己并不完全理解的术语。"),
    (3, "我会自信地谈论自己知之甚少的事情。"),
    (4, "在讨论中，我会编造一些听起来合理的论据。"),
    (5, "即使对某个话题不太了解，我也会试图说服别人。"),
    (6, "我会使用夸张的数字或统计数据来支持自己的观点。"),
    (7, "在社交场合中，我会对各种话题发表权威性的意见。"),
    (8, "我会引用自己并不确定来源的信息来增强说服力。"),
    # Evasive Bullshitting (9-12)
    (9, "当被问到不知道答案的问题时，我会转移话题。"),
    (10, "面对我不确定的问题，我会给出模糊但听起来合理的回答。"),
    (11, "当被问到不想回答的问题时，我会用一些不相关的话来搪塞。"),
    (12, "我会用看似深奥的废话来回避直接回答问题。"),
]

BFS_OPTIONS = [
    ("从不", 1), ("很少", 2), ("有时", 3), ("经常", 4), ("总是", 5)
]

def make_questions():
    return [radio_q(order, text, BFS_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    persuasive_items = " + ".join(f"hx_t_{i}" for i in range(1, 9))
    evasive_items = " + ".join(f"hx_t_{i}" for i in range(9, 13))

    return [
        dimension("说服性吹牛", "persuasive_bs", 1, f"({persuasive_items}) / 8", "", [
            result_rule("hx_wd_y_1 <= 1.5", "说服性吹牛水平较低", "您很少在不了解话题的情况下发表看法或试图说服他人，沟通风格诚实。", "none"),
            result_rule("hx_wd_y_1 > 1.5 && hx_wd_y_1 <= 2.5", "说服性吹牛水平中等", "您偶尔会对自己不太了解的话题发表看法，这在社交中较为常见。", "none"),
            result_rule("hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 3.5", "说服性吹牛水平偏高", "您较频繁地在不了解的情况下发表权威性意见，建议关注沟通的准确性。", "low"),
            result_rule("hx_wd_y_1 > 3.5", "说服性吹牛水平异常偏高", "您的说服性吹牛得分明显偏高，这种行为可能影响他人对您可信度的评价。", "middle"),
        ]),
        dimension("回避性吹牛", "evasive_bs", 2, f"({evasive_items}) / 4", "", [
            result_rule("hx_wd_y_2 <= 1.5", "回避性吹牛水平较低", "您很少使用模糊或回避的方式来应对不确定的问题，沟通风格直接。", "none"),
            result_rule("hx_wd_y_2 > 1.5 && hx_wd_y_2 <= 2.5", "回避性吹牛水平中等", "您偶尔会使用回避性回答，这在日常社交中较为常见。", "none"),
            result_rule("hx_wd_y_2 > 2.5 && hx_wd_y_2 <= 3.5", "回避性吹牛水平偏高", "您较频繁地使用回避性吹牛来应对不确定的问题，建议练习更直接的表达方式。", "low"),
            result_rule("hx_wd_y_2 > 3.5", "回避性吹牛水平异常偏高", "您的回避性吹牛得分明显偏高，建议关注这种行为模式对沟通效果的影响。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="吹牛频率量表(BFS)",
        description="本问卷帮助了解您在面对不熟悉话题时的回答倾向。共12题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
    )

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
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
