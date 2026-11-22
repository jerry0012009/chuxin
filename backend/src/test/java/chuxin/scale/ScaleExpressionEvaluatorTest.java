package chuxin.scale;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;

class ScaleExpressionEvaluatorTest {

  @Test
  void evaluatesLogicalConditions() {
    Map<String, Double> variables = Map.of("hx_wd_y_1", 7D, "hx_t_1", 1D);

    assertThat(ScaleExpressionEvaluator.evaluateBoolean("hx_wd_y_1 >= 5 && hx_wd_y_1 <= 9", variables)).isTrue();
    assertThat(ScaleExpressionEvaluator.evaluateBoolean("hx_wd_y_1 < 5 || hx_t_1 == 1", variables)).isTrue();
    assertThat(ScaleExpressionEvaluator.evaluateBoolean("hx_wd_y_1 >= 10 && hx_wd_y_1 <= 14", variables)).isFalse();
  }

  @Test
  void evaluatesHuaxinyunFunctionsAndTernaryExpressions() {
    Map<String, Double> variables = Map.of(
        "hx_t_1", 1D,
        "hx_t_2", 3D,
        "hx_wd_y_a", 8D,
        "hx_gender", 1D
    );

    assertThat(ScaleExpressionEvaluator.evaluateNumber("max(hx_t_1, hx_t_2, 2)", variables)).isEqualTo(3D);
    assertThat(ScaleExpressionEvaluator.evaluateNumber("min(hx_t_1, hx_t_2, 2)", variables)).isEqualTo(1D);
    assertThat(ScaleExpressionEvaluator.evaluateNumber("hx_wd_y_a > 5 ? 10 : 0", variables)).isEqualTo(10D);
    assertThat(ScaleExpressionEvaluator.evaluateNumber("if (hx_gender == 1, 10, 5)", variables)).isEqualTo(10D);
    assertThat(ScaleExpressionEvaluator.evaluateBoolean("(hx_wd_y_a > 5 ? 1 : 0) == 1", variables)).isTrue();
  }
}
