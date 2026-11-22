package chuxin.scale;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthService;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.math.BigDecimal;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.ColumnMapRowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ScaleAssessmentService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;
  private final AuthService authService;

  public ScaleAssessmentService(
      NamedParameterJdbcTemplate jdbcTemplate,
      ObjectMapper objectMapper,
      AuthService authService) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
    this.authService = authService;
  }

  public List<Map<String, Object>> listSurveys(AuthUser authUser) {
    requireStaff(authUser);
    return query("""
        SELECT s.id, s.code, s.title, s.description, s.cover_url, s.survey_type, s.status,
          s.self_test_enabled, s.sort_order, s.version, s.created_by, s.published_at, s.created_at, s.updated_at,
          (SELECT COUNT(*) FROM scale_questions q WHERE q.survey_id = s.id) AS question_count,
          (SELECT COUNT(*) FROM scale_distribution_records r WHERE r.survey_id = s.id) AS distribution_count
        FROM scale_surveys s
        ORDER BY COALESCE(s.sort_order, 99999), s.updated_at DESC
        """, Map.of());
  }

  public List<Map<String, Object>> listFreeSurveys(AuthUser authUser) {
    authService.requireUser(authUser);
    return query("""
        SELECT s.id, s.code, s.title, s.description, s.cover_url, s.survey_type, s.status,
          s.self_test_enabled, s.sort_order, s.version, s.created_by, s.published_at, s.created_at, s.updated_at,
          (SELECT COUNT(*) FROM scale_questions q WHERE q.survey_id = s.id) AS question_count
        FROM scale_surveys s
        WHERE s.status = 'published' AND s.self_test_enabled = TRUE
        ORDER BY COALESCE(s.sort_order, 99999), s.updated_at DESC
        """, Map.of());
  }

  public Map<String, Object> getSurvey(String surveyId, AuthUser authUser) {
    requireStaff(authUser);
    return loadSurveyDetail(surveyId);
  }

  @Transactional
  public Map<String, Object> createSurvey(Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    String surveyId = uuid();
    saveSurveyBase(surveyId, payload, authUser, true);
    replaceSurveyChildren(surveyId, payload);
    return loadSurveyDetail(surveyId);
  }

  @Transactional
  public Map<String, Object> updateSurvey(String surveyId, Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    ensureExists("SELECT id FROM scale_surveys WHERE id = :id", Map.of("id", surveyId), "量表不存在");
    saveSurveyBase(surveyId, payload, authUser, false);
    if (payload.containsKey("questions") || payload.containsKey("dimensions")) {
      replaceSurveyChildren(surveyId, payload);
    }
    return loadSurveyDetail(surveyId);
  }

  @Transactional
  public Map<String, Object> reorderSurveys(Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    @SuppressWarnings("unchecked")
    List<Map<String, Object>> orders = (List<Map<String, Object>>) payload.get("orders");
    if (orders == null || orders.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请提供排序列表");
    }
    for (Map<String, Object> item : orders) {
      String id = string(item.get("id"), "");
      int sortOrder = intValue(item.get("sort_order"), 0);
      jdbcTemplate.update(
          "UPDATE scale_surveys SET sort_order = :sortOrder, updated_at = :now WHERE id = :id",
          new MapSqlParameterSource()
              .addValue("id", id)
              .addValue("sortOrder", sortOrder)
              .addValue("now", Timestamp.from(Instant.now()))
      );
    }
    return Map.of("updated", orders.size());
  }

  @Transactional
  public Map<String, Object> deleteSurvey(String surveyId, AuthUser authUser) {
    requireStaff(authUser);
    Integer distributions = jdbcTemplate.queryForObject(
        "SELECT COUNT(*) FROM scale_distribution_records WHERE survey_id = :id",
        new MapSqlParameterSource("id", surveyId),
        Integer.class
    );
    if (distributions != null && distributions > 0) {
      jdbcTemplate.update(
          "UPDATE scale_surveys SET status = 'stopped', updated_at = :now WHERE id = :id",
          new MapSqlParameterSource().addValue("id", surveyId).addValue("now", Timestamp.from(Instant.now()))
      );
      return Map.of("id", surveyId, "status", "stopped");
    }
    jdbcTemplate.update("DELETE FROM scale_surveys WHERE id = :id", new MapSqlParameterSource("id", surveyId));
    return Map.of("id", surveyId);
  }

  @Transactional
  public Map<String, Object> publishSurvey(String surveyId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> detail = loadSurveyDetail(surveyId);
    List<Map<String, Object>> questions = list(detail.get("questions"));
    List<Map<String, Object>> dimensions = list(detail.get("dimensions"));
    if (questions.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "发布前至少需要配置一道题目");
    }
    for (Map<String, Object> question : questions) {
      String type = string(question.get("question_type"), "");
      if (("radio".equals(type) || "checkbox".equals(type)) && list(question.get("options")).isEmpty()) {
        throw new ApiException(HttpStatus.BAD_REQUEST, "选择题必须配置选项: " + question.get("stem"));
      }
    }
    for (Map<String, Object> dimension : dimensions) {
      if (string(dimension.get("raw_score_formula"), "").isBlank()) {
        dimension.put("raw_score_formula", "0");
      }
    }

    Map<String, Object> snapshot = buildSurveySnapshot(detail);
    jdbcTemplate.update("""
        UPDATE scale_surveys
        SET status = 'published', survey_json = CAST(:surveyJson AS JSON), published_at = :now, updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", surveyId)
            .addValue("surveyJson", toJson(snapshot))
            .addValue("now", Timestamp.from(Instant.now()))
    );
    return loadSurveyDetail(surveyId);
  }

  @Transactional
  public Map<String, Object> cloneSurvey(String surveyId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> source = loadSurveyDetail(surveyId);
    String cloneId = uuid();
    Map<String, Object> payload = new LinkedHashMap<>(source);
    payload.put("title", string(source.get("title"), "量表") + " 副本");
    payload.put("code", string(source.get("code"), "scale") + "-copy-" + System.currentTimeMillis());
    payload.put("status", "draft");
    payload.put("questions", source.get("questions"));
    payload.put("dimensions", source.get("dimensions"));
    saveSurveyBase(cloneId, payload, authUser, true);
    replaceSurveyChildren(cloneId, payload);
    return loadSurveyDetail(cloneId);
  }

  @Transactional
  public Map<String, Object> createDistributionPlan(Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    String category = string(payload.get("assessment_category"), "scale");
    if ("neuropsych".equals(category)) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "神经心理测评暂未开放，当前仅支持量表类型分发");
    }
    if (!"scale".equals(category)) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "不支持的测评类型");
    }
    List<String> surveyIds = stringList(payload.get("survey_ids"));
    List<String> userIds = stringList(firstNonNull(payload.get("recipient_user_ids"), payload.get("user_ids")));
    if (surveyIds.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择已发布量表");
    }
    if (userIds.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择患者");
    }
    for (String surveyId : surveyIds) {
      Map<String, Object> survey = one("SELECT id, status FROM scale_surveys WHERE id = :id", Map.of("id", surveyId));
      if (survey == null || !"published".equals(survey.get("status"))) {
        throw new ApiException(HttpStatus.BAD_REQUEST, "只能分发已发布量表");
      }
    }
    List<String> validUsers = query("""
        SELECT id FROM profiles
        WHERE role = 'user' AND id IN (:ids)
        """, Map.of("ids", userIds)).stream().map(row -> string(row.get("id"), "")).toList();
    if (validUsers.size() != userIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "患者列表中存在无效用户");
    }

    String planId = uuid();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO scale_distribution_plans (
          id, title, assessment_category, survey_ids, recipient_type, recipient_scope, cover_url,
          start_at, end_at, status, created_by, created_at, updated_at
        ) VALUES (
          :id, :title, :category, CAST(:surveyIds AS JSON), 'users', CAST(:scope AS JSON), :coverUrl,
          :startAt, :endAt, 'active', :createdBy, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", planId)
            .addValue("title", requiredString(payload, "title", "请填写分发主题"))
            .addValue("category", category)
            .addValue("surveyIds", toJson(surveyIds))
            .addValue("scope", toJson(Map.of("user_ids", validUsers)))
            .addValue("coverUrl", nullableString(payload.get("cover_url")))
            .addValue("startAt", timestamp(payload.get("start_at")))
            .addValue("endAt", timestamp(payload.get("end_at")))
            .addValue("createdBy", authUser.id())
            .addValue("now", Timestamp.from(now))
    );

    for (String userId : validUsers) {
      for (String surveyId : surveyIds) {
        jdbcTemplate.update("""
            INSERT IGNORE INTO scale_distribution_records (
              id, plan_id, survey_id, user_id, assessment_category, status, calc_status, sent_at, created_at, updated_at
            ) VALUES (
              :id, :planId, :surveyId, :userId, 'scale', 'pending', 'none', :now, :now, :now
            )
            """,
            new MapSqlParameterSource()
                .addValue("id", uuid())
                .addValue("planId", planId)
                .addValue("surveyId", surveyId)
                .addValue("userId", userId)
                .addValue("now", Timestamp.from(now))
        );
      }
    }
    return getDistributionPlan(planId, authUser);
  }

  public List<Map<String, Object>> listDistributionPlans(AuthUser authUser) {
    requireStaff(authUser);
    return query("""
        SELECT p.*,
          (SELECT COUNT(*) FROM scale_distribution_records r WHERE r.plan_id = p.id) AS record_count,
          (SELECT COUNT(*) FROM scale_distribution_records r WHERE r.plan_id = p.id AND r.status = 'completed') AS completed_count
        FROM scale_distribution_plans p
        ORDER BY p.created_at DESC
        """, Map.of());
  }

  public Map<String, Object> getDistributionPlan(String planId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> plan = one("SELECT * FROM scale_distribution_plans WHERE id = :id", Map.of("id", planId));
    if (plan == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "分发计划不存在");
    }
    plan.put("records", queryRecords("WHERE r.plan_id = :planId", Map.of("planId", planId)));
    return plan;
  }

  @Transactional
  public Map<String, Object> stopDistributionPlan(String planId, AuthUser authUser) {
    requireStaff(authUser);
    jdbcTemplate.update("""
        UPDATE scale_distribution_plans SET status = 'stopped', updated_at = :now WHERE id = :id
        """, new MapSqlParameterSource().addValue("id", planId).addValue("now", Timestamp.from(Instant.now())));
    jdbcTemplate.update("""
        UPDATE scale_distribution_records
        SET status = 'cancelled', updated_at = :now
        WHERE plan_id = :id AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource().addValue("id", planId).addValue("now", Timestamp.from(Instant.now())));
    return getDistributionPlan(planId, authUser);
  }

  public List<Map<String, Object>> listResults(Map<String, Object> filters, AuthUser authUser) {
    requireStaff(authUser);
    List<String> clauses = new ArrayList<>();
    Map<String, Object> params = new LinkedHashMap<>();
    addEqFilter(clauses, params, filters, "survey_id", "r.survey_id");
    addEqFilter(clauses, params, filters, "user_id", "r.user_id");
    addEqFilter(clauses, params, filters, "status", "r.status");
    addEqFilter(clauses, params, filters, "calc_status", "r.calc_status");
    addEqFilter(clauses, params, filters, "warning_level", "r.warning_level");
    String where = clauses.isEmpty() ? "" : "WHERE " + String.join(" AND ", clauses);
    return queryRecords(where, params);
  }

  public Map<String, Object> getResult(String recordId, AuthUser authUser) {
    requireStaff(authUser);
    return loadRecordDetail(recordId, null, true);
  }

  public List<Map<String, Object>> myRecords(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    return queryRecords("WHERE r.user_id = :userId", Map.of("userId", user.id()));
  }

  @Transactional
  public Map<String, Object> startFreeRecord(String surveyCode, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> survey = one("""
        SELECT * FROM scale_surveys
        WHERE (code = :code OR id = :code)
          AND status = 'published'
          AND self_test_enabled = TRUE
        """, Map.of("code", surveyCode));
    if (survey == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "该量表未开放自由测评");
    }
    String recordId = uuid();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO scale_distribution_records (
          id, plan_id, survey_id, user_id, assessment_category, source_type, status, calc_status, sent_at, started_at, created_at, updated_at
        ) VALUES (
          :id, NULL, :surveyId, :userId, 'scale', 'self', 'in_progress', 'none', :now, :now, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("surveyId", survey.get("id"))
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now))
    );
    return loadRecordDetail(recordId, user.id(), true);
  }

  public Map<String, Object> getMyRecord(String recordId, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    return loadRecordDetail(recordId, user.id(), true);
  }

  @Transactional
  public Map<String, Object> startRecord(String recordId, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> record = loadRecordHeader(recordId, user.id());
    assertNotExpired(record);
    if ("completed".equals(record.get("status"))) {
      return loadRecordDetail(recordId, user.id(), true);
    }
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE scale_distribution_records
        SET status = 'in_progress',
            started_at = COALESCE(started_at, :now),
            updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now))
    );
    updatePublishItemForScale(recordId, "in_progress", now);
    return loadRecordDetail(recordId, user.id(), true);
  }

  @Transactional
  public Map<String, Object> submitRecord(String recordId, Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> record = loadRecordHeader(recordId, user.id());
    assertNotExpired(record);
    if ("completed".equals(record.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评已提交");
    }
    List<Map<String, Object>> answers = list(payload.get("answers"));
    if (answers.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "答案不能为空");
    }
    Instant now = Instant.now();
    Timestamp startedAt = record.get("started_at") instanceof Timestamp timestamp ? timestamp : Timestamp.from(now);
    long duration = Math.max(0, Duration.between(startedAt.toInstant(), now).toSeconds());
    jdbcTemplate.update("""
        UPDATE scale_distribution_records
        SET status = 'completed',
            calc_status = 'waiting',
            completed_at = :now,
            started_at = COALESCE(started_at, :now),
            answer_duration_sec = :duration,
            answers_json = CAST(:answers AS JSON),
            updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("userId", user.id())
            .addValue("duration", duration)
            .addValue("answers", toJson(answers))
            .addValue("now", Timestamp.from(now))
    );
    calculateRecord(recordId);
    return loadRecordDetail(recordId, user.id(), true);
  }

  @Transactional
  public Map<String, Object> recalculateRecord(String recordId, AuthUser authUser) {
    requireStaff(authUser);
    calculateRecord(recordId);
    return loadRecordDetail(recordId, null, true);
  }

  public Map<String, Object> exportResults(Map<String, Object> filters, boolean unfinished, AuthUser authUser) {
    requireStaff(authUser);
    List<Map<String, Object>> rows = unfinished
        ? queryRecords("WHERE r.status <> 'completed'", Map.of())
        : listResults(filters == null ? Map.of() : filters, authUser);
    StringBuilder csv = new StringBuilder("患者,量表,主题,状态,计算状态,总分,预警,完成时间\n");
    for (Map<String, Object> row : rows) {
      csv.append(csv(row.get("patient_name"))).append(',')
          .append(csv(row.get("survey_title"))).append(',')
          .append(csv(row.get("plan_title"))).append(',')
          .append(csv(row.get("status"))).append(',')
          .append(csv(row.get("calc_status"))).append(',')
          .append(csv(row.get("total_score"))).append(',')
          .append(csv(row.get("warning_level"))).append(',')
          .append(csv(row.get("completed_at"))).append('\n');
    }
    return Map.of("filename", unfinished ? "scale-unfinished.csv" : "scale-results.csv", "content", csv.toString());
  }

  @Transactional
  public Map<String, Object> importAnswers(Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    List<Map<String, Object>> records = list(payload.get("records"));
    if (records.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "没有可导入的答案");
    }
    int imported = 0;
    for (Map<String, Object> item : records) {
      String recordId = string(firstNonNull(item.get("record_id"), item.get("recordId")), "");
      List<Map<String, Object>> answers = list(item.get("answers"));
      if (recordId.isBlank() || answers.isEmpty()) {
        continue;
      }
      Map<String, Object> record = loadRecordHeader(recordId, null);
      if ("cancelled".equals(record.get("status")) || "expired".equals(record.get("status"))) {
        continue;
      }
      jdbcTemplate.update("""
          UPDATE scale_distribution_records
          SET status = 'completed',
              calc_status = 'waiting',
              completed_at = :now,
              started_at = COALESCE(started_at, :now),
              answer_duration_sec = COALESCE(answer_duration_sec, 0),
              answers_json = CAST(:answers AS JSON),
              updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("answers", toJson(answers))
              .addValue("now", Timestamp.from(Instant.now()))
      );
      calculateRecord(recordId);
      imported++;
    }
    return Map.of("imported", imported);
  }

  private void calculateRecord(String recordId) {
    try {
      Map<String, Object> record = loadRecordHeader(recordId, null);
      Object rawAnswers = parseJsonField(record.get("answers_json"));
      List<Map<String, Object>> submittedAnswers = list(rawAnswers);
      if (submittedAnswers.isEmpty()) {
        throw new ApiException(HttpStatus.BAD_REQUEST, "没有可计算的答案");
      }
      Map<String, Object> survey = loadSurveyDetail(string(record.get("survey_id"), ""));
      Map<String, Object> snapshot = record.get("survey_json") == null
          ? buildSurveySnapshot(survey)
          : map(parseJsonField(record.get("survey_json")));
      List<Map<String, Object>> questions = list(snapshot.get("questions"));
      List<Map<String, Object>> dimensions = list(snapshot.get("dimensions"));
      Map<String, Map<String, Object>> answerMap = submittedAnswers.stream().collect(Collectors.toMap(
          answer -> string(firstNonNull(answer.get("questionId"), answer.get("question_id")), ""),
          answer -> answer,
          (first, ignored) -> first,
          LinkedHashMap::new
      ));

      jdbcTemplate.update("DELETE FROM scale_answers WHERE record_id = :id", new MapSqlParameterSource("id", recordId));
      jdbcTemplate.update("DELETE FROM scale_record_dimensions WHERE record_id = :id", new MapSqlParameterSource("id", recordId));

      Map<String, Double> variables = new LinkedHashMap<>();
      String gender = string(record.get("gender"), "");
      variables.put("hx_gender", gender.contains("男") ? 1D : gender.contains("女") ? 2D : 0D);
      List<Map<String, Object>> answerReports = new ArrayList<>();
      for (Map<String, Object> question : questions) {
        String questionId = string(question.get("id"), "");
        Map<String, Object> submitted = answerMap.get(questionId);
        boolean required = bool(question.get("required"), true);
        String myAnswer = submitted == null ? "" : string(firstNonNull(submitted.get("myAnswer"), submitted.get("my_answer")), "");
        if (required && myAnswer.isBlank()) {
          throw new ApiException(HttpStatus.BAD_REQUEST, "存在未完成的必答题: " + question.get("stem"));
        }
        Map<String, Object> scored = scoreAnswer(question, myAnswer);
        double score = number(scored.get("score"));
        variables.put("hx_t_" + intValue(question.get("order_no"), intValue(question.get("orderNo"), 0)), score);
        insertAnswer(recordId, string(record.get("survey_id"), ""), questionId, string(question.get("question_type"), ""), myAnswer, scored);
        answerReports.add(Map.of(
            "questionId", questionId,
            "orderNo", firstNonNull(question.get("order_no"), question.get("orderNo")),
            "stem", question.get("stem"),
            "answerText", scored.get("answer_text"),
            "score", score
        ));
      }

      List<Map<String, Object>> dimensionReports = new ArrayList<>();
      String highestWarning = "none";
      double totalScore = 0;
      for (Map<String, Object> dimension : dimensions.stream()
          .sorted(Comparator.comparingInt(item -> intValue(item.get("num"), 0))).toList()) {
        int num = intValue(dimension.get("num"), 0);
        double raw = ScaleExpressionEvaluator.evaluateNumber(string(dimension.get("raw_score_formula"), "0"), variables);
        variables.put("hx_wd_y_" + num, raw);
        putDimensionCodeVariable(variables, "hx_wd_y_", dimension.get("code"), raw);
        String standardFormula = string(dimension.get("standard_score_formula"), "");
        double standard = standardFormula.isBlank() ? raw : ScaleExpressionEvaluator.evaluateNumber(standardFormula, variables);
        variables.put("hx_wd_b_" + num, standard);
        putDimensionCodeVariable(variables, "hx_wd_b_", dimension.get("code"), standard);
        totalScore += raw;

        List<String> conclusions = new ArrayList<>();
        List<String> suggestions = new ArrayList<>();
        String dimensionWarning = "none";
        for (Map<String, Object> definition : list(dimension.get("result_definitions"))) {
          if (ScaleExpressionEvaluator.evaluateBoolean(string(definition.get("condition_expression"), "0"), variables)) {
            if (!string(definition.get("conclusion"), "").isBlank()) {
              conclusions.add(string(definition.get("conclusion"), ""));
            }
            if (!string(definition.get("suggestion"), "").isBlank()) {
              suggestions.add(string(definition.get("suggestion"), ""));
            }
            dimensionWarning = maxWarning(dimensionWarning, string(definition.get("warning_level"), "none"));
          }
        }
        highestWarning = maxWarning(highestWarning, dimensionWarning);
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("dimensionId", dimension.get("id"));
        report.put("name", dimension.get("name"));
        report.put("code", dimension.get("code"));
        report.put("rawScore", round(raw));
        report.put("standardScore", round(standard));
        report.put("warningLevel", dimensionWarning);
        report.put("conclusion", String.join("\n", conclusions));
        report.put("suggestion", String.join("\n", suggestions));
        insertDimension(recordId, dimension, raw, standard, report);
        dimensionReports.add(report);
      }
      if (dimensions.size() == 1 && !dimensionReports.isEmpty()) {
        totalScore = number(dimensionReports.getFirst().get("rawScore"));
      }

      Map<String, Object> report = new LinkedHashMap<>();
      report.put("surveyId", record.get("survey_id"));
      report.put("surveyTitle", record.get("survey_title"));
      report.put("recordId", recordId);
      report.put("patientId", record.get("user_id"));
      report.put("totalScore", round(totalScore));
      report.put("warningLevel", highestWarning);
      report.put("completedAt", Instant.now().toString());
      report.put("dimensions", dimensionReports);
      report.put("answers", answerReports);
      String assessmentId = syncAssessment(record, report, totalScore, highestWarning);
      syncRiskAlert(record, report, highestWarning);
      jdbcTemplate.update("""
          UPDATE scale_distribution_records
          SET calc_status = 'done',
              calc_error = NULL,
              total_score = :totalScore,
              warning_level = :warning,
              report = CAST(:report AS JSON),
              assessment_id = :assessmentId,
              updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("totalScore", round(totalScore))
              .addValue("warning", highestWarning)
              .addValue("report", toJson(report))
              .addValue("assessmentId", assessmentId)
              .addValue("now", Timestamp.from(Instant.now()))
      );
      updatePublishItemForScale(recordId, "completed", Instant.now());
    } catch (Exception ex) {
      jdbcTemplate.update("""
          UPDATE scale_distribution_records
          SET calc_status = 'error', calc_error = :error, updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("error", ex.getMessage())
              .addValue("now", Timestamp.from(Instant.now()))
      );
      if (ex instanceof ApiException apiException) {
        throw apiException;
      }
      throw new ApiException(HttpStatus.BAD_REQUEST, "量表计算失败: " + ex.getMessage());
    }
  }

  private void updatePublishItemForScale(String recordId, String status, Instant now) {
    Map<String, Object> itemRecord = one("""
        SELECT * FROM assessment_publish_item_records
        WHERE result_ref_table = 'scale_distribution_records' AND result_ref_id = :recordId
        LIMIT 1
        """, Map.of("recordId", recordId));
    if (itemRecord == null) {
      return;
    }
    jdbcTemplate.update("""
        UPDATE assessment_publish_item_records
        SET status = :status,
            started_at = CASE WHEN :status IN ('in_progress','completed') THEN COALESCE(started_at, :now) ELSE started_at END,
            completed_at = CASE WHEN :status = 'completed' THEN :now ELSE completed_at END,
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", itemRecord.get("id"))
            .addValue("status", status)
            .addValue("now", Timestamp.from(now))
    );
    refreshPublishAssignee(string(itemRecord.get("assignee_id"), ""));
  }

  private void refreshPublishAssignee(String assigneeId) {
    if (assigneeId.isBlank()) {
      return;
    }
    List<Map<String, Object>> siblings = query(
        "SELECT status FROM assessment_publish_item_records WHERE assignee_id = :id",
        Map.of("id", assigneeId)
    );
    boolean completed = !siblings.isEmpty() && siblings.stream()
        .allMatch(row -> "completed".equals(row.get("status")) || "unsupported".equals(row.get("status")));
    boolean started = siblings.stream().anyMatch(row -> !"pending".equals(row.get("status")));
    String status = completed ? "completed" : started ? "in_progress" : "pending";
    jdbcTemplate.update("""
        UPDATE assessment_publish_assignees
        SET status = :status,
            started_at = CASE WHEN :started THEN COALESCE(started_at, :now) ELSE started_at END,
            completed_at = CASE WHEN :completed THEN :now ELSE completed_at END,
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", assigneeId)
            .addValue("status", status)
            .addValue("started", started)
            .addValue("completed", completed)
            .addValue("now", Timestamp.from(Instant.now()))
    );
  }

  private void saveSurveyBase(String surveyId, Map<String, Object> payload, AuthUser authUser, boolean inserting) {
    String code = string(payload.get("code"), "").trim();
    if (code.isBlank()) {
      code = "scale-" + System.currentTimeMillis();
    }
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", surveyId)
        .addValue("code", code)
        .addValue("title", requiredString(payload, "title", "请填写量表标题"))
        .addValue("description", nullableString(payload.get("description")))
        .addValue("coverUrl", nullableString(payload.get("cover_url")))
        .addValue("surveyType", nullableString(payload.get("survey_type")))
        .addValue("status", string(payload.get("status"), "draft"))
        .addValue("selfTestEnabled", bool(payload.get("self_test_enabled"), false))
        .addValue("sortOrder", payload.containsKey("sort_order") ? intValue(payload.get("sort_order"), 0) : null)
        .addValue("createdBy", authUser.id())
        .addValue("now", Timestamp.from(Instant.now()));
    if (inserting) {
      jdbcTemplate.update("""
          INSERT INTO scale_surveys (
            id, code, title, description, cover_url, survey_type, status, self_test_enabled, created_by, created_at, updated_at
          ) VALUES (
            :id, :code, :title, :description, :coverUrl, :surveyType, :status, :selfTestEnabled, :createdBy, :now, :now
          )
          """, params);
    } else {
      jdbcTemplate.update("""
          UPDATE scale_surveys
          SET code = :code,
              title = :title,
              description = :description,
              cover_url = :coverUrl,
              survey_type = :surveyType,
              self_test_enabled = :selfTestEnabled,
              sort_order = COALESCE(:sortOrder, sort_order),
              updated_at = :now
          WHERE id = :id
          """, params);
    }
  }

  private void replaceSurveyChildren(String surveyId, Map<String, Object> payload) {
    jdbcTemplate.update("DELETE rd FROM scale_result_definitions rd JOIN scale_dimensions d ON d.id = rd.dimension_id WHERE d.survey_id = :id", new MapSqlParameterSource("id", surveyId));
    jdbcTemplate.update("DELETE FROM scale_dimensions WHERE survey_id = :id", new MapSqlParameterSource("id", surveyId));
    jdbcTemplate.update("DELETE o FROM scale_options o JOIN scale_questions q ON q.id = o.question_id WHERE q.survey_id = :id", new MapSqlParameterSource("id", surveyId));
    jdbcTemplate.update("DELETE FROM scale_questions WHERE survey_id = :id", new MapSqlParameterSource("id", surveyId));
    for (Map<String, Object> question : list(payload.get("questions"))) {
      String questionId = string(question.get("id"), uuid());
      jdbcTemplate.update("""
          INSERT INTO scale_questions (id, survey_id, question_type, stem, media_url, order_no, required)
          VALUES (:id, :surveyId, :type, :stem, :mediaUrl, :orderNo, :required)
          """,
          new MapSqlParameterSource()
              .addValue("id", questionId)
              .addValue("surveyId", surveyId)
              .addValue("type", string(firstNonNull(question.get("question_type"), question.get("questionType")), "radio"))
              .addValue("stem", requiredString(question, "stem", "题干不能为空"))
              .addValue("mediaUrl", nullableString(question.get("media_url")))
              .addValue("orderNo", intValue(firstNonNull(question.get("order_no"), question.get("orderNo")), 1))
              .addValue("required", bool(question.get("required"), true))
      );
      for (Map<String, Object> option : list(question.get("options"))) {
        jdbcTemplate.update("""
            INSERT INTO scale_options (id, question_id, option_no, label, value, order_no, media_url)
            VALUES (:id, :questionId, :optionNo, :label, :value, :orderNo, :mediaUrl)
            """,
            new MapSqlParameterSource()
                .addValue("id", string(option.get("id"), uuid()))
                .addValue("questionId", questionId)
                .addValue("optionNo", string(firstNonNull(option.get("option_no"), option.get("optionNo")), ""))
                .addValue("label", requiredString(option, "label", "选项文本不能为空"))
                .addValue("value", number(option.get("value")))
                .addValue("orderNo", intValue(firstNonNull(option.get("order_no"), option.get("orderNo")), 1))
                .addValue("mediaUrl", nullableString(option.get("media_url")))
        );
      }
    }
    for (Map<String, Object> dimension : list(payload.get("dimensions"))) {
      String dimensionId = string(dimension.get("id"), uuid());
      jdbcTemplate.update("""
          INSERT INTO scale_dimensions (
            id, survey_id, name, code, num, raw_score_formula, standard_score_formula,
            show_in_full_report, show_in_user_report, show_chart
          ) VALUES (
            :id, :surveyId, :name, :code, :num, :rawFormula, :standardFormula,
            :showFull, :showUser, :showChart
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", dimensionId)
              .addValue("surveyId", surveyId)
              .addValue("name", requiredString(dimension, "name", "维度名称不能为空"))
              .addValue("code", nullableString(dimension.get("code")))
              .addValue("num", intValue(dimension.get("num"), 1))
              .addValue("rawFormula", blankToDefault(dimension.get("raw_score_formula"), "0"))
              .addValue("standardFormula", nullableString(dimension.get("standard_score_formula")))
              .addValue("showFull", bool(dimension.get("show_in_full_report"), true))
              .addValue("showUser", bool(dimension.get("show_in_user_report"), true))
              .addValue("showChart", bool(dimension.get("show_chart"), false))
      );
      Object definitions = firstNonNull(dimension.get("result_definitions"), dimension.get("resultDefinitions"));
      for (Map<String, Object> definition : list(definitions)) {
        jdbcTemplate.update("""
            INSERT INTO scale_result_definitions (
              id, dimension_id, condition_expression, conclusion, suggestion, warning_level, order_no
            ) VALUES (
              :id, :dimensionId, :condition, :conclusion, :suggestion, :warning, :orderNo
            )
            """,
            new MapSqlParameterSource()
                .addValue("id", string(definition.get("id"), uuid()))
                .addValue("dimensionId", dimensionId)
                .addValue("condition", requiredString(definition, "condition_expression", "结果命中条件不能为空"))
                .addValue("conclusion", nullableString(definition.get("conclusion")))
                .addValue("suggestion", nullableString(definition.get("suggestion")))
                .addValue("warning", string(definition.get("warning_level"), "none"))
                .addValue("orderNo", intValue(firstNonNull(definition.get("order_no"), definition.get("orderNo")), 0))
        );
      }
    }
  }

  private Map<String, Object> loadSurveyDetail(String surveyId) {
    Map<String, Object> survey = one("SELECT * FROM scale_surveys WHERE id = :id", Map.of("id", surveyId));
    if (survey == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "量表不存在");
    }
    List<Map<String, Object>> questions = query(
        "SELECT * FROM scale_questions WHERE survey_id = :id ORDER BY order_no ASC",
        Map.of("id", surveyId)
    );
    for (Map<String, Object> question : questions) {
      question.put("options", query(
          "SELECT * FROM scale_options WHERE question_id = :id ORDER BY order_no ASC",
          Map.of("id", question.get("id"))
      ));
    }
    List<Map<String, Object>> dimensions = query(
        "SELECT * FROM scale_dimensions WHERE survey_id = :id ORDER BY num ASC",
        Map.of("id", surveyId)
    );
    for (Map<String, Object> dimension : dimensions) {
      dimension.put("result_definitions", query(
          "SELECT * FROM scale_result_definitions WHERE dimension_id = :id ORDER BY order_no ASC",
          Map.of("id", dimension.get("id"))
      ));
    }
    survey.put("questions", questions);
    survey.put("dimensions", dimensions);
    return survey;
  }

  private Map<String, Object> buildSurveySnapshot(Map<String, Object> detail) {
    Map<String, Object> snapshot = new LinkedHashMap<>();
    for (String key : List.of("id", "code", "title", "description", "cover_url", "survey_type", "version")) {
      snapshot.put(key, detail.get(key));
    }
    snapshot.put("questions", detail.get("questions"));
    snapshot.put("dimensions", detail.get("dimensions"));
    return snapshot;
  }

  private Map<String, Object> loadRecordHeader(String recordId, String userId) {
    List<String> clauses = new ArrayList<>(List.of("r.id = :id"));
    Map<String, Object> params = new LinkedHashMap<>();
    params.put("id", recordId);
    if (userId != null) {
      clauses.add("r.user_id = :userId");
      params.put("userId", userId);
    }
    Map<String, Object> record = queryRecords("WHERE " + String.join(" AND ", clauses), params).stream().findFirst().orElse(null);
    if (record == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "测评任务不存在");
    }
    return record;
  }

  private Map<String, Object> loadRecordDetail(String recordId, String userId, boolean includeSurvey) {
    Map<String, Object> record = loadRecordHeader(recordId, userId);
    record.put("answers", query("SELECT * FROM scale_answers WHERE record_id = :id ORDER BY created_at ASC", Map.of("id", recordId)));
    record.put("dimensions", query("SELECT * FROM scale_record_dimensions WHERE record_id = :id ORDER BY created_at ASC", Map.of("id", recordId)));
    if (includeSurvey) {
      Object snapshot = parseJsonField(record.get("survey_json"));
      record.put("survey", snapshot == null ? buildSurveySnapshot(loadSurveyDetail(string(record.get("survey_id"), ""))) : snapshot);
    }
    return record;
  }

  private List<Map<String, Object>> queryRecords(String where, Map<String, Object> params) {
    return query("""
        SELECT r.*, COALESCE(p.title, '自由测评') AS plan_title, p.start_at, p.end_at, s.title AS survey_title, s.code AS survey_code,
               s.survey_json, pr.username AS patient_username, pr.full_name AS patient_full_name, pr.gender,
               COALESCE(pr.full_name, pr.username) AS patient_name
        FROM scale_distribution_records r
        LEFT JOIN scale_distribution_plans p ON p.id = r.plan_id
        JOIN scale_surveys s ON s.id = r.survey_id
        JOIN profiles pr ON pr.id = r.user_id
        """ + (where == null || where.isBlank() ? "" : " " + where) + " ORDER BY r.created_at DESC",
        params
    );
  }

  private Map<String, Object> scoreAnswer(Map<String, Object> question, String myAnswer) {
    String type = string(question.get("question_type"), "");
    if ("radio".equals(type)) {
      Map<String, Object> option = list(question.get("options")).stream()
          .filter(item -> Objects.equals(string(item.get("id"), ""), myAnswer))
          .findFirst()
          .orElse(Map.of());
      return Map.of(
          "score", number(option.get("value")),
          "answer_text", string(option.get("label"), ""),
          "option_no", string(option.get("option_no"), "")
      );
    }
    if ("checkbox".equals(type)) {
      List<String> ids = Arrays.stream(myAnswer.split(",")).map(String::trim).filter(value -> !value.isBlank()).toList();
      List<Map<String, Object>> selected = list(question.get("options")).stream()
          .filter(item -> ids.contains(string(item.get("id"), "")))
          .toList();
      return Map.of(
          "score", 0D,
          "answer_text", selected.stream().map(item -> string(item.get("label"), "")).collect(Collectors.joining(",")),
          "option_no", selected.stream().map(item -> string(item.get("option_no"), "")).collect(Collectors.joining(","))
      );
    }
    return Map.of("score", 0D, "answer_text", myAnswer, "option_no", "");
  }

  private void insertAnswer(String recordId, String surveyId, String questionId, String questionType, String myAnswer, Map<String, Object> scored) {
    jdbcTemplate.update("""
        INSERT INTO scale_answers (
          id, record_id, survey_id, question_id, question_type, my_answer, answer_text, option_no, score
        ) VALUES (
          :id, :recordId, :surveyId, :questionId, :questionType, :myAnswer, :answerText, :optionNo, :score
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", uuid())
            .addValue("recordId", recordId)
            .addValue("surveyId", surveyId)
            .addValue("questionId", questionId)
            .addValue("questionType", questionType)
            .addValue("myAnswer", myAnswer)
            .addValue("answerText", scored.get("answer_text"))
            .addValue("optionNo", scored.get("option_no"))
            .addValue("score", scored.get("score"))
    );
  }

  private void insertDimension(String recordId, Map<String, Object> dimension, double raw, double standard, Map<String, Object> report) {
    jdbcTemplate.update("""
        INSERT INTO scale_record_dimensions (
          id, record_id, dimension_id, dimension_name, dimension_code, raw_score, standard_score,
          conclusion, suggestion, warning_level
        ) VALUES (
          :id, :recordId, :dimensionId, :dimensionName, :dimensionCode, :rawScore, :standardScore,
          :conclusion, :suggestion, :warning
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", uuid())
            .addValue("recordId", recordId)
            .addValue("dimensionId", dimension.get("id"))
            .addValue("dimensionName", dimension.get("name"))
            .addValue("dimensionCode", dimension.get("code"))
            .addValue("rawScore", round(raw))
            .addValue("standardScore", round(standard))
            .addValue("conclusion", report.get("conclusion"))
            .addValue("suggestion", report.get("suggestion"))
            .addValue("warning", report.get("warningLevel"))
    );
  }

  private void putDimensionCodeVariable(Map<String, Double> variables, String prefix, Object codeValue, double score) {
    String code = string(codeValue, "").trim();
    if (code.isBlank()) {
      return;
    }
    variables.put(prefix + code, score);
    variables.put(prefix + code.toLowerCase(Locale.ROOT), score);
    variables.put(prefix + code.toUpperCase(Locale.ROOT), score);
  }

  private String syncAssessment(Map<String, Object> record, Map<String, Object> report, double totalScore, String warning) {
    String existingId = string(record.get("assessment_id"), "");
    String assessmentId = existingId.isBlank() ? uuid() : existingId;
    int riskLevel = warningRisk(warning);
    Map<String, Object> assessmentReport = Map.of(
        "scaleData", Map.of(
            "source", "scale_assessment",
            "recordId", record.get("id"),
            "surveyId", record.get("survey_id"),
            "surveyTitle", record.get("survey_title"),
            "score", round(totalScore),
            "warningLevel", warning,
            "dimensionScores", report.get("dimensions")
        ),
        "summary", "量表测评完成，风险等级：" + warningText(warning)
    );
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", assessmentId)
        .addValue("userId", record.get("user_id"))
        .addValue("score", Math.round(totalScore))
        .addValue("riskLevel", riskLevel)
        .addValue("report", toJson(assessmentReport))
        .addValue("now", Timestamp.from(Instant.now()));
    if (existingId.isBlank()) {
      jdbcTemplate.update("""
          INSERT INTO assessments (
            id, user_id, assessment_type, risk_level, score, report, created_at, updated_at
          ) VALUES (
            :id, :userId, 'scale_assessment', :riskLevel, :score, CAST(:report AS JSON), :now, :now
          )
          """, params);
    } else {
      jdbcTemplate.update("""
          UPDATE assessments
          SET risk_level = :riskLevel, score = :score, report = CAST(:report AS JSON), updated_at = :now
          WHERE id = :id
          """, params);
    }
    return assessmentId;
  }

  private void syncRiskAlert(Map<String, Object> record, Map<String, Object> report, String warning) {
    int risk = warningRisk(warning);
    if (risk < 6) {
      return;
    }
    Map<String, Object> existing = one("""
        SELECT id FROM risk_alerts WHERE data_source = 'scale_assessment' AND source_id = :sourceId LIMIT 1
        """, Map.of("sourceId", record.get("id")));
    String description = "量表《" + record.get("survey_title") + "》结果为" + warningText(warning)
        + "，总分 " + report.get("totalScore") + "。建议医生查看量表报告并进行随访。";
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", existing == null ? uuid() : existing.get("id"))
        .addValue("patientId", record.get("user_id"))
        .addValue("risk", risk)
        .addValue("description", description)
        .addValue("sourceId", record.get("id"))
        .addValue("now", Timestamp.from(Instant.now()));
    if (existing == null) {
      jdbcTemplate.update("""
          INSERT INTO risk_alerts (
            id, patient_id, alert_type, risk_level, description, data_source, source_id, is_handled, created_at
          ) VALUES (
            :id, :patientId, '量表测评预警', :risk, :description, 'scale_assessment', :sourceId, false, :now
          )
          """, params);
    } else {
      jdbcTemplate.update("""
          UPDATE risk_alerts
          SET risk_level = :risk, description = :description, is_handled = false
          WHERE id = :id
          """, params);
    }
  }

  private List<Map<String, Object>> query(String sql, Map<String, ?> params) {
    return jdbcTemplate.query(sql, new MapSqlParameterSource(params), new ColumnMapRowMapper())
        .stream()
        .map(this::normalizeRow)
        .toList();
  }

  private Map<String, Object> one(String sql, Map<String, ?> params) {
    return query(sql, params).stream().findFirst().orElse(null);
  }

  private void ensureExists(String sql, Map<String, ?> params, String message) {
    if (one(sql, params) == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, message);
    }
  }

  private Map<String, Object> normalizeRow(Map<String, Object> row) {
    Map<String, Object> normalized = new LinkedHashMap<>();
    row.forEach((key, value) -> {
      String normalizedKey = key.toLowerCase(Locale.ROOT);
      if (value instanceof Timestamp timestamp) {
        normalized.put(normalizedKey, timestamp.toInstant().toString());
      } else if (value instanceof BigDecimal decimal) {
        normalized.put(normalizedKey, decimal.doubleValue());
      } else if (List.of("survey_json", "survey_ids", "recipient_scope", "answers_json", "report").contains(normalizedKey)) {
        normalized.put(normalizedKey, parseJsonField(value));
      } else {
        normalized.put(normalizedKey, value);
      }
    });
    return normalized;
  }

  private Object parseJsonField(Object value) {
    if (value == null) {
      return null;
    }
    if (!(value instanceof String text)) {
      return value;
    }
    if (text.isBlank()) {
      return null;
    }
    try {
      return objectMapper.readValue(text, new TypeReference<Object>() {});
    } catch (JsonProcessingException ignored) {
      return value;
    }
  }

  private void assertNotExpired(Map<String, Object> record) {
    Object endAt = record.get("end_at");
    if (endAt instanceof String value && !value.isBlank() && Instant.parse(value).isBefore(Instant.now())) {
      jdbcTemplate.update("""
          UPDATE scale_distribution_records
          SET status = 'expired', updated_at = :now
          WHERE id = :id AND status <> 'completed'
          """,
          new MapSqlParameterSource()
              .addValue("id", record.get("id"))
              .addValue("now", Timestamp.from(Instant.now()))
      );
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评已过期");
    }
  }

  private AuthUser requireStaff(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可操作");
    }
    return user;
  }

  private void addEqFilter(List<String> clauses, Map<String, Object> params, Map<String, Object> filters, String key, String column) {
    if (filters != null && filters.get(key) != null && !String.valueOf(filters.get(key)).isBlank()) {
      clauses.add(column + " = :" + key);
      params.put(key, filters.get(key));
    }
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

  @SuppressWarnings("unchecked")
  private Map<String, Object> map(Object value) {
    return value instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
  }

  private List<String> stringList(Object value) {
    if (value instanceof Collection<?> collection) {
      return collection.stream().map(item -> string(item, "")).filter(item -> !item.isBlank()).distinct().toList();
    }
    if (value instanceof String text && !text.isBlank()) {
      return Arrays.stream(text.split(",")).map(String::trim).filter(item -> !item.isBlank()).distinct().toList();
    }
    return List.of();
  }

  private String toJson(Object value) {
    try {
      return objectMapper.writeValueAsString(value);
    } catch (JsonProcessingException e) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "JSON 序列化失败");
    }
  }

  private String requiredString(Map<String, Object> payload, String key, String message) {
    String value = string(payload.get(key), "").trim();
    if (value.isBlank()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, message);
    }
    return value;
  }

  private String nullableString(Object value) {
    String text = string(value, "").trim();
    return text.isBlank() ? null : text;
  }

  private String blankToDefault(Object value, String fallback) {
    String text = string(value, "").trim();
    return text.isBlank() ? fallback : text;
  }

  private String string(Object value, String fallback) {
    return value == null ? fallback : String.valueOf(value);
  }

  private boolean bool(Object value, boolean fallback) {
    return value == null ? fallback : Boolean.parseBoolean(String.valueOf(value));
  }

  private int intValue(Object value, int fallback) {
    if (value instanceof Number number) {
      return number.intValue();
    }
    try {
      return value == null ? fallback : Integer.parseInt(String.valueOf(value));
    } catch (NumberFormatException ex) {
      return fallback;
    }
  }

  private double number(Object value) {
    if (value instanceof Number number) {
      return number.doubleValue();
    }
    try {
      return value == null || String.valueOf(value).isBlank() ? 0D : Double.parseDouble(String.valueOf(value));
    } catch (NumberFormatException ex) {
      return 0D;
    }
  }

  private double round(double value) {
    return Math.round(value * 100D) / 100D;
  }

  private Timestamp timestamp(Object value) {
    if (value == null || String.valueOf(value).isBlank()) {
      return null;
    }
    return Timestamp.from(Instant.parse(String.valueOf(value)));
  }

  private Object firstNonNull(Object first, Object second) {
    return first != null ? first : second;
  }

  private String uuid() {
    return UUID.randomUUID().toString();
  }

  private int warningRank(String warning) {
    return switch (string(warning, "none")) {
      case "high" -> 3;
      case "middle" -> 2;
      case "low" -> 1;
      default -> 0;
    };
  }

  private String maxWarning(String current, String candidate) {
    return warningRank(candidate) > warningRank(current) ? candidate : current;
  }

  private int warningRisk(String warning) {
    return switch (string(warning, "none")) {
      case "high" -> 9;
      case "middle" -> 6;
      case "low" -> 3;
      default -> 0;
    };
  }

  private String warningText(String warning) {
    return switch (string(warning, "none")) {
      case "high" -> "高风险";
      case "middle" -> "中风险";
      case "low" -> "低风险";
      default -> "无明显风险";
    };
  }

  private String csv(Object value) {
    String text = value == null ? "" : String.valueOf(value);
    return "\"" + text.replace("\"", "\"\"") + "\"";
  }
}
