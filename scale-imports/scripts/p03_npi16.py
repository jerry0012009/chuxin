"""P0-3: NPI-16 - Narcissistic Personality Inventory 16-item version
(Ames, Rose & Anderson, 2006)
16 forced-choice pairs. Score 1 for narcissistic response, 0 otherwise.
Mean score range 0-1. Threshold >0.5 = narcissistic.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "npi16-narcissism"
IMPORT_CODE = "huaxinyun-npi16-narcissism"

# NPI-16 items: (order, chinese_A, chinese_B, narcissistic_option)
# narcissistic_option: 'A' or 'B' - which option gets score 1
ITEMS = [
    (1,
     "我知道我很优秀，因为大家都这么说。",
     "当别人夸奖我时，我有时会感到尴尬。",
     "A"),
    (2,
     "统治世界的想法让我感到恐惧。",
     "如果我统治世界，世界会变得更美好。",
     "B"),
    (3,
     "我通常能靠口才摆脱任何困境。",
     "我努力承担自己行为的后果。",
     "A"),
    (4,
     "我喜欢成为众人关注的焦点。",
     "我更喜欢融入人群中。",
     "A"),
    (5,
     "我认为自己是一个与众不同的人。",
     "我不比大多数人好，也不比大多数人差。",
     "A"),
    (6,
     "我认为自己是一个好的领导者。",
     "我认为自己是一个好的追随者。",
     "A"),
    (7,
     "我是一个果断自信的人。",
     "我希望自己能更加果断自信。",
     "A"),
    (8,
     "我喜欢拥有支配他人的权力。",
     "我不介意服从命令。",
     "A"),
    (9,
     "我觉得操纵别人很容易。",
     "当我发现自己在操纵别人时，我会感到不舒服。",
     "A"),
    (10,
     "我坚持获得应得的尊重。",
     "我通常能得到应有的尊重。",
     "A"),
    (11,
     "如果有机会，我倾向于炫耀自己。",
     "我不是那种喜欢炫耀的人。",
     "A"),
    (12,
     "我总是很清楚自己在做什么。",
     "有时我并不确定自己在做什么。",
     "A"),
    (13,
     "我比其他人更有能力。",
     "我可以从别人身上学到很多东西。",
     "A"),
    (14,
     "我注定会成为一个了不起的人。",
     "我希望自己能够取得成功。",
     "A"),
    (15,
     "我能让别人相信我想让他们相信的任何事情。",
     "我不喜欢操纵别人。",
     "A"),
    (16,
     "我是一个天生的领导者。",
     "领导力是需要后天赢得的。",
     "A"),
]

def make_questions():
    qs = []
    for order, text_a, text_b, narc_opt in ITEMS:
        if narc_opt == "A":
            # Option A = narcissistic (score 1), Option B = non-narcissistic (score 0)
            opts = [(text_a, 1), (text_b, 0)]
        else:
            # Option B = narcissistic (score 1), Option A = non-narcissistic (score 0)
            opts = [(text_a, 0), (text_b, 1)]
        qs.append(radio_q(order, f"以下两个描述，哪一个更符合你？\nA. {text_a}\nB. {text_b}", opts))
    return qs

def make_dimensions():
    # Mean of all 16 items: (sum of hx_t_1..hx_t_16) / 16
    total = q_range(1, 16)
    mean_formula = f"({total}) / 16"
    return [
        dimension("自恋", "narcissism", 1, mean_formula, "", [
            result_rule("hx_wd_y_1 <= 0.25", "自恋水平较低",
                "您的自恋水平较低，表明您具有较为谦逊和务实的自我认知。您能够客观地看待自己的优缺点，在人际关系中倾向于平等和真诚。",
                "none"),
            result_rule("hx_wd_y_1 > 0.25 && hx_wd_y_1 <= 0.50", "自恋水平正常偏低",
                "您的自恋水平处于正常范围的较低端，表明您具有适度的自信，同时保持了良好的自我觉察能力和共情能力。",
                "none"),
            result_rule("hx_wd_y_1 > 0.50 && hx_wd_y_1 <= 0.75", "自恋水平偏高",
                "您的自恋水平偏高，表明您对自我重要性有较强的感受，可能倾向于自我中心化和夸大自我。建议关注他人的感受和需求，培养共情能力。",
                "low"),
            result_rule("hx_wd_y_1 > 0.75", "自恋水平显著偏高",
                "您的自恋水平显著偏高，表明您具有较强的自我中心倾向、对赞美的渴望以及对权力的追求。这可能影响您的人际关系质量。建议进行深入的自我反思，如有需要可寻求专业心理咨询。",
                "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="自恋人格量表简版(NPI-16)",
        description="本问卷帮助了解您对自己的看法和态度，包括自信、自我关注等方面。共16题，大约需要3分钟完成。",
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
