#!/usr/bin/env python3
"""导入 LSAS 社交焦虑量表"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

OPT_FEAR = [('无', 0), ('轻度', 1), ('中度', 2), ('重度', 3)]
OPT_AVOID = [('从不', 0), ('偶尔', 1), ('经常', 2), ('通常', 3)]

QUESTIONS_RAW = [(1, '恐惧程度：在公众面前打电话', False), (2, '恐惧程度：参加小组活动', False), (3, '恐惧程度：在公众场合吃东西', False), (4, '恐惧程度：在公众场合喝东西', False), (5, '恐惧程度：与权威人物交谈', False), (6, '恐惧程度：在观众面前表演或演讲', False), (7, '恐惧程度：参加聚会', False), (8, '恐惧程度：在他人注视下工作', False), (9, '恐惧程度：当别人看着你时写东西', False), (10, '恐惧程度：在不太熟悉的人面前打电话', False), (11, '恐惧程度：与不太熟悉的人交谈', False), (12, '恐惧程度：与陌生人见面', False), (13, '恐惧程度：使用公共洗手间', False), (14, '恐惧程度：进入已有人就座的房间', False), (15, '恐惧程度：成为关注的中心', False), (16, '恐惧程度：在会议上发言', False), (17, '恐惧程度：参加考试', False), (18, '恐惧程度：对不太熟悉的人表达不同意见', False), (19, '恐惧程度：与不太熟悉的人眼神接触', False), (20, '恐惧程度：在小组面前做报告', False), (21, '恐惧程度：试图与某人搭讪', False), (22, '恐惧程度：参加大型聚会或社交活动', False), (23, '恐惧程度：在不太熟悉的人面前做某事', False), (24, '恐惧程度：在别人面前排队', False), (25, '回避程度：在公众面前打电话', False), (26, '回避程度：参加小组活动', False), (27, '回避程度：在公众场合吃东西', False), (28, '回避程度：在公众场合喝东西', False), (29, '回避程度：与权威人物交谈', False), (30, '回避程度：在观众面前表演或演讲', False), (31, '回避程度：参加聚会', False), (32, '回避程度：在他人注视下工作', False), (33, '回避程度：当别人看着你时写东西', False), (34, '回避程度：在不太熟悉的人面前打电话', False), (35, '回避程度：与不太熟悉的人交谈', False), (36, '回避程度：与陌生人见面', False), (37, '回避程度：使用公共洗手间', False), (38, '回避程度：进入已有人就座的房间', False), (39, '回避程度：成为关注的中心', False), (40, '回避程度：在会议上发言', False), (41, '回避程度：参加考试', False), (42, '回避程度：对不太熟悉的人表达不同意见', False), (43, '回避程度：与不太熟悉的人眼神接触', False), (44, '回避程度：在小组面前做报告', False), (45, '回避程度：试图与某人搭讪', False), (46, '回避程度：参加大型聚会或社交活动', False), (47, '回避程度：在不太熟悉的人面前做某事', False), (48, '回避程度：在别人面前排队', False)]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_AVOID if order > 24 else OPT_FEAR
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    return [{'dimensionName': '恐惧', 'dimensionCode': 'fear', 'num': 1, 'evaluateExpression': 'hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20 + hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_1 <= 20.0', 'conclusionAnalysis': '恐惧水平正常', 'suggestion': '您在社交场合的恐惧程度在正常范围内。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_1 > 20.0 && hx_wd_y_1 <= 40.0', 'conclusionAnalysis': '恐惧水平轻度', 'suggestion': '您在部分社交场合会感到轻度恐惧。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_1 > 40.0 && hx_wd_y_1 <= 60.0', 'conclusionAnalysis': '恐惧水平中度', 'suggestion': '您在多数社交场合会感到明显恐惧，建议关注。', 'assessmentWarning': 'medium'}, {'evaluateExpression': 'hx_wd_y_1 > 60.0', 'conclusionAnalysis': '恐惧水平较高', 'suggestion': '您在社交场合有强烈的恐惧，建议寻求专业帮助。', 'assessmentWarning': 'high'}]}, {'dimensionName': '回避', 'dimensionCode': 'avoidance', 'num': 2, 'evaluateExpression': 'hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30 + hx_t_31 + hx_t_32 + hx_t_33 + hx_t_34 + hx_t_35 + hx_t_36 + hx_t_37 + hx_t_38 + hx_t_39 + hx_t_40 + hx_t_41 + hx_t_42 + hx_t_43 + hx_t_44 + hx_t_45 + hx_t_46 + hx_t_47 + hx_t_48', 'standardScoreFormula': '', 'results': [{'evaluateExpression': 'hx_wd_y_2 <= 20.0', 'conclusionAnalysis': '回避水平正常', 'suggestion': '您较少回避社交场合。', 'assessmentWarning': 'none'}, {'evaluateExpression': 'hx_wd_y_2 > 20.0 && hx_wd_y_2 <= 40.0', 'conclusionAnalysis': '回避水平轻度', 'suggestion': '您偶尔会回避某些社交场合。', 'assessmentWarning': 'low'}, {'evaluateExpression': 'hx_wd_y_2 > 40.0 && hx_wd_y_2 <= 60.0', 'conclusionAnalysis': '回避水平中度', 'suggestion': '您经常回避社交场合，可能影响日常生活。', 'assessmentWarning': 'medium'}, {'evaluateExpression': 'hx_wd_y_2 > 60.0', 'conclusionAnalysis': '回避水平较高', 'suggestion': '您严重回避社交场合，建议寻求专业帮助。', 'assessmentWarning': 'high'}]}]

if __name__ == "__main__":
    scale = build_scale("Liebowitz社交焦虑量表(LSAS)", "本问卷帮助了解您在各种社交场合中的恐惧和回避程度。共48题（24个场景×2），大约需要8分钟完成。",
        "lsas-social-anxiety", make_questions(), make_dimensions())
    result = import_scale(scale, overwrite=True)
    print(result)
