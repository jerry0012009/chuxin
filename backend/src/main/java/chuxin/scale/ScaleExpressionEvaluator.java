package chuxin.scale;

import chuxin.common.ApiException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;

final class ScaleExpressionEvaluator {

  private final String input;
  private final Map<String, Double> variables;
  private int position;

  private ScaleExpressionEvaluator(String input, Map<String, Double> variables) {
    this.input = input == null ? "" : input;
    this.variables = variables;
  }

  static double evaluateNumber(String expression, Map<String, Double> variables) {
    ScaleExpressionEvaluator evaluator = new ScaleExpressionEvaluator(expression, variables);
    double value = evaluator.parseTernary();
    evaluator.skipWhitespace();
    if (!evaluator.isEnd()) {
      throw evaluator.error("公式存在无法解析的内容");
    }
    return value;
  }

  static boolean evaluateBoolean(String expression, Map<String, Double> variables) {
    return Math.abs(evaluateNumber(expression, variables)) > 0.000001;
  }

  private double parseTernary() {
    double condition = parseOr();
    skipWhitespace();
    if (!match("?")) {
      return condition;
    }
    double whenTrue = parseTernary();
    expect(":");
    double whenFalse = parseTernary();
    return truthy(condition) ? whenTrue : whenFalse;
  }

  private double parseOr() {
    double value = parseAnd();
    while (true) {
      skipWhitespace();
      if (match("||")) {
        double right = parseAnd();
        value = truthy(value) || truthy(right) ? 1 : 0;
      } else {
        return value;
      }
    }
  }

  private double parseAnd() {
    double value = parseComparison();
    while (true) {
      skipWhitespace();
      if (match("&&")) {
        double right = parseComparison();
        value = truthy(value) && truthy(right) ? 1 : 0;
      } else {
        return value;
      }
    }
  }

  private double parseComparison() {
    double value = parseAddSub();
    while (true) {
      skipWhitespace();
      if (match(">=")) {
        value = value >= parseAddSub() ? 1 : 0;
      } else if (match("<=")) {
        value = value <= parseAddSub() ? 1 : 0;
      } else if (match("==")) {
        value = Math.abs(value - parseAddSub()) < 0.000001 ? 1 : 0;
      } else if (match("!=")) {
        value = Math.abs(value - parseAddSub()) >= 0.000001 ? 1 : 0;
      } else if (match(">")) {
        value = value > parseAddSub() ? 1 : 0;
      } else if (match("<")) {
        value = value < parseAddSub() ? 1 : 0;
      } else {
        return value;
      }
    }
  }

  private double parseAddSub() {
    double value = parseMulDiv();
    while (true) {
      skipWhitespace();
      if (match("+")) {
        value += parseMulDiv();
      } else if (match("-")) {
        value -= parseMulDiv();
      } else {
        return value;
      }
    }
  }

  private double parseMulDiv() {
    double value = parseUnary();
    while (true) {
      skipWhitespace();
      if (match("*")) {
        value *= parseUnary();
      } else if (match("/")) {
        double divisor = parseUnary();
        if (Math.abs(divisor) < 0.000001) {
          throw error("公式出现除以 0");
        }
        value /= divisor;
      } else {
        return value;
      }
    }
  }

  private double parseUnary() {
    skipWhitespace();
    if (match("+")) {
      return parseUnary();
    }
    if (match("-")) {
      return -parseUnary();
    }
    if (match("!")) {
      return truthy(parseUnary()) ? 0 : 1;
    }
    return parsePrimary();
  }

  private double parsePrimary() {
    skipWhitespace();
    if (match("(")) {
      double value = parseTernary();
      expect(")");
      return value;
    }
    if (peekDigit() || peek('.')) {
      return parseNumber();
    }
    if (peekIdentifierStart()) {
      String name = parseIdentifier();
      skipWhitespace();
      if (match("(")) {
        List<Double> args = new ArrayList<>();
        skipWhitespace();
        if (!peek(')')) {
          do {
            args.add(parseTernary());
            skipWhitespace();
          } while (match(","));
        }
        expect(")");
        return callFunction(name, args);
      }
      return variables.getOrDefault(name, 0D);
    }
    throw error("公式语法错误");
  }

  private double parseNumber() {
    int start = position;
    while (!isEnd() && (Character.isDigit(input.charAt(position)) || input.charAt(position) == '.')) {
      position++;
    }
    try {
      return Double.parseDouble(input.substring(start, position));
    } catch (NumberFormatException ex) {
      throw error("数字格式错误");
    }
  }

  private String parseIdentifier() {
    int start = position;
    while (!isEnd()) {
      char ch = input.charAt(position);
      if (Character.isLetterOrDigit(ch) || ch == '_') {
        position++;
      } else {
        break;
      }
    }
    return input.substring(start, position);
  }

  private double callFunction(String name, List<Double> args) {
    if (args.isEmpty()) {
      throw error("函数缺少参数: " + name);
    }
    double target = args.getFirst();
    return switch (name) {
      case "max" -> args.stream().max(Comparator.naturalOrder()).orElseThrow(() -> error("函数缺少参数: " + name));
      case "min" -> args.stream().min(Comparator.naturalOrder()).orElseThrow(() -> error("函数缺少参数: " + name));
      case "if" -> {
        if (args.size() != 3) {
          throw error("if 函数需要 3 个参数");
        }
        yield truthy(args.get(0)) ? args.get(1) : args.get(2);
      }
      case "hx_calc_equal_count" -> args.stream().skip(1).filter(value -> Math.abs(value - target) < 0.000001).count();
      case "hx_calc_gt_count" -> args.stream().skip(1).filter(value -> value > target).count();
      case "hx_calc_ge_count" -> args.stream().skip(1).filter(value -> value >= target).count();
      case "hx_calc_lt_count" -> args.stream().skip(1).filter(value -> value < target).count();
      case "hx_calc_le_count" -> args.stream().skip(1).filter(value -> value <= target).count();
      default -> throw error("不支持的公式函数: " + name);
    };
  }

  private boolean truthy(double value) {
    return Math.abs(value) > 0.000001;
  }

  private void expect(String token) {
    if (!match(token)) {
      throw error("缺少 " + token);
    }
  }

  private boolean match(String token) {
    skipWhitespace();
    if (input.startsWith(token, position)) {
      position += token.length();
      return true;
    }
    return false;
  }

  private boolean peek(char ch) {
    skipWhitespace();
    return !isEnd() && input.charAt(position) == ch;
  }

  private boolean peekDigit() {
    skipWhitespace();
    return !isEnd() && Character.isDigit(input.charAt(position));
  }

  private boolean peekIdentifierStart() {
    skipWhitespace();
    return !isEnd() && (Character.isLetter(input.charAt(position)) || input.charAt(position) == '_');
  }

  private void skipWhitespace() {
    while (!isEnd() && Character.isWhitespace(input.charAt(position))) {
      position++;
    }
  }

  private boolean isEnd() {
    return position >= input.length();
  }

  private ApiException error(String message) {
    return new ApiException(HttpStatus.BAD_REQUEST, message + ": " + input);
  }
}
