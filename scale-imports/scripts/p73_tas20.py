#!/usr/bin/env python3
"""导入 多伦多述情障碍量表(TAS-20)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_N = [('非常不同意', 1), ('不同意', 2), ('不确定', 3), ('同意', 4), ('非常同意', 5)]
OPT_R = [('非常同意', 1), ('同意', 2), ('不确定', 3), ('不同意', 4), ('非常不同意', 5)]
QUESTIONS_RAW = [(1, '我常常搞不清楚自己有什么感受', False), (2, '我常常很难找到合适的词语来描述我的感受', False), (3, '我有一些别人觉得不寻常的身体感觉，医生却说没问题', False), (4, '我很容易描述自己的感受', True), (5, '我更喜欢分析问题而不是简单地描述它们', False), (6, '当我心里难受时，我不知道自己是悲伤、害怕还是愤怒', False), (7, '我常常对身体的感觉感到困惑', False), (8, '我更喜欢让事情顺其自然，而不是去理解为什么会这样', False), (9, '我有一些感受，即使医生也无法解释', False), (10, '能够用语言描述自己的感受对我来说很重要', False), (11, '我很难描述自己对别人有什么感受', False), (12, '人们让我描述我的感受时，我不知道该怎么说', False), (13, '我不知道自己内心正在发生什么', False), (14, '我常常不知道自己为什么会生气', False), (15, '我更喜欢和别人谈日常活动而不是谈感受', False), (16, '我更喜欢看轻松的娱乐节目而不是深入的情感戏剧', False), (17, '即使和很亲近的人在一起，我也很难表达内心的感受', False), (18, '我能在身体感觉到之前就觉察到自己在感受什么', True), (19, '我发现很难向别人表达内心深处的感受', False), (20, '当别人跟我倾诉他们的烦恼时，我感到很困难', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_R if is_rev else OPT_N
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '难以识别感受', 'dimensionCode': 'diff_identify', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_3 + hx_t_6 + hx_t_7 + hx_t_9 + hx_t_13 + hx_t_14', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 2.0', 'conclusionAnalysis': '难以识别感受较低', 'suggestion': '您能较好地识别和区分自己的情绪感受。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0', 'conclusionAnalysis': '难以识别感受中等', 'suggestion': '您在某些情况下可能难以准确识别自己的感受。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 3.0', 'conclusionAnalysis': '难以识别感受较高', 'suggestion': '您可能较难识别和区分自己的情绪感受，建议关注情绪觉察能力的培养。', 'assessmentWarning': 'medium'}]}, {'dimensionName': '难以描述感受', 'dimensionCode': 'diff_describe', 'num': 2, 'evaluateExpression': 'hx_t_2 + hx_t_4 + hx_t_11 + hx_t_12 + hx_t_17 + hx_t_19', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 2.0', 'conclusionAnalysis': '难以描述感受较低', 'suggestion': '您能较好地用语言描述自己的感受。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.0', 'conclusionAnalysis': '难以描述感受中等', 'suggestion': '您在某些情况下可能难以用语言表达感受。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 3.0', 'conclusionAnalysis': '难以描述感受较高', 'suggestion': '您可能较难用语言表达内心感受，建议练习情绪表达。', 'assessmentWarning': 'medium'}]}, {'dimensionName': '外向型思维', 'dimensionCode': 'extern_thinking', 'num': 3, 'evaluateExpression': 'hx_t_5 + hx_t_8 + hx_t_10 + hx_t_15 + hx_t_16 + hx_t_18 + hx_t_20', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_3 <= 2.0', 'conclusionAnalysis': '外向型思维较低', 'suggestion': '您倾向于关注内心感受和体验。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.0', 'conclusionAnalysis': '外向型思维中等', 'suggestion': '您在关注外部事实和内在感受之间较为平衡。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_3 > 3.0', 'conclusionAnalysis': '外向型思维较高', 'suggestion': '您倾向于关注外部事实而非内心感受，可能较少进行内省。', 'assessmentWarning': 'low'}]}]

if __name__ == "__main__":
    scale = build_scale("多伦多述情障碍量表(TAS-20)", "本问卷帮助了解您识别和描述自身感受的能力。共20题，大约需要4分钟完成。", "tas20-alexithymia", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
