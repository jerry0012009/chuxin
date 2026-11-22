"""P1-19: EQ - Emotional Intelligence Scale (Schutte et al., 1998)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "eq-emotional-intelligence"
IMPORT_CODE = "huaxinyun-eq-emotional-intelligence"

# EQ (Schutte): 33 items, 5-point Likert (1=strongly disagree to 5=strongly agree)
# Reverse items: 5, 28, 33
# Sum 33-165

EQ_5_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
]

QUESTIONS = [
    (1, "我知道何时该向他人倾诉我的个人问题。"),
    (2, "当我遇到障碍时，我会想起曾经面对并克服类似障碍的经历。"),
    (3, "我期望自己在大多数事情上都能做好。"),
    (4, "别人觉得向我倾诉很容易。"),
    (5, "我发现很难理解他人的非语言信息。"),
    (6, "我生命中的一些重大事件促使我重新评估什么是重要的。"),
    (7, "当我的情绪改变时，我会看到新的可能性。"),
    (8, "情绪是让我的生活有价值的事物之一。"),
    (9, "我能意识到自己正在体验的情绪。"),
    (10, "我期望好事发生。"),
    (11, "我喜欢与他人分享我的情绪。"),
    (12, "当我体验到积极情绪时，我知道如何让它持续。"),
    (13, "我会安排让别人开心的活动。"),
    (14, "我会寻找能让自己开心的活动。"),
    (15, "我能意识到自己传递的非语言信息。"),
    (16, "我以给人留下好印象的方式展示自己。"),
    (17, "当我处于积极情绪状态时，解决问题对我来说很容易。"),
    (18, "通过观察他人的面部表情，我能知道他们正在体验的情绪。"),
    (19, "我知道自己的情绪为什么会变化。"),
    (20, "当我处于积极情绪状态时，我能产生新的想法。"),
    (21, "我能控制自己的情绪。"),
    (22, "我能很容易地识别自己正在体验的情绪。"),
    (23, "我通过想象任务的良好结果来激励自己。"),
    (24, "当别人做得好时，我会赞美他们。"),
    (25, "我能意识到他人传递的非语言信息。"),
    (26, "当别人告诉我他生活中的重要事件时，我几乎感觉自己也经历了那个事件。"),
    (27, "当我感受到情绪变化时，我倾向于产生新的想法。"),
    (28, "当我面对挑战时，我会因为相信自己会失败而放弃。"),
    (29, "仅通过观察他人，我就能知道他们的感受。"),
    (30, "当别人情绪低落时，我会帮助他们感觉好起来。"),
    (31, "我利用好情绪帮助自己在面对障碍时坚持不懈。"),
    (32, "通过倾听他人说话的语调，我能判断他们的感受。"),
    (33, "我很难理解人们为什么会那样感受。"),
]

def make_questions():
    return [radio_q(order, text, EQ_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Reverse items: 5, 28, 33 → (6 - value)
    def item_formula(i):
        if i in (5, 28, 33):
            return f"(6 - hx_t_{i})"
        return f"hx_t_{i}"

    sum_formula = " + ".join(item_formula(i) for i in range(1, 34))

    return [
        dimension("情商总分", "eq_total", 1, f"({sum_formula})", "", [
            result_rule("hx_wd_y_1 <= 100", "情商水平较低", "您的情商得分较低，建议在情绪识别和管理方面多加练习。", "low"),
            result_rule("hx_wd_y_1 > 100 && hx_wd_y_1 <= 120", "情商水平中等偏低", "您的情商处于中等偏低水平，仍有提升空间。", "none"),
            result_rule("hx_wd_y_1 > 120 && hx_wd_y_1 <= 135", "情商水平中等", "您的情商处于中等水平，与一般人群平均水平相当（女性均值约131，男性约125）。", "none"),
            result_rule("hx_wd_y_1 > 135 && hx_wd_y_1 <= 150", "情商水平较高", "您的情商得分较高，情绪识别和管理能力良好（与心理咨询师群体均值相当）。", "none"),
            result_rule("hx_wd_y_1 > 150", "情商水平很高", "您的情商得分非常高，在情绪感知、理解和管理方面表现出色。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="情商量表(EQ)",
        description="本问卷帮助了解您感知、理解和管理情绪的能力。共33题，大约需要6分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
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
