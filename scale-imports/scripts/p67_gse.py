#!/usr/bin/env python3
"""导入 一般自我效能量表(GSE)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('完全不正确', 1), ('有点正确', 2), ('多数正确', 3), ('完全正确', 4)]
OPT_R = [('完全不正确', 1), ('有点正确', 2), ('多数正确', 3), ('完全正确', 4)]
QUESTIONS_RAW = [(1, '如果我尽力去做的话，我总是能够解决问题的', False), (2, '即使别人反对我，我仍有办法取得我所要的', False), (3, '对我来说，坚持理想和达成目标是轻而易举的', False), (4, '我自信能有效地应付任何突如其来的事情', False), (5, '以我的才智，我定能应付意料之外的情况', False), (6, '如果我付出必要的努力，我一定能解决大多数的难题', False), (7, '我能冷静地面对困难，因为我信赖自己处理问题的能力', False), (8, '面对一个难题时，我通常能找到几个解决方法', False), (9, '有麻烦的时候，我通常能想到一些应付的方法', False), (10, '无论什么事在我身上发生，我都能够应付自如', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '自我效能', 'dimensionCode': 'self_efficacy', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.0', 'conclusionAnalysis': '自我效能感较低', 'suggestion': '您对自己应对挑战的信心不足。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0', 'conclusionAnalysis': '自我效能感中等', 'suggestion': '您对自己应对挑战的能力有一定信心。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 3.0', 'conclusionAnalysis': '自我效能感较高', 'suggestion': '您对自己应对各种困难充满信心。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("一般自我效能量表(GSE)", "本问卷帮助了解您对自己应对各种困难的信心程度。共10题，大约需要2分钟完成。", "gse-self-efficacy", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
