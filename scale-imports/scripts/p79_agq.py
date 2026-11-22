#!/usr/bin/env python3
"""导入 成就目标问卷(AGQ)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '对我来说，尽可能掌握学习内容很重要', False), (2, '我担心自己可能无法像其他人一样学得好', False), (3, '我想要比班上其他同学学得更好', False), (4, '我担心自己可能无法完全理解学习材料', False), (5, '对我来说，尽可能深入理解学习材料很重要', False), (6, '我的目标是比大多数同学表现得更好', False), (7, '我希望彻底掌握课堂上的知识', False), (8, '我有时担心自己在课堂上表现不够好', False), (9, '我的目标是比其他同学表现更好', False), (10, '我希望尽可能掌握尽可能多的知识', False), (11, '我担心自己可能无法达到对自己设定的标准', False), (12, '对我来说，比其他同学表现更好很重要', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '掌握趋近', 'dimensionCode': 'mastery_approach', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_5 + hx_t_7', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 3.5', 'conclusionAnalysis': '掌握趋近目标较低', 'suggestion': '您对深入理解和掌握知识的追求较低。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 3.5 && hx_wd_y_1 <= 5.5', 'conclusionAnalysis': '掌握趋近目标中等', 'suggestion': '您有一定的掌握知识的内在追求。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 5.5', 'conclusionAnalysis': '掌握趋近目标较高', 'suggestion': '您强烈追求深入理解和掌握知识，这是最健康的学习目标。', 'assessmentWarning': 'none'}]}, {'dimensionName': '掌握回避', 'dimensionCode': 'mastery_avoid', 'num': 2, 'evaluateExpression': 'hx_t_4 + hx_t_8 + hx_t_11', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '掌握回避目标较低', 'suggestion': '您较少担心自己无法理解学习内容。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0', 'conclusionAnalysis': '掌握回避目标中等', 'suggestion': '您有时会担心自己的理解不够深入。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 5.0', 'conclusionAnalysis': '掌握回避目标较高', 'suggestion': '您过度担心自己无法完全理解，可能带来不必要的压力。', 'assessmentWarning': 'low'}]}, {'dimensionName': '成绩趋近', 'dimensionCode': 'performance_approach', 'num': 3, 'evaluateExpression': 'hx_t_3 + hx_t_6 + hx_t_9', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_3 <= 3.0', 'conclusionAnalysis': '成绩趋近目标较低', 'suggestion': '您不太追求在成绩上超越他人。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 3.0 && hx_wd_y_3 <= 5.0', 'conclusionAnalysis': '成绩趋近目标中等', 'suggestion': '您有一定的竞争意识。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 5.0', 'conclusionAnalysis': '成绩趋近目标较高', 'suggestion': '您强烈追求在竞争中胜出，适度竞争有益但过度可能带来压力。', 'assessmentWarning': 'low'}]}, {'dimensionName': '成绩回避', 'dimensionCode': 'performance_avoid', 'num': 4, 'evaluateExpression': 'hx_t_2 + hx_t_4 + hx_t_12', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_4 <= 3.0', 'conclusionAnalysis': '成绩回避目标较低', 'suggestion': '您较少担心自己在他人面前表现不佳。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_4 > 3.0 && hx_wd_y_4 <= 5.0', 'conclusionAnalysis': '成绩回避目标中等', 'suggestion': '您有时会担心自己在他人眼中表现不好。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_4 > 5.0', 'conclusionAnalysis': '成绩回避目标较高', 'suggestion': '您过度担心在他人面前表现不佳，建议关注学习过程本身。', 'assessmentWarning': 'low'}]}]

if __name__ == "__main__":
    scale = build_scale("成就目标问卷(AGQ)", "本问卷帮助了解您在学习中的四种目标导向。共12题，大约需要3分钟完成。", "agq-achievement-goals", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
