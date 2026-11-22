package chuxin.neuropsych;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.common.ApiException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
public class NeuropsychMetricsCalculator {

  private final ObjectMapper objectMapper;

  public NeuropsychMetricsCalculator(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
  }

  public Map<String, Object> calculate(String testCode, Object rawData) {
    List<Map<String, Object>> trials = normalizeTrials(rawData);
    if (trials.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "没有可计算的实验数据");
    }
    String normalizedTestCode = testCode != null && testCode.endsWith("-demo")
        ? testCode.substring(0, testCode.length() - "-demo".length())
        : testCode;
    Map<String, Object> result = switch (normalizedTestCode) {
      case "go-nogo" -> calculateGoNogo(trials);
      case "columbia-card-task-hot" -> calculateColumbiaCardTaskHot(trials);
      case "discount-titrate" -> calculateDiscountTitrate(trials);
      case "stroop" -> calculateStroop(trials);
      case "emotion-regulation" -> calculateEmotionRegulation(trials);
      case "digit-span" -> calculateDigitSpan(trials);
      case "flanker" -> calculateFlanker(trials);
      case "n-back" -> calculateNBack(trials);
      case "stop-signal" -> calculateStopSignal(trials);
      case "simon" -> calculateSimon(trials);
      case "ant" -> calculateAnt(trials);
      case "ax-cpt" -> calculateAxCpt(trials);
      case "simple-reaction-time" -> calculateSimpleReactionTime(trials);
      case "spatial-span" -> calculateSpatialSpan(trials);
      case "tower-of-london" -> calculateTowerOfLondon(trials);
      case "ravens" -> calculateRavens(trials);
      case "number-letter" -> calculateNumberLetter(trials);
      default -> throw new ApiException(HttpStatus.BAD_REQUEST, "不支持的神经心理测评: " + testCode);
    };
    // Extract post-task survey feedback (from survey-text blocks)
    List<Map<String, Object>> feedbackTrials = trials.stream()
        .filter(t -> "post task questions".equals(string(t.get("trial_id")))
            || "post_task".equals(string(t.get("trial_id"))))
        .toList();
    if (!feedbackTrials.isEmpty()) {
      Map<String, Object> feedback = new LinkedHashMap<>();
      for (Map<String, Object> ft : feedbackTrials) {
        String responses = string(ft.get("responses"));
        if (responses != null && !responses.isBlank()) {
          try {
            @SuppressWarnings("unchecked")
            Map<String, Object> parsed = objectMapper.readValue(responses, new TypeReference<Map<String, Object>>() {});
            feedback.putAll(parsed);
          } catch (Exception e) {
            feedback.put("raw", responses);
          }
        }
        Object rt = ft.get("rt");
        if (rt != null) {
          feedback.put("feedbackRt", rt);
        }
      }
      if (!feedback.isEmpty()) {
        result.put("feedback", feedback);
      }
    }
    return result;
  }

  public List<Map<String, Object>> normalizeTrials(Object rawData) {
    Object value = rawData;
    if (value instanceof String json) {
      value = parseJson(json);
    }
    if (value instanceof Map<?, ?> map) {
      for (String key : List.of("trials", "data", "rawData", "raw_data", "rows")) {
        Object nested = map.get(key);
        if (nested != null) {
          return normalizeTrials(nested);
        }
      }
      Object rawJson = map.get("rawJson");
      if (rawJson != null) {
        return normalizeTrials(rawJson);
      }
      return List.of(castMap(map));
    }
    if (value instanceof List<?> list) {
      List<Map<String, Object>> rows = new ArrayList<>();
      for (Object item : list) {
        if (item instanceof Map<?, ?> itemMap) {
          rows.add(castMap(itemMap));
        }
      }
      return rows;
    }
    return List.of();
  }

  private Map<String, Object> calculateGoNogo(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> string(row.get("trial_type")).contains("single-stim"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream().filter(row -> row.containsKey("correct_response")).toList();
    }
    int goCount = 0;
    int goCorrect = 0;
    int goMiss = 0;
    int nogoCount = 0;
    int nogoFalseAlarm = 0;
    List<Double> goRt = new ArrayList<>();
    List<Double> allRt = new ArrayList<>();
    for (Map<String, Object> trial : stim) {
      double correctResponse = number(trial.get("correct_response"), -999);
      double keyPress = number(trial.get("key_press"), -1);
      double rt = number(trial.get("rt"), -1);
      boolean isNoGo = correctResponse == -1 || "nogo".equalsIgnoreCase(string(trial.get("condition")));
      if (isNoGo) {
        nogoCount++;
        if (keyPress != -1) {
          nogoFalseAlarm++;
          if (rt > 0) {
            allRt.add(rt);
          }
        }
      } else {
        goCount++;
        boolean responded = keyPress != -1;
        boolean correct = booleanValue(trial.get("correct"), responded && (correctResponse == -999 || keyPress == correctResponse));
        if (correct) {
          goCorrect++;
          if (rt > 0) {
            goRt.add(rt);
            allRt.add(rt);
          }
        } else if (!responded) {
          goMiss++;
        }
      }
    }
    double hitRate = correctedRate(goCorrect, goCount);
    double falseAlarmRate = correctedRate(nogoFalseAlarm, nogoCount);
    double dPrime = inverseNormal(hitRate) - inverseNormal(falseAlarmRate);
    double criterion = -0.5 * (inverseNormal(hitRate) + inverseNormal(falseAlarmRate));
    double nogoFalseAlarmRate = rate(nogoFalseAlarm, nogoCount);
    double goAccuracy = rate(goCorrect, goCount);
    String warning = nogoFalseAlarmRate >= 0.35 || dPrime < 1 ? "high"
        : nogoFalseAlarmRate >= 0.2 || dPrime < 1.5 ? "middle"
        : nogoFalseAlarmRate >= 0.12 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("goCount", goCount);
    metrics.put("nogoCount", nogoCount);
    metrics.put("goRtMean", round(mean(goRt)));
    metrics.put("goRtSd", round(sd(goRt)));
    metrics.put("responseRtSd", round(sd(allRt)));
    metrics.put("goAccuracy", round(goAccuracy));
    metrics.put("goMissRate", round(rate(goMiss, goCount)));
    metrics.put("nogoFalseAlarmRate", round(nogoFalseAlarmRate));
    metrics.put("dPrime", round(dPrime));
    metrics.put("criterionC", round(criterion));
    metrics.put("completedTrials", stim.size());

    return buildResult(metrics, warning, "反应抑制能力", "NoGo虚报率", percent(nogoFalseAlarmRate), "d'敏感性", format(dPrime));
  }

  private Map<String, Object> calculateColumbiaCardTaskHot(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> row.containsKey("which_round") || row.containsKey("round_points"))
        .toList();
    Map<Integer, List<Map<String, Object>>> byRound = new LinkedHashMap<>();
    for (Map<String, Object> row : stim) {
      int round = intValue(row.get("which_round"), -1);
      if (round > 0) {
        byRound.computeIfAbsent(round, ignored -> new ArrayList<>()).add(row);
      }
    }
    int completedRounds = byRound.size();
    int lossRounds = 0;
    double totalScore = 0;
    double cards = 0;
    double highLossCards = 0;
    int highLossRounds = 0;
    double lowLossCards = 0;
    int lowLossRounds = 0;
    List<Double> rts = new ArrayList<>();
    for (List<Map<String, Object>> rows : byRound.values()) {
      Map<String, Object> last = rows.stream()
          .max(Comparator.comparingDouble(row -> number(row.get("num_click_in_round"), 0)))
          .orElse(rows.getLast());
      double clicks = rows.stream()
          .mapToDouble(row -> number(row.get("num_click_in_round"), 0))
          .max()
          .orElse(rows.size());
      double turned = Math.max(0, clicks - 1);
      cards += turned;
      boolean loss = rows.stream().anyMatch(row -> booleanValue(row.get("clicked_on_loss_card"), false));
      if (loss) {
        lossRounds++;
      }
      totalScore += number(last.get("round_points"), 0);
      double lossAmount = number(last.get("loss_amount"), 0);
      if (lossAmount >= 750) {
        highLossCards += turned;
        highLossRounds++;
      } else if (lossAmount > 0) {
        lowLossCards += turned;
        lowLossRounds++;
      }
      rows.stream().map(row -> number(row.get("rt"), -1)).filter(rt -> rt > 0).forEach(rts::add);
    }
    double avgCards = completedRounds == 0 ? 0 : cards / completedRounds;
    double lossHitRate = rate(lossRounds, completedRounds);
    double riskAdjustment = lowLossRounds == 0 || highLossRounds == 0 ? 0 : (lowLossCards / lowLossRounds) - (highLossCards / highLossRounds);
    String warning = avgCards >= 8 && lossHitRate >= 0.35 ? "high"
        : avgCards >= 5 && lossHitRate >= 0.25 ? "middle"
        : avgCards >= 4 || lossHitRate >= 0.18 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("completedRounds", completedRounds);
    metrics.put("avgCardsPerRound", round(avgCards));
    metrics.put("lossRounds", lossRounds);
    metrics.put("lossHitRate", round(lossHitRate));
    metrics.put("totalScore", round(totalScore));
    metrics.put("decisionRtMean", round(mean(rts)));
    metrics.put("riskAdjustment", round(riskAdjustment));

    return buildResult(metrics, warning, "风险决策", "平均翻牌数", format(avgCards), "损失回合比例", percent(lossHitRate));
  }

  private Map<String, Object> calculateDiscountTitrate(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("choice") || row.containsKey("chosen_amount"))
        .toList();
    int total = 0;
    int immediate = 0;
    int delayed = 0;
    int modelConsistent = 0;
    List<Double> rts = new ArrayList<>();
    List<Map<String, Object>> choices = new ArrayList<>();
    for (Map<String, Object> row : stim) {
      String choice = string(row.get("choice"));
      if (choice.isBlank()) {
        continue;
      }
      total++;
      if ("smaller_sooner".equals(choice)) {
        immediate++;
      } else if ("larger_later".equals(choice)) {
        delayed++;
      }
      double rt = number(row.get("rt"), -1);
      if (rt > 0) {
        rts.add(rt);
      }
      choices.add(row);
    }
    double bestK = estimateDiscountK(choices);
    for (Map<String, Object> row : choices) {
      double small = number(row.get("smaller_amount"), 0);
      double large = number(row.get("larger_amount"), 0);
      double sooner = delayDays(row.get("sooner_delay"));
      double later = delayDays(row.get("later_delay"));
      double smallValue = small / (1 + bestK * sooner);
      double largeValue = large / (1 + bestK * later);
      String predicted = smallValue >= largeValue ? "smaller_sooner" : "larger_later";
      if (predicted.equals(string(row.get("choice")))) {
        modelConsistent++;
      }
    }
    double immediateRate = rate(immediate, total);
    double consistency = rate(modelConsistent, total);
    String warning = immediateRate >= 0.75 && consistency >= 0.55 ? "high"
        : immediateRate >= 0.6 && consistency >= 0.5 ? "middle"
        : immediateRate >= 0.5 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("trialCount", total);
    metrics.put("immediateChoiceRate", round(immediateRate));
    metrics.put("delayedChoiceRate", round(rate(delayed, total)));
    metrics.put("discountK", round(bestK));
    metrics.put("consistency", round(consistency));
    metrics.put("decisionRtMean", round(mean(rts)));
    metrics.put("decisionPattern", immediateRate >= 0.65 ? "冲动型" : immediateRate <= 0.35 ? "耐心型" : consistency < 0.45 ? "低一致性型" : "情境敏感型");

    return buildResult(metrics, warning, "延迟折扣", "即时选择比例", percent(immediateRate), "延迟折扣k值", format(bestK));
  }

  private Map<String, Object> buildResult(
      Map<String, Object> metrics,
      String warning,
      String cardTitle,
      String firstLabel,
      String firstValue,
      String secondLabel,
      String secondValue) {
    boolean valid = number(metrics.getOrDefault("completedTrials", metrics.getOrDefault("trialCount", metrics.getOrDefault("completedRounds", 1))), 1) > 0;
    String summary = switch (warning) {
      case "high" -> "本次结果提示较高风险，建议尽快联系医生进一步评估。";
      case "middle" -> "本次结果提示中等风险，建议结合近期状态和医生建议继续观察。";
      case "low" -> "本次结果提示轻度风险，建议保持规律作息并按需复测。";
      default -> "本次结果未提示明显风险，可作为当前认知表现的参考。";
    };
    Map<String, Object> quality = Map.of(
        "valid", valid,
        "message", valid ? "数据完整" : "有效试次不足，本次结果参考价值有限"
    );
    Map<String, Object> card = new LinkedHashMap<>();
    card.put("title", cardTitle);
    card.put("subtitle", "神经心理测评反馈");
    card.put("level", warning);
    card.put("primaryValue", warningLabel(warning));
    card.put("items", List.of(
        Map.of("label", firstLabel, "value", firstValue, "trend", "reference"),
        Map.of("label", secondLabel, "value", secondValue, "trend", "reference")
    ));
    card.put("conclusion", summary);
    card.put("suggestion", "测评结果不能替代临床诊断。如近期状态波动明显，请联系医生进行综合评估。");

    Map<String, Object> result = new LinkedHashMap<>();
    result.put("metrics", metrics);
    result.put("warningLevel", warning);
    result.put("summary", summary);
    result.put("quality", quality);
    result.put("feedbackCards", List.of(card));
    result.put("sections", List.of(Map.of(
        "title", cardTitle,
        "level", warning,
        "conclusion", summary,
        "suggestion", "建议结合睡眠、情绪、用药和近期压力事件综合判断。"
    )));
    return result;
  }

  private double estimateDiscountK(List<Map<String, Object>> choices) {
    if (choices.isEmpty()) {
      return 0;
    }
    double bestK = 0;
    int bestScore = -1;
    for (double k : discountCandidates()) {
      int score = 0;
      for (Map<String, Object> row : choices) {
        double small = number(row.get("smaller_amount"), 0);
        double large = number(row.get("larger_amount"), 0);
        double sooner = delayDays(row.get("sooner_delay"));
        double later = delayDays(row.get("later_delay"));
        double smallValue = small / (1 + k * sooner);
        double largeValue = large / (1 + k * later);
        String predicted = smallValue >= largeValue ? "smaller_sooner" : "larger_later";
        if (predicted.equals(string(row.get("choice")))) {
          score++;
        }
      }
      if (score > bestScore) {
        bestScore = score;
        bestK = k;
      }
    }
    return bestK;
  }

  private List<Double> discountCandidates() {
    List<Double> values = new ArrayList<>();
    values.add(0D);
    for (double k = 0.0005; k <= 0.2; k *= 1.35) {
      values.add(k);
    }
    return values;
  }

  private double delayDays(Object value) {
    String text = string(value);
    if (text.isBlank() || text.contains("今天") || text.equalsIgnoreCase("today")) {
      return 0;
    }
    if (text.contains("2")) {
      return 14;
    }
    if (text.contains("4")) {
      return 28;
    }
    if (text.contains("6")) {
      return 42;
    }
    return number(value, 0);
  }

  private Map<String, Object> calculateEmotionRegulation(List<Map<String, Object>> trials) {
    List<Map<String, Object>> choices = trials.stream()
        .filter(row -> "choice".equals(string(row.get("trial_id"))))
        .filter(row -> "test".equals(string(row.get("exp_stage"))))
        .toList();
    if (choices.isEmpty()) {
      choices = trials.stream()
          .filter(row -> row.containsKey("chosen_strategy") || row.containsKey("choice_side"))
          .toList();
    }
    int distract = 0;
    int reappraise = 0;
    int high = 0;
    int highReappraise = 0;
    int low = 0;
    int lowReappraise = 0;
    List<Double> rts = new ArrayList<>();
    for (Map<String, Object> trial : choices) {
      String strategy = string(trial.get("chosen_strategy"));
      if ("distract".equals(strategy)) {
        distract++;
      } else if ("reappraise".equals(strategy)) {
        reappraise++;
      }
      String intensity = string(trial.get("intensity"));
      if ("high".equals(intensity)) {
        high++;
        if ("reappraise".equals(strategy)) highReappraise++;
      } else if ("low".equals(intensity)) {
        low++;
        if ("reappraise".equals(strategy)) lowReappraise++;
      }
      double rt = number(trial.get("rt"), -1);
      if (rt > 0) rts.add(rt);
    }
    int total = choices.size();
    double reappraiseRate = rate(reappraise, total);
    double distractRate = rate(distract, total);
    double highReappraiseRate = rate(highReappraise, high);
    double lowReappraiseRate = rate(lowReappraise, low);
    String warning = total == 0 ? "high"
        : reappraiseRate < 0.25 ? "middle"
        : reappraiseRate > 0.85 ? "low" : "none";
    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("trialCount", total);
    metrics.put("reappraiseCount", reappraise);
    metrics.put("distractCount", distract);
    metrics.put("reappraiseRate", round(reappraiseRate));
    metrics.put("distractRate", round(distractRate));
    metrics.put("highReappraiseRate", round(highReappraiseRate));
    metrics.put("lowReappraiseRate", round(lowReappraiseRate));
    metrics.put("choiceRtMean", round(mean(rts)));
    return buildResult(metrics, warning, "情绪调节策略", "重新评价选择率", percent(reappraiseRate), "平均决策时长", round(mean(rts)) + "ms");
  }

  private Map<String, Object> calculateDigitSpan(List<Map<String, Object>> trials) {
    List<Map<String, Object>> responses = trials.stream()
        .filter(row -> "response".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("condition"))
        .toList();
    int forwardTotal = 0;
    int reverseTotal = 0;
    int forwardCorrect = 0;
    int reverseCorrect = 0;
    int forwardMax = 0;
    int reverseMax = 0;
    List<Double> rts = new ArrayList<>();
    for (Map<String, Object> trial : responses) {
      String condition = string(trial.get("condition"));
      boolean correct = booleanValue(trial.get("correct"), false);
      int span = intValue(trial.get("num_digits"), 0);
      if ("forward".equals(condition)) {
        forwardTotal++;
        if (correct) {
          forwardCorrect++;
          forwardMax = Math.max(forwardMax, span);
        }
      } else if ("reverse".equals(condition)) {
        reverseTotal++;
        if (correct) {
          reverseCorrect++;
          reverseMax = Math.max(reverseMax, span);
        }
      }
      double rt = number(trial.get("rt"), -1);
      if (rt > 0) rts.add(rt);
    }
    int total = forwardTotal + reverseTotal;
    int correct = forwardCorrect + reverseCorrect;
    double accuracy = rate(correct, total);
    int totalSpan = forwardMax + reverseMax;
    String warning = total == 0 ? "high"
        : totalSpan <= 6 || accuracy < 0.35 ? "middle"
        : totalSpan <= 8 || accuracy < 0.5 ? "low" : "none";
    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("trialCount", total);
    metrics.put("forwardMaxSpan", forwardMax);
    metrics.put("reverseMaxSpan", reverseMax);
    metrics.put("totalSpan", totalSpan);
    metrics.put("forwardAccuracy", round(rate(forwardCorrect, forwardTotal)));
    metrics.put("reverseAccuracy", round(rate(reverseCorrect, reverseTotal)));
    metrics.put("overallAccuracy", round(accuracy));
    metrics.put("responseRtMean", round(mean(rts)));
    return buildResult(metrics, warning, "工作记忆广度", "总广度", String.valueOf(totalSpan), "总正确率", percent(accuracy));
  }

  private Map<String, Object> calculateFlanker(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> "test".equals(string(row.get("exp_stage"))))
        .filter(row -> row.containsKey("condition"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("condition") && row.containsKey("correct_response"))
          .toList();
    }
    List<Double> compatibleRt = new ArrayList<>();
    List<Double> incompatibleRt = new ArrayList<>();
    int compatibleCorrect = 0;
    int compatibleTotal = 0;
    int incompatibleCorrect = 0;
    int incompatibleTotal = 0;
    for (Map<String, Object> trial : stim) {
      String condition = string(trial.get("condition"));
      double rt = number(trial.get("rt"), -1);
      boolean correct = booleanValue(trial.get("correct"), false);
      if ("compatible".equals(condition)) {
        compatibleTotal++;
        if (correct) {
          compatibleCorrect++;
          if (rt > 0) compatibleRt.add(rt);
        }
      } else if ("incompatible".equals(condition)) {
        incompatibleTotal++;
        if (correct) {
          incompatibleCorrect++;
          if (rt > 0) incompatibleRt.add(rt);
        }
      }
    }
    double compatibleRtMean = mean(compatibleRt);
    double incompatibleRtMean = mean(incompatibleRt);
    double flankerEffect = incompatibleRtMean > 0 && compatibleRtMean > 0 ? incompatibleRtMean - compatibleRtMean : 0;
    double incompatibleAccuracy = rate(incompatibleCorrect, incompatibleTotal);
    double overallAccuracy = rate(compatibleCorrect + incompatibleCorrect, compatibleTotal + incompatibleTotal);
    String warning = flankerEffect > 160 || incompatibleAccuracy < 0.7 ? "high"
        : flankerEffect > 100 || incompatibleAccuracy < 0.8 ? "middle"
        : flankerEffect > 60 ? "low" : "none";
    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("compatibleRtMean", round(compatibleRtMean));
    metrics.put("incompatibleRtMean", round(incompatibleRtMean));
    metrics.put("flankerEffect", round(flankerEffect));
    metrics.put("compatibleAccuracy", round(rate(compatibleCorrect, compatibleTotal)));
    metrics.put("incompatibleAccuracy", round(incompatibleAccuracy));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("compatibleRtSd", round(sd(compatibleRt)));
    metrics.put("incompatibleRtSd", round(sd(incompatibleRt)));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "选择性注意与抑制控制", "Flanker干扰效应", round(flankerEffect) + "ms", "不一致条件正确率", percent(incompatibleAccuracy));
  }

  // ==================== N-Back (工作记忆) ====================
  private Map<String, Object> calculateNBack(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("target"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("correct_response") && row.containsKey("key_press"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
          .toList();
    }
    int hitCount = 0;
    int missCount = 0;
    int falseAlarm = 0;
    int correctReject = 0;
    int targetTotal = 0;
    int nonTargetTotal = 0;
    List<Double> targetRts = new ArrayList<>();
    List<Double> nonTargetRts = new ArrayList<>();
    for (Map<String, Object> trial : stim) {
      double keyPress = number(trial.get("key_press"), -1);
      double rt = number(trial.get("rt"), -1);
      String stimLetter = string(trial.get("stim"));
      String targetLetter = string(trial.get("target"));
      boolean isTarget = stimLetter.equalsIgnoreCase(targetLetter);
      boolean responded = keyPress != -1;
      if (isTarget) {
        targetTotal++;
        if (responded) {
          hitCount++;
          if (rt > 0) targetRts.add(rt);
        } else {
          missCount++;
        }
      } else {
        nonTargetTotal++;
        if (responded) {
          falseAlarm++;
          if (rt > 0) nonTargetRts.add(rt);
        } else {
          correctReject++;
        }
      }
    }
    double hitRate = correctedRate(hitCount, targetTotal);
    double falseAlarmRate = correctedRate(falseAlarm, nonTargetTotal);
    double dPrime = inverseNormal(hitRate) - inverseNormal(falseAlarmRate);
    double overallAccuracy = rate(hitCount + correctReject, targetTotal + nonTargetTotal);
    String warning = dPrime < 0.5 || overallAccuracy < 0.5 ? "high"
        : dPrime < 1.0 || overallAccuracy < 0.65 ? "middle"
        : dPrime < 1.5 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("targetTotal", targetTotal);
    metrics.put("nonTargetTotal", nonTargetTotal);
    metrics.put("hitRate", round(hitRate));
    metrics.put("falseAlarmRate", round(falseAlarmRate));
    metrics.put("dPrime", round(dPrime));
    metrics.put("targetRtMean", round(mean(targetRts)));
    metrics.put("nonTargetRtMean", round(mean(nonTargetRts)));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "工作记忆", "d' 敏感性", format(dPrime), "总正确率", percent(overallAccuracy));
  }

  // ==================== Stop Signal (反应抑制) ====================
  private Map<String, Object> calculateStopSignal(List<Map<String, Object>> trials) {
    // Separate go and stop trials using SS_trial_type field from jsPsych plugin
    List<Map<String, Object>> go = new ArrayList<>();
    List<Map<String, Object>> stop = new ArrayList<>();
    for (Map<String, Object> trial : trials) {
      String expStage = string(trial.get("exp_stage"));
      if ("NoSS_practice".equals(expStage) || "practice".equals(expStage)) continue;
      if ("instruction".equals(string(trial.get("trial_id")))) continue;
      String ssTrialType = string(trial.get("SS_trial_type"));
      if ("stop".equals(ssTrialType)) {
        stop.add(trial);
      } else if ("go".equals(ssTrialType)) {
        go.add(trial);
      }
    }
    int goCorrect = 0;
    int goTotal = 0;
    int goMiss = 0;
    List<Double> goRts = new ArrayList<>();
    for (Map<String, Object> trial : go) {
      double keyPress = number(trial.get("key_press"), -1);
      double rt = number(trial.get("rt"), -1);
      goTotal++;
      if (keyPress == -1) {
        goMiss++;
      } else {
        double correctResp = number(trial.get("correct_response"), -999);
        if (correctResp == -999 || keyPress == correctResp) {
          goCorrect++;
        }
        if (rt > 0) goRts.add(rt);
      }
    }
    int stopTotal = stop.size();
    int stopSuccess = 0;
    List<Double> ssds = new ArrayList<>();
    for (Map<String, Object> trial : stop) {
      double keyPress = number(trial.get("key_press"), -1);
      if (keyPress == -1) stopSuccess++;
      double ssd = number(trial.get("SS_delay"), -1);
      if (ssd > 0) ssds.add(ssd);
    }
    double goRtMean = mean(goRts);
    double goAccuracy = rate(goCorrect, goTotal);
    double stopSuccessRate = rate(stopSuccess, stopTotal);
    // SSRT = mean go RT - mean SSD (simplified integration method)
    double meanSsd = mean(ssds);
    double ssrt = goRts.isEmpty() || ssds.isEmpty() ? 0 : goRtMean - meanSsd;
    String warning = ssrt < 150 || stopSuccessRate > 0.75 ? "none"
        : ssrt < 250 || stopSuccessRate > 0.6 ? "low"
        : ssrt < 350 || stopSuccessRate > 0.4 ? "middle" : "high";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("goTotal", goTotal);
    metrics.put("goCorrect", goCorrect);
    metrics.put("goMiss", goMiss);
    metrics.put("goRtMean", round(goRtMean));
    metrics.put("goAccuracy", round(goAccuracy));
    metrics.put("stopTotal", stopTotal);
    metrics.put("stopSuccess", stopSuccess);
    metrics.put("stopSuccessRate", round(stopSuccessRate));
    metrics.put("meanSsd", round(meanSsd));
    metrics.put("ssrt", round(ssrt));
    return buildResult(metrics, warning, "反应抑制", "SSRT", round(ssrt) + "ms", "停止成功率", percent(stopSuccessRate));
  }
  // ==================== Simon (空间冲突) ====================
  private Map<String, Object> calculateSimon(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> row.containsKey("condition"))
        .filter(row -> row.containsKey("correct_response"))
        .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
        .toList();
    List<Double> congruentRt = new ArrayList<>();
    List<Double> incongruentRt = new ArrayList<>();
    int congruentCorrect = 0;
    int congruentTotal = 0;
    int incongruentCorrect = 0;
    int incongruentTotal = 0;
    for (Map<String, Object> trial : stim) {
      String condition = string(trial.get("condition"));
      double rt = number(trial.get("rt"), -1);
      boolean correct = booleanValue(trial.get("correct"), false);
      if ("congruent".equals(condition)) {
        congruentTotal++;
        if (correct) {
          congruentCorrect++;
          if (rt > 0) congruentRt.add(rt);
        }
      } else if ("incongruent".equals(condition)) {
        incongruentTotal++;
        if (correct) {
          incongruentCorrect++;
          if (rt > 0) incongruentRt.add(rt);
        }
      }
    }
    double congruentRtMean = mean(congruentRt);
    double incongruentRtMean = mean(incongruentRt);
    double simonEffect = incongruentRtMean > 0 && congruentRtMean > 0 ? incongruentRtMean - congruentRtMean : 0;
    double congruentAccuracy = rate(congruentCorrect, congruentTotal);
    double incongruentAccuracy = rate(incongruentCorrect, incongruentTotal);
    double overallAccuracy = rate(congruentCorrect + incongruentCorrect, congruentTotal + incongruentTotal);
    String warning = simonEffect > 100 || incongruentAccuracy < 0.7 ? "high"
        : simonEffect > 60 || incongruentAccuracy < 0.8 ? "middle"
        : simonEffect > 30 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("congruentRtMean", round(congruentRtMean));
    metrics.put("incongruentRtMean", round(incongruentRtMean));
    metrics.put("simonEffect", round(simonEffect));
    metrics.put("congruentAccuracy", round(congruentAccuracy));
    metrics.put("incongruentAccuracy", round(incongruentAccuracy));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("congruentRtSd", round(sd(congruentRt)));
    metrics.put("incongruentRtSd", round(sd(incongruentRt)));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "空间冲突解决", "Simon效应", round(simonEffect) + "ms", "不一致条件正确率", percent(incongruentAccuracy));
  }
  // ==================== ANT (注意力网络测试) ====================
  private Map<String, Object> calculateAnt(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("cue"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("flanker_middle_direction") || row.containsKey("cue"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
          .toList();
    }
    // Classify by cue type and flanker condition
    List<Double> noCueRt = new ArrayList<>();
    List<Double> centerCueRt = new ArrayList<>();
    List<Double> spatialCueRt = new ArrayList<>();
    List<Double> congruentRt = new ArrayList<>();
    List<Double> incongruentRt = new ArrayList<>();
    List<Double> neutralRt = new ArrayList<>();
    int totalCorrect = 0;
    int total = 0;
    for (Map<String, Object> trial : stim) {
      String cue = string(trial.get("cue"));
      double rt = number(trial.get("rt"), -1);
      double keyPress = number(trial.get("key_press"), -1);
      double correctResp = number(trial.get("correct_response"), -999);
      boolean correct = keyPress != -1 && (correctResp == -999 || keyPress == correctResp);
      total++;
      if (correct) {
        totalCorrect++;
        if (rt > 0) {
          // Classify by cue
          if ("nocue".equals(cue)) noCueRt.add(rt);
          else if ("center".equals(cue)) centerCueRt.add(rt);
          else if ("spatial".equals(cue)) spatialCueRt.add(rt);

          // Classify by flanker condition
          String flankerDir = string(trial.get("flanker_middle_direction"));
          String targetDir = string(trial.get("target_direction"));
          if (flankerDir.isEmpty()) flankerDir = string(trial.get("direction"));
          if (targetDir.isEmpty()) targetDir = flankerDir;
          // Use congruency data if available, otherwise infer
          String cond = string(trial.get("flanker_type"));
          if (cond.isEmpty()) cond = string(trial.get("condition"));
          if ("congruent".equals(cond)) {
            congruentRt.add(rt);
          } else if ("incongruent".equals(cond)) {
            incongruentRt.add(rt);
          } else if ("neutral".equals(cond)) {
            neutralRt.add(rt);
          }
        }
      }
    }
    // Compute network effects
    double alertingEffect = mean(noCueRt) > 0 && mean(centerCueRt) > 0 ? mean(noCueRt) - mean(centerCueRt) : 0;
    double orientingEffect = mean(centerCueRt) > 0 && mean(spatialCueRt) > 0 ? mean(centerCueRt) - mean(spatialCueRt) : 0;
    double conflictEffect = mean(incongruentRt) > 0 && mean(congruentRt) > 0 ? mean(incongruentRt) - mean(congruentRt) : 0;
    List<Double> allRt = new ArrayList<>();
    allRt.addAll(noCueRt);
    allRt.addAll(centerCueRt);
    allRt.addAll(spatialCueRt);
    double overallRt = mean(allRt);
    double overallAccuracy = rate(totalCorrect, total);
    String warning = conflictEffect > 200 || overallAccuracy < 0.7 ? "high"
        : conflictEffect > 120 || overallAccuracy < 0.8 ? "middle"
        : conflictEffect > 60 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("alertingEffect", round(alertingEffect));
    metrics.put("orientingEffect", round(orientingEffect));
    metrics.put("conflictEffect", round(conflictEffect));
    metrics.put("noCueRtMean", round(mean(noCueRt)));
    metrics.put("centerCueRtMean", round(mean(centerCueRt)));
    metrics.put("spatialCueRtMean", round(mean(spatialCueRt)));
    metrics.put("congruentRtMean", round(mean(congruentRt)));
    metrics.put("incongruentRtMean", round(mean(incongruentRt)));
    metrics.put("overallRtMean", round(overallRt));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "注意力网络", "冲突效应", round(conflictEffect) + "ms", "总正确率", percent(overallAccuracy));
  }
  // ==================== AX-CPT (持续注意+认知控制) ====================
  private Map<String, Object> calculateAxCpt(List<Map<String, Object>> trials) {
    List<Map<String, Object>> probes = trials.stream()
        .filter(row -> "probe".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("condition"))
        .toList();
    if (probes.isEmpty()) {
      probes = trials.stream()
          .filter(row -> row.containsKey("condition"))
          .filter(row -> row.containsKey("correct_response"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))) && !"end".equals(string(row.get("trial_id"))))
          .toList();
    }
    // Classify by condition (AX, AY, BX, BY)
    int axTotal = 0, axCorrect = 0;
    int ayTotal = 0, ayFalseAlarm = 0;
    int bxTotal = 0, bxFalseAlarm = 0;
    int byTotal = 0, byCorrectReject = 0;
    List<Double> axRts = new ArrayList<>();
    for (Map<String, Object> trial : probes) {
      String condition = string(trial.get("condition"));
      double keyPress = number(trial.get("key_press"), -1);
      double rt = number(trial.get("rt"), -1);
      boolean responded = keyPress != -1;
      boolean correct = booleanValue(trial.get("correct"), false);
      switch (condition) {
        case "AX" -> {
          axTotal++;
          if (correct || (responded && keyPress == 77)) { axCorrect++; if (rt > 0) axRts.add(rt); }
        }
        case "AY" -> { ayTotal++; if (responded && keyPress == 77) ayFalseAlarm++; }
        case "BX" -> { bxTotal++; if (responded && keyPress == 77) bxFalseAlarm++; }
        case "BY" -> { byTotal++; if (!responded || keyPress == 90) byCorrectReject++; }
        default -> {}
      }
    }
    double axHitRate = correctedRate(axCorrect, axTotal);
    double ayFalseAlarmRate = correctedRate(ayFalseAlarm, ayTotal);
    double bxFalseAlarmRate = correctedRate(bxFalseAlarm, bxTotal);
    double byCorrectRejectRate = correctedRate(byCorrectReject, byTotal);
    double dPrimeContext = inverseNormal(axHitRate) - inverseNormal(bxFalseAlarmRate);
    double biasC = -0.5 * (inverseNormal(axHitRate) + inverseNormal(bxFalseAlarmRate));
    // Proactive control index: AX accuracy vs AY false alarm (higher = more proactive)
    double proactiveIndex = axHitRate - ayFalseAlarmRate;
    String warning = dPrimeContext < 1.0 || proactiveIndex < 0 ? "high"
        : dPrimeContext < 1.5 || proactiveIndex < 0.2 ? "middle"
        : dPrimeContext < 2.0 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("axTotal", axTotal);
    metrics.put("axHitRate", round(axHitRate));
    metrics.put("ayFalseAlarmRate", round(ayFalseAlarmRate));
    metrics.put("bxFalseAlarmRate", round(bxFalseAlarmRate));
    metrics.put("byCorrectRejectRate", round(byCorrectRejectRate));
    metrics.put("dPrimeContext", round(dPrimeContext));
    metrics.put("biasC", round(biasC));
    metrics.put("proactiveIndex", round(proactiveIndex));
    metrics.put("axRtMean", round(mean(axRts)));
    metrics.put("completedTrials", probes.size());
    return buildResult(metrics, warning, "持续注意与认知控制", "情境 d'", format(dPrimeContext), "AX正确率", percent(axHitRate));
  }

  // ==================== Simple Reaction Time (处理速度) ====================
  private Map<String, Object> calculateSimpleReactionTime(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("rt") && row.containsKey("key_press"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
          .filter(row -> !"end".equals(string(row.get("trial_id"))))
          .toList();
    }
    int totalTrials = stim.size();
    int responded = 0;
    int missed = 0;
    int falseStarts = 0;
    List<Double> validRts = new ArrayList<>();
    for (Map<String, Object> trial : stim) {
      double rt = number(trial.get("rt"), -1);
      double keyPress = number(trial.get("key_press"), -1);
      if (keyPress == -1 || rt <= 0) {
        missed++;
      } else {
        responded++;
        if (rt < 125) {
          falseStarts++;
        }
        if (rt > 100) {
          validRts.add(rt);
        }
      }
    }
    double medianRt = median(validRts);
    double meanRt = mean(validRts);
    double sdRt = sd(validRts);
    double missedPercent = rate(missed, totalTrials);
    String warning = medianRt > 500 || missedPercent > 0.4 ? "high"
        : medianRt > 400 || missedPercent > 0.25 ? "middle"
        : medianRt > 350 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("totalTrials", totalTrials);
    metrics.put("responded", responded);
    metrics.put("missed", missed);
    metrics.put("missedPercent", round(missedPercent));
    metrics.put("medianRt", round(medianRt));
    metrics.put("meanRt", round(meanRt));
    metrics.put("sdRt", round(sdRt));
    metrics.put("falseStarts", falseStarts);
    metrics.put("validTrialCount", validRts.size());
    return buildResult(metrics, warning, "反应速度", "中位反应时", round(medianRt) + "ms", "漏反应率", percent(missedPercent));
  }

  // ==================== Spatial Span (空间工作记忆) ====================
  private Map<String, Object> calculateSpatialSpan(List<Map<String, Object>> trials) {
    List<Map<String, Object>> responses = trials.stream()
        .filter(row -> "response".equals(string(row.get("trial_id"))))
        .filter(row -> row.containsKey("condition"))
        .toList();
    if (responses.isEmpty()) {
      responses = trials.stream()
          .filter(row -> row.containsKey("num_spaces") && row.containsKey("correct"))
          .toList();
    }
    int forwardCorrect = 0;
    int forwardTotal = 0;
    int reverseCorrect = 0;
    int reverseTotal = 0;
    int forwardMaxSpan = 0;
    int reverseMaxSpan = 0;
    List<Double> rts = new ArrayList<>();
    for (Map<String, Object> trial : responses) {
      String condition = string(trial.get("condition"));
      boolean correct = booleanValue(trial.get("correct"), false);
      int span = intValue(trial.get("num_spaces"), 0);
      double rt = number(trial.get("rt"), -1);
      if (rt > 0) rts.add(rt);
      if ("forward".equals(condition)) {
        forwardTotal++;
        if (correct) {
          forwardCorrect++;
          forwardMaxSpan = Math.max(forwardMaxSpan, span);
        }
      } else if ("reverse".equals(condition)) {
        reverseTotal++;
        if (correct) {
          reverseCorrect++;
          reverseMaxSpan = Math.max(reverseMaxSpan, span);
        }
      }
    }
    int totalSpan = forwardMaxSpan + reverseMaxSpan;
    int total = forwardTotal + reverseTotal;
    int correct = forwardCorrect + reverseCorrect;
    double accuracy = rate(correct, total);
    String warning = total == 0 ? "high"
        : totalSpan <= 6 || accuracy < 0.35 ? "middle"
        : totalSpan <= 8 || accuracy < 0.5 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("trialCount", total);
    metrics.put("forwardMaxSpan", forwardMaxSpan);
    metrics.put("reverseMaxSpan", reverseMaxSpan);
    metrics.put("totalSpan", totalSpan);
    metrics.put("forwardAccuracy", round(rate(forwardCorrect, forwardTotal)));
    metrics.put("reverseAccuracy", round(rate(reverseCorrect, reverseTotal)));
    metrics.put("overallAccuracy", round(accuracy));
    metrics.put("responseRtMean", round(mean(rts)));
    return buildResult(metrics, warning, "空间工作记忆", "总广度", String.valueOf(totalSpan), "总正确率", percent(accuracy));
  }

  // ==================== Tower of London (计划/执行功能) ====================
  private Map<String, Object> calculateTowerOfLondon(List<Map<String, Object>> trials) {
    // Step 1: Build a feedback map (problem_id → correct) from feedback trials
    // This handles the OLD game format where correct is only on feedback trials
    Map<Integer, Boolean> feedbackCorrect = new LinkedHashMap<>();
    Map<Integer, Double> feedbackTime = new LinkedHashMap<>();
    for (Map<String, Object> trial : trials) {
      if ("feedback".equals(string(trial.get("trial_id")))) {
        // feedback trials don't have problem_id, but they have exp_stage = test
        // and they come after the problem trials. We'll use a different approach.
      }
    }

    // Step 2: Collect problem completion events
    // Filter for to_hand trials (the last trial of each problem)
    List<Map<String, Object>> problems = trials.stream()
        .filter(row -> "to_hand".equals(string(row.get("trial_id"))) || "to_board".equals(string(row.get("trial_id"))))
        .filter(row -> !"practice".equals(string(row.get("problem_id"))))
        .toList();
    // Fallback: if primary filter yields nothing, try broader match
    if (problems.isEmpty()) {
      problems = trials.stream()
          .filter(row -> row.containsKey("problem_id") && row.containsKey("correct"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
          .filter(row -> !"end".equals(string(row.get("trial_id"))))
          .filter(row -> !"practice".equals(string(row.get("problem_id"))))
          .toList();
    }

    // Step 3: Build feedback map from feedback trials (for old format)
    // In old format, feedback trials have trial_id="feedback", correct=true/false, exp_stage="test"
    // We need to match them to problem_ids by order
    List<Boolean> feedbackOrder = new ArrayList<>();
    List<Double> feedbackTimeOrder = new ArrayList<>();
    for (Map<String, Object> trial : trials) {
      if ("feedback".equals(string(trial.get("trial_id"))) && "test".equals(string(trial.get("exp_stage")))) {
        feedbackOrder.add(booleanValue(trial.get("correct"), false));
        feedbackTimeOrder.add(number(trial.get("problem_time"), -1));
      }
    }

    // Step 4: Group by problem_id
    Map<Integer, Map<String, Object>> problemData = new LinkedHashMap<>();
    int feedbackIdx = 0;
    for (Map<String, Object> trial : problems) {
      int pid = intValue(trial.get("problem_id"), -1);
      if (pid < 0) continue;
      problemData.computeIfAbsent(pid, k -> new LinkedHashMap<>());
      Map<String, Object> pd = problemData.get(pid);
      int moves = intValue(trial.get("num_moves_made"), 0);
      if (moves > 0) pd.put("num_moves", moves);
      int minMoves = intValue(trial.get("min_moves"), 0);
      if (minMoves > 0) pd.put("min_moves", minMoves);

      // NEW format: correct is directly on the trial
      if (trial.containsKey("correct")) {
        boolean correct = booleanValue(trial.get("correct"), false);
        if (correct) pd.put("correct", true);
      }
      // OLD format: correct is on feedback trials - use problem_id to match
      if (!pd.containsKey("correct") && feedbackOrder.size() > pid) {
        if (feedbackOrder.get(pid)) pd.put("correct", true);
      }

      // timing_exceeded
      if (trial.containsKey("timing_exceeded")) {
        boolean exceeded = booleanValue(trial.get("timing_exceeded"), false);
        if (exceeded) pd.put("exceeded", true);
      }

      double rt = number(trial.get("rt"), -1);
      if (rt > 0) {
        @SuppressWarnings("unchecked")
        List<Double> rts = (List<Double>) pd.computeIfAbsent("rts", k -> new ArrayList<Double>());
        rts.add(rt);
      }
    }
    int totalProblems = problemData.size();
    int solved = 0;
    int timedOut = 0;
    List<Double> efficiencies = new ArrayList<>();
    List<Double> allRts = new ArrayList<>();
    for (Map<String, Object> pd : problemData.values()) {
      boolean correct = booleanValue(pd.get("correct"), false);
      if (correct) solved++;
      boolean exceeded = booleanValue(pd.get("exceeded"), false);
      if (exceeded) timedOut++;
      int moves = intValue(pd.get("num_moves"), 0);
      int minMoves = intValue(pd.get("min_moves"), 0);
      if (minMoves > 0 && moves > 0) {
        efficiencies.add((double) minMoves / moves);
      }
      @SuppressWarnings("unchecked")
      List<Double> rts = (List<Double>) pd.getOrDefault("rts", new ArrayList<Double>());
      allRts.addAll(rts);
    }
    double accuracy = rate(solved, totalProblems);
    double meanEfficiency = mean(efficiencies);
    String warning = accuracy < 0.3 || timedOut >= totalProblems / 2 ? "high"
        : accuracy < 0.5 ? "middle"
        : accuracy < 0.7 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("totalProblems", totalProblems);
    metrics.put("solvedCount", solved);
    metrics.put("timedOut", timedOut);
    metrics.put("accuracy", round(accuracy));
    metrics.put("meanEfficiency", round(meanEfficiency));
    metrics.put("meanRt", round(mean(allRts)));
    return buildResult(metrics, warning, "计划与执行功能", "正确率", percent(accuracy), "平均效率", format(meanEfficiency));
  }

  // ==================== Ravens (流体智力) ====================
  private Map<String, Object> calculateRavens(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> row.containsKey("score_response"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> "stim".equals(string(row.get("trial_id"))) && row.containsKey("correct"))
          .toList();
    }
    int totalItems = stim.size();
    int totalScore = 0;
    List<Double> rts = new ArrayList<>();
    for (Map<String, Object> trial : stim) {
      int score = intValue(trial.get("score_response"), -1);
      if (score < 0) {
        score = booleanValue(trial.get("correct"), false) ? 1 : 0;
      }
      totalScore += score;
      double rt = number(trial.get("rt"), -1);
      if (rt > 0) rts.add(rt);
    }
    double accuracyRate = rate(totalScore, totalItems);
    String warning = totalItems == 0 ? "high"
        : accuracyRate < 0.3 ? "high"
        : accuracyRate < 0.5 ? "middle"
        : accuracyRate < 0.7 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("totalItems", totalItems);
    metrics.put("totalScore", totalScore);
    metrics.put("accuracyRate", round(accuracyRate));
    metrics.put("meanRt", round(mean(rts)));
    metrics.put("sdRt", round(sd(rts)));
    return buildResult(metrics, warning, "流体智力", "总分", totalScore + "/" + totalItems, "正确率", percent(accuracyRate));
  }

  // ==================== Number-Letter (认知灵活性) ====================
  private Map<String, Object> calculateNumberLetter(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> "test".equals(string(row.get("exp_stage"))))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("condition") && row.containsKey("rt"))
          .filter(row -> !"instruction".equals(string(row.get("trial_id"))))
          .filter(row -> !"end".equals(string(row.get("trial_id"))))
          .filter(row -> !"gap".equals(string(row.get("trial_id"))))
          .toList();
    }
    List<Double> repeatRt = new ArrayList<>();
    List<Double> switchRt = new ArrayList<>();
    int repeatCorrect = 0;
    int repeatTotal = 0;
    int switchCorrect = 0;
    int switchTotal = 0;
    List<Double> allRts = new ArrayList<>();
    int totalCorrect = 0;
    int total = 0;
    for (Map<String, Object> trial : stim) {
      String condition = string(trial.get("condition"));
      double rt = number(trial.get("rt"), -1);
      boolean correct = booleanValue(trial.get("correct"), false);
      total++;
      if (correct) totalCorrect++;
      if (rt > 0 && rt < 3000) allRts.add(rt);
      boolean isSwitch = condition.contains("switch") || condition.contains("rotate");
      if (isSwitch) {
        switchTotal++;
        if (correct) switchCorrect++;
        if (rt > 200 && rt < 3000) switchRt.add(rt);
      } else {
        repeatTotal++;
        if (correct) repeatCorrect++;
        if (rt > 200 && rt < 3000) repeatRt.add(rt);
      }
    }
    double repeatRtMean = mean(repeatRt);
    double switchRtMean = mean(switchRt);
    double switchCost = switchRtMean > 0 && repeatRtMean > 0 ? switchRtMean - repeatRtMean : 0;
    double overallAccuracy = rate(totalCorrect, total);
    double switchAccuracy = rate(switchCorrect, switchTotal);
    double repeatAccuracy = rate(repeatCorrect, repeatTotal);
    String warning = switchCost > 200 || overallAccuracy < 0.6 ? "high"
        : switchCost > 100 || overallAccuracy < 0.75 ? "middle"
        : switchCost > 50 ? "low" : "none";

    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("totalTrials", total);
    metrics.put("repeatRtMean", round(repeatRtMean));
    metrics.put("switchRtMean", round(switchRtMean));
    metrics.put("switchCost", round(switchCost));
    metrics.put("repeatAccuracy", round(repeatAccuracy));
    metrics.put("switchAccuracy", round(switchAccuracy));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("overallRtMean", round(mean(allRts)));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "认知灵活性", "切换成本", round(switchCost) + "ms", "总体正确率", percent(overallAccuracy));
  }

  private Object parseJson(String json) {
    try {
      return objectMapper.readValue(json, new TypeReference<Object>() {});
    } catch (JsonProcessingException ex) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "实验数据不是有效 JSON");
    }
  }

  private Map<String, Object> castMap(Map<?, ?> source) {
    Map<String, Object> result = new LinkedHashMap<>();
    source.forEach((key, value) -> result.put(String.valueOf(key), value));
    return result;
  }

  private double correctedRate(int count, int total) {
    if (total <= 0) {
      return 0.5;
    }
    return (count + 0.5) / (total + 1.0);
  }

  private double rate(int count, int total) {
    return total <= 0 ? 0 : (double) count / total;
  }

  private double mean(List<Double> values) {
    return values.isEmpty() ? 0 : values.stream().mapToDouble(Double::doubleValue).average().orElse(0);
  }

  private double sd(List<Double> values) {
    if (values.size() < 2) {
      return 0;
    }
    double mean = mean(values);
    double sum = values.stream().mapToDouble(value -> Math.pow(value - mean, 2)).sum();
    return Math.sqrt(sum / (values.size() - 1));
  }

  private double median(List<Double> values) {
    if (values.isEmpty()) return 0;
    List<Double> sorted = new ArrayList<>(values);
    sorted.sort(Comparator.naturalOrder());
    int n = sorted.size();
    if (n % 2 == 1) return sorted.get(n / 2);
    return (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2.0;
  }

  private double inverseNormal(double p) {
    double clipped = Math.max(0.000001, Math.min(0.999999, p));
    double[] a = {-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.3577518672690, -30.66479806614716, 2.506628277459239};
    double[] b = {-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572};
    double[] c = {-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783};
    double[] d = {0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416};
    double plow = 0.02425;
    double phigh = 1 - plow;
    if (clipped < plow) {
      double q = Math.sqrt(-2 * Math.log(clipped));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
          / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (clipped > phigh) {
      double q = Math.sqrt(-2 * Math.log(1 - clipped));
      return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
          / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    double q = clipped - 0.5;
    double r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }

  private boolean booleanValue(Object value, boolean fallback) {
    if (value instanceof Boolean bool) {
      return bool;
    }
    if (value == null) {
      return fallback;
    }
    if (value instanceof Number num) {
      return num.intValue() != 0;
    }
    String s = String.valueOf(value).trim().toLowerCase();
    if ("1".equals(s) || "yes".equals(s)) return true;
    if ("0".equals(s) || "no".equals(s)) return false;
    return Boolean.parseBoolean(s);
  }

  private int intValue(Object value, int fallback) {
    return (int) Math.round(number(value, fallback));
  }

  private double number(Object value, double fallback) {
    if (value instanceof Number number) {
      return number.doubleValue();
    }
    if (value instanceof String text && !text.isBlank()) {
      try {
        return Double.parseDouble(text);
      } catch (NumberFormatException ignored) {
      }
    }
    return fallback;
  }

  private String string(Object value) {
    return value == null ? "" : String.valueOf(value).trim();
  }

  private double round(double value) {
    if (!Double.isFinite(value)) {
      return 0;
    }
    return BigDecimal.valueOf(value).setScale(4, RoundingMode.HALF_UP).doubleValue();
  }

  private String percent(double value) {
    return BigDecimal.valueOf(value * 100).setScale(1, RoundingMode.HALF_UP) + "%";
  }

  private String format(double value) {
    if (!Double.isFinite(value)) {
      return "0";
    }
    return String.format(Locale.ROOT, "%.3f", value);
  }

  private Map<String, Object> calculateStroop(List<Map<String, Object>> trials) {
    List<Map<String, Object>> stim = trials.stream()
        .filter(row -> "stim".equals(string(row.get("trial_id"))))
        .filter(row -> "test".equals(string(row.get("exp_stage"))))
        .filter(row -> row.containsKey("condition"))
        .toList();
    if (stim.isEmpty()) {
      stim = trials.stream()
          .filter(row -> row.containsKey("condition") && row.containsKey("correct_response"))
          .toList();
    }
    List<Double> congruentRt = new ArrayList<>();
    List<Double> incongruentRt = new ArrayList<>();
    int congruentCorrect = 0;
    int congruentTotal = 0;
    int incongruentCorrect = 0;
    int incongruentTotal = 0;
    for (Map<String, Object> trial : stim) {
      String condition = string(trial.get("condition"));
      double rt = number(trial.get("rt"), -1);
      boolean correct = booleanValue(trial.get("correct"), false);
      if ("congruent".equals(condition)) {
        congruentTotal++;
        if (correct) {
          congruentCorrect++;
          if (rt > 0) congruentRt.add(rt);
        }
      } else if ("incongruent".equals(condition)) {
        incongruentTotal++;
        if (correct) {
          incongruentCorrect++;
          if (rt > 0) incongruentRt.add(rt);
        }
      }
    }
    double congruentRtMean = mean(congruentRt);
    double incongruentRtMean = mean(incongruentRt);
    double stroopEffect = incongruentRtMean > 0 && congruentRtMean > 0 ? incongruentRtMean - congruentRtMean : 0;
    double stroopEffectRatio = congruentRtMean > 0 ? stroopEffect / congruentRtMean : 0;
    double congruentAccuracy = rate(congruentCorrect, congruentTotal);
    double incongruentAccuracy = rate(incongruentCorrect, incongruentTotal);
    double overallAccuracy = rate(congruentCorrect + incongruentCorrect, congruentTotal + incongruentTotal);
    String warning = stroopEffect > 200 || incongruentAccuracy < 0.7 ? "high"
        : stroopEffect > 120 || incongruentAccuracy < 0.8 ? "middle"
        : stroopEffect > 80 ? "low" : "none";
    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("congruentRtMean", round(congruentRtMean));
    metrics.put("incongruentRtMean", round(incongruentRtMean));
    metrics.put("stroopEffect", round(stroopEffect));
    metrics.put("stroopEffectRatio", round(stroopEffectRatio));
    metrics.put("congruentAccuracy", round(congruentAccuracy));
    metrics.put("incongruentAccuracy", round(incongruentAccuracy));
    metrics.put("overallAccuracy", round(overallAccuracy));
    metrics.put("congruentRtSd", round(sd(congruentRt)));
    metrics.put("incongruentRtSd", round(sd(incongruentRt)));
    metrics.put("completedTrials", stim.size());
    return buildResult(metrics, warning, "注意控制能力", "Stroop干扰效应", round(stroopEffect) + "ms", "不一致条件正确率", percent(incongruentAccuracy));
  }

  private String warningLabel(String warning) {
    return switch (Objects.toString(warning, "none")) {
      case "high" -> "高风险";
      case "middle" -> "中风险";
      case "low" -> "轻度风险";
      default -> "正常范围";
    };
  }
}
