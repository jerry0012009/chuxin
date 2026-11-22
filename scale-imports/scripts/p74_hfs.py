#!/usr/bin/env python3
"""导入 宽恕量表(HFS)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('有点不同意', 3), ('不确定', 4), ('有点同意', 5), ('同意', 6), ('非常同意', 7)]
OPT_R = [('非常同意', 1), ('同意', 2), ('有点同意', 3), ('不确定', 4), ('有点不同意', 5), ('不同意', 6), ('非常不同意', 7)]
QUESTIONS_RAW = [(1, '尽管我不情愿，但我仍然会发现自己会从另一个角度来看待那些伤害过我的事情', False), (2, '我很难控制自己的愤怒', True), (3, '尽管有些事情让我很受伤，但随着时间推移我能够释怀', False), (4, '当别人不公平对待我时，我会在很长时间里怀恨在心', True), (5, '当我为自己的过错感到自责时，我会努力去理解和接受自己', False), (6, '随着时间推移，我对曾经伤害我的人会变得越来越冷漠', True), (7, '即使在最糟糕的情况下，我也能从困境中找到积极的意义', False), (8, '我很难停止对发生在我身上的不幸感到不满', True), (9, '我接受自己的不完美和失败', False), (10, '我会因为别人对我不公平而很难原谅他们', True), (11, '当坏事发生在我身上时，我会把它们看作学习和成长的机会', False), (12, '我会因为自己犯的错误而持续自责', True), (13, '我能原谅那些曾经伤害过我的人', False), (14, '我会因为生活中发生过的事情而长期感到痛苦', True), (15, '我对自己比较宽容', False), (16, '我会让曾经的错误阻碍我前进', True), (17, '即使情况很困难，我也能接受它们', False), (18, '我很难不去想别人对我的伤害', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '宽恕自我', 'dimensionCode': 'forgive_self', 'num': 1, 'evaluateExpression': 'hx_t_5 + hx_t_9 + hx_t_12 + hx_t_15 + hx_t_16', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 3.0', 'conclusionAnalysis': '自我宽恕较低', 'suggestion': '您可能对自己的过错和不完美较难释怀，倾向于持续自责。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 5.0', 'conclusionAnalysis': '自我宽恕中等', 'suggestion': '您能适度地接受自己的不完美。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 5.0', 'conclusionAnalysis': '自我宽恕较高', 'suggestion': '您善于宽容地对待自己的过错和不完美。', 'assessmentWarning': 'none'}]}, {'dimensionName': '宽恕他人', 'dimensionCode': 'forgive_others', 'num': 2, 'evaluateExpression': 'hx_t_4 + hx_t_6 + hx_t_10 + hx_t_13 + hx_t_18', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '宽恕他人较低', 'suggestion': '您可能较难原谅他人的过错，容易怀恨在心。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0', 'conclusionAnalysis': '宽恕他人中等', 'suggestion': '您能适度地原谅他人的过错。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 5.0', 'conclusionAnalysis': '宽恕他人较高', 'suggestion': '您善于原谅他人的过错，不记仇。', 'assessmentWarning': 'none'}]}, {'dimensionName': '宽恕情境', 'dimensionCode': 'forgive_situations', 'num': 3, 'evaluateExpression': 'hx_t_1 + hx_t_3 + hx_t_7 + hx_t_8 + hx_t_11 + hx_t_14 + hx_t_17', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_3 <= 3.0', 'conclusionAnalysis': '情境宽恕较低', 'suggestion': '您可能较难接受生活中的不幸和困难。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_3 > 3.0 && hx_wd_y_3 <= 5.0', 'conclusionAnalysis': '情境宽恕中等', 'suggestion': '您能适度地接受生活中的困难处境。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 5.0', 'conclusionAnalysis': '情境宽恕较高', 'suggestion': '您善于从困境中找到积极意义，能接受无法改变的事情。', 'assessmentWarning': 'none'}]}]

if __name__ == "__main__":
    scale = build_scale("宽恕量表(HFS)", "本问卷帮助了解您对自己、他人和生活情境的宽恕态度。共18题，大约需要4分钟完成。", "hfs-forgiveness", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
