#!/usr/bin/env python3
"""导入 生命意义问卷(MLQ)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '我理解自己生命的意义', False), (2, '我在寻找人生中让自己感到生命有意义的东西', False), (3, '我总是在寻找自己人生的目的', False), (4, '我的生活有明确的目标感', False), (5, '我很清楚什么使我的生命有意义', False), (6, '我在寻找生命的意义', False), (7, '我知道为什么活着', False), (8, '我在寻找让自己生命有意义的东西', False), (9, '我的生活没有明确的目标感', True), (10, '我正在发现自己生命中真正重要的东西', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '存在意义感', 'dimensionCode': 'presence_meaning', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_4 + hx_t_5 + hx_t_7 + hx_t_9', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 3.0', 'conclusionAnalysis': '存在意义感较低', 'suggestion': '您可能还没有找到生活的目的和意义。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 5.0', 'conclusionAnalysis': '存在意义感中等', 'suggestion': '您对自己的人生意义有一定认识。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 5.0', 'conclusionAnalysis': '存在意义感较高', 'suggestion': '您清楚自己的人生目标和意义，这是心理健康的重要保护因素。', 'assessmentWarning': 'none'}]}, {'dimensionName': '寻找意义感', 'dimensionCode': 'search_meaning', 'num': 2, 'evaluateExpression': 'hx_t_2 + hx_t_3 + hx_t_6 + hx_t_8 + hx_t_10', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '寻找意义感较低', 'suggestion': '您较少主动探索生命的意义和目的。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0', 'conclusionAnalysis': '寻找意义感中等', 'suggestion': '您正在积极探索人生的意义。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 5.0', 'conclusionAnalysis': '寻找意义感较高', 'suggestion': '您正在积极寻找生命的意义和目的。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("生命意义问卷(MLQ)", "本问卷帮助了解您对生命意义的感知和探索。共10题，大约需要2分钟完成。", "mlq-meaning-life", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
