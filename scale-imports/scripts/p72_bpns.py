#!/usr/bin/env python3
"""导入 基本心理需求量表(BPNS)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '我觉得我做的很多事情都是我不得不做的', True), (2, '在日常生活中，我经常不得不做别人要求我做的事', True), (3, '我和身边的人相处融洽', False), (4, '我对自己所做的事情感到很能干', False), (5, '在和他人交往时，我感到很自在', False), (6, '我觉得我可以真实地做自己', False), (7, '我经常感到被排斥或孤立', True), (8, '我对自己完成日常任务的能力很有信心', False), (9, '我在生活中有一些真正关心我的人', False), (10, '我感到有压力要去做别人期望的事', True), (11, '我对自己处理问题的能力感到满意', False), (12, '我与生活中重要的人关系亲密', False), (13, '我感到生活中充满了有趣的事情', False), (14, '我感到有压力去做很多事情', True), (15, '我在大多数时间里感到自己有能力', False), (16, '我觉得我能自由地选择如何过自己的生活', False), (17, '我在生活中感到被孤立', True), (18, '我觉得我在做事情时游刃有余', False), (19, '我经常感到被迫做自己不想做的事', True), (20, '我的日常活动让我感到被理解和接纳', False), (21, '我能按照自己的意愿去做事', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '自主需求', 'dimensionCode': 'autonomy', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_6 + hx_t_10 + hx_t_14 + hx_t_16 + hx_t_19', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 3.0', 'conclusionAnalysis': '自主需求满足较低', 'suggestion': '您在日常生活中较少感受到自主和自由选择的空间。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 5.0', 'conclusionAnalysis': '自主需求满足中等', 'suggestion': '您在日常生活中有一定的自主空间。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 5.0', 'conclusionAnalysis': '自主需求满足较高', 'suggestion': '您在日常生活中能自由地按照自己的意愿行事。', 'assessmentWarning': 'none'}]}, {'dimensionName': '能力需求', 'dimensionCode': 'competence', 'num': 2, 'evaluateExpression': 'hx_t_4 + hx_t_8 + hx_t_11 + hx_t_13 + hx_t_15 + hx_t_18', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '能力需求满足较低', 'suggestion': '您较少感到自己在日常活动中是有能力的。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0', 'conclusionAnalysis': '能力需求满足中等', 'suggestion': '您对自己的能力有适度的信心。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 5.0', 'conclusionAnalysis': '能力需求满足较高', 'suggestion': '您在日常生活中感到自己能胜任各种任务。', 'assessmentWarning': 'none'}]}, {'dimensionName': '关系需求', 'dimensionCode': 'relatedness', 'num': 3, 'evaluateExpression': 'hx_t_3 + hx_t_5 + hx_t_7 + hx_t_9 + hx_t_12 + hx_t_17 + hx_t_20', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_3 <= 3.0', 'conclusionAnalysis': '关系需求满足较低', 'suggestion': '您较少感受到与他人的亲密联系和归属感。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_3 > 3.0 && hx_wd_y_3 <= 5.0', 'conclusionAnalysis': '关系需求满足中等', 'suggestion': '您与他人有适度的亲密联系。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 5.0', 'conclusionAnalysis': '关系需求满足较高', 'suggestion': '您与生活中重要的人有亲密和温暖的关系。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("基本心理需求量表(BPNS)", "本问卷帮助了解您在自主、能力和关系三个基本心理需求方面的满足程度。共21题，大约需要4分钟完成。", "bpns-basic-needs", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
