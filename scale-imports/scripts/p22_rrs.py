"""P2-22: RRS - Rumination Response Scale (Nolen-Hoeksema & Morrow, 1991)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "rrs-rumination"
IMPORT_CODE = "huaxinyun-rrs-rumination"

# RRS: 22 items, 4-point (1=almost never to 4=almost always)
# Single dimension. Sum 22-88. Norms: women ~42, men ~39.6.

QUESTIONS = [
    (1, "我会想：我为什么总是遇到这样的事情？"),
    (2, "我会想：我到底出了什么问题？"),
    (3, "我会独自思考自己的感受。"),
    (4, "我会分析自己最近的经历，试图理解为什么会感到沮丧。"),
    (5, "我会写日记来理解自己的感受。"),
    (6, "我会想：集中注意力很困难。"),
    (7, "我会想：我对正在做的事情无法集中注意力。"),
    (8, "我会想：我为什么反应这么强烈。"),
    (9, "我会独自待着，思考自己的感受。"),
    (10, "我会想：我无法把事情做好，因为我记不住东西。"),
    (11, "我会退一步来审视自己的感受。"),
    (12, "我会去一个安静的地方思考自己的感受。"),
    (13, "我会想：我为什么不能开始做事情？"),
    (14, "我会想：我总是把事情搞砸。"),
    (15, "我会想：我感到非常疲惫。"),
    (16, "我会思考自己是否有身体疾病。"),
    (17, "我会想：我无法完成任务，因为我总是记不住东西。"),
    (18, "我会分析自己的性格，试图理解自己的沮丧。"),
    (19, "我会想：我在社交场合中感到不自在。"),
    (20, "我会想：我对自己的生活不满。"),
    (21, "我会独自思考为什么我会这样感受。"),
    (22, "我会想：我好像对什么都没有动力。"),
]

RRS_OPTIONS = [
    ("从不", 1), ("偶尔", 2), ("经常", 3), ("几乎总是", 4)
]

def make_questions():
    return [radio_q(order, text, RRS_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    total_items = " + ".join(f"hx_t_{i}" for i in range(1, 23))

    return [
        dimension("反刍思维", "rumination", 1, total_items, "", [
            result_rule("hx_wd_y_1 <= 32", "反刍思维水平较低", "您的反刍思维水平较低，面对困境时较少陷入反复思考，应对方式较为健康。", "none"),
            result_rule("hx_wd_y_1 > 32 && hx_wd_y_1 <= 40", "反刍思维水平中等", "您的反刍思维处于正常范围，偶尔会陷入对消极事件的反复思考。", "none"),
            result_rule("hx_wd_y_1 > 40 && hx_wd_y_1 <= 52", "反刍思维水平偏高", "您的反刍思维得分高于平均水平（男均值39.6，女均值42），建议关注是否经常陷入消极思维循环。", "low"),
            result_rule("hx_wd_y_1 > 52", "反刍思维水平异常偏高", "您的反刍思维得分明显偏高，过度的反刍思维与抑郁和焦虑密切相关，建议寻求专业心理帮助。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="反刍思维量表(RRS)",
        description="本问卷帮助了解您在遇到困难或情绪低落时的思维习惯。共22题，大约需要4分钟完成。",
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
