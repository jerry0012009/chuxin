"""P48: HEXACO-60 六大人格量表"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "hexaco-60"
IMPORT_CODE = "huaxinyun-hexaco-60"

OPT_NORMAL = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]
OPT_REVERSE = [
    ("非常准确", 1), ("比较准确", 2), ("不确定", 3), ("比较不准确", 4), ("非常不准确", 5)
]

QUESTIONS_RAW = [
    (1, "如果有机会作弊而不被发现，我会作弊", True),
    (2, "我会接受贿赂", True),
    (3, "我会假装喜欢那些对我有用的人", True),
    (4, "我不会因为有人拥有我想要的东西就去偷", False),
    (5, "我不会为了得到好处而奉承别人", False),
    (6, "我认为我比大多数人更值得获得特殊待遇", True),
    (7, "我想要别人仰慕我", True),
    (8, "我觉得自己应该得到特别优待", True),
    (9, "我想要别人注意到我", True),
    (10, "我觉得我比别人更重要", True),
    (11, "我会因为别人的情绪而受到影响", False),
    (12, "看到别人哭的时候我也会想哭", False),
    (13, "我会为别人的不幸感到难过", False),
    (14, "当朋友向我倾诉他们的问题时，我会感到担忧", False),
    (15, "面对危急情况我会恐慌", False),
    (16, "面对令人害怕的情况时我会感到紧张", False),
    (17, "我会因为压力而失眠", False),
    (18, "我害怕很多事物", False),
    (19, "我在有压力的情况下会感到不知所措", False),
    (20, "我经常担心自己的健康", False),
    (21, "我喜欢和别人聊天", False),
    (22, "我喜欢有很多人的社交场合", False),
    (23, "我在社交场合中感到自在", False),
    (24, "我喜欢成为大家注意的焦点", False),
    (25, "我能轻松地让别人感到放松", False),
    (26, "我在社交中充满活力", False),
    (27, "我能和各种各样的人相处融洽", False),
    (28, "我喜欢人多热闹的场合", False),
    (29, "我能很快和陌生人打成一片", False),
    (30, "我在大型聚会上感到快乐", False),
    (31, "我会体谅别人的感受", False),
    (32, "我会原谅别人的过错", False),
    (33, "我尊重别人的意见即使不同意", False),
    (34, "我会耐心地对待别人的缺点", False),
    (35, "我会容忍别人的不同观点", False),
    (36, "我对别人很友善", False),
    (37, "我愿意帮助有需要的人", False),
    (38, "我能和很难相处的人合作", False),
    (39, "我会考虑别人的感受", False),
    (40, "我很少对别人发脾气", False),
    (41, "我会提前做好计划", False),
    (42, "我的工作很有条理", False),
    (43, "我会按时完成任务", False),
    (44, "我做事很认真", False),
    (45, "我会坚持把工作做完", False),
    (46, "我会遵守承诺", False),
    (47, "我会仔细检查工作中的错误", False),
    (48, "我做事有始有终", False),
    (49, "我会为未来做准备", False),
    (50, "我的工作质量很高", False),
    (51, "我对抽象的概念感兴趣", False),
    (52, "我喜欢思考复杂的哲学问题", False),
    (53, "我对各种艺术形式感兴趣", False),
    (54, "我喜欢尝试新事物", False),
    (55, "我有丰富的想象力", False),
    (56, "我对不同文化感兴趣", False),
    (57, "我喜欢阅读深度文章", False),
    (58, "我对科学发现感兴趣", False),
    (59, "我能理解抽象的概念", False),
    (60, "我喜欢学习新的知识", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [
        dimension("诚实-谦逊", "honesty_humility", 1, q_range(1, 10), "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您在诚实-谦逊维度上得分较低，倾向于关注个人利益和社会地位。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您在诚实-谦逊维度上得分中等。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您在诚实-谦逊维度上得分较高，为人真诚谦逊，不追求特权。", "none"),
        ]),
        dimension("情绪性", "emotionality", 2, q_range(11, 20), "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您在情绪性维度上得分较低，情绪较为稳定。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您在情绪性维度上得分中等。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您在情绪性维度上得分较高，情感丰富，共情能力强。", "none"),
        ]),
        dimension("外向性", "extraversion", 3, q_range(21, 30), "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您在外向性维度上得分较低，偏好安静独处。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您在外向性维度上得分中等。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您在外向性维度上得分较高，社交活跃，精力充沛。", "none"),
        ]),
        dimension("宜人性", "agreeableness", 4, q_range(31, 40), "", [
            result_rule("hx_wd_y_4 <= 2.0", "低", "您在宜人性维度上得分较低，可能较为挑剔或固执。", "none"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "中", "您在宜人性维度上得分中等。", "none"),
            result_rule("hx_wd_y_4 > 3.5", "高", "您在宜人性维度上得分较高，待人友善，善于合作。", "none"),
        ]),
        dimension("尽责性", "conscientiousness", 5, q_range(41, 50), "", [
            result_rule("hx_wd_y_5 <= 2.0", "低", "您在尽责性维度上得分较低，做事较为随意。", "none"),
            result_rule("hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "中", "您在尽责性维度上得分中等。", "none"),
            result_rule("hx_wd_y_5 > 3.5", "高", "您在尽责性维度上得分较高，做事认真负责。", "none"),
        ]),
        dimension("开放性", "openness", 6, q_range(51, 60), "", [
            result_rule("hx_wd_y_6 <= 2.0", "低", "您在开放性维度上得分较低，偏好传统和熟悉的事物。", "none"),
            result_rule("hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "中", "您在开放性维度上得分中等。", "none"),
            result_rule("hx_wd_y_6 > 3.5", "高", "您在开放性维度上得分较高，思维开阔，善于接受新事物。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="六大人格量表(HEXACO-60)",
        description="本问卷帮助了解您在诚实谦逊、情绪管理、社交倾向等六大人格维度上的特点。共60题，大约需要10分钟完成。",
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
