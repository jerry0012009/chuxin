"""P62: IRI-C 人际反应指针量表 (Interpersonal Reactivity Index-C)
Davis (1980), 中文版 张凤凤等 (2010)
22 items, 0-4 五点计分. 4维度: 观点采择/想象/共情关注/个人忧伤.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "iri-c"
IMPORT_CODE = "huaxinyun-iri-c"

OPT_NORMAL = [
    ("不恰当", 0), ("比较不恰当", 1), ("一般", 2), ("恰当", 3), ("很恰当", 4)
]
OPT_REVERSE = [
    ("很恰当", 0), ("恰当", 1), ("一般", 2), ("比较不恰当", 3), ("不恰当", 4)
]

# 22 items: (order, text, is_reverse)
# PT: 6,9,15,19,22 | FS: 3,5,10,12,17,20 | EC: 1,2,7,11,14,16 | PD: 4,8,13,18,21
# Reverse: 2,5,10,11,14
QUESTIONS_RAW = [
    (1,  "对那些比我不幸的人，我经常有心软和关怀的感觉。", False),
    (2,  "有时候当其他人有困难或问题时，我并不为他们感到很难过。", True),
    (3,  "我的确会投入小说人物中的感情世界。", False),
    (4,  "在紧急状况中，我感到担忧、害怕而难以平静。", False),
    (5,  "看电影或看戏时，我通常是旁观的，而且不经常全心投入。", True),
    (6,  "在做决定前，我试着从争论中去看每个人的立场。", False),
    (7,  "当我看到有人被别人利用时，我有点感到想要保护他们。", False),
    (8,  "当我处在一个情绪非常激动的情况中时，我往往会感到无依无靠，不知如何是好。", False),
    (9,  "有时候我想象从我的朋友的观点来看事情的样子，以便更了解他们。", False),
    (10, "对我来说，全心地投入一本好书或一部好电影中，是很少有的事。", True),
    (11, "其他人的不幸通常不会带给我很大的烦忧。", True),
    (12, "看完戏或电影之后，我会觉得自己好像是剧中的某一个角色。", False),
    (13, "处在紧张情绪的状况中，我会惊慌害怕。", False),
    (14, "当我看到有人受到不公平的对待时，我有时并不感到非常同情他们。", True),
    (15, "我相信每个问题都有两面观点，所以我常试着从这不同的观点来看问题。", False),
    (16, "我认为自己是一个相当软心肠的人。", False),
    (17, "当我观赏一部好电影时，我很容易站在某个主角的立场去感受他的心情。", False),
    (18, "在紧急状况中，我紧张得几乎无法控制自己。", False),
    (19, "当我对一个人生气时，我通常会试着去想一下他的立场。", False),
    (20, "当我阅读一篇引人的故事或小说时，我想象着：如果故事中的事件发生在我身上，我会感觉怎么样？", False),
    (21, "当我看到有人发生意外而极需帮助的时候，我紧张得几乎精神崩溃。", False),
    (22, "在批评别人前，我会试着想象：假如我处在他的情况，我的感受如何？", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # PT: items 6,9,15,19,22
    pt_items = "hx_t_6 + hx_t_9 + hx_t_15 + hx_t_19 + hx_t_22"
    # FS: items 3,5,10,12,17,20
    fs_items = "hx_t_3 + hx_t_5 + hx_t_10 + hx_t_12 + hx_t_17 + hx_t_20"
    # EC: items 1,2,7,11,14,16
    ec_items = "hx_t_1 + hx_t_2 + hx_t_7 + hx_t_11 + hx_t_14 + hx_t_16"
    # PD: items 4,8,13,18,21
    pd_items = "hx_t_4 + hx_t_8 + hx_t_13 + hx_t_18 + hx_t_21"
    total = " + ".join(f"hx_t_{i}" for i in range(1, 23))

    return [
        dimension("观点采择", "pt", 1, pt_items, "", [
            result_rule("hx_wd_y_1 <= 4", "观点采择能力较低",
                "您较少自发地从他人角度看待问题，在人际互动中可能更倾向于关注自身立场。", "none"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 10", "观点采择能力中等",
                "您在一定程度上能够从他人角度思考问题，在熟悉的情境中表现较好。", "none"),
            result_rule("hx_wd_y_1 > 10", "观点采择能力较高",
                "您善于从他人角度看待问题，能够理解不同立场，在人际交往中表现出较强的换位思考能力。", "none"),
        ]),
        dimension("想象", "fs", 2, fs_items, "", [
            result_rule("hx_wd_y_2 <= 6", "想象能力较低",
                "您对虚构人物的代入感较弱，不太容易被文学或影视作品中的角色所打动。", "none"),
            result_rule("hx_wd_y_2 > 6 && hx_wd_y_2 <= 14", "想象能力中等",
                "您在欣赏文学或影视作品时有一定的代入感，能够适度体验虚构角色的情感。", "none"),
            result_rule("hx_wd_y_2 > 14", "想象能力较高",
                "您很容易投入虚构作品中，能够深刻体会角色的情感和经历，具有丰富的想象力。", "none"),
        ]),
        dimension("共情关注", "ec", 3, ec_items, "", [
            result_rule("hx_wd_y_3 <= 8", "共情关注较低",
                "您对他人的不幸和困境关注较少，情感共鸣能力有待提升。", "none"),
            result_rule("hx_wd_y_3 > 8 && hx_wd_y_3 <= 16", "共情关注中等",
                "您对他人的不幸有一定的同情心，能够在适当的情境中表达关怀。", "none"),
            result_rule("hx_wd_y_3 > 16", "共情关注较高",
                "您对他人的不幸和困境有强烈的同情心，经常关心和帮助他人，情感共鸣能力强。", "none"),
        ]),
        dimension("个人忧伤", "pd", 4, pd_items, "", [
            result_rule("hx_wd_y_4 <= 4", "个人忧伤较低",
                "您在紧张的人际情境中能保持冷静，面对他人困境时不易感到焦虑或无助。", "none"),
            result_rule("hx_wd_y_4 > 4 && hx_wd_y_4 <= 10", "个人忧伤中等",
                "您在面对他人困境或紧张情境时会有一定程度的焦虑和不适感。", "none"),
            result_rule("hx_wd_y_4 > 10", "个人忧伤较高",
                "您在紧张的人际情境中容易感到焦虑、害怕和无助，建议学习情绪调节技巧以缓解过度的情绪反应。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="人际反应指针量表(IRI-C)",
        description="本问卷帮助了解您的共情能力。共22题，大约需要5分钟完成。",
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
