"""P61: 人际环形模型量表(IPC)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ipc-interpersonal"
IMPORT_CODE = "huaxinyun-ipc-interpersonal"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "在社交中我会主动发起对话"),
    (2, "我会在团体中承担领导角色"),
    (3, "我善于说服别人"),
    (4, "我在争论中不会退缩"),
    (5, "我会主动表达自己的观点"),
    (6, "我会在别人犹豫时率先行动"),
    (7, "我喜欢掌控局面"),
    (8, "我在团队中经常充当决策者"),
    (9, "我喜欢和很多人在一起"),
    (10, "我在社交场合中充满活力"),
    (11, "我喜欢和别人聊天"),
    (12, "我很容易和别人建立友谊"),
    (13, "我喜欢参加聚会"),
    (14, "我会主动和陌生人打招呼"),
    (15, "我在人群中感到快乐"),
    (16, "我喜欢热闹的社交活动"),
    (17, "我更喜欢独处"),
    (18, "我不太关心社交活动"),
    (19, "我很少主动和别人交往"),
    (20, "我在社交场合中感到不自在"),
    (21, "我更喜欢安静的环境"),
    (22, "我会避免不必要的社交"),
    (23, "我不喜欢成为关注的焦点"),
    (24, "我在人多的场合会感到疲惫"),
    (25, "我在社交中常常感到紧张"),
    (26, "我会担心别人对我的看法"),
    (27, "我在新场合中会感到不安"),
    (28, "我很难自信地表达自己"),
    (29, "我会因为担心被拒绝而避免社交"),
    (30, "我在别人面前常常感到害羞"),
    (31, "我害怕在公众场合发言"),
    (32, "我会因为社交焦虑而回避活动"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("自信支配", "assured_dominant", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8) / 8", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您在社交中较为被动，不太喜欢主导。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的自信支配程度适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您在社交中自信果断，善于领导和说服。", "none"),
        ]),
        dimension("合群外向", "gregarious_extravert", 2, "(hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16) / 8", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您的社交活跃度较低，偏好独处。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的合群外向程度适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您非常合群外向，喜欢社交活动。", "none"),
        ]),
        dimension("冷漠内向", "aloof_introvert", 3, "(hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20 + hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24) / 8", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您对社交的回避程度较低。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您的冷漠内向程度适中。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您较为冷漠内向，偏好独处和安静环境。", "none"),
        ]),
        dimension("不安顺从", "unassured_submissive", 4, "(hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30 + hx_t_31 + hx_t_32) / 8", "", [
            result_rule("hx_wd_y_4 <= 2.0", "低", "您在社交中较为自信，不太容易紧张。", "none"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "中", "您的社交焦虑程度适中。", "none"),
            result_rule("hx_wd_y_4 > 3.5", "高", "您在社交中容易感到紧张和不安，可能会回避社交场合。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="人际环形模型量表(IPC)",
        description="本问卷帮助了解您在人际交往中的风格特点，包括支配性、温暖度等方面。共32题，大约需要6分钟完成。",
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
