"""P2-23: LiES - Lying in Everyday Situations (Lupoli et al., 2017)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "lies-deception"
IMPORT_CODE = "huaxinyun-lies-deception"

# LiES: 14 items, 7-point (1=strongly disagree to 7=strongly agree)
# 2 subscales: Relational lying (items 1-7), Antisocial lying (items 8-14)
# Sum per subscale 7-49. No clinical cutoffs.

QUESTIONS = [
    # Relational Lying (1-7)
    (1, "为了维护人际关系，我会说一些不完全真实的话。"),
    (2, "为了避免伤害他人的感情，我会隐瞒真相。"),
    (3, "我会对朋友说一些善意的谎言来让他们感觉好一些。"),
    (4, "为了维持和谐的关系，我会在某些事情上不完全坦诚。"),
    (5, "当真相可能让别人不开心时，我倾向于说一些好听的话。"),
    (6, "我会夸大他人做得好的方面来鼓励他们。"),
    (7, "为了避免冲突，我会在某些问题上表现出与内心不同的态度。"),
    # Antisocial Lying (8-14)
    (8, "为了获得利益，我会在必要时对他人撒谎。"),
    (9, "如果撒谎能让我避免麻烦，我会毫不犹豫地这样做。"),
    (10, "我会对权威人物撒谎来保护自己的利益。"),
    (11, "我在日常生活中经常说一些不真实的话。"),
    (12, "欺骗他人对我来说是一件很容易的事情。"),
    (13, "我会编造故事来让自己在社交场合中看起来更好。"),
    (14, "为了达到目的，我会在简历或个人经历中夸大事实。"),
]

LIES_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("有些不同意", 3), ("不确定", 4),
    ("有些同意", 5), ("同意", 6), ("非常同意", 7)
]

def make_questions():
    return [radio_q(order, text, LIES_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    relational_items = " + ".join(f"hx_t_{i}" for i in range(1, 8))
    antisocial_items = " + ".join(f"hx_t_{i}" for i in range(8, 15))

    return [
        dimension("关系性谎言", "relational_lying", 1, relational_items, "", [
            result_rule("hx_wd_y_1 <= 14", "关系性谎言水平较低", "您在人际关系中很少使用谎言来维护关系，沟通风格较为直接。", "none"),
            result_rule("hx_wd_y_1 > 14 && hx_wd_y_1 <= 24", "关系性谎言水平中等", "您在人际关系中偶尔会使用善意的谎言，这在社交中较为常见。", "none"),
            result_rule("hx_wd_y_1 > 24 && hx_wd_y_1 <= 35", "关系性谎言水平偏高", "您在人际关系中较频繁地使用谎言来维护关系，建议关注诚实沟通的重要性。", "low"),
            result_rule("hx_wd_y_1 > 35", "关系性谎言水平异常偏高", "您在人际关系中过度依赖谎言，可能影响关系的真实性和深度。", "middle"),
        ]),
        dimension("反社会性谎言", "antisocial_lying", 2, antisocial_items, "", [
            result_rule("hx_wd_y_2 <= 11", "反社会性谎言水平较低", "您很少为了个人利益而欺骗他人，道德操守良好。", "none"),
            result_rule("hx_wd_y_2 > 11 && hx_wd_y_2 <= 20", "反社会性谎言水平中等", "您偶尔会为了个人利益而使用欺骗手段，建议反思诚实的重要性。", "none"),
            result_rule("hx_wd_y_2 > 20 && hx_wd_y_2 <= 30", "反社会性谎言水平偏高", "您较频繁地使用反社会性谎言，建议关注这种行为对人际关系和社会信任的影响。", "low"),
            result_rule("hx_wd_y_2 > 30", "反社会性谎言水平异常偏高", "您的反社会性谎言得分明显偏高，这种行为模式可能对您的社会关系造成严重影响。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="日常说谎量表(LiES)",
        description="本问卷帮助了解您在日常生活中的说谎倾向和频率。共14题，大约需要3分钟完成。",
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
