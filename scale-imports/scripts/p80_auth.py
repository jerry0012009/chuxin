#!/usr/bin/env python3
"""导入 真实性量表(Authenticity)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '我觉得自己不是真正的自己', True), (2, '我能按照自己的价值观生活', False), (3, '我觉得自己在假装', True), (4, '我觉得自己活得很真实', False), (5, '我觉得别人对我有很大的影响力', True), (6, '我觉得自己做的事情是发自内心的', False), (7, '我很难接受自己的真实感受', True), (8, '我能真实地表达自己的感受', False), (9, '我倾向于改变自己来迎合他人', True), (10, '我按照自己的信念行事', False), (11, '我觉得自己在生活中戴着面具', True), (12, '我觉得自己与真实的自我是一致的', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '自我疏离', 'dimensionCode': 'self_alienation', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_3 + hx_t_7 + hx_t_11', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.5', 'conclusionAnalysis': '自我疏离较低', 'suggestion': '您与真实的自我联系紧密，能认识和接纳自己。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 4.0', 'conclusionAnalysis': '自我疏离中等', 'suggestion': '您有时会感到与真实的自我有所疏离。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_4 > 4.0', 'conclusionAnalysis': '自我疏离较高', 'suggestion': '您可能感到与真实的自我脱节，建议花时间探索自己的内心。', 'assessmentWarning': 'low'}]}, {'dimensionName': '真实生活', 'dimensionCode': 'authentic_living', 'num': 2, 'evaluateExpression': 'hx_t_2 + hx_t_4 + hx_t_6 + hx_t_8 + hx_t_10', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '真实生活较低', 'suggestion': '您可能较少按照自己的真实想法行事。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0', 'conclusionAnalysis': '真实生活中等', 'suggestion': '您能部分按照自己的价值观生活。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 5.0', 'conclusionAnalysis': '真实生活较高', 'suggestion': '您能按照自己的价值观和信念生活，活得真实。', 'assessmentWarning': 'none'}]}, {'dimensionName': '接受外部影响', 'dimensionCode': 'accept_external', 'num': 3, 'evaluateExpression': 'hx_t_5 + hx_t_9', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_3 <= 2.5', 'conclusionAnalysis': '接受外部影响较低', 'suggestion': '您较少受到他人意见的影响，能保持独立。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 2.5 && hx_wd_y_3 <= 4.0', 'conclusionAnalysis': '接受外部影响中等', 'suggestion': '您在保持独立和接受他人影响之间较为平衡。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 4.0', 'conclusionAnalysis': '接受外部影响较高', 'suggestion': '您可能过度受他人影响，建议增强自我意识。', 'assessmentWarning': 'low'}]}]

if __name__ == "__main__":
    scale = build_scale("真实性量表(Authenticity)", "本问卷帮助了解您在生活中展现真实自我的程度。共12题，大约需要3分钟完成。", "authenticity", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
