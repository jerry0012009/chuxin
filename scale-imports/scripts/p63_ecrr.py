"""P63: ECR-R 亲密关系经历量表 (Experiences in Close Relationships)
Brennan, Clark & Shaver (1998), 中文版 李同归 & 加藤和生 (2006)
36 items, 7-point scale. 2 dimensions: 依恋焦虑/依恋回避.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ecr"
IMPORT_CODE = "huaxinyun-ecr"

OPT7 = [
    ("非常不同意", 1), ("比较不同意", 2), ("有点不同意", 3),
    ("不确定", 4), ("有点同意", 5), ("比较同意", 6), ("非常同意", 7)
]
OPT7_REVERSE = [
    ("非常同意", 1), ("比较同意", 2), ("有点同意", 3),
    ("不确定", 4), ("有点不同意", 5), ("比较不同意", 6), ("非常不同意", 7)
]

# 36 items: (order, text, is_reverse)
# Avoidance: 1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35
# Anxiety: 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36
# Reverse (avoidance): 3,15,19,25,27,29,31,33,35
# Reverse (anxiety): 22
QUESTIONS_RAW = [
    (1,  "总的来说，我不喜欢让恋人知道自己内心深处的感觉。", False),
    (2,  "我担心我会被抛弃。", False),
    (3,  "我觉得跟恋人亲近是一件惬意的事情。", True),
    (4,  "我很担心我的恋爱关系。", False),
    (5,  "当恋人开始要跟我亲近时，我发现我自己在退缩。", False),
    (6,  "我担心恋人不会像我关心他（她）那样地关心我。", False),
    (7,  "当恋人希望跟我非常亲近时，我会觉得不自在。", False),
    (8,  "我有点担心会失去恋人。", False),
    (9,  "我觉得对恋人开诚布公，不是一件很舒服的事情。", False),
    (10, "我常常希望恋人对我的感情和我对恋人的感情一样强烈。", False),
    (11, "我想与恋人亲近，但我又总是会退缩不前。", False),
    (12, "我常常想与恋人形影不离，但有时这样会把恋人吓跑。", False),
    (13, "当恋人跟我过分亲密的时候，我会感到内心紧张。", False),
    (14, "我担心一个人独处。", False),
    (15, "我愿意把我内心的想法和感觉告诉恋人，我觉得这是一件自在的事情。", True),
    (16, "我想跟恋人非常亲密的愿望，有时会把恋人吓跑。", False),
    (17, "我试图避免与恋人变得太亲近。", False),
    (18, "我需要我的恋人一再地保证他/她是爱我的。", False),
    (19, "我觉得我比较容易与恋人亲近。", True),
    (20, "我觉得自己在要求恋人把更多的感觉，以及对恋爱关系的投入程度表现出来。", False),
    (21, "我发现让我依赖恋人，是一件困难的事情。", False),
    (22, "我并不是常常担心被恋人抛弃。", True),
    (23, "我倾向于不跟恋人过分亲密。", False),
    (24, "如果我无法得到恋人的注意和关心，我会心烦意乱或者生气。", False),
    (25, "我跟恋人什么事情都讲。", True),
    (26, "我发现恋人并不愿意像我所想的那样跟我亲近。", False),
    (27, "我经常与恋人讨论我所遇到的问题以及我关心的事情。", True),
    (28, "如果我还没有恋人的话，我会感到有点焦虑和不安。", False),
    (29, "我觉得依赖恋人是很自在的事情。", True),
    (30, "如果恋人不能像我所希望的那样在我身边时，我会感到灰心丧气。", False),
    (31, "我并不在意从恋人那里寻找安慰，听取劝告，得到帮助。", True),
    (32, "如果在我需要的时候，恋人却不在我身边，我会感到沮丧。", False),
    (33, "在需要的时候，我向恋人求助，是很有用的。", True),
    (34, "当恋人不赞同我时，我觉得确实是我不好。", False),
    (35, "我会求助于恋人做很多事情，包括寻求安慰和保证。", True),
    (36, "当恋人花时间离开我时，我会感到愤恨。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT7_REVERSE if is_rev else OPT7
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # Avoidance: odd items 1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35
    av_items = "+".join(f"hx_t_{i}" for i in range(1, 37, 2))
    av_formula = f"({av_items}) / 18"
    # Anxiety: even items 2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36
    ax_items = "+".join(f"hx_t_{i}" for i in range(2, 37, 2))
    ax_formula = f"({ax_items}) / 18"

    return [
        dimension("依恋回避", "avoidance", 1, av_formula, "", [
            result_rule("hx_wd_y_1 <= 2.5", "回避倾向较低",
                "您在亲密关系中感到自在，愿意与恋人亲近和分享内心感受，能够自然地依赖对方。", "none"),
            result_rule("hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 4.5", "回避倾向中等",
                "您在亲密关系中有时会保持一定距离，在亲近和独立之间寻求平衡。", "none"),
            result_rule("hx_wd_y_1 > 4.5", "回避倾向较高",
                "您在亲密关系中倾向于保持情感距离，可能对过度亲近感到不适，建议反思自己的依恋模式。", "none"),
        ]),
        dimension("依恋焦虑", "anxiety", 2, ax_formula, "", [
            result_rule("hx_wd_y_2 <= 2.5", "焦虑倾向较低",
                "您在亲密关系中感到安全和自信，不太担心被抛弃或不被重视。", "none"),
            result_rule("hx_wd_y_2 > 2.5 && hx_wd_y_2 <= 4.5", "焦虑倾向中等",
                "您在亲密关系中偶尔会感到不安，对关系的稳定性有一定的关注。", "none"),
            result_rule("hx_wd_y_2 > 4.5", "焦虑倾向较高",
                "您在亲密关系中容易感到焦虑和不安，经常担心被抛弃或不被重视，建议通过沟通增强安全感。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="亲密关系经历量表(ECR)",
        description="本问卷帮助了解您在亲密关系中的依恋风格。共36题，大约需要10分钟完成。",
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
