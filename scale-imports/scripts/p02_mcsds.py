"""P0-2: MC-SDS - Marlowe-Crowne Social Desirability Scale (Crowne & Marlowe, 1960)
33 True/False items measuring social desirability bias.
Scoring: T-keyed items score 1 for True; F-keyed items score 1 for False.
Total score 0-33. Thresholds: 0-8 low, 9-19 average, 20-33 high.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "mcsds-social-desirability"
IMPORT_CODE = "huaxinyun-mcsds-social-desirability"

# Items: (order_num, Chinese_text, scoring_key)
# T = True response scores 1; F = False response scores 1
ITEMS = [
    (1,  "在投票前，我会彻底调查所有候选人的资格。", "T"),
    (2,  "我从不犹豫去帮助有困难的人。", "T"),
    (3,  "如果没有受到鼓励，我有时很难继续工作。", "F"),
    (4,  "我从未讨厌过任何人。", "T"),
    (5,  "我有时会怀疑自己能否在人生中取得成功。", "F"),
    (6,  "当我不能如愿时，我有时会感到怨恨。", "F"),
    (7,  "我总是注意自己的穿着打扮。", "T"),
    (8,  "我在家里的餐桌礼仪和在餐厅吃饭时一样好。", "F"),
    (9,  "如果我能逃票看一场电影，且确保没人看到，我可能会这样做。", "F"),
    (10, "有几次，我因为觉得自己能力不够而放弃了做某事。", "F"),
    (11, "我有时喜欢说闲话。", "F"),
    (12, "我偶尔会想要打破规则或法律。", "F"),
    (13, "在争论中，我偶尔会想要说一些刻薄的话来反驳对方。", "F"),
    (14, "我总是乐于承认自己的错误。", "T"),
    (15, "我总是对他人彬彬有礼，即使对令人讨厌的人也是如此。", "T"),
    (16, "我从未想过为了自己的利益而欺骗他人。", "T"),
    (17, "我有时觉得别人的好运让我嫉妒。", "T"),
    (18, "我总是会向别人道歉，如果我做了伤害他们的事。", "T"),
    (19, "我偶尔会有不好的念头。", "F"),
    (20, "我有时觉得很难原谅那些冒犯了我的人。", "F"),
    (21, "在对别人做出承诺之前，我会仔细考虑。", "T"),
    (22, "我偶尔会利用别人。", "F"),
    (23, "我偶尔会和别人争论。", "F"),
    (24, "当我不被允许做某件事时，我有时会感到不满。", "F"),
    (25, "我做事总是有始有终。", "T"),
    (26, "我偶尔会违反交通规则。", "F"),
    (27, "我总是说到做到。", "T"),
    (28, "我从不在背后说别人坏话。", "T"),
    (29, "我偶尔会对别人的行为感到恼火。", "F"),
    (30, "我总是按时完成工作。", "T"),
    (31, "我从不觉得自己是无用之人。", "T"),
    (32, "我偶尔会因为自己的粗心而犯错。", "F"),
    (33, "我从小到大从来没有撒过谎。", "T"),
]

T_KEYED = {1,2,4,7,9,10,14,15,16,17,18,21,25,27,28,30,31,33}
# F_KEYED = {3,5,6,8,11,12,13,19,20,22,23,24,26,29,32}

def make_questions():
    qs = []
    for order, text_zh, key in ITEMS:
        if key == "T":
            # True = 1 (socially desirable answer), False = 0
            opts = [("对", 1), ("错", 0)]
        else:
            # False = 1 (socially desirable answer), True = 0
            opts = [("对", 0), ("错", 1)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def make_dimensions():
    total_formula = q_range(1, 33)
    return [
        dimension("社会赞许性", "social_desirability", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 8", "社会赞许性较低",
                "您的社会赞许性反应较低，说明您在问卷作答中较为坦诚，没有刻意迎合社会期望。这是积极的自我认知表现。",
                "none"),
            result_rule("hx_wd_y_1 > 8 && hx_wd_y_1 <= 19", "社会赞许性处于平均水平",
                "您的社会赞许性得分处于正常范围，说明您在自我呈现与真实性之间保持了较好的平衡。",
                "none"),
            result_rule("hx_wd_y_1 > 19 && hx_wd_y_1 <= 33", "社会赞许性较高",
                "您的社会赞许性得分较高，说明您倾向于以社会期望的方式作答。这可能反映了您对自我形象的高度重视，也可能意味着某些自我认知存在偏差。建议结合其他测评结果综合分析。",
                "low"),
        ]),
    ]

def build():
    return build_scale(
        title="马洛-克罗恩社会赞许性量表(MC-SDS)",
        description="本问卷用于了解您在回答问题时的倾向性，帮助更准确地理解您的真实想法。共20题，大约需要3分钟完成。",
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
