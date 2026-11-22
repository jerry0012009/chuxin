"""P71: Ryff心理幸福感量表 (Psychological Well-Being Scale, 42-item)
Ryff (1989), 中文修订版
42 items, 6-point scale (1=非常同意 ~ 6=很不同意).
6 dimensions: 自主/环境掌控/个人成长/积极关系/生活目的/自我接纳
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "pwb-42"
IMPORT_CODE = "huaxinyun-pwb-42"

OPT_NORMAL = [
    ("非常同意", 1), ("同意", 2), ("有点同意", 3),
    ("有点不同意", 4), ("不同意", 5), ("很不同意", 6)
]
OPT_REVERSE = [
    ("很不同意", 1), ("不同意", 2), ("有点不同意", 3),
    ("有点同意", 4), ("同意", 5), ("非常同意", 6)
]

# 42 items: (order, text, is_reverse)
# Dimension assignments:
#   自主(Autonomy): 1, 10, 13, 16, 19, 21, 24
#   环境掌控(Environmental Mastery): 3, 12, 15, 20, 22, 25, 42
#   个人成长(Personal Growth): 2, 5, 7, 14, 17, 28, 37
#   积极关系(Positive Relations): 4, 8, 18, 27, 30, 38
#   生活目的(Purpose in Life): 6, 9, 11, 29, 32, 33, 39
#   自我接纳(Self-Acceptance): 31, 34, 35, 36, 40, 41
QUESTIONS_RAW = [
    (1,  "即使与多数人的意见分歧，我也不怕发表自己的意见。", False),
    (2,  "对我来说，生活是一个不断学习、变化和成长的过程。", False),
    (3,  "总的来说，我觉得我要对我的生活状况负责。", False),
    (4,  "人们认为我是一个肯付出并且愿意和他人分享自己的时间的人。", False),
    (5,  "对那些能扩展自己眼界的活动，我都不感兴趣。", True),
    (6,  "我喜欢为将来定下计划并努力去实践。", False),
    (7,  "依我看，无论什么年纪的人都能继续成长和发展。", False),
    (8,  "对我来说，与人保持亲密的关系很困难，而且令我感到沮丧。", True),
    (9,  "我得过且过，从没真正的思考过未来。", True),
    (10, "我比较在意别人对我的看法。", True),
    (11, "我并不很理解生活中我要做的事情的意义。", True),
    (12, "我难以用一种令我满意的方式来安排生活。", True),
    (13, "我的决定很少受他人的影响。", False),
    (14, "我早就不想对自己的生活作出重大的改善或改变了。", True),
    (15, "每天的生活需求经常令我感到沮丧。", True),
    (16, "如果朋友和家人不同意，我常常会改变自己的决定。", True),
    (17, "我认为，获得新经验是十分重要的。这些经验可以挑战我们对自己和对世界的既定看法。", False),
    (18, "我很少与别人有彼此关怀、互相信任的关系。", True),
    (19, "我很在意别人怎样评价我在生活中做出的选择。", True),
    (20, "我对于日常生活中许多职责都处理得很好。", False),
    (21, "我不是按别人的标准，而是按自己认为重要的标准来衡量自己。", False),
    (22, "我很难融入周围的人及环境。", True),
    (23, "我对于生活有明确的目标和方向。", False),
    (24, "我很容易被那些很有主见的人影响。", True),
    (25, "我不喜欢那些需要我改变以往处事方式的新环境。", True),
    (26, "总的来说，我对自己是肯定的，并对自己充满信心。", False),
    (27, "我和我的朋友都认为我们之间是可以互相信任的。", False),
    (28, "回顾过去，我觉得自己并没有真正的取得进步。", True),
    (29, "有些人生活没有目标，但我不是这样的人。", False),
    (30, "我经常感到孤独，因为我很少有好朋友可以为我分忧。", True),
    (31, "当我把自己和朋友、熟人相比时，我的自我感觉良好。", False),
    (32, "我不太清楚自己的人生目标是什么。", True),
    (33, "有时我感到已经做完了一生中所有要做的事情。", True),
    (34, "我觉得我认识的许多人在生活中得到的比我多。", True),
    (35, "即使与人们的观点相悖，我仍然坚信自己的观点。", False),
    (36, "我已按照自己喜欢的方式营建家庭和生活方式。", False),
    (37, "随着时间的流逝，我感到自己成长了很多。", False),
    (38, "我很喜欢与家人或朋友作深入的沟通，彼此了解。", False),
    (39, "我的日常活动看起来既琐碎又微不足道。", True),
    (40, "我对自己的性格大致感到满意。", False),
    (41, "对我来说很难在有争议的问题上发表自己的见解。", True),
    (42, "我常常被自己所承担的责任压得喘不过气来。", True),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    auto = "hx_t_1 + hx_t_10 + hx_t_13 + hx_t_16 + hx_t_19 + hx_t_21 + hx_t_24"
    em = "hx_t_3 + hx_t_12 + hx_t_15 + hx_t_20 + hx_t_22 + hx_t_25 + hx_t_42"
    pg = "hx_t_2 + hx_t_5 + hx_t_7 + hx_t_14 + hx_t_17 + hx_t_28 + hx_t_37"
    pr = "hx_t_4 + hx_t_8 + hx_t_18 + hx_t_27 + hx_t_30 + hx_t_38"
    pl = "hx_t_6 + hx_t_9 + hx_t_11 + hx_t_23 + hx_t_29 + hx_t_32 + hx_t_33 + hx_t_39"
    sa = "hx_t_26 + hx_t_31 + hx_t_34 + hx_t_35 + hx_t_36 + hx_t_40 + hx_t_41"

    def rules(dim_num):
        return [
            result_rule(f"hx_wd_y_{dim_num} <= 2.5", "低",
                "该维度得分较低，说明您在该方面的心理幸福感有待提升。建议关注自身需求，寻求积极的改变。", "none"),
            result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.5", "中",
                "该维度得分中等，说明您在该方面的心理幸福感处于一般水平。", "none"),
            result_rule(f"hx_wd_y_{dim_num} > 4.5", "高",
                "该维度得分较高，说明您在该方面具有较好的心理幸福感。", "none"),
        ]

    return [
        dimension("自主", "autonomy", 1, f"({auto}) / 7", "", rules(1)),
        dimension("环境掌控", "env_mastery", 2, f"({em}) / 7", "", rules(2)),
        dimension("个人成长", "personal_growth", 3, f"({pg}) / 7", "", rules(3)),
        dimension("积极关系", "positive_relations", 4, f"({pr}) / 6", "", rules(4)),
        dimension("生活目的", "purpose_life", 5, f"({pl}) / 8", "", rules(5)),
        dimension("自我接纳", "self_acceptance", 6, f"({sa}) / 7", "", rules(6)),
    ]

def build():
    return build_scale(
        title="Ryff心理幸福感量表",
        description="本问卷帮助了解您在自主、环境掌控、个人成长、积极关系、生活目的和自我接纳六个方面的心理幸福感。共42题，大约需要10分钟完成。",
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
