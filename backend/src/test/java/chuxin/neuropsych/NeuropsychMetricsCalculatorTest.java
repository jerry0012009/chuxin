package chuxin.neuropsych;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class NeuropsychMetricsCalculatorTest {

  private final NeuropsychMetricsCalculator calculator = new NeuropsychMetricsCalculator(new ObjectMapper());

  @Test
  void calculatesGoNogoSignalDetectionMetrics() {
    List<Map<String, Object>> trials = new ArrayList<>();
    for (int i = 0; i < 20; i++) {
      trials.add(Map.of(
          "trial_id", "stim",
          "trial_type", "poldrack-single-stim",
          "correct_response", 32,
          "key_press", 32,
          "rt", 420,
          "correct", true
      ));
    }
    for (int i = 0; i < 10; i++) {
      trials.add(Map.of(
          "trial_id", "stim",
          "trial_type", "poldrack-single-stim",
          "correct_response", -1,
          "key_press", i < 2 ? 32 : -1,
          "rt", i < 2 ? 390 : -1,
          "correct", i >= 2
      ));
    }

    Map<String, Object> result = calculator.calculate("go-nogo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("goAccuracy")).isEqualTo(1.0);
    assertThat((Double) metrics.get("nogoFalseAlarmRate")).isCloseTo(0.2, within(0.0001));
    assertThat((Double) metrics.get("dPrime")).isGreaterThan(1.5);
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesColumbiaCardTaskHotRoundMetrics() {
    List<Map<String, Object>> trials = List.of(
        Map.of("which_round", 1, "num_click_in_round", 1, "round_points", 30, "loss_amount", 250, "clicked_on_loss_card", false, "rt", 1000),
        Map.of("which_round", 1, "num_click_in_round", 3, "round_points", 60, "loss_amount", 250, "clicked_on_loss_card", false, "rt", 1200),
        Map.of("which_round", 2, "num_click_in_round", 1, "round_points", 10, "loss_amount", 750, "clicked_on_loss_card", false, "rt", 900),
        Map.of("which_round", 2, "num_click_in_round", 4, "round_points", -720, "loss_amount", 750, "clicked_on_loss_card", true, "rt", 1400)
    );

    Map<String, Object> result = calculator.calculate("columbia-card-task-hot", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("completedRounds")).isEqualTo(2);
    assertThat((Double) metrics.get("avgCardsPerRound")).isGreaterThan(1);
    assertThat(metrics.get("lossRounds")).isEqualTo(1);
  }

  @Test
  void calculatesDiscountTitrateChoicePattern() {
    List<Map<String, Object>> trials = List.of(
        trial("smaller_sooner", 20, 30, "今天", "2周后", 700),
        trial("smaller_sooner", 25, 40, "今天", "4周后", 800),
        trial("larger_later", 15, 35, "2周后", "6周后", 900),
        trial("larger_later", 18, 30, "今天", "2周后", 850)
    );

    Map<String, Object> result = calculator.calculate("discount-titrate", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("trialCount")).isEqualTo(4);
    assertThat(metrics.get("immediateChoiceRate")).isEqualTo(0.5);
    assertThat(metrics).containsKey("discountK");
  }

  @Test
  void demoCodesReuseTheOriginalScoringModels() {
    List<Map<String, Object>> trials = List.of(
        trial("smaller_sooner", 20, 30, "今天", "2周后", 700),
        trial("larger_later", 18, 30, "今天", "2周后", 850)
    );

    Map<String, Object> result = calculator.calculate("discount-titrate-demo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("trialCount")).isEqualTo(2);
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesStroopInterferenceMetricsForDemoCode() {
    List<Map<String, Object>> trials = List.of(
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "congruent", "correct", true, "rt", 420),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "congruent", "correct", true, "rt", 460),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "incongruent", "correct", true, "rt", 610),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "incongruent", "correct", false, "rt", 700),
        Map.of("trial_id", "stim", "exp_stage", "practice", "condition", "incongruent", "correct", true, "rt", 900)
    );

    Map<String, Object> result = calculator.calculate("stroop-demo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("completedTrials")).isEqualTo(4);
    assertThat(metrics.get("congruentRtMean")).isEqualTo(440.0);
    assertThat(metrics.get("incongruentRtMean")).isEqualTo(610.0);
    assertThat(metrics.get("stroopEffect")).isEqualTo(170.0);
    assertThat(metrics.get("incongruentAccuracy")).isEqualTo(0.5);
    assertThat(result.get("warningLevel")).isEqualTo("high");
  }

  @Test
  void calculatesEmotionRegulationStrategyMetrics() {
    List<Map<String, Object>> trials = List.of(
        Map.of("trial_id", "choice", "exp_stage", "test", "chosen_strategy", "reappraise", "intensity", "high", "rt", 900),
        Map.of("trial_id", "choice", "exp_stage", "test", "chosen_strategy", "distract", "intensity", "high", "rt", 700),
        Map.of("trial_id", "choice", "exp_stage", "test", "chosen_strategy", "reappraise", "intensity", "low", "rt", 800),
        Map.of("trial_id", "choice", "exp_stage", "practice", "chosen_strategy", "distract", "intensity", "low", "rt", 600)
    );

    Map<String, Object> result = calculator.calculate("emotion-regulation-demo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("trialCount")).isEqualTo(3);
    assertThat(metrics.get("reappraiseCount")).isEqualTo(2);
    assertThat(metrics.get("reappraiseRate")).isEqualTo(0.6667);
    assertThat(metrics.get("highReappraiseRate")).isEqualTo(0.5);
  }

  @Test
  void calculatesDigitSpanForwardAndReverseSpans() {
    List<Map<String, Object>> trials = List.of(
        Map.of("trial_id", "response", "condition", "forward", "num_digits", 3, "correct", true, "rt", 1000),
        Map.of("trial_id", "response", "condition", "forward", "num_digits", 4, "correct", true, "rt", 1100),
        Map.of("trial_id", "response", "condition", "reverse", "num_digits", 3, "correct", true, "rt", 1200),
        Map.of("trial_id", "response", "condition", "reverse", "num_digits", 4, "correct", false, "rt", 1300)
    );

    Map<String, Object> result = calculator.calculate("digit-span-demo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("forwardMaxSpan")).isEqualTo(4);
    assertThat(metrics.get("reverseMaxSpan")).isEqualTo(3);
    assertThat(metrics.get("totalSpan")).isEqualTo(7);
    assertThat(metrics.get("overallAccuracy")).isEqualTo(0.75);
  }

  @Test
  void calculatesFlankerConflictMetrics() {
    List<Map<String, Object>> trials = List.of(
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "compatible", "correct", true, "rt", 430),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "compatible", "correct", true, "rt", 470),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "incompatible", "correct", true, "rt", 590),
        Map.of("trial_id", "stim", "exp_stage", "test", "condition", "incompatible", "correct", false, "rt", 640)
    );

    Map<String, Object> result = calculator.calculate("flanker-demo", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("completedTrials")).isEqualTo(4);
    assertThat(metrics.get("compatibleRtMean")).isEqualTo(450.0);
    assertThat(metrics.get("incompatibleRtMean")).isEqualTo(590.0);
    assertThat(metrics.get("flankerEffect")).isEqualTo(140.0);
    assertThat(metrics.get("incompatibleAccuracy")).isEqualTo(0.5);
  }

  private Map<String, Object> trial(String choice, double small, double large, String sooner, String later, int rt) {
    return Map.of(
        "trial_id", "stim",
        "choice", choice,
        "smaller_amount", small,
        "larger_amount", large,
        "sooner_delay", sooner,
        "later_delay", later,
        "rt", rt
    );
  }

  private org.assertj.core.data.Offset<Double> within(double offset) {
    return org.assertj.core.data.Offset.offset(offset);
  }



  @Test
  void calculatesNBackSignalDetectionMetrics() {
    List<Map<String, Object>> trials = new ArrayList<>();
    // 10 target trials (respond with ArrowLeft=37)
    for (int i = 0; i < 10; i++) {
      trials.add(Map.of("trial_id", "stim", "stim", "B", "target", "B",
          "key_press", 37, "rt", 500, "correct", true));
    }
    // 10 non-target trials (correct rejection - no response)
    for (int i = 0; i < 10; i++) {
      trials.add(Map.of("trial_id", "stim", "stim", "G", "target", "T",
          "key_press", -1, "rt", -1, "correct", true));
    }
    // 2 false alarms on non-target (responded when shouldn't)
    trials.add(Map.of("trial_id", "stim", "stim", "D", "target", "V",
        "key_press", 37, "rt", 450, "correct", false));
    trials.add(Map.of("trial_id", "stim", "stim", "K", "target", "G",
        "key_press", 37, "rt", 480, "correct", false));

    Map<String, Object> result = calculator.calculate("n-back", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("targetTotal")).isEqualTo(10);
    assertThat(metrics.get("nonTargetTotal")).isEqualTo(12);
    assertThat((Double) metrics.get("overallAccuracy")).isGreaterThan(0.8);
    assertThat((Double) metrics.get("dPrime")).isGreaterThan(1.0);
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesStopSignalSsrt() {
    List<Map<String, Object>> trials = new ArrayList<>();
    // 20 go trials (correct responses)
    for (int i = 0; i < 20; i++) {
      trials.add(Map.of("trial_type", "poldrack-single-stim", "trial_id", "stim",
          "condition", "go", "correct_response", 37, "key_press", 37, "rt", 450));
    }
    // 10 stop trials (5 successful stops, 5 failures)
    for (int i = 0; i < 5; i++) {
      trials.add(Map.of("trial_type", "stop-signal", "trial_id", "stim",
          "condition", "stop", "stop_signal_delay", 200, "key_press", -1, "rt", -1));
    }
    for (int i = 0; i < 5; i++) {
      trials.add(Map.of("trial_type", "stop-signal", "trial_id", "stim",
          "condition", "stop", "stop_signal_delay", 200, "key_press", 37, "rt", 350));
    }

    Map<String, Object> result = calculator.calculate("stop-signal", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("goTotal")).isEqualTo(20);
    assertThat(metrics.get("stopTotal")).isEqualTo(10);
    assertThat(metrics.get("stopSuccess")).isEqualTo(5);
    assertThat((Double) metrics.get("stopSuccessRate")).isCloseTo(0.5, within(0.01));
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesSimonEffect() {
    List<Map<String, Object>> trials = new ArrayList<>();
    // 10 congruent trials
    for (int i = 0; i < 10; i++) {
      trials.add(Map.of("trial_id", "stim", "condition", "congruent",
          "correct_response", 37, "key_press", 37, "rt", 400, "correct", true));
    }
    // 10 incongruent trials (slower)
    for (int i = 0; i < 10; i++) {
      trials.add(Map.of("trial_id", "stim", "condition", "incongruent",
          "correct_response", 37, "key_press", 37, "rt", 500, "correct", true));
    }

    Map<String, Object> result = calculator.calculate("simon", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat((Double) metrics.get("congruentRtMean")).isCloseTo(400.0, within(1.0));
    assertThat((Double) metrics.get("incongruentRtMean")).isCloseTo(500.0, within(1.0));
    assertThat((Double) metrics.get("simonEffect")).isCloseTo(100.0, within(1.0));
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesAntNetworkEffects() {
    List<Map<String, Object>> trials = new ArrayList<>();
    // nocue trials
    for (int i = 0; i < 5; i++) {
      trials.add(Map.of("trial_id", "stim", "cue", "nocue", "flanker_middle_direction", "left",
          "correct_response", 37, "key_press", 37, "rt", 550));
    }
    // center cue trials
    for (int i = 0; i < 5; i++) {
      trials.add(Map.of("trial_id", "stim", "cue", "center", "flanker_middle_direction", "left",
          "correct_response", 37, "key_press", 37, "rt", 500));
    }
    // spatial cue trials
    for (int i = 0; i < 5; i++) {
      trials.add(Map.of("trial_id", "stim", "cue", "spatial", "flanker_middle_direction", "left",
          "correct_response", 37, "key_press", 37, "rt", 430));
    }

    Map<String, Object> result = calculator.calculate("ant", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat((Double) metrics.get("alertingEffect")).isCloseTo(50.0, within(5.0));
    assertThat((Double) metrics.get("orientingEffect")).isCloseTo(70.0, within(5.0));
    assertThat(metrics.get("completedTrials")).isEqualTo(15);
    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }

  @Test
  void calculatesAxCptContextSensitivity() {
    List<Map<String, Object>> trials = new ArrayList<>();
    // 15 AX trials (high target, respond M=77)
    for (int i = 0; i < 15; i++) {
      Map<String, Object> trial = new java.util.HashMap<>();
      trial.put("trial_id", "probe"); trial.put("condition", "AX"); trial.put("cue", "A");
      trial.put("correct_response", 77); trial.put("key_press", 77); trial.put("rt", 400); trial.put("correct", true);
      trials.add(trial);
    }
    // 3 AY trials (A cue, non-X probe - should NOT respond M)
    for (int i = 0; i < 3; i++) {
      Map<String, Object> trial = new java.util.HashMap<>();
      trial.put("trial_id", "probe"); trial.put("condition", "AY"); trial.put("cue", "A");
      trial.put("correct_response", 90); trial.put("key_press", 77); trial.put("rt", 380); trial.put("correct", false);
      trials.add(trial);
    }
    // 3 BX trials (non-A cue, X probe - should NOT respond M)
    for (int i = 0; i < 3; i++) {
      Map<String, Object> trial = new java.util.HashMap<>();
      trial.put("trial_id", "probe"); trial.put("condition", "BX"); trial.put("cue", "B");
      trial.put("correct_response", 90); trial.put("key_press", 90); trial.put("rt", 420); trial.put("correct", true);
      trials.add(trial);
    }
    // 3 BY trials (neither)
    for (int i = 0; i < 3; i++) {
      Map<String, Object> trial = new java.util.HashMap<>();
      trial.put("trial_id", "probe"); trial.put("condition", "BY"); trial.put("cue", "B");
      trial.put("correct_response", 90); trial.put("key_press", 90); trial.put("rt", 440); trial.put("correct", true);
      trials.add(trial);
    }

    Map<String, Object> result = calculator.calculate("ax-cpt", trials);
    @SuppressWarnings("unchecked")
    Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");

    assertThat(metrics.get("axTotal")).isEqualTo(15);
    assertThat((Double) metrics.get("axHitRate")).isGreaterThan(0.9);

    assertThat(result.get("feedbackCards")).isInstanceOf(List.class);
  }
}
