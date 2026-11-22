#!/usr/bin/env python3
"""导入 De Jong Gierveld孤独量表"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('否', 1), ('不确定', 2), ('是', 3)]
OPT_R = [('是', 1), ('不确定', 2), ('否', 3)]
QUESTIONS_RAW = [(1, '我感到自己身边有很多人可以依靠', False), (2, '我感到自己有很多亲近的人', False), (3, '我感到自己与周围的人完全失去联系', True), (4, '我经常感到被抛弃', True), (5, '我有很多人可以完全信任', False), (6, '我经常感到非常孤独', True), (7, '我经常体验到被排斥的感觉', True), (8, '我身边有足够多的人可以求助', False), (9, '我身边缺少陪伴', True), (10, '我能得到足够的爱和感情', False), (11, '我经常感到与他人的关系不够亲密', True)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '情感孤独', 'dimensionCode': 'emotional_loneliness', 'num': 1, 'evaluateExpression': 'hx_t_2 + hx_t_4 + hx_t_7 + hx_t_9 + hx_t_10', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 1.5', 'conclusionAnalysis': '情感孤独较低', 'suggestion': '您在情感上有充足的亲密关系支持。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 1.5 && hx_wd_y_1 <= 2.2', 'conclusionAnalysis': '情感孤独中等', 'suggestion': '您有时会感到情感上的空虚。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 2.2', 'conclusionAnalysis': '情感孤独较高', 'suggestion': '您可能缺乏亲密的情感关系，建议主动建立深层人际联系。', 'assessmentWarning': 'medium'}]}, {'dimensionName': '社交孤独', 'dimensionCode': 'social_loneliness', 'num': 2, 'evaluateExpression': 'hx_t_1 + hx_t_3 + hx_t_5 + hx_t_6 + hx_t_8 + hx_t_11', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 1.5', 'conclusionAnalysis': '社交孤独较低', 'suggestion': '您拥有充足的社交网络和朋友关系。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 1.5 && hx_wd_y_2 <= 2.2', 'conclusionAnalysis': '社交孤独中等', 'suggestion': '您有时会感到社交网络不够充实。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 2.2', 'conclusionAnalysis': '社交孤独较高', 'suggestion': '您可能缺乏足够的社交联系，建议扩大社交圈。', 'assessmentWarning': 'medium'}]}]

if __name__ == "__main__":
    scale = build_scale("De Jong Gierveld孤独量表", "本问卷帮助了解您在情感和社交两个维度上的孤独体验。共11题，大约需要2分钟完成。", "djgls-loneliness", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
