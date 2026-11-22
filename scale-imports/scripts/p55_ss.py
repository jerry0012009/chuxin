"""P55: 感觉寻求量表(SS)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "sensation-seeking"
IMPORT_CODE = "huaxinyun-sensation-seeking"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我喜欢极限运动"),
    (2, "我想尝试跳伞"),
    (3, "我喜欢高速驾驶的感觉"),
    (4, "我喜欢攀岩等危险活动"),
    (5, "我愿意尝试任何刺激的活动"),
    (6, "我喜欢冒险"),
    (7, "我想体验自由落体的感觉"),
    (8, "我喜欢不安全但刺激的活动"),
    (9, "我喜欢冲浪或滑雪等极限运动"),
    (10, "我愿意去未知的地方探险"),
    (11, "我做事经常不考虑后果"),
    (12, "我喜欢即兴做事而不是提前计划"),
    (13, "我很容易感到无聊"),
    (14, "我需要不断寻找新的刺激"),
    (15, "我喜欢变化多的生活"),
    (16, "我对重复的事情很快失去兴趣"),
    (17, "我经常会一时冲动做决定"),
    (18, "我喜欢新鲜和刺激的体验"),
    (19, "我很难忍受一成不变的生活"),
    (20, "我经常寻求新的感官刺激"),
    (21, "我会为了获得刺激的体验而提前做计划"),
    (22, "我会主动寻找新的冒险机会"),
    (23, "我会精心策划刺激的旅行"),
    (24, "我会为了寻求刺激而参加各种活动"),
    (25, "我会提前安排刺激的活动"),
    (26, "我会为了体验新事物而制定计划"),
    (27, "我会主动参加有挑战性的活动"),
    (28, "我会为自己安排有趣的冒险"),
    (29, "我会寻找机会来挑战自己"),
    (30, "我会主动寻找刺激的体验机会"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("危险感觉寻求", "dangerous_ss", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您较少追求危险刺激的体验。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您对危险刺激的追求适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您喜欢追求危险刺激的体验，愿意冒险。", "none"),
        ]),
        dimension("冲动感觉寻求", "impulsive_ss", 2, "(hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20) / 10", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您的冲动性感觉寻求较低，偏好稳定。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的冲动性感觉寻求适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您容易感到无聊，需要不断寻求新的刺激。", "none"),
        ]),
        dimension("计划性感觉寻求", "planned_ss", 3, "(hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24 + hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30) / 10", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您较少主动规划刺激体验。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您会适度地计划刺激体验。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您善于主动寻找和规划刺激的体验机会。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="感觉寻求量表(SS)",
        description="本问卷帮助了解您对新奇刺激体验的追求倾向，包括冒险、冲动和计划性三个维度。共30题，大约需要6分钟完成。",
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
