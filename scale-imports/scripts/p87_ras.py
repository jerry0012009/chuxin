#!/usr/bin/env python3
"""导入 Rathus自信量表(RAS)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('不确定', 3), ('同意', 4), ('非常同意', 5)]
OPT_R = [('非常同意', 1), ('同意', 2), ('不确定', 3), ('不同意', 4), ('非常不同意', 5)]
QUESTIONS_RAW = [(1, '当我觉得自己是对的的时候，我会表达自己的看法', False), (2, '当别人插队时，我会让他知道', False), (3, '我很难拒绝推销员', True), (4, '当我不理解某人的行为时，我会直接问', False), (5, '我总是为自己的权利辩护', False), (6, '在聚会中我会主动和陌生人攀谈', False), (7, '当别人占用我的时间时，我会让他知道', False), (8, '我很难拒绝朋友的请求', True), (9, '我不太愿意和权威人士争论', True), (10, '我会主动向别人介绍自己', False), (11, '当我觉得受到不公平对待时，我会说出来', False), (12, '我在社交场合中比较被动', True), (13, '我会表达自己的不同意见', False), (14, '当别人对我提出不合理要求时，我会拒绝', False), (15, '我很难在课堂上主动发言', True), (16, '我会主动邀请别人一起做事', False), (17, '我会为自己争取应得的利益', False), (18, '我倾向于避免与人发生冲突', True), (19, '当别人的行为让我不舒服时，我会告诉他', False), (20, '我在新环境中会主动社交', False), (21, "我很难对别人说'不'", True), (22, '我会在团队中表达自己的想法', False), (23, '我会主动和老师或领导交流', False), (24, '当受到批评时，我会为自己辩护', False), (25, '我不太愿意在公众场合发言', True), (26, '我会主动帮助陌生人', False), (27, '当别人误解我时，我会解释清楚', False), (28, '我会拒绝我不想做的事情', False), (29, '我会主动参加社交活动', False), (30, '当我有不同意见时，我会保持沉默', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '自信', 'dimensionCode': 'assertiveness', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20 + hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24 + hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.5', 'conclusionAnalysis': '自信水平较低', 'suggestion': '您在人际交往中可能较为被动，不太敢于表达自己的需求和意见。建议从小的场景开始练习自信表达。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 3.5', 'conclusionAnalysis': '自信水平中等', 'suggestion': '您能在多数情况下适度表达自己。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 3.5', 'conclusionAnalysis': '自信水平较高', 'suggestion': '您善于在人际交往中自信地表达自己的需求和意见。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("Rathus自信量表(RAS)", "本问卷帮助了解您在人际交往中的自信程度。共30题，大约需要5分钟完成。", "ras-assertiveness", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
