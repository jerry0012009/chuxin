#!/usr/bin/env python3
"""导入 Tangney自我控制量表简版(SCS)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('不确定', 3), ('同意', 4), ('非常同意', 5)]
OPT_R = [('非常同意', 1), ('同意', 2), ('不确定', 3), ('不同意', 4), ('非常不同意', 5)]
QUESTIONS_RAW = [(1, '我善于抵制诱惑', False), (2, '我很难改掉坏习惯', True), (3, '我会做一些对自己不好但难以停止的事', True), (4, '人们认为我有很强的自制力', False), (5, '我会说一些让自己后悔的话', True), (6, '我会做一些让自己后悔的事', True), (7, '我能有效地朝着长期目标努力', False), (8, '我经常在不该花钱的时候花钱', True), (9, '我会在早上按掉闹钟继续睡', True), (10, '我会在不该吃东西的时候吃东西', True), (11, '我有时会因喝酒或暴食而影响第二天的状态', True), (12, '我做事有条理', False), (13, '我有时会因为拖延而影响任务完成', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '自我控制', 'dimensionCode': 'self_control', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.5', 'conclusionAnalysis': '自我控制较低', 'suggestion': '您可能较难控制冲动行为，容易受诱惑影响。建议建立良好的习惯系统。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 3.5', 'conclusionAnalysis': '自我控制中等', 'suggestion': '您的自我控制能力适中。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 3.5', 'conclusionAnalysis': '自我控制较高', 'suggestion': '您善于控制冲动行为，能有效朝着目标努力。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("Tangney自我控制量表简版(SCS)", "本问卷帮助了解您控制冲动行为和管理自我的能力。共13题，大约需要3分钟完成。", "tscs-self-control", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
