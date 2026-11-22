"""P2-21: OCI-R - Obsessive-Compulsive Inventory Revised (Foa et al., 2002)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "oci-r-ocd"
IMPORT_CODE = "huaxinyun-oci-r-ocd"

# OCI-R: 18 items, 5-point (0=not at all to 4=extremely)
# Subscales:
#   Washing: 2, 5, 11, 15
#   Checking: 3, 7, 14, 17
#   Ordering: 4, 8, 12, 16
#   Obsessing: 1, 6, 10, 13
#   Hoarding: 9, 18
# Total sum 0-72. Clinical cutoff >=21.

QUESTIONS = [
    (1, "我囤积了太多东西，以至于它们妨碍了我的生活。"),
    (2, "我检查东西的次数比必要的多得多。"),
    (3, "我反复检查门、窗、抽屉等是否关好。"),
    (4, "我发现自己很难控制某些想法。"),
    (5, "我有时觉得自己被污染了，必须清洗或清洁自己。"),
    (6, "违背我意愿的不愉快想法进入我的脑海，让我心烦。"),
    (7, "我觉得自己需要一遍又一遍地检查东西。"),
    (8, "如果物品没有摆放整齐，我会感到不安。"),
    (9, "我害怕扔掉东西，因为我以后可能需要它们。"),
    (10, "我担心丢失东西，或者扔掉以后可能需要的东西。"),
    (11, "当我觉得自己被污染时，很难不去洗手。"),
    (12, "当我知道某个物体被陌生人碰过时，我很难去碰它。"),
    (13, "侵入性的想法让我感到困扰，且难以控制。"),
    (14, "我反复检查煤气、水龙头、电灯开关等。"),
    (15, "我洗手的次数比必要的多，或洗的时间比必要的长。"),
    (16, "我需要把东西按照特定的方式排列整齐。"),
    (17, "我觉得某些数字有好坏之分，或者它们会带来好运或厄运。"),
    (18, "我害怕自己会丢掉重要的东西。"),
]

OCI_OPTIONS = [
    ("完全没有", 0), ("轻度", 1), ("中度", 2), ("重度", 3), ("极重度", 4)
]

WASHING = [2, 5, 11, 15]
CHECKING = [3, 7, 14, 17]
ORDERING = [4, 8, 12, 16]
OBSESSING = [1, 6, 10, 13]
HOARDING = [9, 18]

def make_questions():
    return [radio_q(order, text, OCI_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    washing_items = " + ".join(f"hx_t_{i}" for i in WASHING)
    checking_items = " + ".join(f"hx_t_{i}" for i in CHECKING)
    ordering_items = " + ".join(f"hx_t_{i}" for i in ORDERING)
    obsessing_items = " + ".join(f"hx_t_{i}" for i in OBSESSING)
    hoarding_items = " + ".join(f"hx_t_{i}" for i in HOARDING)
    total_items = " + ".join(f"hx_t_{i}" for i in range(1, 19))

    return [
        dimension("清洗", "washing", 1, washing_items, "", [
            result_rule("hx_wd_y_1 <= 2", "清洗倾向较低", "您的清洗/清洁相关强迫症状较轻。", "none"),
            result_rule("hx_wd_y_1 > 2 && hx_wd_y_1 <= 5", "清洗倾向中等", "您存在一定的清洗/清洁相关强迫症状，建议关注。", "none"),
            result_rule("hx_wd_y_1 > 5 && hx_wd_y_1 <= 8", "清洗倾向偏高", "您的清洗相关症状得分偏高，建议关注清洁行为是否影响日常生活。", "low"),
            result_rule("hx_wd_y_1 > 8", "清洗倾向异常偏高", "您的清洗相关症状明显偏高，建议寻求专业心理评估。", "middle"),
        ]),
        dimension("检查", "checking", 2, checking_items, "", [
            result_rule("hx_wd_y_2 <= 2", "检查倾向较低", "您的检查相关强迫症状较轻。", "none"),
            result_rule("hx_wd_y_2 > 2 && hx_wd_y_2 <= 5", "检查倾向中等", "您存在一定的检查相关强迫症状，建议关注。", "none"),
            result_rule("hx_wd_y_2 > 5 && hx_wd_y_2 <= 8", "检查倾向偏高", "您的检查行为得分偏高，建议关注是否反复检查影响效率。", "low"),
            result_rule("hx_wd_y_2 > 8", "检查倾向异常偏高", "您的检查相关症状明显偏高，建议寻求专业心理评估。", "middle"),
        ]),
        dimension("排序", "ordering", 3, ordering_items, "", [
            result_rule("hx_wd_y_3 <= 2", "排序倾向较低", "您的排序/排列相关强迫症状较轻。", "none"),
            result_rule("hx_wd_y_3 > 2 && hx_wd_y_3 <= 5", "排序倾向中等", "您存在一定的排序相关强迫症状，建议关注。", "none"),
            result_rule("hx_wd_y_3 > 5 && hx_wd_y_3 <= 8", "排序倾向偏高", "您的排序行为得分偏高，建议关注对整齐和对称的需求。", "low"),
            result_rule("hx_wd_y_3 > 8", "排序倾向异常偏高", "您的排序相关症状明显偏高，建议寻求专业心理评估。", "middle"),
        ]),
        dimension("强迫思维", "obsessing", 4, obsessing_items, "", [
            result_rule("hx_wd_y_4 <= 2", "强迫思维较少", "您的侵入性思维相关症状较轻。", "none"),
            result_rule("hx_wd_y_4 > 2 && hx_wd_y_4 <= 5", "强迫思维中等", "您存在一定的侵入性思维，建议关注。", "none"),
            result_rule("hx_wd_y_4 > 5 && hx_wd_y_4 <= 8", "强迫思维偏高", "您的侵入性思维得分偏高，建议关注思维控制能力。", "low"),
            result_rule("hx_wd_y_4 > 8", "强迫思维异常偏高", "您的侵入性思维症状明显偏高，建议寻求专业心理评估。", "middle"),
        ]),
        dimension("囤积", "hoarding", 5, hoarding_items, "", [
            result_rule("hx_wd_y_5 <= 1", "囤积倾向较低", "您的囤积相关症状较轻。", "none"),
            result_rule("hx_wd_y_5 > 1 && hx_wd_y_5 <= 3", "囤积倾向中等", "您存在一定的囤积倾向，建议关注。", "none"),
            result_rule("hx_wd_y_5 > 3 && hx_wd_y_5 <= 5", "囤积倾向偏高", "您的囤积行为得分偏高，建议关注是否影响生活空间。", "low"),
            result_rule("hx_wd_y_5 > 5", "囤积倾向异常偏高", "您的囤积症状明显偏高，建议寻求专业心理评估。", "middle"),
        ]),
        dimension("总分", "total", 6, total_items, "", [
            result_rule("hx_wd_y_6 <= 10", "强迫症状较轻", "您的OCI-R总分较低，强迫症状不明显。", "none"),
            result_rule("hx_wd_y_6 > 10 && hx_wd_y_6 <= 20", "强迫症状轻度", "您的OCI-R总分处于轻度范围，可能存在轻微的强迫症状。", "none"),
            result_rule("hx_wd_y_6 >= 21 && hx_wd_y_6 <= 35", "强迫症状中度", "您的OCI-R总分达到临床筛查标准（≥21），建议进一步评估。", "low"),
            result_rule("hx_wd_y_6 > 35", "强迫症状重度", "您的OCI-R总分显著偏高（≥21为临床截断值），强烈建议寻求专业心理评估和干预。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="强迫症量表修订版(OCI-R)",
        description="本问卷帮助了解您是否存在反复出现的想法或行为，如反复检查、清洗等。共18题，大约需要3分钟完成。",
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
