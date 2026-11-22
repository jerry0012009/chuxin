#!/usr/bin/env python3
"""Generate 13 corrected import scripts using the correct API."""
import os, json, textwrap

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def write_script(filename, content):
    path = os.path.join(SCRIPTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Wrote {filename}")

# ============================================================
# p47_ipip_neo120.py
# ============================================================
def gen_p47():
    # Items from the old file
    items = ['为很多事情感到担心', '很容易交到朋友', '有丰富的想象力', '信任其他人', '能成功完成任务', '很容易生气', '喜欢参加大型聚会', '认为艺术是很重要的', '会利用他人来达成自己的目的', '喜欢整洁', '时常感到忧郁', '承担责任', '能强烈感受到自己的情绪', '乐于帮助他人', '信守承诺', '感觉自己很难接近别人', '总是是很忙碌', '相比墨守成规，我更喜欢有变化', '喜欢和别人比试', '工作努力', '大吃大喝寻欢作乐', '喜欢追求刺激', '喜欢阅读有挑战性的材料', '相信自己比别人更好', '我总是有所准备', '容易慌张', '我的快乐会感染周围的人', '认为自己在政治方面非常自由开放', '同情流浪汉', '会不经过思考就开始行动', '担心会发生最糟糕的情况', '和其他人待在一起时我觉得很自在', '喜欢天马行空地幻想', '相信他人的出发点是好的', '在自己所从事的领域出类拔萃', '容易被激怒', '在聚会上我会和很多不同的人交谈', '我能发现别人看不到的美', '为了领先别人我会采用作弊的方式', '经常忘记把东西放回原处', '不喜欢自己', '我会尝试去领导他人', '能感受到他人的情绪', '关心他人', '我会实话实说', '害怕引起他人的注意', '总是是在奔波', '我更喜欢做自己熟悉的事情', '会冲人大喊大叫', '我会超出预期地完成任务或工作', '很少过度放纵自己', '喜欢冒险', '会避免参与关于哲学的讨论', '觉得自己很了不起', '能执行自己制定的计划', '感到被各种事情压得喘不过气来', '我的生活很快乐', '相信没有绝对的对错之分', '我同情那些处境不如自己的人', '会做出草率的决定', '对很多事情感到害怕', '避免和他人接触', '喜欢做白日梦', '相信他人说的话', '能轻松完成任务', '发脾气', '更喜欢一个人独处', '不喜欢诗歌', '占别人的便宜', '我的房间很乱', '经常情绪低落', '掌控局面', '很少察觉到自己的情绪反应', '对他人的感受漠不关心', '破坏规则', '只有和朋友在一起的时候我才会感到自在', '我的闲暇时间非常充实', '不喜欢改变', '侮辱他人', '在工作或学习上我不会多做过得去就行', '能轻松抵御诱惑', '喜欢不计后果地行事', '理解抽象概念对我来说有些困难', '对自己的评价很高', '浪费时间', '感觉自己处理事情力不从心', '热爱生活', '我在政治上比较保守', '对别人遇到的麻烦事不感兴趣', '仓促行事', '我很容易觉得压力大', '和他人保持距离', '喜欢陷入沉思', '不相信别人', '知道如何完成任务', '不会轻易被惹恼', '避开人多的地方', '不喜欢去美术馆', '给别人使坏', '我的东西放得到处都是', '对自己感到满意', '等着别人来带头', '不理解那些情绪化的人', '不愿为他人花费时间', '违背自己的承诺', '不会被复杂的社交情境所困扰', '喜欢慢慢来', '我喜欢传统的方式', '报复别人', '对工作或学业不怎么投入时间和精力', '可以控制自己的欲望', '我的行为狂放不羁', '对理论性的讨论不感兴趣', '吹嘘自己的美德', '拖很久才开始做一件事', '在压力下能保持冷静', '看到生活中好的一面', '认为我们应该严惩犯罪', '我尽量不去想那些需要帮助的人', '做事不经过思考']
    
    # Reverse items (0-indexed from old code)
    rev_0idx = [95, 100, 105, 50, 80, 110, 115, 61, 91, 66, 96, 101, 106, 67, 97, 72, 102, 47, 77, 107, 52, 82, 112, 87, 117, 93, 73, 103, 88, 118, 39, 69, 99, 74, 104, 79, 109, 84, 114]
    rev_1idx = set(i + 1 for i in rev_0idx)

    facets = [
        ("N1_焦虑", "N1", [1, 31, 61, 91]),
        ("N2_愤怒", "N2", [6, 36, 66, 96]),
        ("N3_抑郁", "N3", [11, 41, 71, 101]),
        ("N4_自我意识", "N4", [16, 46, 76, 106]),
        ("N5_冲动性", "N5", [21, 51, 81, 111]),
        ("N6_脆弱性", "N6", [26, 56, 86, 116]),
        ("E1_热情", "E1", [2, 32, 62, 92]),
        ("E2_合群", "E2", [7, 37, 67, 97]),
        ("E3_果断", "E3", [12, 42, 72, 102]),
        ("E4_活跃", "E4", [17, 47, 77, 107]),
        ("E5_寻求刺激", "E5", [22, 52, 82, 112]),
        ("E6_积极情绪", "E6", [27, 57, 87, 117]),
        ("O1_想象力", "O1", [3, 33, 63, 93]),
        ("O2_审美", "O2", [8, 38, 68, 98]),
        ("O3_情感", "O3", [13, 43, 73, 103]),
        ("O4_冒险", "O4", [18, 48, 78, 108]),
        ("O5_思想", "O5", [23, 53, 83, 113]),
        ("O6_价值", "O6", [28, 58, 88, 118]),
        ("A1_信任", "A1", [4, 34, 64, 94]),
        ("A2_坦率", "A2", [9, 39, 69, 99]),
        ("A3_利他", "A3", [14, 44, 74, 104]),
        ("A4_顺从", "A4", [19, 49, 79, 109]),
        ("A5_谦逊", "A5", [24, 54, 84, 114]),
        ("A6_敏感", "A6", [29, 59, 89, 119]),
        ("C1_胜任", "C1", [5, 35, 65, 95]),
        ("C2_秩序", "C2", [10, 40, 70, 100]),
        ("C3_责任感", "C3", [15, 45, 75, 105]),
        ("C4_成就努力", "C4", [20, 50, 80, 110]),
        ("C5_自律", "C5", [25, 55, 85, 115]),
        ("C6_审慎", "C6", [30, 60, 90, 120]),
    ]
    domain_totals = [
        ("神经质", "N_total", [1,31,61,91, 6,36,66,96, 11,41,71,101, 16,46,76,106, 21,51,81,111, 26,56,86,116]),
        ("外向性", "E_total", [2,32,62,92, 7,37,67,97, 12,42,72,102, 17,47,77,107, 22,52,82,112, 27,57,87,117]),
        ("开放性", "O_total", [3,33,63,93, 8,38,68,98, 13,43,73,103, 18,48,78,108, 23,53,83,113, 28,58,88,118]),
        ("宜人性", "A_total", [4,34,64,94, 9,39,69,99, 14,44,74,104, 19,49,79,109, 24,54,84,114, 29,59,89,119]),
        ("尽责性", "C_total", [5,35,65,95, 10,40,70,100, 15,45,75,105, 20,50,80,110, 25,55,85,115, 30,60,90,120]),
    ]

    lines = []
    lines.append('"""P47: IPIP-NEO-120 大五人格120题"""')
    lines.append('import sys, os, json')
    lines.append('sys.path.insert(0, os.path.dirname(__file__))')
    lines.append('from import_helpers import *')
    lines.append('')
    lines.append('SCALE_CODE = "ipip-neo120"')
    lines.append('IMPORT_CODE = "huaxinyun-ipip-neo120"')
    lines.append('')
    lines.append('OPT_NORMAL = [')
    lines.append('    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)')
    lines.append(']')
    lines.append('OPT_REVERSE = [')
    lines.append('    ("非常准确", 1), ("比较准确", 2), ("不确定", 3), ("比较不准确", 4), ("非常不准确", 5)')
    lines.append(']')
    lines.append('')
    lines.append('QUESTIONS_RAW = [')
    for i, text in enumerate(items):
        order = i + 1
        is_rev = order in rev_1idx
        lines.append(f'    ({order}, "{text}", {is_rev}),')
    lines.append(']')
    lines.append('')
    lines.append('def make_questions():')
    lines.append('    qs = []')
    lines.append('    for order, text, is_rev in QUESTIONS_RAW:')
    lines.append('        opts = OPT_REVERSE if is_rev else OPT_NORMAL')
    lines.append('        qs.append(radio_q(order, text, opts))')
    lines.append('    return qs')
    lines.append('')
    lines.append('def mean_formula(qs):')
    lines.append('    return f"({q_range(qs[0], qs[-1])}) / {len(qs)}"')
    lines.append('')
    lines.append('def low_mid_high(dim_num):')
    lines.append('    return [')
    lines.append(f'        result_rule(f"hx_wd_y_{{dim_num}} <= 2.0", "低", "您在该维度上得分较低。", "none"),')
    lines.append(f'        result_rule(f"hx_wd_y_{{dim_num}} > 2.0 && hx_wd_y_{{dim_num}} <= 3.5", "中", "您在该维度上得分中等。", "none"),')
    lines.append(f'        result_rule(f"hx_wd_y_{{dim_num}} > 3.5", "高", "您在该维度上得分较高。", "none"),')
    lines.append('    ]')
    lines.append('')
    lines.append('def make_dimensions():')
    lines.append('    dims = []')
    dim_num = 1
    for name, code, qs in facets:
        lines.append(f'    dims.append(dimension("{name}", "{code}", {dim_num}, mean_formula({qs}), "", low_mid_high({dim_num})))')
        dim_num += 1
    for name, code, qs in domain_totals:
        lines.append(f'    dims.append(dimension("{name}", "{code}", {dim_num}, mean_formula({qs}), "", low_mid_high({dim_num})))')
        dim_num += 1
    lines.append('    return dims')
    lines.append('')
    lines.append('def build():')
    lines.append('    return build_scale(')
    lines.append('        title="IPIP大五人格120题(IPIP-NEO-120)",')
    lines.append('        description="本问卷帮助全面了解您在30个人格特质维度上的表现，是大五人格的精细评估工具。共120题，大约需要20分钟完成。",')
    lines.append('        code=SCALE_CODE,')
    lines.append('        questions=make_questions(),')
    lines.append('        dimensions=make_dimensions(),')
    lines.append('    )')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    scale = build()')
    lines.append('    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")')
    lines.append('    os.makedirs(os.path.dirname(json_path), exist_ok=True)')
    lines.append('    with open(json_path, "w", encoding="utf-8") as f:')
    lines.append('        json.dump(scale, f, ensure_ascii=False, indent=2)')
    lines.append('    print(f"✅ JSON saved: {json_path}")')
    lines.append('    print(f"   Questions: {len(scale[\'questions\'])}")')
    lines.append('    print(f"   Dimensions: {len(scale[\'dimensions\'])}")')
    lines.append('')
    lines.append('    print("\\n--- Dry Run ---")')
    lines.append('    result = import_scale(scale, dry_run=True, publish=True)')
    lines.append('    print(f"   Importable: {result.get(\'importable\', 0)}")')
    lines.append('    print(f"   Publishable: {result.get(\'publishable\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | issues={item.get(\'issues\')} | warnings={item.get(\'warnings\')}")')
    lines.append('')
    lines.append('    print("\\n--- Importing ---")')
    lines.append('    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)')
    lines.append('    print(f"   Imported: {result.get(\'imported\', 0)}")')
    lines.append('    print(f"   Updated: {result.get(\'updated\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | id={item.get(\'survey_id\', \'N/A\')}")')
    lines.append('')
    lines.append('    print("\\n--- DB Verify ---")')
    lines.append('    print(verify_in_db(IMPORT_CODE))')
    lines.append('')

    write_script("p47_ipip_neo120.py", "\n".join(lines))

# ============================================================
# p48_hexaco60.py
# ============================================================
def gen_p48():
    items = ['如果有机会作弊而不被发现，我会作弊', '我会接受贿赂', '我会假装喜欢那些对我有用的人', '我不会因为有人拥有我想要的东西就去偷', '我不会为了得到好处而奉承别人', '我认为我比大多数人更值得获得特殊待遇', '我想要别人仰慕我', '我觉得自己应该得到特别优待', '我想要别人注意到我', '我觉得我比别人更重要', '我会因为别人的情绪而受到影响', '看到别人哭的时候我也会想哭', '我会为别人的不幸感到难过', '当朋友向我倾诉他们的问题时，我会感到担忧', '面对危急情况我会恐慌', '面对令人害怕的情况时我会感到紧张', '我会因为压力而失眠', '我害怕很多事物', '我在有压力的情况下会感到不知所措', '我经常担心自己的健康', '我喜欢和别人聊天', '我喜欢有很多人的社交场合', '我在社交场合中感到自在', '我喜欢成为大家注意的焦点', '我能轻松地让别人感到放松', '我在社交中充满活力', '我能和各种各样的人相处融洽', '我喜欢人多热闹的场合', '我能很快和陌生人打成一片', '我在大型聚会上感到快乐', '我会体谅别人的感受', '我会原谅别人的过错', '我尊重别人的意见即使不同意', '我会耐心地对待别人的缺点', '我会容忍别人的不同观点', '我对别人很友善', '我愿意帮助有需要的人', '我能和很难相处的人合作', '我会考虑别人的感受', '我很少对别人发脾气', '我会提前做好计划', '我的工作很有条理', '我会按时完成任务', '我做事很认真', '我会坚持把工作做完', '我会遵守承诺', '我会仔细检查工作中的错误', '我做事有始有终', '我会为未来做准备', '我的工作质量很高', '我对抽象的概念感兴趣', '我喜欢思考复杂的哲学问题', '我对各种艺术形式感兴趣', '我喜欢尝试新事物', '我有丰富的想象力', '我对不同文化感兴趣', '我喜欢阅读深度文章', '我对科学发现感兴趣', '我能理解抽象的概念', '我喜欢学习新的知识']
    
    # H domain: items 1-10, reverse items at 0-idx [0,1,2,5,6,7,8,9] -> 1-idx [1,2,3,6,7,8,9,10]
    # Other domains: no reverse items
    h_rev = {1, 2, 3, 6, 7, 8, 9, 10}
    
    lines = []
    lines.append('"""P48: HEXACO-60 六大人格量表"""')
    lines.append('import sys, os, json')
    lines.append('sys.path.insert(0, os.path.dirname(__file__))')
    lines.append('from import_helpers import *')
    lines.append('')
    lines.append('SCALE_CODE = "hexaco-60"')
    lines.append('IMPORT_CODE = "huaxinyun-hexaco-60"')
    lines.append('')
    lines.append('OPT_NORMAL = [')
    lines.append('    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)')
    lines.append(']')
    lines.append('OPT_REVERSE = [')
    lines.append('    ("非常准确", 1), ("比较准确", 2), ("不确定", 3), ("比较不准确", 4), ("非常不准确", 5)')
    lines.append(']')
    lines.append('')
    lines.append('QUESTIONS_RAW = [')
    for i, text in enumerate(items):
        order = i + 1
        is_rev = order in h_rev
        lines.append(f'    ({order}, "{text}", {is_rev}),')
    lines.append(']')
    lines.append('')
    lines.append('def make_questions():')
    lines.append('    qs = []')
    lines.append('    for order, text, is_rev in QUESTIONS_RAW:')
    lines.append('        opts = OPT_REVERSE if is_rev else OPT_NORMAL')
    lines.append('        qs.append(radio_q(order, text, opts))')
    lines.append('    return qs')
    lines.append('')
    lines.append('def make_dimensions():')
    lines.append('    return [')
    lines.append('        dimension("诚实-谦逊", "honesty_humility", 1, q_range(1, 10), "", [')
    lines.append('            result_rule("hx_wd_y_1 <= 2.0", "低", "您在诚实-谦逊维度上得分较低，倾向于关注个人利益和社会地位。", "none"),')
    lines.append('            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您在诚实-谦逊维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_1 > 3.5", "高", "您在诚实-谦逊维度上得分较高，为人真诚谦逊，不追求特权。", "none"),')
    lines.append('        ]),')
    lines.append('        dimension("情绪性", "emotionality", 2, q_range(11, 20), "", [')
    lines.append('            result_rule("hx_wd_y_2 <= 2.0", "低", "您在情绪性维度上得分较低，情绪较为稳定。", "none"),')
    lines.append('            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您在情绪性维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_2 > 3.5", "高", "您在情绪性维度上得分较高，情感丰富，共情能力强。", "none"),')
    lines.append('        ]),')
    lines.append('        dimension("外向性", "extraversion", 3, q_range(21, 30), "", [')
    lines.append('            result_rule("hx_wd_y_3 <= 2.0", "低", "您在外向性维度上得分较低，偏好安静独处。", "none"),')
    lines.append('            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您在外向性维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_3 > 3.5", "高", "您在外向性维度上得分较高，社交活跃，精力充沛。", "none"),')
    lines.append('        ]),')
    lines.append('        dimension("宜人性", "agreeableness", 4, q_range(31, 40), "", [')
    lines.append('            result_rule("hx_wd_y_4 <= 2.0", "低", "您在宜人性维度上得分较低，可能较为挑剔或固执。", "none"),')
    lines.append('            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "中", "您在宜人性维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_4 > 3.5", "高", "您在宜人性维度上得分较高，待人友善，善于合作。", "none"),')
    lines.append('        ]),')
    lines.append('        dimension("尽责性", "conscientiousness", 5, q_range(41, 50), "", [')
    lines.append('            result_rule("hx_wd_y_5 <= 2.0", "低", "您在尽责性维度上得分较低，做事较为随意。", "none"),')
    lines.append('            result_rule("hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "中", "您在尽责性维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_5 > 3.5", "高", "您在尽责性维度上得分较高，做事认真负责。", "none"),')
    lines.append('        ]),')
    lines.append('        dimension("开放性", "openness", 6, q_range(51, 60), "", [')
    lines.append('            result_rule("hx_wd_y_6 <= 2.0", "低", "您在开放性维度上得分较低，偏好传统和熟悉的事物。", "none"),')
    lines.append('            result_rule("hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "中", "您在开放性维度上得分中等。", "none"),')
    lines.append('            result_rule("hx_wd_y_6 > 3.5", "高", "您在开放性维度上得分较高，思维开阔，善于接受新事物。", "none"),')
    lines.append('        ]),')
    lines.append('    ]')
    lines.append('')
    lines.append('def build():')
    lines.append('    return build_scale(')
    lines.append('        title="六大人格量表(HEXACO-60)",')
    lines.append('        description="本问卷帮助了解您在诚实谦逊、情绪管理、社交倾向等六大人格维度上的特点。共60题，大约需要10分钟完成。",')
    lines.append('        code=SCALE_CODE,')
    lines.append('        questions=make_questions(),')
    lines.append('        dimensions=make_dimensions(),')
    lines.append('    )')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    scale = build()')
    lines.append('    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")')
    lines.append('    os.makedirs(os.path.dirname(json_path), exist_ok=True)')
    lines.append('    with open(json_path, "w", encoding="utf-8") as f:')
    lines.append('        json.dump(scale, f, ensure_ascii=False, indent=2)')
    lines.append('    print(f"✅ JSON saved: {json_path}")')
    lines.append('    print(f"   Questions: {len(scale[\'questions\'])}")')
    lines.append('    print(f"   Dimensions: {len(scale[\'dimensions\'])}")')
    lines.append('')
    lines.append('    print("\\n--- Dry Run ---")')
    lines.append('    result = import_scale(scale, dry_run=True, publish=True)')
    lines.append('    print(f"   Importable: {result.get(\'importable\', 0)}")')
    lines.append('    print(f"   Publishable: {result.get(\'publishable\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | issues={item.get(\'issues\')} | warnings={item.get(\'warnings\')}")')
    lines.append('')
    lines.append('    print("\\n--- Importing ---")')
    lines.append('    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)')
    lines.append('    print(f"   Imported: {result.get(\'imported\', 0)}")')
    lines.append('    print(f"   Updated: {result.get(\'updated\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | id={item.get(\'survey_id\', \'N/A\')}")')
    lines.append('')
    lines.append('    print("\\n--- DB Verify ---")')
    lines.append('    print(verify_in_db(IMPORT_CODE))')
    lines.append('')
    
    write_script("p48_hexaco60.py", "\n".join(lines))

# ============================================================
# Generic single-dimension script generator
# ============================================================
def gen_simple(filename, docstring, scale_code, import_code, title, description,
               items, dimensions_spec, has_reverse=False, reverse_set=None):
    """Generate a simple script with items and dimensions.
    
    dimensions_spec: list of (name, code, dim_num, (start, end), conclusions)
    where conclusions are (label, condition, text) tuples
    """
    lines = []
    lines.append(f'"""{docstring}"""')
    lines.append('import sys, os, json')
    lines.append('sys.path.insert(0, os.path.dirname(__file__))')
    lines.append('from import_helpers import *')
    lines.append('')
    lines.append(f'SCALE_CODE = "{scale_code}"')
    lines.append(f'IMPORT_CODE = "{import_code}"')
    lines.append('')
    
    if has_reverse:
        lines.append('OPT_NORMAL = [')
        lines.append('    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)')
        lines.append(']')
        lines.append('OPT_REVERSE = [')
        lines.append('    ("非常准确", 1), ("比较准确", 2), ("不确定", 3), ("比较不准确", 4), ("非常不准确", 5)')
        lines.append(']')
        lines.append('')
    else:
        lines.append('OPTIONS = [')
        lines.append('    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)')
        lines.append(']')
        lines.append('')
    
    lines.append('QUESTIONS_RAW = [')
    for i, text in enumerate(items):
        order = i + 1
        if has_reverse:
            is_rev = order in (reverse_set or set())
            lines.append(f'    ({order}, "{text}", {is_rev}),')
        else:
            lines.append(f'    ({order}, "{text}"),')
    lines.append(']')
    lines.append('')
    
    lines.append('def make_questions():')
    if has_reverse:
        lines.append('    qs = []')
        lines.append('    for order, text, is_rev in QUESTIONS_RAW:')
        lines.append('        opts = OPT_REVERSE if is_rev else OPT_NORMAL')
        lines.append('        qs.append(radio_q(order, text, opts))')
        lines.append('    return qs')
    else:
        lines.append('    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]')
    lines.append('')
    
    lines.append('def make_dimensions():')
    lines.append('    return [')
    for name, code, dim_num, (start, end), conclusions in dimensions_spec:
        n_items = end - start + 1
        lines.append(f'        dimension("{name}", "{code}", {dim_num}, "({q_range_str(start, end)}) / {n_items}", "", [')
        for label, cond, text in conclusions:
            lines.append(f'            result_rule("{cond}", "{label}", "{text}", "none"),')
        lines.append('        ]),')
    lines.append('    ]')
    lines.append('')
    
    lines.append('def build():')
    lines.append('    return build_scale(')
    lines.append(f'        title="{title}",')
    lines.append(f'        description="{description}",')
    lines.append('        code=SCALE_CODE,')
    lines.append('        questions=make_questions(),')
    lines.append('        dimensions=make_dimensions(),')
    lines.append('    )')
    lines.append('')
    
    lines.append('if __name__ == "__main__":')
    lines.append('    scale = build()')
    lines.append('    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")')
    lines.append('    os.makedirs(os.path.dirname(json_path), exist_ok=True)')
    lines.append('    with open(json_path, "w", encoding="utf-8") as f:')
    lines.append('        json.dump(scale, f, ensure_ascii=False, indent=2)')
    lines.append('    print(f"✅ JSON saved: {json_path}")')
    lines.append('    print(f"   Questions: {len(scale[\'questions\'])}")')
    lines.append('    print(f"   Dimensions: {len(scale[\'dimensions\'])}")')
    lines.append('')
    lines.append('    print("\\n--- Dry Run ---")')
    lines.append('    result = import_scale(scale, dry_run=True, publish=True)')
    lines.append('    print(f"   Importable: {result.get(\'importable\', 0)}")')
    lines.append('    print(f"   Publishable: {result.get(\'publishable\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | issues={item.get(\'issues\')} | warnings={item.get(\'warnings\')}")')
    lines.append('')
    lines.append('    print("\\n--- Importing ---")')
    lines.append('    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)')
    lines.append('    print(f"   Imported: {result.get(\'imported\', 0)}")')
    lines.append('    print(f"   Updated: {result.get(\'updated\', 0)}")')
    lines.append('    for item in result.get("items", []):')
    lines.append('        print(f"   {item.get(\'title\')}: {item.get(\'action\')} | id={item.get(\'survey_id\', \'N/A\')}")')
    lines.append('')
    lines.append('    print("\\n--- DB Verify ---")')
    lines.append('    print(verify_in_db(IMPORT_CODE))')
    lines.append('')
    
    write_script(filename, "\n".join(lines))

def q_range_str(start, end):
    """Generate q_range formula string for inline use."""
    return " + ".join(f"hx_t_{i}" for i in range(start, end + 1))

# ============================================================
# p49_loc.py - 30 items, 3 dimensions, all OPT_NORMAL
# ============================================================
def gen_p49():
    items = ['我能否得到晋升主要取决于我的能力', '当我制定计划时，我几乎肯定能实现它', '我的成绩完全取决于我的努力程度', '对我来说，坚持自己的理想和目标是可能的', '只要我下定决心，就能影响身边发生的事', '我过着的生活很大程度上是由我自己决定的', '在与人交往时，我通常能掌控局面', '我的命运由自己掌握', '只要足够努力，我就能实现目标', '我在生活中取得的成就完全取决于我的能力', '能否得到我想要的晋升取决于有影响力的人', '我生活中发生的事大多是由有权势的人决定的', '在制定计划时，我需要确保它们不会触怒有权势的人', '为了实现目标，我需要获得有影响力的人的支持', '我的人生道路很大程度上取决于有权势的人', '有影响力的人决定了我能否成功', '要升职加薪，我必须讨好上司', '那些有权力的人掌控着我的生活', '我感到自己无法改变与权威人士的关系', '在社会中，普通人很难影响决策者', '很多事情的发生纯属偶然', '我的人生很大程度上取决于运气', '我常常发现好事会自然而然地发生', '我很难理解为什么有些事情会发生在我身上', '命运对我有很大影响', '运气在决定我的人生方向中起重要作用', '我生活中很多好事都是碰巧发生的', '我觉得很多事情都无法预料和控制', '我经常凭运气做成事情', '机遇决定了我人生中的大部分事情']
    
    gen_simple("p49_loc.py",
        "P49: 控制源量表(LOC)", "loc-control", "huaxinyun-loc-control",
        "控制源量表(LOC)",
        "本问卷帮助了解您对生活中事件归因方式的倾向，是内控还是外控。共30题，大约需要6分钟完成。",
        items,
        [
            ("内控性", "internality", 1, (1, 10), [
                ("低", "hx_wd_y_1 <= 2.0", "您倾向于认为外部因素决定事件结果，较少相信自己能掌控局面。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您对内外控制源的看法较为平衡。"),
                ("高", "hx_wd_y_1 > 3.5", "您倾向于认为自己的行为和努力能够影响事件结果，具有较强的自主感。"),
            ]),
            ("权威他人", "powerful_others", 2, (11, 20), [
                ("低", "hx_wd_y_2 <= 2.0", "您较少认为他人（权威、领导）控制着自己的生活。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您对权威他人影响力的感知中等。"),
                ("高", "hx_wd_y_2 > 3.5", "您倾向于认为有权势的人掌控着自己的生活方向。"),
            ]),
            ("机遇", "chance", 3, (21, 30), [
                ("低", "hx_wd_y_3 <= 2.0", "您较少将生活事件归因于运气或偶然。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您对机遇因素的看法较为中立。"),
                ("高", "hx_wd_y_3 > 3.5", "您倾向于认为运气和机遇在生活中起重要作用。"),
            ]),
        ])

# ============================================================
# p50_ei.py - 56 items, 7 dimensions, all OPT_NORMAL
# ============================================================
def gen_p50():
    items = ['当我很开心的时候，别人很容易看出来', '人们能从我的表情中读出我的情绪', '当我感到快乐时，我会通过言行表现出来', '我的朋友们能轻易察觉我的好心情', '我善于表达积极的情绪', '当我开心时，我身边的人也会被感染', '我很容易向别人展示我的快乐', '我的积极情绪很有感染力', '当我难过时，别人能看出我的情绪变化', '我的面部表情会暴露我的坏心情', '当我情绪低落时，身边的人能察觉到', '我很难隐藏自己的悲伤', '当我焦虑时，我的言行会有所体现', '别人能轻易看出我是否紧张', '我的烦恼会通过我的行为表现出来', '当我生气时，周围的人都知道', '我经常关注自己的情绪变化', '我会仔细体会自己的感受', '我善于觉察自己的情绪状态', '我总是留意自己心情的变化', '我花很多时间思考自己的感受', '我对自己的情绪很敏感', '我能准确地识别自己的情绪', '我经常反思自己的情绪反应', '我在做决定时会考虑自己的情绪', '我的情绪会影响我的判断', '我会根据自己的感受来做出选择', '我在决策时会参考自己的情绪状态', '我的心情会影响我的决定', '我在做重要决定时会关注自己的直觉', '我的感受帮助我做出好的决定', '我的情绪为我的决策提供有用信息', '当别人分享好消息时，我会由衷地为他们高兴', '朋友成功时我会真心为他们感到高兴', '我能分享他人的快乐', '当别人开心时，我也会感到快乐', '我善于回应他人的好消息', '看到别人幸福我会感到温暖', '我很容易被别人的好心情感染', '当别人取得成就时我会真诚祝贺', '当别人难过时，我也会感到悲伤', '看到别人受苦我会感到不安', '朋友遇到困难时我会很担心', '我能感受到他人的痛苦', '当别人情绪低落时我也会受影响', '看到别人哭泣我会很难过', '我对别人的不幸有强烈的反应', '他人的悲伤会引起我的共鸣', '我非常关心他人的感受', '我会主动帮助情绪低落的朋友', '我对别人的痛苦感同身受', '我会照顾身边人的情绪需要', '我对他人有很强的同理心', '我愿意花时间倾听别人的烦恼', '我能设身处地为他人着想', '我对别人的情感需求很敏感']
    
    gen_simple("p50_ei.py",
        "P50: 情绪智力量表(EI)", "ei-emotional-intelligence", "huaxinyun-ei-emotional-intelligence",
        "情绪智力量表(EI)",
        "本问卷帮助了解您在情绪感知、表达和运用方面的七个能力维度。共56题，大约需要10分钟完成。",
        items,
        [
            ("正面表达", "positive_expressivity", 1, (1, 8), [
                ("低", "hx_wd_y_1 <= 2.0", "您在表达积极情绪方面较为内敛。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您在表达积极情绪方面较为适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您善于表达和分享积极情绪，感染力强。"),
            ]),
            ("负面表达", "negative_expressivity", 2, (9, 16), [
                ("低", "hx_wd_y_2 <= 2.0", "您不太容易在外在表现中流露负面情绪。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的负面情绪表达较为适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您的负面情绪较容易通过言行表现出来。"),
            ]),
            ("关注情绪", "attending_emotions", 3, (17, 24), [
                ("低", "hx_wd_y_3 <= 2.0", "您较少主动关注和反思自己的情绪。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您对自身情绪的关注度适中。"),
                ("高", "hx_wd_y_3 > 3.5", "您善于觉察和关注自己的情绪变化。"),
            ]),
            ("情绪决策", "emotion_decision", 4, (25, 32), [
                ("低", "hx_wd_y_4 <= 2.0", "您在决策时较少受情绪影响。"),
                ("中", "hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "您的决策方式较为平衡。"),
                ("高", "hx_wd_y_4 > 3.5", "您善于利用情绪信息辅助决策。"),
            ]),
            ("响应快乐", "responsive_joy", 5, (33, 40), [
                ("低", "hx_wd_y_5 <= 2.0", "您对他人快乐情绪的共鸣度较低。"),
                ("中", "hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "您能适当地回应他人的快乐。"),
                ("高", "hx_wd_y_5 > 3.5", "您善于分享和回应他人的快乐，共情能力强。"),
            ]),
            ("响应痛苦", "responsive_distress", 6, (41, 48), [
                ("低", "hx_wd_y_6 <= 2.0", "您对他人痛苦的共情度较低。"),
                ("中", "hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "您的共情程度适中。"),
                ("高", "hx_wd_y_6 > 3.5", "您对他人的痛苦有很强的共情能力。"),
            ]),
            ("同理心", "empathy", 7, (49, 56), [
                ("低", "hx_wd_y_7 <= 2.0", "您的同理心水平较低。"),
                ("中", "hx_wd_y_7 > 2.0 && hx_wd_y_7 <= 3.5", "您的同理心水平适中。"),
                ("高", "hx_wd_y_7 > 3.5", "您有很强的同理心，善于理解和关心他人。"),
            ]),
        ])

# ============================================================
# p51_dissoc.py - 17 items, 3 dimensions
# ============================================================
def gen_p51():
    items = ['有时候我感觉自己的身体好像不是自己的', '我有时会感觉自己像在做梦一样', '我有时会觉得自己在从远处观察自己', '有时候我感觉自己和周围的世界之间有一层隔膜', '我有时会经历一种不真实的感觉', '有时候我感觉自己像是一个旁观者在看自己的生活', '我会完全沉浸在白日梦中以至于忘记周围的一切', '我经常陷入自己的想象中', '我会沉浸在电影或书中以至于完全意识不到周围发生的事', '听音乐时我会完全忘记自己的存在', '有时我会完全沉浸在自己的思绪中', '我会被自己的幻想深深吸引', '我有时会忘记自己刚才说了什么', '我有时想不起自己是否做过某件事', '我有时会忘记最近发生的事的细节', '我会忘记自己是否告诉过别人某件事', '我有时会忘记自己把东西放在哪里了']
    
    gen_simple("p51_dissoc.py",
        "P51: 解离体验量表(Dissociation)", "dissociation", "huaxinyun-dissociation",
        "解离体验量表(Dissociation)",
        "本问卷帮助了解您是否存在解离体验，如感觉不真实、记忆空白或过度沉浸。共17题，大约需要4分钟完成。",
        items,
        [
            ("去人格化", "depersonalization", 1, (1, 6), [
                ("低", "hx_wd_y_1 <= 2.0", "您很少有不真实的自我体验。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您偶尔会有轻微的不真实感。"),
                ("高", "hx_wd_y_1 > 3.5", "您经常体验到不真实感或与自身分离的感觉。"),
            ]),
            ("吸收", "absorption", 2, (7, 12), [
                ("低", "hx_wd_y_2 <= 2.0", "您较少沉浸在想象或幻想中。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的想象力和沉浸程度适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您容易完全沉浸在想象、幻想或体验中。"),
            ]),
            ("遗忘", "amnesia", 3, (13, 17), [
                ("低", "hx_wd_y_3 <= 2.0", "您的日常记忆力正常。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您偶尔会出现记忆空白。"),
                ("高", "hx_wd_y_3 > 3.5", "您经常出现记忆空白或遗忘近期事件的情况。"),
            ]),
        ])

# ============================================================
# p52_sm.py - 10 items, 1 dimension
# ============================================================
def gen_p52():
    items = ['我善于根据不同的社交场合调整自己的行为', '在不同的人面前我会表现得不一样', '我能够根据场合改变自己的形象', '我在社交中善于察言观色', '我会根据对方的反应调整自己的言行', '我善于在不同场合展现不同的自己', '我能够很好地掩饰自己的真实感受', '我善于读懂社交情境中的潜规则', '我会根据周围人的期望来调整自己', '我在与不同类型的人交往时表现不同']
    
    gen_simple("p52_sm.py",
        "P52: 自我监控量表(SM)", "self-monitoring", "huaxinyun-self-monitoring",
        "自我监控量表(SM)",
        "本问卷帮助了解您在社交场合中调整自己言行举止的能力。共10题，大约需要2分钟完成。",
        items,
        [
            ("自我监控", "self_monitoring", 1, (1, 10), [
                ("低", "hx_wd_y_1 <= 2.0", "您的自我监控能力较低，倾向于在不同场合保持一致的自我表现。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的自我监控能力适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您善于根据社交场合调整自己的言行举止，社交适应能力强。"),
            ]),
        ])

# ============================================================
# p53_bidr_im.py - 20 items, 1 dimension
# ============================================================
def gen_p53():
    items = ['我从来没有说过谎话', '我总是遵守交通规则', '我从来没有在背后说过别人的坏话', '我总是按时完成所有工作', '我从来没有迟到过', '我对每个人都很友善', '我从来没有有过不好的想法', '我总是做正确的事情', '我从来没有有过不道德的行为', '我总是诚实地回答所有问题', '我从来没有利用过别人', '我总是对自己的行为负责', '我从来没有违反过规则', '我总是考虑别人的感受', '我从来没有对人生过气', '我总是帮助有需要的人', '我从来没有撒过小谎', '我总是尊重每一个人', '我从来没有偷看过别人的东西', '我做事总是问心无愧']
    
    gen_simple("p53_bidr_im.py",
        "P53: 印象管理量表(BIDR-IM)", "bidr-impression-management", "huaxinyun-bidr-impression-management",
        "印象管理量表(BIDR-IM)",
        "本问卷帮助了解您在回答问题时是否存在刻意美化自己的倾向。共20题，大约需要4分钟完成。",
        items,
        [
            ("印象管理", "impression_management", 1, (1, 20), [
                ("低", "hx_wd_y_1 <= 2.0", "您在回答问题时较为坦诚，不太刻意美化自己。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的印象管理倾向适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您在回答问题时倾向于呈现理想化的自我形象，可能存在美化自己的倾向。"),
            ]),
        ])

# ============================================================
# p54_bidr_sd.py - 10 items, 1 dimension
# ============================================================
def gen_p54():
    items = ['我对自己的判断力很有信心', '我从不后悔自己做过的决定', '我总是能客观地看待自己', '我的第一直觉总是正确的', '我很少对自己的能力产生怀疑', '我对自己的未来充满信心', '我总是能正确地评估形势', '我很少犯判断上的错误', '我的决定总是正确的', '我对自己很满意']
    
    gen_simple("p54_bidr_sd.py",
        "P54: 自我欺骗量表(BIDR-SD)", "bidr-self-deception", "huaxinyun-bidr-self-deception",
        "自我欺骗量表(BIDR-SD)",
        "本问卷帮助了解您是否存在无意识地过高评价自己的倾向。共10题，大约需要2分钟完成。",
        items,
        [
            ("自我欺骗", "self_deception", 1, (1, 10), [
                ("低", "hx_wd_y_1 <= 2.0", "您的自我认知较为客观，较少无意识的正性偏差。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的自我欺骗倾向适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您可能存在无意识地过高评价自己的倾向。"),
            ]),
        ])

# ============================================================
# p55_ss.py - 30 items, 3 dimensions
# ============================================================
def gen_p55():
    items = ['我喜欢极限运动', '我想尝试跳伞', '我喜欢高速驾驶的感觉', '我喜欢攀岩等危险活动', '我愿意尝试任何刺激的活动', '我喜欢冒险', '我想体验自由落体的感觉', '我喜欢不安全但刺激的活动', '我喜欢冲浪或滑雪等极限运动', '我愿意去未知的地方探险', '我做事经常不考虑后果', '我喜欢即兴做事而不是提前计划', '我很容易感到无聊', '我需要不断寻找新的刺激', '我喜欢变化多的生活', '我对重复的事情很快失去兴趣', '我经常会一时冲动做决定', '我喜欢新鲜和刺激的体验', '我很难忍受一成不变的生活', '我经常寻求新的感官刺激', '我会为了获得刺激的体验而提前做计划', '我会主动寻找新的冒险机会', '我会精心策划刺激的旅行', '我会为了寻求刺激而参加各种活动', '我会提前安排刺激的活动', '我会为了体验新事物而制定计划', '我会主动参加有挑战性的活动', '我会为自己安排有趣的冒险', '我会寻找机会来挑战自己', '我会主动寻找刺激的体验机会']
    
    gen_simple("p55_ss.py",
        "P55: 感觉寻求量表(SS)", "sensation-seeking", "huaxinyun-sensation-seeking",
        "感觉寻求量表(SS)",
        "本问卷帮助了解您对新奇刺激体验的追求倾向，包括冒险、冲动和计划性三个维度。共30题，大约需要6分钟完成。",
        items,
        [
            ("危险感觉寻求", "dangerous_ss", 1, (1, 10), [
                ("低", "hx_wd_y_1 <= 2.0", "您较少追求危险刺激的体验。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您对危险刺激的追求适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您喜欢追求危险刺激的体验，愿意冒险。"),
            ]),
            ("冲动感觉寻求", "impulsive_ss", 2, (11, 20), [
                ("低", "hx_wd_y_2 <= 2.0", "您的冲动性感觉寻求较低，偏好稳定。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的冲动性感觉寻求适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您容易感到无聊，需要不断寻求新的刺激。"),
            ]),
            ("计划性感觉寻求", "planned_ss", 3, (21, 30), [
                ("低", "hx_wd_y_3 <= 2.0", "您较少主动规划刺激体验。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您会适度地计划刺激体验。"),
                ("高", "hx_wd_y_3 > 3.5", "您善于主动寻找和规划刺激的体验机会。"),
            ]),
        ])

# ============================================================
# p56_ocdp.py - 10 items, 1 dimension
# ============================================================
def gen_p56():
    items = ['我觉得事情必须做得完美才满意', '我很难容忍自己犯错', '我对自己有非常高的标准', '我会反复检查自己的工作直到满意', '我经常觉得自己做得不够好', '我会花很多时间确保事情做到最好', '我很难接受不完美的结果', '我会因为追求完美而拖延', '我对细节有近乎苛刻的要求', '我经常因为达不到自己的标准而沮丧']
    
    gen_simple("p56_ocdp.py",
        "P56: 完美主义量表(OCD-P)", "ocd-perfectionism", "huaxinyun-ocd-perfectionism",
        "完美主义量表(OCD-P)",
        "本问卷帮助了解您是否存在完美主义倾向或难以控制的反复想法。共10题，大约需要2分钟完成。",
        items,
        [
            ("完美主义", "perfectionism", 1, (1, 10), [
                ("低", "hx_wd_y_1 <= 2.0", "您的完美主义倾向较低，能接受不完美的结果。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的完美主义倾向适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您有较强的完美主义倾向，对自己要求很高，可能因此感到压力。"),
            ]),
        ])

# ============================================================
# p59_hyp.py - 24 items, 2 dimensions
# ============================================================
def gen_p59():
    items = ['我喜欢成为大家关注的中心', '我喜欢在别人面前表现自己', '我常常觉得自己与众不同', '我觉得自己有特殊的才能', '我喜欢让别人印象深刻', '我觉得自己比大多数人更有魅力', '我经常有很多新的想法和计划', '我有时候觉得自己无所不能', '我喜欢冒险和尝试新事物', '我的精力比大多数人更充沛', '我经常感到特别兴奋', '我觉得自己比别人更有创造力', '我的情绪波动很大', '我会突然从开心变得难过', '有时候我会非常兴奋，有时候又会非常低落', '我的心情变化很快', '有时候我会毫无原因地感到特别开心', '我会突然精力旺盛到不需要睡觉', '有时候我说话比平时快很多', '我的想法有时会跳跃得很快', '有时候我会同时做很多事情', '我有时会突然做出冲动的决定', '有时候我会花很多钱买不需要的东西', '我有时会突然想去旅行或做大的改变']
    
    gen_simple("p59_hyp.py",
        "P59: 轻躁狂特质量表(HYP)", "hypomanic-traits", "huaxinyun-hypomanic-traits",
        "轻躁狂特质量表(HYP)",
        "本问卷帮助了解您是否存在情绪高涨、精力旺盛或冲动等方面的特质。共24题，大约需要5分钟完成。",
        items,
        [
            ("表现欲", "exhibitionism", 1, (1, 12), [
                ("低", "hx_wd_y_1 <= 2.0", "您的表现欲较低，偏好低调。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的表现欲适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您有较强的表现欲，喜欢成为关注的中心，可能有夸大的自我评价。"),
            ]),
            ("情绪强度与变化", "mood_intensity", 2, (13, 24), [
                ("低", "hx_wd_y_2 <= 2.0", "您的情绪较为稳定，波动不大。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的情绪波动程度适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您的情绪波动较大，可能出现精力旺盛和冲动行为。"),
            ]),
        ])

# ============================================================
# p60_catpd.py - 33 items, 7 dimensions
# ============================================================
def gen_p60():
    items = ['我善于说服别人做我想要的事', '我知道如何利用别人来达到自己的目的', '我会用奉承来获得好处', '我能轻易地操纵他人的感受', '我擅长假装关心别人', '我对别人的痛苦无动于衷', '我很少感到内疚', '我不太关心他人的感受', '看到别人哭我不会有什么感觉', '我对别人的困难漠不关心', '我容易被激怒并采取行动', '当别人惹我时我会报复', '我有时会用暴力解决问题', '我经常和别人发生冲突', '我会因为小事大发雷霆', '我认为自己比别人优秀', '我觉得自己应该得到特殊待遇', '我相信自己注定会成功', '我觉得自己比大多数人更有能力', '我期待别人崇拜我', '我很难信任别人', '我总觉得别人在背后议论我', '我怀疑别人的动机', '我觉得别人对我有敌意', '我经常觉得别人想害我', '我很难拒绝别人的要求', '我会为了取悦别人而委屈自己', '我害怕得罪别人', '我经常为了维持关系而妥协', '我很难表达不同意见', '我很难从工作中抽身', '我把工作看得比什么都重要', '我即使很累也会继续工作']
    
    gen_simple("p60_catpd.py",
        "P60: 人格障碍筛查量表(CAT-PD-SF)", "catpd-personality-disorder", "huaxinyun-catpd-personality-disorder",
        "人格障碍筛查量表(CAT-PD-SF)",
        "本问卷帮助了解您在人际互动和行为模式方面的特点，用于人格特征的初步筛查。共33题，大约需要6分钟完成。",
        items,
        [
            ("操控性", "manipulativeness", 1, (1, 5), [
                ("低", "hx_wd_y_1 <= 2.0", "您的操控倾向较低，为人坦诚。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的操控倾向适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您可能善于利用和操纵他人来达到自己的目的。"),
            ]),
            ("冷酷无情", "callousness", 2, (6, 10), [
                ("低", "hx_wd_y_2 <= 2.0", "您对他人的感受很敏感，富有同理心。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的共情程度适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您可能对他人的痛苦较为冷漠，缺乏共情。"),
            ]),
            ("敌意攻击", "hostile_aggression", 3, (11, 15), [
                ("低", "hx_wd_y_3 <= 2.0", "您的攻击性较低，善于控制情绪。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您的攻击性适中。"),
                ("高", "hx_wd_y_3 > 3.5", "您可能有较强的攻击性倾向，容易与人发生冲突。"),
            ]),
            ("自大", "grandiosity", 4, (16, 20), [
                ("低", "hx_wd_y_4 <= 2.0", "您的自我评价较为谦虚。"),
                ("中", "hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "您的自大倾向适中。"),
                ("高", "hx_wd_y_4 > 3.5", "您可能有夸大的自我评价和优越感。"),
            ]),
            ("猜疑", "mistrust", 5, (21, 25), [
                ("低", "hx_wd_y_5 <= 2.0", "您对他人的信任度较高。"),
                ("中", "hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "您的猜疑程度适中。"),
                ("高", "hx_wd_y_5 > 3.5", "您可能对他人有较强的不信任感。"),
            ]),
            ("顺从", "submissiveness", 6, (26, 30), [
                ("低", "hx_wd_y_6 <= 2.0", "您较为独立，不太容易屈从他人。"),
                ("中", "hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "您的顺从程度适中。"),
                ("高", "hx_wd_y_6 > 3.5", "您可能过于顺从他人，难以表达自己的需求。"),
            ]),
            ("工作狂", "workaholism", 7, (31, 33), [
                ("低", "hx_wd_y_7 <= 2.0", "您能较好地平衡工作与生活。"),
                ("中", "hx_wd_y_7 > 2.0 && hx_wd_y_7 <= 3.5", "您的工作投入程度适中。"),
                ("高", "hx_wd_y_7 > 3.5", "您可能过度投入工作，需要注意劳逸结合。"),
            ]),
        ])

# ============================================================
# p61_ipc.py - 32 items, 4 dimensions
# ============================================================
def gen_p61():
    items = ['在社交中我会主动发起对话', '我会在团体中承担领导角色', '我善于说服别人', '我在争论中不会退缩', '我会主动表达自己的观点', '我会在别人犹豫时率先行动', '我喜欢掌控局面', '我在团队中经常充当决策者', '我喜欢和很多人在一起', '我在社交场合中充满活力', '我喜欢和别人聊天', '我很容易和别人建立友谊', '我喜欢参加聚会', '我会主动和陌生人打招呼', '我在人群中感到快乐', '我喜欢热闹的社交活动', '我更喜欢独处', '我不太关心社交活动', '我很少主动和别人交往', '我在社交场合中感到不自在', '我更喜欢安静的环境', '我会避免不必要的社交', '我不喜欢成为关注的焦点', '我在人多的场合会感到疲惫', '我在社交中常常感到紧张', '我会担心别人对我的看法', '我在新场合中会感到不安', '我很难自信地表达自己', '我会因为担心被拒绝而避免社交', '我在别人面前常常感到害羞', '我害怕在公众场合发言', '我会因为社交焦虑而回避活动']
    
    gen_simple("p61_ipc.py",
        "P61: 人际环形模型量表(IPC)", "ipc-interpersonal", "huaxinyun-ipc-interpersonal",
        "人际环形模型量表(IPC)",
        "本问卷帮助了解您在人际交往中的风格特点，包括支配性、温暖度等方面。共32题，大约需要6分钟完成。",
        items,
        [
            ("自信支配", "assured_dominant", 1, (1, 8), [
                ("低", "hx_wd_y_1 <= 2.0", "您在社交中较为被动，不太喜欢主导。"),
                ("中", "hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "您的自信支配程度适中。"),
                ("高", "hx_wd_y_1 > 3.5", "您在社交中自信果断，善于领导和说服。"),
            ]),
            ("合群外向", "gregarious_extravert", 2, (9, 16), [
                ("低", "hx_wd_y_2 <= 2.0", "您的社交活跃度较低，偏好独处。"),
                ("中", "hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "您的合群外向程度适中。"),
                ("高", "hx_wd_y_2 > 3.5", "您非常合群外向，喜欢社交活动。"),
            ]),
            ("冷漠内向", "aloof_introvert", 3, (17, 24), [
                ("低", "hx_wd_y_3 <= 2.0", "您对社交的回避程度较低。"),
                ("中", "hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "您的冷漠内向程度适中。"),
                ("高", "hx_wd_y_3 > 3.5", "您较为冷漠内向，偏好独处和安静环境。"),
            ]),
            ("不安顺从", "unassured_submissive", 4, (25, 32), [
                ("低", "hx_wd_y_4 <= 2.0", "您在社交中较为自信，不太容易紧张。"),
                ("中", "hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "您的社交焦虑程度适中。"),
                ("高", "hx_wd_y_4 > 3.5", "您在社交中容易感到紧张和不安，可能会回避社交场合。"),
            ]),
        ])

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("Generating 13 corrected import scripts...")
    gen_p47()
    gen_p48()
    gen_p49()
    gen_p50()
    gen_p51()
    gen_p52()
    gen_p53()
    gen_p54()
    gen_p55()
    gen_p56()
    gen_p59()
    gen_p60()
    gen_p61()
    print("\n✅ All 13 scripts generated successfully!")
