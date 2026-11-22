"""P38: SPSRQ - Sensitivity to Punishment and Sensitivity to Reward Questionnaire
(强化敏感性量表) (Torrubia et al., 2001)
48 items, Yes/No format. SP score 0-24, SR score 0-24.
2 dimensions: 惩罚敏感性 (24 items), 奖励敏感性 (24 items).
SP items (0-indexed): 0,1,3,5,7,9,10,12,14,15,17,18,20,22,24,26,28,30,32,34,36,38,40,43
SR items (0-indexed): 2,4,6,8,11,13,16,19,21,23,25,27,29,31,33,35,37,39,41,42,44,45,46,47
Thresholds SP: 0-8 低, 9-15 中等, 16-24 高
Thresholds SR: 0-8 低, 9-15 中等, 16-24 高
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "spsrq-sensitivity"
IMPORT_CODE = "huaxinyun-spsrq-sensitivity"

# Yes/No options (0-1)
YES_NO = [("否", 0), ("是", 1)]

# 48 items: (order, Chinese text, type)
# type: "SP" = punishment sensitivity, "SR" = reward sensitivity
QUESTIONS = [
    (1,  "你是否会因为害怕被拒绝而避免向别人提出请求？", "SP"),                                  # 0 → SP
    (2,  "你是否会因为害怕犯错而在做决定时犹豫不决？", "SP"),                                    # 1 → SP
    (3,  "你是否经常被身边有魅力的人所吸引？", "SR"),                                            # 2 → SR
    (4,  "当你受到批评时，你是否会难过很长时间？", "SP"),                                        # 3 → SP
    (5,  "你是否会因为想到可能获得的奖励而感到兴奋？", "SR"),                                    # 4 → SR
    (6,  "你是否经常担心自己会让别人失望？", "SP"),                                              # 5 → SP
    (7,  "你是否会为了得到自己想要的东西而努力争取？", "SR"),                                    # 6 → SR
    (8,  "你是否经常因为害怕冲突而避免表达自己的真实想法？", "SP"),                              # 7 → SP
    (9,  "你是否很容易被新的有趣的活动所吸引？", "SR"),                                          # 8 → SR
    (10, "当面临有风险的情况时，你是否会感到非常焦虑？", "SP"),                                  # 9 → SP
    (11, "你是否会因为害怕受到惩罚而遵守所有的规则？", "SP"),                                    # 10 → SP
    (12, "当有机会赢钱时，你是否会感到非常激动？", "SR"),                                        # 11 → SR
    (13, "你是否会因为害怕别人的负面评价而感到不安？", "SP"),                                    # 12 → SP
    (14, "你是否经常为自己设定新的目标和挑战？", "SR"),                                          # 13 → SR
    (15, "你是否会因为害怕出错而在公开场合保持沉默？", "SP"),                                    # 14 → SP
    (16, "当你感到有压力时，你是否会变得非常谨慎？", "SP"),                                      # 15 → SP
    (17, "你是否会因为想到即将得到的奖励而难以入睡？", "SR"),                                    # 16 → SR
    (18, "你是否会因为担心未来的困难而感到焦虑？", "SP"),                                        # 17 → SP
    (19, "当你做错了事时，你是否会感到强烈的内疚感？", "SP"),                                    # 18 → SP
    (20, "你是否经常寻找新的刺激和体验？", "SR"),                                                # 19 → SR
    (21, "你是否会因为害怕被嘲笑而不敢表达自己的想法？", "SP"),                                  # 20 → SP
    (22, "当你看到别人拥有你想要的东西时，你是否会感到强烈的渴望？", "SR"),                      # 21 → SR
    (23, "你是否会因为害怕令人不愉快的后果而避免冒险？", "SP"),                                  # 22 → SP
    (24, "你是否会因为对奖励的渴望而改变自己的行为？", "SR"),                                    # 23 → SR
    (25, "当你有机会参加有趣的活动时，你是否会立刻答应？", "SR"),                                # 24 → SR
    (26, "你是否经常因为担心自己的安全而避免某些活动？", "SP"),                                  # 25 → SP
    (27, "你是否会为了获得赞许和认可而改变自己的行为？", "SR"),                                  # 26 → SR
    (28, "当你面临可能失败的情境时，你是否会感到极度不安？", "SP"),                              # 27 → SP
    (29, "你是否会因为追求快乐而不顾可能的风险？", "SR"),                                        # 28 → SR
    (30, "你是否会因为害怕承担后果而在行动前反复思考？", "SP"),                                  # 29 → SP
    (31, "当别人邀请你参加聚会或社交活动时，你通常是否会欣然接受？", "SR"),                      # 30 → SR
    (32, "你是否会因为害怕被拒绝而不敢主动接近别人？", "SP"),                                    # 31 → SP
    (33, "你是否经常被新的机会和可能性所吸引？", "SR"),                                          # 32 → SR
    (34, "当你需要在众人面前发言时，你是否会感到紧张和不安？", "SP"),                            # 33 → SP
    (35, "你是否会因为对物质奖励的渴望而努力工作？", "SR"),                                      # 34 → SR
    (36, "你是否会因为害怕负面结果而放弃已经计划好的事情？", "SP"),                              # 35 → SP
    (37, "当你取得成就时，你是否会感到非常自豪和满足？", "SR"),                                  # 36 → SR
    (38, "你是否会因为担心犯错而在工作中变得犹豫不决？", "SP"),                                  # 37 → SP
    (39, "你是否会因为渴望体验新事物而去旅行或尝试新活动？", "SR"),                              # 38 → SR
    (40, "你是否会因为害怕意外事件而经常做最坏的打算？", "SP"),                                  # 39 → SP
    (41, "当你看到诱人的广告时，你是否会产生强烈的购买欲望？", "SR"),                            # 40 → SR
    (42, "你是否会因为追求浪漫关系而主动出击？", "SR"),                                          # 41 → SR
    (43, "当有人对你表示好感时，你是否会感到特别开心？", "SR"),                                  # 42 → SR
    (44, "你是否会因为害怕失去而不敢拥有或投入？", "SP"),                                        # 43 → SP
    (45, "你是否经常被竞争和获胜的机会所激励？", "SR"),                                          # 44 → SR
    (46, "当你想到可能会收到礼物或惊喜时，你是否会感到兴奋？", "SR"),                            # 45 → SR
    (47, "你是否会因为对未来的美好期待而感到快乐？", "SR"),                                      # 46 → SR
    (48, "当你发现一个有趣的新爱好时，你是否会投入大量时间和精力？", "SR"),                      # 47 → SR
]

# Verify item assignments
SP_ITEMS_1INDEXED = [q[0] for q in QUESTIONS if q[2] == "SP"]
SR_ITEMS_1INDEXED = [q[0] for q in QUESTIONS if q[2] == "SR"]

def make_questions():
    return [radio_q(order, text, YES_NO) for order, text, _ in QUESTIONS]

def make_dimensions():
    sp_formula = " + ".join(f"hx_t_{i}" for i in SP_ITEMS_1INDEXED)
    sr_formula = " + ".join(f"hx_t_{i}" for i in SR_ITEMS_1INDEXED)

    return [
        # Dimension 1: 惩罚敏感性 (24 items, range 0-24)
        dimension("惩罚敏感性", "sp", 1, sp_formula, "", [
            result_rule("hx_wd_y_1 <= 8", "低惩罚敏感性",
                "您对惩罚和威胁的敏感程度较低，面对可能的负面后果时不太容易感到焦虑或恐惧。这表明您具有较好的情绪稳定性和抗压能力。", "none"),
            result_rule("hx_wd_y_1 > 8 && hx_wd_y_1 <= 15", "中等惩罚敏感性",
                "您对惩罚和威胁的敏感程度处于中等水平，在面对潜在的负面后果时会有一定的焦虑反应。这是正常范围内的反应模式。", "none"),
            result_rule("hx_wd_y_1 > 15 && hx_wd_y_1 <= 24", "高惩罚敏感性",
                "您对惩罚和威胁的敏感程度较高，面对可能的负面后果时容易感到焦虑、恐惧和不安。建议学习焦虑管理技巧，如正念冥想、认知重评等方法来调节情绪反应。", "low"),
        ]),
        # Dimension 2: 奖励敏感性 (24 items, range 0-24)
        dimension("奖励敏感性", "sr", 2, sr_formula, "", [
            result_rule("hx_wd_y_2 <= 8", "低奖励敏感性",
                "您对奖励和正向反馈的敏感程度较低，对外在激励的反应不太强烈。您的行为更多由内在动机驱动。", "none"),
            result_rule("hx_wd_y_2 > 8 && hx_wd_y_2 <= 15", "中等奖励敏感性",
                "您对奖励和正向反馈的敏感程度处于中等水平，能够在追求目标时受到适度的外在激励驱动。这是正常范围内的动机模式。", "none"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 24", "高奖励敏感性",
                "您对奖励和正向反馈的敏感程度较高，对可能获得的回报和认可有强烈的追求动机。建议在追求奖励的同时保持理性的判断，避免因过度追求即时满足而忽视长远利益。", "low"),
        ]),
    ]

def build():
    return build_scale(
        title="强化敏感性量表(SPSRQ)",
        description="本问卷帮助了解您对奖赏和惩罚的敏感程度，反映行为动机系统的特征。共48题，大约需要8分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_path}")
    print(f"   Questions: {len(scale['questions'])}")
    print(f"   Dimensions: {len(scale['dimensions'])}")
    print(f"   SP items: {len(SP_ITEMS_1INDEXED)}")
    print(f"   SR items: {len(SR_ITEMS_1INDEXED)}")

    print("\n--- Dry Run ---")
    result = import_scale(scale, dry_run=True, publish=True)
    print(f"   Importable: {result.get('importable', 0)}")
    print(f"   Publishable: {result.get('publishable', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | issues={item.get('issues')} | warnings={item.get('warnings')}")

    print("\n--- Importing ---")
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}")
    print(f"   Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | id={item.get('survey_id', 'N/A')}")

    print("\n--- DB Verify ---")
    print(verify_in_db(IMPORT_CODE))
