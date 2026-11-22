"""P32: UCLA Loneliness Scale (Version 3)
(Russell, 1996)
20 items, 4-point scale (1-4). Total score 20-80.
Reverse-scored items (positive): 1, 5, 6, 9, 10, 15, 16, 19, 20.
Thresholds: 20-34 low, 35-44 moderate, 45-54 high, 55-80 very high.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ucla-loneliness"
IMPORT_CODE = "huaxinyun-ucla-loneliness"

# Reverse items (1-indexed): 1, 5, 6, 9, 10, 15, 16, 19, 20
REVERSE_ITEMS = {1, 5, 6, 9, 10, 15, 16, 19, 20}

# 20 items: (order, Chinese text)
QUESTIONS = [
    (1,  "您是否经常感到与周围的人很亲近？"),
    (2,  "您是否经常感到缺少陪伴？"),
    (3,  "您是否经常感到没有人真正了解您？"),
    (4,  "您是否经常感到自己被孤立？"),
    (5,  "您是否经常感到自己属于某个群体的一部分？"),
    (6,  "您是否经常感到自己有很多共同话题可以和别人分享？"),
    (7,  "您是否经常感到自己不再亲近任何人？"),
    (8,  "您是否经常感到自己的兴趣和想法与周围的人不同？"),
    (9,  "您是否经常感到自己是外向和友好的？"),
    (10, "您是否经常感到自己很容易与人亲近？"),
    (11, "您是否经常感到被冷落？"),
    (12, "您是否经常感到自己与他人的关系没有意义？"),
    (13, "您是否经常感到没有人可以求助？"),
    (14, "您是否经常感到自己孤独寂寞？"),
    (15, "您是否经常感到自己是快乐的？"),
    (16, "您是否经常感到自己与周围的人很合得来？"),
    (17, "您是否经常感到自己感到不舒服和不自在？"),
    (18, "您是否经常感到人们在身边但不在一起？"),
    (19, "您是否经常感到自己有很多可以信赖的人？"),
    (20, "您是否经常感到自己和别人之间有真正的亲密感？"),
]

def make_questions():
    qs = []
    for order, text_zh in QUESTIONS:
        if order in REVERSE_ITEMS:
            # Positive items: reverse scoring (1->4, 2->3, 3->2, 4->1)
            opts = [("从未有此感觉", 4), ("很少有此感觉", 3), ("有时有此感觉", 2), ("一直有此感觉", 1)]
        else:
            # Negative items: normal scoring
            opts = [("从未有此感觉", 1), ("很少有此感觉", 2), ("有时有此感觉", 3), ("一直有此感觉", 4)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def make_dimensions():
    # Single dimension: total score of all 20 items (range 20-80)
    total_formula = q_range(1, 20)

    return [
        dimension("孤独感", "loneliness", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 34", "低孤独感",
                "您的孤独感水平较低，说明您有良好的社交联系和情感归属。您能够从周围的人际关系中获得足够的支持和温暖。建议继续保持积极的社交生活。", "none"),
            result_rule("hx_wd_y_1 > 34 && hx_wd_y_1 <= 44", "中等孤独感",
                "您的孤独感处于中等水平，说明您在某些时候会感到社交联系不足。建议主动拓展社交圈，尝试参加社区活动或兴趣小组，加强与朋友和家人的联系。", "low"),
            result_rule("hx_wd_y_1 > 44 && hx_wd_y_1 <= 54", "较高孤独感",
                "您的孤独感水平较高，说明您经常感到与他人疏离或缺乏情感支持。长期的孤独感可能影响身心健康。建议主动寻求社交机会，也可以考虑寻求心理咨询来探索改善人际关系的方法。", "middle"),
            result_rule("hx_wd_y_1 > 54", "非常高孤独感",
                "您的孤独感水平非常高，说明您在社交联系和情感归属方面存在显著困难。长期的孤独感可能对身心健康产生不良影响。强烈建议寻求专业心理咨询或支持，帮助您建立更有意义的人际关系。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="孤独感量表(UCLA)",
        description="本问卷帮助了解您近期的孤独感体验，包括社交联系和情感归属等方面。共20题，大约需要4分钟完成。",
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
