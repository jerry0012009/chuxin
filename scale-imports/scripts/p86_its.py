"""P86: ITS 人际信任量表 (Interpersonal Trust Scale)
Rotter (1967), 中文版
25 items, 5-point scale. Single dimension: 人际信任.
Reverse items: 3,7,9,14,16,18,22,23,24
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "its"
IMPORT_CODE = "huaxinyun-its"

OPT_5 = [
    ("完全同意", 1), ("部分同意", 2), ("同意与不同意相等", 3),
    ("部分不同意", 4), ("完全不同意", 5)
]
OPT_5_REV = [
    ("完全不同意", 1), ("部分不同意", 2), ("同意与不同意相等", 3),
    ("部分同意", 4), ("完全同意", 5)
]

# Reverse items: 3,7,9,14,16,18,22,23,24
QUESTIONS_RAW = [
    (1,  "在我们这个社会里虚伪的现象越来越多了。", False),
    (2,  "与陌生人打交道时，你最好小心，除非他们拿出可以证明其值得信任的依据。", False),
    (3,  "除非我们吸引更多的人进入政界，这个国家的前途将十分黯淡。", True),
    (4,  "阻止多数人触犯法律的是恐惧、社会廉耻或惩罚而不是良心。", False),
    (5,  "考试时教师不到场监考可能会导致更多的人作弊。", False),
    (6,  "通常父母在遵守诺言方面是可以信赖的。", False),
    (7,  "联合国永远也不会成为维持世界和平的有效力量。", True),
    (8,  "法院是我们都能受到公正对待的场所。", False),
    (9,  "如果得知公众听到和看到的新闻有多少已被歪曲，多数人会感到震惊的。", True),
    (10, "不管人们怎样表白，最好还是认为多数人主要关心其自身幸福。", False),
    (11, "尽管在报纸、收音机和电视中均可看到新闻，但我们很难得到关于公共事件的客观报道。", False),
    (12, "未来似乎很有希望。", False),
    (13, "如果真正了解到国际上正在发生的政治事件，那么公众有理由比现在更加担心。", False),
    (14, "多数获选官员在竞选中的许诺是诚恳的。", True),
    (15, "许多重大的全国性体育比赛均受到某种形式操纵和利用。", False),
    (16, "多数专家有关其知识局限性的表白是可信的。", True),
    (17, "多数父母关于实施惩罚的威胁是可信的。", False),
    (18, "多数人如果说出自己的打算就一定会去实现。", True),
    (19, "在这个竞争的年代里，如果不保持警惕，别人就可能占你的便宜。", False),
    (20, "多数理想主义者是诚恳的并按照他们自己所宣扬的信条行事。", False),
    (21, "多数推销人员在描述他们的产品时是诚实的。", False),
    (22, "多数学生即使在有把握不会被发现时也不作弊。", True),
    (23, "多数维修人员即使认为你不懂其专业知识也不会多收费。", True),
    (24, "对保险公司的控告有相当一部分是假的。", True),
    (25, "多数人诚实地回答民意测验中的问题。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_5_REV if is_rev else OPT_5
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    formula = q_range(1, 25) + " / 25"
    return [
        dimension("人际信任", "interpersonal_trust", 1, formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "人际信任水平较低",
                "您对他人的信任程度较低，倾向于对他人持怀疑态度。这可能影响您的人际关系和社会交往。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "人际信任水平中等",
                "您对他人持有适度的信任水平，能够在一定程度上相信他人，同时保持合理的警惕。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "人际信任水平较高",
                "您对他人有较高的信任水平，倾向于相信大多数人是诚实可靠的。这有助于建立良好的人际关系。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="人际信任量表(ITS)",
        description="本量表帮助了解您对他人和社会的信任程度。共25题，大约需要5分钟完成。",
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
