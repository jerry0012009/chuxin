package chuxin.scale;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthService;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ScaleHuaxinyunImportService {

  private static final Pattern HUAXINYUN_DIMENSION_PLACEHOLDER = Pattern.compile("\\{#([A-Za-z0-9_]+)}");
  private static final List<String> WARNING_LEVELS = List.of("none", "low", "middle", "high");

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;
  private final AuthService authService;
  private final ScaleAssessmentService scaleAssessmentService;

  public ScaleHuaxinyunImportService(
      NamedParameterJdbcTemplate jdbcTemplate,
      ObjectMapper objectMapper,
      AuthService authService,
      ScaleAssessmentService scaleAssessmentService) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
    this.authService = authService;
    this.scaleAssessmentService = scaleAssessmentService;
  }

  public Map<String, Object> importSurveys(Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可导入量表");
    }

    boolean dryRun = bool(firstNonNull(payload.get("dry_run"), payload.get("dryRun")), true);
    boolean publish = bool(payload.get("publish"), false);
    boolean overwrite = bool(payload.get("overwrite"), false);
    boolean skipInvalid = bool(firstNonNull(payload.get("skip_invalid"), payload.get("skipInvalid")), true);
    List<JsonNode> sourceSurveys = parseSurveyNodes(payload.get("content"));
    if (sourceSurveys.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "未解析到可导入的华心云量表 JSON");
    }

    List<Map<String, Object>> items = new ArrayList<>();
    int importable = 0;
    int publishable = 0;
    int imported = 0;
    int updated = 0;
    int skipped = 0;
    int failed = 0;
    for (JsonNode source : sourceSurveys) {
      ImportCandidate candidate = buildCandidate(source, publish);
      if (candidate.canImport()) {
        importable++;
      }
      if (candidate.canPublish()) {
        publishable++;
      }

      Map<String, Object> item = candidate.item();
      if (dryRun) {
        item.put("action", candidate.canImport() && (!publish || candidate.canPublish()) ? "would_import" : "would_skip");
        items.add(item);
        continue;
      }

      if (!candidate.canImport() || (publish && !candidate.canPublish())) {
        failed++;
        item.put("action", "invalid");
        items.add(item);
        if (!skipInvalid) {
          throw new ApiException(HttpStatus.BAD_REQUEST, "存在不可导入量表: " + item.get("title"));
        }
        continue;
      }

      try {
        String existingId = existingSurveyId(candidate.code());
        if (existingId != null) {
          if (!overwrite) {
            skipped++;
            item.put("action", "skipped_existing");
            item.put("survey_id", existingId);
            items.add(item);
            continue;
          }
          if (distributionCount(existingId) > 0) {
            skipped++;
            item.put("action", "skipped_has_records");
            item.put("survey_id", existingId);
            addIssue(item, "已有答题记录，不能覆盖量表结构，请复制新版本后再导入");
            items.add(item);
            continue;
          }
          scaleAssessmentService.updateSurvey(existingId, candidate.payload(), user);
          if (publish) {
            scaleAssessmentService.publishSurvey(existingId, user);
          }
          updated++;
          item.put("action", publish ? "updated_published" : "updated");
          item.put("survey_id", existingId);
          items.add(item);
          continue;
        }

        Map<String, Object> created = scaleAssessmentService.createSurvey(candidate.payload(), user);
        String surveyId = string(created.get("id"), "");
        if (publish) {
          scaleAssessmentService.publishSurvey(surveyId, user);
        }
        imported++;
        item.put("action", publish ? "imported_published" : "imported");
        item.put("survey_id", surveyId);
        items.add(item);
      } catch (Exception ex) {
        failed++;
        item.put("action", "failed");
        addIssue(item, ex.getMessage());
        items.add(item);
        if (!skipInvalid) {
          if (ex instanceof ApiException apiException) {
            throw apiException;
          }
          throw new ApiException(HttpStatus.BAD_REQUEST, "量表导入失败: " + ex.getMessage());
        }
      }
    }

    Map<String, Object> result = new LinkedHashMap<>();
    result.put("dry_run", dryRun);
    result.put("publish", publish);
    result.put("overwrite", overwrite);
    result.put("skip_invalid", skipInvalid);
    result.put("total", sourceSurveys.size());
    result.put("importable", importable);
    result.put("publishable", publishable);
    result.put("imported", imported);
    result.put("updated", updated);
    result.put("skipped", skipped);
    result.put("failed", failed);
    result.put("items", items);
    return result;
  }

  private ImportCandidate buildCandidate(JsonNode source, boolean publish) {
    List<String> issues = new ArrayList<>();
    List<String> warnings = new ArrayList<>();
    String sourceId = text(source, "id", "");
    String title = text(source, "title", "");
    String code = "huaxinyun-" + (sourceId.isBlank() ? UUID.randomUUID() : sourceId);
    if (title.isBlank()) {
      issues.add("量表标题为空");
      title = "未命名华心云量表";
    }

    List<Map<String, Object>> questions = new ArrayList<>();
    Map<Integer, Boolean> seenQuestionOrders = new LinkedHashMap<>();
    int questionFallbackOrder = 1;
    for (JsonNode question : iterable(source.path("questions"))) {
      String type = text(question, "type", "radio");
      if (!List.of("radio", "checkbox", "text").contains(type)) {
        issues.add("不支持的题型: " + type);
      }
      int orderNo = intValue(question.get("orderNum"), questionFallbackOrder);
      if (seenQuestionOrders.containsKey(orderNo)) {
        issues.add("题号重复: " + orderNo);
      }
      seenQuestionOrders.put(orderNo, true);
      String stem = text(question, "text", "");
      if (stem.isBlank()) {
        issues.add("第 " + orderNo + " 题题干为空");
      }
      Map<String, Object> mappedQuestion = new LinkedHashMap<>();
      mappedQuestion.put("id", uuid());
      mappedQuestion.put("question_type", type);
      mappedQuestion.put("stem", stem);
      mappedQuestion.put("order_no", orderNo);
      mappedQuestion.put("required", true);
      List<Map<String, Object>> options = new ArrayList<>();
      int optionOrder = 1;
      for (JsonNode option : iterable(question.path("options"))) {
        String label = text(option, "text", "");
        if (label.isBlank()) {
          issues.add("第 " + orderNo + " 题存在空选项");
        }
        Object value = decimalValue(option.get("value"), issues, "第 " + orderNo + " 题选项分值不是数字");
        Map<String, Object> mappedOption = new LinkedHashMap<>();
        mappedOption.put("id", uuid());
        mappedOption.put("option_no", text(option, "optionNo", String.valueOf(optionOrder)));
        mappedOption.put("label", label);
        mappedOption.put("value", value);
        mappedOption.put("order_no", optionOrder++);
        options.add(mappedOption);
      }
      if (("radio".equals(type) || "checkbox".equals(type)) && options.isEmpty()) {
        issues.add("第 " + orderNo + " 题缺少选项");
      }
      mappedQuestion.put("options", options);
      questions.add(mappedQuestion);
      questionFallbackOrder++;
    }
    if (questions.isEmpty()) {
      issues.add("量表没有题目");
    }

    List<Map<String, Object>> dimensions = new ArrayList<>();
    int dimensionFallbackNum = 1;
    for (JsonNode dimension : iterable(source.path("dimensions"))) {
      int num = intValue(dimension.get("num"), dimensionFallbackNum);
      String name = text(dimension, "dimensionName", "维度 " + num);
      String rawFormula = normalizeFormula(text(dimension, "evaluateExpression", ""));
      if (rawFormula.isBlank()) {
        warnings.add("维度「" + name + "」原始分公式为空，已按 0 分处理");
        rawFormula = "0";
      } else {
        validateFormula(rawFormula, issues, "维度「" + name + "」原始分公式");
      }
      String standardFormula = normalizeFormula(text(dimension, "standardScoreFormula", ""));
      if ("0".equals(standardFormula.trim())) {
        warnings.add("维度「" + name + "」标准分公式为 0，已按原始分展示");
        standardFormula = "";
      } else if (!standardFormula.isBlank()) {
        validateFormula(standardFormula, issues, "维度「" + name + "」标准分公式");
      }
      Map<String, Object> mappedDimension = new LinkedHashMap<>();
      mappedDimension.put("id", uuid());
      mappedDimension.put("name", name);
      mappedDimension.put("code", text(dimension, "dimensionCode", "").toLowerCase(Locale.ROOT));
      mappedDimension.put("num", num);
      mappedDimension.put("raw_score_formula", rawFormula);
      mappedDimension.put("standard_score_formula", standardFormula);
      mappedDimension.put("show_in_full_report", true);
      mappedDimension.put("show_in_user_report", true);
      mappedDimension.put("show_chart", false);
      List<Map<String, Object>> definitions = new ArrayList<>();
      int definitionOrder = 1;
      for (JsonNode result : iterable(dimension.path("results"))) {
        String condition = normalizeFormula(text(result, "evaluateExpression", ""));
        if (condition.isBlank()) {
          issues.add("维度「" + name + "」存在空结果条件");
        } else {
          validateFormula(condition, issues, "维度「" + name + "」结果条件");
        }
        Map<String, Object> definition = new LinkedHashMap<>();
        definition.put("id", uuid());
        definition.put("condition_expression", condition);
        definition.put("conclusion", text(result, "conclusionAnalysis", ""));
        definition.put("suggestion", text(result, "suggestion", ""));
        definition.put("warning_level", warningLevel(text(result, "assessmentWarning", "none")));
        definition.put("order_no", definitionOrder++);
        definitions.add(definition);
      }
      if (definitions.isEmpty()) {
        warnings.add("维度「" + name + "」没有结果解释，报告将仅展示分数且不触发该维度预警");
      }
      mappedDimension.put("result_definitions", definitions);
      dimensions.add(mappedDimension);
      dimensionFallbackNum++;
    }
    if (dimensions.isEmpty()) {
      warnings.add("量表没有维度和阈值，发布后可答题，报告将展示 0 分与空维度");
    }

    boolean canImport = issues.isEmpty();
    boolean canPublish = canImport && !questions.isEmpty();
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("title", title);
    payload.put("code", code);
    payload.put("description", source.hasNonNull("description")
        ? text(source, "description", "")
        : "来源：华心云量表导入");
    payload.put("survey_type", text(source, "type", "basic"));
    payload.put("status", "draft");
    payload.put("self_test_enabled", false);
    payload.put("questions", questions);
    payload.put("dimensions", dimensions);

    Map<String, Object> item = new LinkedHashMap<>();
    item.put("source_id", sourceId);
    item.put("code", code);
    item.put("title", title);
    item.put("question_count", questions.size());
    item.put("dimension_count", dimensions.size());
    item.put("result_count", dimensions.stream().mapToInt(dimension -> list(dimension.get("result_definitions")).size()).sum());
    item.put("can_import", canImport);
    item.put("can_publish", canPublish);
    item.put("issues", issues);
    item.put("warnings", warnings);
    return new ImportCandidate(code, payload, item, canImport, canPublish);
  }

  private List<JsonNode> parseSurveyNodes(Object content) {
    JsonNode root = toJsonNode(content);
    List<JsonNode> surveys = new ArrayList<>();
    collectSurveyNodes(root, surveys);
    return surveys;
  }

  private void collectSurveyNodes(JsonNode node, List<JsonNode> surveys) {
    if (node == null || node.isNull()) {
      return;
    }
    if (node.isArray()) {
      for (JsonNode item : node) {
        collectSurveyNodes(item, surveys);
      }
      return;
    }
    if (!node.isObject()) {
      return;
    }
    if (node.has("surveyJson")) {
      collectSurveyNodes(toJsonNode(text(node, "surveyJson", "")), surveys);
      return;
    }
    JsonNode list = node.path("data").path("list");
    if (list.isArray()) {
      collectSurveyNodes(list, surveys);
      return;
    }
    if (node.has("questions")) {
      surveys.add(node);
    }
  }

  private JsonNode toJsonNode(Object value) {
    if (value == null) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "导入内容不能为空");
    }
    try {
      if (value instanceof String text) {
        return objectMapper.readTree(text);
      }
      return objectMapper.valueToTree(value);
    } catch (JsonProcessingException ex) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "导入内容不是合法 JSON");
    }
  }

  private String normalizeFormula(String formula) {
    if (formula == null || formula.isBlank()) {
      return "";
    }
    Matcher matcher = HUAXINYUN_DIMENSION_PLACEHOLDER.matcher(formula.trim());
    StringBuffer normalized = new StringBuffer();
    while (matcher.find()) {
      matcher.appendReplacement(normalized, "hx_wd_y_" + matcher.group(1).toLowerCase(Locale.ROOT));
    }
    matcher.appendTail(normalized);
    return normalized.toString();
  }

  private void validateFormula(String expression, List<String> issues, String label) {
    try {
      ScaleExpressionEvaluator.evaluateNumber(expression, Map.of());
    } catch (ApiException ex) {
      issues.add(label + "不兼容: " + ex.getMessage());
    }
  }

  private String existingSurveyId(String code) {
    List<Map<String, Object>> rows = jdbcTemplate.queryForList(
        "SELECT id FROM scale_surveys WHERE code = :code LIMIT 1",
        new MapSqlParameterSource("code", code)
    );
    return rows.isEmpty() ? null : string(rows.getFirst().get("id"), "");
  }

  private int distributionCount(String surveyId) {
    Integer count = jdbcTemplate.queryForObject(
        "SELECT COUNT(*) FROM scale_distribution_records WHERE survey_id = :id",
        new MapSqlParameterSource("id", surveyId),
        Integer.class
    );
    return count == null ? 0 : count;
  }

  private Iterable<JsonNode> iterable(JsonNode node) {
    return node != null && node.isArray() ? node::elements : List.<JsonNode>of();
  }

  @SuppressWarnings("unchecked")
  private List<Map<String, Object>> list(Object value) {
    if (value instanceof List<?> items) {
      return items.stream()
          .filter(Map.class::isInstance)
          .map(item -> (Map<String, Object>) item)
          .toList();
    }
    return List.of();
  }

  private Object decimalValue(JsonNode node, List<String> issues, String message) {
    try {
      String value = node == null || node.isNull() ? "0" : node.asText();
      return new BigDecimal(value);
    } catch (NumberFormatException ex) {
      issues.add(message);
      return BigDecimal.ZERO;
    }
  }

  private String warningLevel(String value) {
    String normalized = value == null ? "none" : value.trim().toLowerCase(Locale.ROOT);
    return WARNING_LEVELS.contains(normalized) ? normalized : "none";
  }

  private void addIssue(Map<String, Object> item, String message) {
    List<String> issues = objectMapper.convertValue(
        item.getOrDefault("issues", List.of()),
        new TypeReference<List<String>>() {}
    );
    List<String> nextIssues = new ArrayList<>(issues);
    nextIssues.add(message);
    item.put("issues", nextIssues);
    item.put("can_import", false);
    item.put("can_publish", false);
  }

  private String text(JsonNode node, String field, String fallback) {
    JsonNode value = node == null ? null : node.get(field);
    return value == null || value.isNull() ? fallback : value.asText(fallback);
  }

  private int intValue(JsonNode node, int fallback) {
    if (node == null || node.isNull()) {
      return fallback;
    }
    if (node.isNumber()) {
      return node.asInt();
    }
    try {
      return Integer.parseInt(node.asText());
    } catch (NumberFormatException ex) {
      return fallback;
    }
  }

  private boolean bool(Object value, boolean fallback) {
    return value == null ? fallback : Boolean.parseBoolean(String.valueOf(value));
  }

  private Object firstNonNull(Object first, Object second) {
    return first != null ? first : second;
  }

  private String string(Object value, String fallback) {
    return value == null ? fallback : String.valueOf(value);
  }

  private String uuid() {
    return UUID.randomUUID().toString();
  }

  private record ImportCandidate(
      String code,
      Map<String, Object> payload,
      Map<String, Object> item,
      boolean canImport,
      boolean canPublish
  ) {}
}
