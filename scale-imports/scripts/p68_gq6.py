#!/usr/bin/env python3
"""导入 感恩问卷(GQ-6)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '我的生活中有很多值得感恩的事', False), (2, '如果要列出所有我感恩的事情，这张清单会很长', False), (3, '看到世界上的各种苦难，我并不觉得自己特别幸运', True), (4, '我感恩各种各样的人', False), (5, '随着年龄增长，我越来越能体会到人生中各种人和事对我的帮助', False), (6, '要花很长时间才能让我对某人或某事产生感恩之心', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '感恩', 'dimensionCode': 'gratitude', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 4.0', 'conclusionAnalysis': '感恩倾向较低', 'suggestion': '您在日常生活中较少体验到感恩情绪。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 4.0 && hx_wd_y_1 <= 5.5', 'conclusionAnalysis': '感恩倾向中等', 'suggestion': '您能适度地感受到生活中的美好。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 5.5', 'conclusionAnalysis': '感恩倾向较高', 'suggestion': '您善于发现和感恩生活中的美好事物。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("感恩问卷(GQ-6)", "本问卷帮助了解您在日常生活中体验感恩情绪的倾向。共6题，大约需要1分钟完成。", "gq6-gratitude", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
