"""P47: IPIP-NEO-120 大五人格120题"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ipip-neo120"
IMPORT_CODE = "huaxinyun-ipip-neo120"

OPT_NORMAL = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]
OPT_REVERSE = [
    ("非常准确", 1), ("比较准确", 2), ("不确定", 3), ("比较不准确", 4), ("非常不准确", 5)
]

QUESTIONS_RAW = [
    (1, "为很多事情感到担心", False),
    (2, "很容易交到朋友", False),
    (3, "有丰富的想象力", False),
    (4, "信任其他人", False),
    (5, "能成功完成任务", False),
    (6, "很容易生气", False),
    (7, "喜欢参加大型聚会", False),
    (8, "认为艺术是很重要的", False),
    (9, "会利用他人来达成自己的目的", False),
    (10, "喜欢整洁", False),
    (11, "时常感到忧郁", False),
    (12, "承担责任", False),
    (13, "能强烈感受到自己的情绪", False),
    (14, "乐于帮助他人", False),
    (15, "信守承诺", False),
    (16, "感觉自己很难接近别人", False),
    (17, "总是是很忙碌", False),
    (18, "相比墨守成规，我更喜欢有变化", False),
    (19, "喜欢和别人比试", False),
    (20, "工作努力", False),
    (21, "大吃大喝寻欢作乐", False),
    (22, "喜欢追求刺激", False),
    (23, "喜欢阅读有挑战性的材料", False),
    (24, "相信自己比别人更好", False),
    (25, "我总是有所准备", False),
    (26, "容易慌张", False),
    (27, "我的快乐会感染周围的人", False),
    (28, "认为自己在政治方面非常自由开放", False),
    (29, "同情流浪汉", False),
    (30, "会不经过思考就开始行动", False),
    (31, "担心会发生最糟糕的情况", False),
    (32, "和其他人待在一起时我觉得很自在", False),
    (33, "喜欢天马行空地幻想", False),
    (34, "相信他人的出发点是好的", False),
    (35, "在自己所从事的领域出类拔萃", False),
    (36, "容易被激怒", False),
    (37, "在聚会上我会和很多不同的人交谈", False),
    (38, "我能发现别人看不到的美", False),
    (39, "为了领先别人我会采用作弊的方式", False),
    (40, "经常忘记把东西放回原处", True),
    (41, "不喜欢自己", False),
    (42, "我会尝试去领导他人", False),
    (43, "能感受到他人的情绪", False),
    (44, "关心他人", False),
    (45, "我会实话实说", False),
    (46, "害怕引起他人的注意", False),
    (47, "总是是在奔波", False),
    (48, "我更喜欢做自己熟悉的事情", True),
    (49, "会冲人大喊大叫", False),
    (50, "我会超出预期地完成任务或工作", False),
    (51, "很少过度放纵自己", True),
    (52, "喜欢冒险", False),
    (53, "会避免参与关于哲学的讨论", True),
    (54, "觉得自己很了不起", False),
    (55, "能执行自己制定的计划", False),
    (56, "感到被各种事情压得喘不过气来", False),
    (57, "我的生活很快乐", False),
    (58, "相信没有绝对的对错之分", False),
    (59, "我同情那些处境不如自己的人", False),
    (60, "会做出草率的决定", False),
    (61, "对很多事情感到害怕", False),
    (62, "避免和他人接触", True),
    (63, "喜欢做白日梦", False),
    (64, "相信他人说的话", False),
    (65, "能轻松完成任务", False),
    (66, "发脾气", False),
    (67, "更喜欢一个人独处", True),
    (68, "不喜欢诗歌", True),
    (69, "占别人的便宜", False),
    (70, "我的房间很乱", True),
    (71, "经常情绪低落", False),
    (72, "掌控局面", False),
    (73, "很少察觉到自己的情绪反应", True),
    (74, "对他人的感受漠不关心", True),
    (75, "破坏规则", True),
    (76, "只有和朋友在一起的时候我才会感到自在", False),
    (77, "我的闲暇时间非常充实", False),
    (78, "不喜欢改变", True),
    (79, "侮辱他人", False),
    (80, "在工作或学习上我不会多做过得去就行", True),
    (81, "能轻松抵御诱惑", True),
    (82, "喜欢不计后果地行事", False),
    (83, "理解抽象概念对我来说有些困难", True),
    (84, "对自己的评价很高", False),
    (85, "浪费时间", True),
    (86, "感觉自己处理事情力不从心", False),
    (87, "热爱生活", False),
    (88, "我在政治上比较保守", True),
    (89, "对别人遇到的麻烦事不感兴趣", True),
    (90, "仓促行事", False),
    (91, "我很容易觉得压力大", False),
    (92, "和他人保持距离", True),
    (93, "喜欢陷入沉思", False),
    (94, "不相信别人", True),
    (95, "知道如何完成任务", False),
    (96, "不会轻易被惹恼", True),
    (97, "避开人多的地方", True),
    (98, "不喜欢去美术馆", True),
    (99, "给别人使坏", False),
    (100, "我的东西放得到处都是", True),
    (101, "对自己感到满意", True),
    (102, "等着别人来带头", True),
    (103, "不理解那些情绪化的人", True),
    (104, "不愿为他人花费时间", True),
    (105, "违背自己的承诺", True),
    (106, "不会被复杂的社交情境所困扰", True),
    (107, "喜欢慢慢来", True),
    (108, "我喜欢传统的方式", True),
    (109, "报复别人", False),
    (110, "对工作或学业不怎么投入时间和精力", True),
    (111, "可以控制自己的欲望", True),
    (112, "我的行为狂放不羁", False),
    (113, "对理论性的讨论不感兴趣", True),
    (114, "吹嘘自己的美德", False),
    (115, "拖很久才开始做一件事", True),
    (116, "在压力下能保持冷静", True),
    (117, "看到生活中好的一面", False),
    (118, "认为我们应该严惩犯罪", True),
    (119, "我尽量不去想那些需要帮助的人", True),
    (120, "做事不经过思考", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def mean_formula(qs):
    terms = " + ".join(f"hx_t_{q}" for q in qs)
    return f"({terms}) / {len(qs)}"

def low_mid_high(dim_num):
    return [
        result_rule(f"hx_wd_y_{dim_num} <= 2.0", "低", "您在该维度上得分较低。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.0 && hx_wd_y_{dim_num} <= 3.5", "中", "您在该维度上得分中等。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 3.5", "高", "您在该维度上得分较高。", "none"),
    ]

def make_dimensions():
    dims = []
    dims.append(dimension("N1_焦虑", "N1", 1, mean_formula([1, 31, 61, 91]), "", low_mid_high(1)))
    dims.append(dimension("N2_愤怒", "N2", 2, mean_formula([6, 36, 66, 96]), "", low_mid_high(2)))
    dims.append(dimension("N3_抑郁", "N3", 3, mean_formula([11, 41, 71, 101]), "", low_mid_high(3)))
    dims.append(dimension("N4_自我意识", "N4", 4, mean_formula([16, 46, 76, 106]), "", low_mid_high(4)))
    dims.append(dimension("N5_冲动性", "N5", 5, mean_formula([21, 51, 81, 111]), "", low_mid_high(5)))
    dims.append(dimension("N6_脆弱性", "N6", 6, mean_formula([26, 56, 86, 116]), "", low_mid_high(6)))
    dims.append(dimension("E1_热情", "E1", 7, mean_formula([2, 32, 62, 92]), "", low_mid_high(7)))
    dims.append(dimension("E2_合群", "E2", 8, mean_formula([7, 37, 67, 97]), "", low_mid_high(8)))
    dims.append(dimension("E3_果断", "E3", 9, mean_formula([12, 42, 72, 102]), "", low_mid_high(9)))
    dims.append(dimension("E4_活跃", "E4", 10, mean_formula([17, 47, 77, 107]), "", low_mid_high(10)))
    dims.append(dimension("E5_寻求刺激", "E5", 11, mean_formula([22, 52, 82, 112]), "", low_mid_high(11)))
    dims.append(dimension("E6_积极情绪", "E6", 12, mean_formula([27, 57, 87, 117]), "", low_mid_high(12)))
    dims.append(dimension("O1_想象力", "O1", 13, mean_formula([3, 33, 63, 93]), "", low_mid_high(13)))
    dims.append(dimension("O2_审美", "O2", 14, mean_formula([8, 38, 68, 98]), "", low_mid_high(14)))
    dims.append(dimension("O3_情感", "O3", 15, mean_formula([13, 43, 73, 103]), "", low_mid_high(15)))
    dims.append(dimension("O4_冒险", "O4", 16, mean_formula([18, 48, 78, 108]), "", low_mid_high(16)))
    dims.append(dimension("O5_思想", "O5", 17, mean_formula([23, 53, 83, 113]), "", low_mid_high(17)))
    dims.append(dimension("O6_价值", "O6", 18, mean_formula([28, 58, 88, 118]), "", low_mid_high(18)))
    dims.append(dimension("A1_信任", "A1", 19, mean_formula([4, 34, 64, 94]), "", low_mid_high(19)))
    dims.append(dimension("A2_坦率", "A2", 20, mean_formula([9, 39, 69, 99]), "", low_mid_high(20)))
    dims.append(dimension("A3_利他", "A3", 21, mean_formula([14, 44, 74, 104]), "", low_mid_high(21)))
    dims.append(dimension("A4_顺从", "A4", 22, mean_formula([19, 49, 79, 109]), "", low_mid_high(22)))
    dims.append(dimension("A5_谦逊", "A5", 23, mean_formula([24, 54, 84, 114]), "", low_mid_high(23)))
    dims.append(dimension("A6_敏感", "A6", 24, mean_formula([29, 59, 89, 119]), "", low_mid_high(24)))
    dims.append(dimension("C1_胜任", "C1", 25, mean_formula([5, 35, 65, 95]), "", low_mid_high(25)))
    dims.append(dimension("C2_秩序", "C2", 26, mean_formula([10, 40, 70, 100]), "", low_mid_high(26)))
    dims.append(dimension("C3_责任感", "C3", 27, mean_formula([15, 45, 75, 105]), "", low_mid_high(27)))
    dims.append(dimension("C4_成就努力", "C4", 28, mean_formula([20, 50, 80, 110]), "", low_mid_high(28)))
    dims.append(dimension("C5_自律", "C5", 29, mean_formula([25, 55, 85, 115]), "", low_mid_high(29)))
    dims.append(dimension("C6_审慎", "C6", 30, mean_formula([30, 60, 90, 120]), "", low_mid_high(30)))
    dims.append(dimension("神经质", "N_total", 31, mean_formula([1, 31, 61, 91, 6, 36, 66, 96, 11, 41, 71, 101, 16, 46, 76, 106, 21, 51, 81, 111, 26, 56, 86, 116]), "", low_mid_high(31)))
    dims.append(dimension("外向性", "E_total", 32, mean_formula([2, 32, 62, 92, 7, 37, 67, 97, 12, 42, 72, 102, 17, 47, 77, 107, 22, 52, 82, 112, 27, 57, 87, 117]), "", low_mid_high(32)))
    dims.append(dimension("开放性", "O_total", 33, mean_formula([3, 33, 63, 93, 8, 38, 68, 98, 13, 43, 73, 103, 18, 48, 78, 108, 23, 53, 83, 113, 28, 58, 88, 118]), "", low_mid_high(33)))
    dims.append(dimension("宜人性", "A_total", 34, mean_formula([4, 34, 64, 94, 9, 39, 69, 99, 14, 44, 74, 104, 19, 49, 79, 109, 24, 54, 84, 114, 29, 59, 89, 119]), "", low_mid_high(34)))
    dims.append(dimension("尽责性", "C_total", 35, mean_formula([5, 35, 65, 95, 10, 40, 70, 100, 15, 45, 75, 105, 20, 50, 80, 110, 25, 55, 85, 115, 30, 60, 90, 120]), "", low_mid_high(35)))
    return dims

def build():
    return build_scale(
        title="IPIP大五人格120题(IPIP-NEO-120)",
        description="本问卷帮助全面了解您在30个人格特质维度上的表现，是大五人格的精细评估工具。共120题，大约需要20分钟完成。",
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
