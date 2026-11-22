"""P50: 情绪智力量表(EI)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ei-emotional-intelligence"
IMPORT_CODE = "huaxinyun-ei-emotional-intelligence"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "当我很开心的时候，别人很容易看出来"),
    (2, "人们能从我的表情中读出我的情绪"),
    (3, "当我感到快乐时，我会通过言行表现出来"),
    (4, "我的朋友们能轻易察觉我的好心情"),
    (5, "我善于表达积极的情绪"),
    (6, "当我开心时，我身边的人也会被感染"),
    (7, "我很容易向别人展示我的快乐"),
    (8, "我的积极情绪很有感染力"),
    (9, "当我难过时，别人能看出我的情绪变化"),
    (10, "我的面部表情会暴露我的坏心情"),
    (11, "当我情绪低落时，身边的人能察觉到"),
    (12, "我很难隐藏自己的悲伤"),
    (13, "当我焦虑时，我的言行会有所体现"),
    (14, "别人能轻易看出我是否紧张"),
    (15, "我的烦恼会通过我的行为表现出来"),
    (16, "当我生气时，周围的人都知道"),
    (17, "我经常关注自己的情绪变化"),
    (18, "我会仔细体会自己的感受"),
    (19, "我善于觉察自己的情绪状态"),
    (20, "我总是留意自己心情的变化"),
    (21, "我花很多时间思考自己的感受"),
    (22, "我对自己的情绪很敏感"),
    (23, "我能准确地识别自己的情绪"),
    (24, "我经常反思自己的情绪反应"),
    (25, "我在做决定时会考虑自己的情绪"),
    (26, "我的情绪会影响我的判断"),
    (27, "我会根据自己的感受来做出选择"),
    (28, "我在决策时会参考自己的情绪状态"),
    (29, "我的心情会影响我的决定"),
    (30, "我在做重要决定时会关注自己的直觉"),
    (31, "我的感受帮助我做出好的决定"),
    (32, "我的情绪为我的决策提供有用信息"),
    (33, "当别人分享好消息时，我会由衷地为他们高兴"),
    (34, "朋友成功时我会真心为他们感到高兴"),
    (35, "我能分享他人的快乐"),
    (36, "当别人开心时，我也会感到快乐"),
    (37, "我善于回应他人的好消息"),
    (38, "看到别人幸福我会感到温暖"),
    (39, "我很容易被别人的好心情感染"),
    (40, "当别人取得成就时我会真诚祝贺"),
    (41, "当别人难过时，我也会感到悲伤"),
    (42, "看到别人受苦我会感到不安"),
    (43, "朋友遇到困难时我会很担心"),
    (44, "我能感受到他人的痛苦"),
    (45, "当别人情绪低落时我也会受影响"),
    (46, "看到别人哭泣我会很难过"),
    (47, "我对别人的不幸有强烈的反应"),
    (48, "他人的悲伤会引起我的共鸣"),
    (49, "我非常关心他人的感受"),
    (50, "我会主动帮助情绪低落的朋友"),
    (51, "我对别人的痛苦感同身受"),
    (52, "我会照顾身边人的情绪需要"),
    (53, "我对他人有很强的同理心"),
    (54, "我愿意花时间倾听别人的烦恼"),
    (55, "我能设身处地为他人着想"),
    (56, "我对别人的情感需求很敏感"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("正面表达", "positive_expressivity", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8) / 8", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您在表达积极情绪方面较为内敛。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您在表达积极情绪方面较为适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您善于表达和分享积极情绪，感染力强。", "none"),
        ]),
        dimension("负面表达", "negative_expressivity", 2, "(hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16) / 8", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您不太容易在外在表现中流露负面情绪。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的负面情绪表达较为适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您的负面情绪较容易通过言行表现出来。", "none"),
        ]),
        dimension("关注情绪", "attending_emotions", 3, "(hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20 + hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24) / 8", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您较少主动关注和反思自己的情绪。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您对自身情绪的关注度适中。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您善于觉察和关注自己的情绪变化。", "none"),
        ]),
        dimension("情绪决策", "emotion_decision", 4, "(hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30 + hx_t_31 + hx_t_32) / 8", "", [
            result_rule("hx_wd_y_4 <= 2.0", "低", "您在决策时较少受情绪影响。", "none"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "中", "您的决策方式较为平衡。", "none"),
            result_rule("hx_wd_y_4 > 3.5", "高", "您善于利用情绪信息辅助决策。", "none"),
        ]),
        dimension("响应快乐", "responsive_joy", 5, "(hx_t_33 + hx_t_34 + hx_t_35 + hx_t_36 + hx_t_37 + hx_t_38 + hx_t_39 + hx_t_40) / 8", "", [
            result_rule("hx_wd_y_5 <= 2.0", "低", "您对他人快乐情绪的共鸣度较低。", "none"),
            result_rule("hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "中", "您能适当地回应他人的快乐。", "none"),
            result_rule("hx_wd_y_5 > 3.5", "高", "您善于分享和回应他人的快乐，共情能力强。", "none"),
        ]),
        dimension("响应痛苦", "responsive_distress", 6, "(hx_t_41 + hx_t_42 + hx_t_43 + hx_t_44 + hx_t_45 + hx_t_46 + hx_t_47 + hx_t_48) / 8", "", [
            result_rule("hx_wd_y_6 <= 2.0", "低", "您对他人痛苦的共情度较低。", "none"),
            result_rule("hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "中", "您的共情程度适中。", "none"),
            result_rule("hx_wd_y_6 > 3.5", "高", "您对他人的痛苦有很强的共情能力。", "none"),
        ]),
        dimension("同理心", "empathy", 7, "(hx_t_49 + hx_t_50 + hx_t_51 + hx_t_52 + hx_t_53 + hx_t_54 + hx_t_55 + hx_t_56) / 8", "", [
            result_rule("hx_wd_y_7 <= 2.0", "低", "您的同理心水平较低。", "none"),
            result_rule("hx_wd_y_7 > 2.0 && hx_wd_y_7 <= 3.5", "中", "您的同理心水平适中。", "none"),
            result_rule("hx_wd_y_7 > 3.5", "高", "您有很强的同理心，善于理解和关心他人。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="情绪智力量表(EI)",
        description="本问卷帮助了解您在情绪感知、表达和运用方面的七个能力维度。共56题，大约需要10分钟完成。",
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
