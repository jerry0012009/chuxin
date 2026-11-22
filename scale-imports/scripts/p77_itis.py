#!/usr/bin/env python3
"""导入 成长心态量表(ITIS)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('有点同意', 4), ('同意', 5), ('非常同意', 6)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('有点不同意', 4), ('不同意', 5), ('非常不同意', 6)]
QUESTIONS_RAW = [(1, '你的智力是固定的，你无法真正改变它', True), (2, '你总是可以大幅改变你的智力水平', False), (3, '无论你付出多少努力，你的智力都无法真正改变', True), (4, '你可以学习新事物，但无法真正改变你的基本智力', True), (5, '通过努力，你总是可以变得更聪明', False), (6, '你的智力水平是固定的，无法通过努力改变', True), (7, '通过持续学习，你可以提高自己的智力', False), (8, '你无法真正改变你的智力，因为它是天生的', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '成长心态', 'dimensionCode': 'growth_mindset', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.5', 'conclusionAnalysis': '固定心态倾向', 'suggestion': '您倾向于认为智力是固定的，建议培养成长心态，相信努力可以带来改变。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 4.0', 'conclusionAnalysis': '心态较为平衡', 'suggestion': '您对智力的可塑性持开放态度。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 4.0', 'conclusionAnalysis': '成长心态较强', 'suggestion': '您相信通过努力和学习可以提升能力，这是积极的学习态度。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("成长心态量表(ITIS)", "本问卷帮助了解您对智力可塑性的信念。共8题，大约需要2分钟完成。", "itis-growth-mindset", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
