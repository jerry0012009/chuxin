package chuxin.neuropsych;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthService;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.ColumnMapRowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class NeuropsychAssessmentService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;
  private final AuthService authService;
  private final NeuropsychMetricsCalculator calculator;

  public NeuropsychAssessmentService(
      NamedParameterJdbcTemplate jdbcTemplate,
      ObjectMapper objectMapper,
      AuthService authService,
      NeuropsychMetricsCalculator calculator) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
    this.authService = authService;
    this.calculator = calculator;
  }

  public List<Map<String, Object>> listTests(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (user.isStaff()) {
      return query("""
          SELECT t.*,
            (SELECT COUNT(*) FROM neuropsych_records r WHERE r.test_id = t.id) AS record_count,
            (SELECT COUNT(*) FROM neuropsych_records r WHERE r.test_id = t.id AND r.status = 'completed') AS completed_count
          FROM neuropsych_tests t
          ORDER BY t.estimated_minutes ASC, t.created_at ASC
          """, Map.of());
    }
    return query("""
        SELECT * FROM neuropsych_tests
        WHERE status = 'active'
        ORDER BY estimated_minutes ASC, created_at ASC
        """, Map.of());
  }

  public List<Map<String, Object>> listFreeTests(AuthUser authUser) {
    authService.requireUser(authUser);
    return query("""
        SELECT * FROM neuropsych_tests
        WHERE status = 'active' AND self_test_enabled = TRUE
        ORDER BY estimated_minutes ASC, created_at ASC
        """, Map.of());
  }

  @Transactional
  public Map<String, Object> updateTest(String testId, Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", testId)
        .addValue("title", string(payload.get("title")))
        .addValue("description", nullableString(payload.get("description")))
        .addValue("dimension", nullableString(payload.get("dimension")))
        .addValue("clinicalMeaning", nullableString(payload.get("clinical_meaning")))
        .addValue("estimatedMinutes", intValue(payload.get("estimated_minutes"), 0))
        .addValue("status", normalizeStatus(string(payload.get("status"))))
        .addValue("selfTestEnabled", bool(payload.get("self_test_enabled"), false))
        .addValue("configJson", toJson(firstNonNull(payload.get("config_json"), Map.of())))
        .addValue("metricSchemaJson", toJson(firstNonNull(payload.get("metric_schema_json"), Map.of())))
        .addValue("now", Timestamp.from(Instant.now()));
    int updated = jdbcTemplate.update("""
        UPDATE neuropsych_tests
        SET title = COALESCE(NULLIF(:title, ''), title),
            description = :description,
            dimension = :dimension,
            clinical_meaning = :clinicalMeaning,
            estimated_minutes = :estimatedMinutes,
            status = :status,
            self_test_enabled = :selfTestEnabled,
            config_json = CAST(:configJson AS JSON),
            metric_schema_json = CAST(:metricSchemaJson AS JSON),
            updated_at = :now
        WHERE id = :id
        """, params);
    if (updated == 0) {
      throw new ApiException(HttpStatus.NOT_FOUND, "神经心理测试不存在");
    }
    return loadTest(testId);
  }

  @Transactional
  public Map<String, Object> createDistributionPlan(Map<String, Object> payload, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    List<String> testIds = stringList(firstNonNull(payload.get("test_ids"), payload.get("neuropsych_test_ids")));
    List<String> userIds = stringList(firstNonNull(payload.get("user_ids"), payload.get("recipient_user_ids")));
    if (testIds.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择神经心理测评");
    }
    if (userIds.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择患者");
    }
    List<Map<String, Object>> tests = query("""
        SELECT * FROM neuropsych_tests WHERE id IN (:ids) AND status = 'active'
        """, Map.of("ids", testIds));
    if (tests.size() != testIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "只能分发已启用的神经心理测评");
    }
    List<String> validUsers = validPatientIds(userIds);
    if (validUsers.size() != userIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "患者列表中存在无效用户");
    }
    String batchId = uuid();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO assessment_publish_batches (
          id, title, description, status, start_at, end_at, recipient_type, recipient_scope, created_by, published_at, created_at, updated_at
        ) VALUES (
          :id, :title, :description, 'active', :startAt, :endAt, 'users', CAST(:scope AS JSON), :createdBy, :now, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("title", requiredString(payload, "title", "请填写分发主题"))
            .addValue("description", nullableString(payload.get("description")))
            .addValue("startAt", timestamp(payload.get("start_at")))
            .addValue("endAt", timestamp(payload.get("end_at")))
            .addValue("scope", toJson(Map.of("user_ids", validUsers)))
            .addValue("createdBy", staff.id())
            .addValue("now", Timestamp.from(now)));
    for (int i = 0; i < tests.size(); i++) {
      Map<String, Object> test = tests.get(i);
      String itemId = uuid();
      jdbcTemplate.update("""
          INSERT INTO assessment_publish_items (id, batch_id, item_type, target_id, title, required, order_no, status, created_at)
          VALUES (:id, :batchId, 'neuropsych', :targetId, :title, TRUE, :orderNo, 'enabled', :now)
          """,
          new MapSqlParameterSource()
              .addValue("id", itemId)
              .addValue("batchId", batchId)
              .addValue("targetId", test.get("id"))
              .addValue("title", test.get("title"))
              .addValue("orderNo", i + 1)
              .addValue("now", Timestamp.from(now)));
    }
    createAssigneesAndRecords(batchId, validUsers, now);
    return Map.of("id", batchId, "created_records", validUsers.size() * tests.size());
  }

  public List<Map<String, Object>> listResults(Map<String, Object> filters, AuthUser authUser) {
    requireStaff(authUser);
    List<String> clauses = new ArrayList<>();
    Map<String, Object> params = new LinkedHashMap<>();
    addEqFilter(clauses, params, filters, "test_id", "r.test_id");
    addEqFilter(clauses, params, filters, "user_id", "r.user_id");
    addEqFilter(clauses, params, filters, "status", "r.status");
    addEqFilter(clauses, params, filters, "calc_status", "r.calc_status");
    addEqFilter(clauses, params, filters, "warning_level", "r.warning_level");
    return queryRecords(clauses.isEmpty() ? "" : "WHERE " + String.join(" AND ", clauses), params, false);
  }

  public Map<String, Object> getResult(String recordId, AuthUser authUser) {
    requireStaff(authUser);
    return loadRecordDetail(recordId, null);
  }

  public List<Map<String, Object>> myRecords(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    return queryRecords("WHERE r.user_id = :userId", Map.of("userId", user.id()), false);
  }

  public Map<String, Object> getMyReport(String recordId, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    return loadRecordDetail(recordId, user.id());
  }

  @Transactional
  public Map<String, Object> startFreeRecord(String testCode, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> test = one("""
        SELECT * FROM neuropsych_tests
        WHERE code = :code AND status = 'active' AND self_test_enabled = TRUE
        """, Map.of("code", testCode));
    if (test == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "该神经心理测评未开放自由测评");
    }
    String recordId = uuid();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO neuropsych_records (
          id, test_id, user_id, source_type, status, calc_status, started_at, created_at, updated_at
        ) VALUES (
          :id, :testId, :userId, 'self', 'in_progress', 'none', :now, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("testId", test.get("id"))
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now)));
    return loadRecordDetail(recordId, user.id());
  }

  @Transactional
  public Map<String, Object> startRecord(String recordId, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> record = loadRecordHeader(recordId, user.id());
    assertNotExpired(record);
    if ("completed".equals(record.get("status"))) {
      return loadRecordDetail(recordId, user.id());
    }
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE neuropsych_records
        SET status = 'in_progress', started_at = COALESCE(started_at, :now), updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now)));
    updatePublishItemStatus(string(record.get("publish_item_record_id")), "in_progress", now);
    refreshAssignee(record);
    return loadRecordDetail(recordId, user.id());
  }

  @Transactional
  public Map<String, Object> submitRecord(String recordId, Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> record = loadRecordHeader(recordId, user.id());
    assertNotExpired(record);
    if ("completed".equals(record.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评已提交");
    }
    Object rawData = firstNonNull(payload.get("raw_data_json"), payload.get("rawData"), payload.get("rawJson"), payload.get("data"));
    if (rawData == null) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "实验结果不能为空");
    }
    Instant now = Instant.now();
    Timestamp startedAt = record.get("started_at") instanceof Timestamp timestamp ? timestamp : Timestamp.from(now);
    long durationMs = Math.max(0, Duration.between(startedAt.toInstant(), now).toMillis());
    jdbcTemplate.update("""
        UPDATE neuropsych_records
        SET status = 'completed',
            calc_status = 'waiting',
            completed_at = :now,
            started_at = COALESCE(started_at, :now),
            duration_ms = :durationMs,
            raw_data_json = CAST(:rawData AS JSON),
            updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("userId", user.id())
            .addValue("durationMs", durationMs)
            .addValue("rawData", toJson(rawData))
            .addValue("now", Timestamp.from(now)));
    calculateRecord(recordId);
    Map<String, Object> updated = loadRecordHeader(recordId, user.id());
    updatePublishItemStatus(string(updated.get("publish_item_record_id")), "completed", now);
    refreshAssignee(updated);
    return loadRecordDetail(recordId, user.id());
  }

  @Transactional
  public Map<String, Object> recalculateRecord(String recordId, AuthUser authUser) {
    requireStaff(authUser);
    calculateRecord(recordId);
    return loadRecordDetail(recordId, null);
  }

  private void calculateRecord(String recordId) {
    try {
      Map<String, Object> record = loadRecordHeader(recordId, null);
      Object rawData = parseJsonField(record.get("raw_data_json"));
      Map<String, Object> calculated = calculator.calculate(string(record.get("test_code")), rawData);
      Map<String, Object> metrics = map(calculated.get("metrics"));
      String warning = string(calculated.get("warningLevel"), "none");
      Map<String, Object> report = new LinkedHashMap<>();
      report.put("recordId", recordId);
      report.put("testId", record.get("test_id"));
      report.put("testCode", record.get("test_code"));
      report.put("testTitle", record.get("test_title"));
      report.put("patientId", record.get("user_id"));
      report.put("completedAt", Instant.now().toString());
      report.put("summary", calculated.get("summary"));
      report.put("warningLevel", warning);
      report.put("quality", calculated.get("quality"));
      report.put("metrics", metrics);
      report.put("feedbackCards", calculated.get("feedbackCards"));
      Object feedback = calculated.get("feedback");
      if (feedback != null) {
        report.put("feedback", feedback);
      }
      report.put("sections", calculated.get("sections"));
      report.put("rawDataPreview", calculator.normalizeTrials(rawData).stream().limit(8).toList());
      String assessmentId = syncAssessment(record, report, warning);
      syncRiskAlert(record, report, warning);
      jdbcTemplate.update("""
          UPDATE neuropsych_records
          SET calc_status = 'done',
              calc_error = NULL,
              metrics_json = CAST(:metrics AS JSON),
              report = CAST(:report AS JSON),
              warning_level = :warning,
              assessment_id = :assessmentId,
              updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("metrics", toJson(metrics))
              .addValue("report", toJson(report))
              .addValue("warning", warning)
              .addValue("assessmentId", assessmentId)
              .addValue("now", Timestamp.from(Instant.now())));
    } catch (Exception ex) {
      jdbcTemplate.update("""
          UPDATE neuropsych_records
          SET calc_status = 'error', calc_error = :error, updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("error", ex.getMessage())
              .addValue("now", Timestamp.from(Instant.now())));
      if (ex instanceof ApiException apiException) {
        throw apiException;
      }
      throw new ApiException(HttpStatus.BAD_REQUEST, "神经心理测评计算失败: " + ex.getMessage());
    }
  }

  private void createAssigneesAndRecords(String batchId, List<String> userIds, Instant now) {
    List<Map<String, Object>> items = query("SELECT * FROM assessment_publish_items WHERE batch_id = :batchId ORDER BY order_no", Map.of("batchId", batchId));
    for (String userId : userIds) {
      String assigneeId = uuid();
      jdbcTemplate.update("""
          INSERT INTO assessment_publish_assignees (id, batch_id, user_id, status, created_at, updated_at)
          VALUES (:id, :batchId, :userId, 'pending', :now, :now)
          """,
          new MapSqlParameterSource()
              .addValue("id", assigneeId)
              .addValue("batchId", batchId)
              .addValue("userId", userId)
              .addValue("now", Timestamp.from(now)));
      for (Map<String, Object> item : items) {
        String itemRecordId = uuid();
        jdbcTemplate.update("""
            INSERT INTO assessment_publish_item_records (
              id, assignee_id, batch_id, item_id, user_id, item_type, status, created_at, updated_at
            ) VALUES (
              :id, :assigneeId, :batchId, :itemId, :userId, 'neuropsych', 'pending', :now, :now
            )
            """,
            new MapSqlParameterSource()
                .addValue("id", itemRecordId)
                .addValue("assigneeId", assigneeId)
                .addValue("batchId", batchId)
                .addValue("itemId", item.get("id"))
                .addValue("userId", userId)
                .addValue("now", Timestamp.from(now)));
        String recordId = uuid();
        jdbcTemplate.update("""
            INSERT INTO neuropsych_records (
              id, test_id, user_id, source_type, publish_item_record_id, status, calc_status, created_at, updated_at
            ) VALUES (
              :id, :testId, :userId, 'assigned', :itemRecordId, 'pending', 'none', :now, :now
            )
            """,
            new MapSqlParameterSource()
                .addValue("id", recordId)
                .addValue("testId", item.get("target_id"))
                .addValue("userId", userId)
                .addValue("itemRecordId", itemRecordId)
                .addValue("now", Timestamp.from(now)));
        jdbcTemplate.update("""
            UPDATE assessment_publish_item_records
            SET result_ref_table = 'neuropsych_records', result_ref_id = :recordId
            WHERE id = :itemRecordId
            """,
            new MapSqlParameterSource().addValue("recordId", recordId).addValue("itemRecordId", itemRecordId));
      }
    }
  }

  private String syncAssessment(Map<String, Object> record, Map<String, Object> report, String warning) {
    String assessmentId = string(record.get("assessment_id"));
    if (assessmentId.isBlank()) {
      assessmentId = uuid();
      jdbcTemplate.update("""
          INSERT INTO assessments (
            id, user_id, assessment_type, conversation_history, ai_analysis, risk_level, score, report, created_at, updated_at
          ) VALUES (
            :id, :userId, 'neuropsych_assessment', CAST('[]' AS JSON), CAST('{}' AS JSON), :riskLevel, NULL,
            CAST(:report AS JSON), :now, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", assessmentId)
              .addValue("userId", record.get("user_id"))
              .addValue("riskLevel", warningToRisk(warning))
              .addValue("report", toJson(Map.of("neuropsychData", report)))
              .addValue("now", Timestamp.from(Instant.now())));
    } else {
      jdbcTemplate.update("""
          UPDATE assessments
          SET risk_level = :riskLevel, report = CAST(:report AS JSON), updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource()
              .addValue("id", assessmentId)
              .addValue("riskLevel", warningToRisk(warning))
              .addValue("report", toJson(Map.of("neuropsychData", report)))
              .addValue("now", Timestamp.from(Instant.now())));
    }
    return assessmentId;
  }

  private void syncRiskAlert(Map<String, Object> record, Map<String, Object> report, String warning) {
    int risk = warningToRisk(warning);
    if (risk < 2) {
      return;
    }
    Integer existing = jdbcTemplate.queryForObject(
        "SELECT COUNT(*) FROM risk_alerts WHERE data_source = 'neuropsych_assessment' AND source_id = :id",
        new MapSqlParameterSource("id", record.get("id")),
        Integer.class);
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("patientId", record.get("user_id"))
        .addValue("riskLevel", risk)
        .addValue("description", string(report.get("summary"), "神经心理测评提示风险"))
        .addValue("sourceId", record.get("id"))
        .addValue("now", Timestamp.from(Instant.now()));
    if (existing != null && existing > 0) {
      jdbcTemplate.update("""
          UPDATE risk_alerts
          SET risk_level = :riskLevel, description = :description
          WHERE data_source = 'neuropsych_assessment' AND source_id = :sourceId
          """, params);
    } else {
      jdbcTemplate.update("""
          INSERT INTO risk_alerts (
            id, patient_id, alert_type, risk_level, description, data_source, source_id, is_handled, created_at
          ) VALUES (
            :id, :patientId, '神经心理测评预警', :riskLevel, :description, 'neuropsych_assessment', :sourceId, FALSE, :now
          )
          """, params.addValue("id", uuid()));
    }
  }

  private void updatePublishItemStatus(String itemRecordId, String status, Instant now) {
    if (itemRecordId.isBlank()) {
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
            .addValue("id", itemRecordId)
            .addValue("status", status)
            .addValue("now", Timestamp.from(now)));
  }

  private void refreshAssignee(Map<String, Object> record) {
    String itemRecordId = string(record.get("publish_item_record_id"));
    if (itemRecordId.isBlank()) {
      return;
    }
    Map<String, Object> itemRecord = one("SELECT * FROM assessment_publish_item_records WHERE id = :id", Map.of("id", itemRecordId));
    if (itemRecord == null) {
      return;
    }
    String assigneeId = string(itemRecord.get("assignee_id"));
    List<Map<String, Object>> siblings = query("SELECT status FROM assessment_publish_item_records WHERE assignee_id = :id", Map.of("id", assigneeId));
    boolean completed = siblings.stream().allMatch(row -> "completed".equals(row.get("status")) || "unsupported".equals(row.get("status")));
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
            .addValue("now", Timestamp.from(Instant.now())));
  }

  private Map<String, Object> loadTest(String testId) {
    Map<String, Object> test = one("SELECT * FROM neuropsych_tests WHERE id = :id", Map.of("id", testId));
    if (test == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "神经心理测试不存在");
    }
    return test;
  }

  private Map<String, Object> loadRecordHeader(String recordId, String userId) {
    Map<String, Object> params = new LinkedHashMap<>();
    params.put("id", recordId);
    String userClause = "";
    if (userId != null) {
      userClause = " AND r.user_id = :userId";
      params.put("userId", userId);
    }
    Map<String, Object> record = one("""
        SELECT r.*, t.code AS test_code, t.title AS test_title, t.source_path, t.estimated_minutes, t.config_json,
          b.title AS batch_title, b.start_at AS batch_start_at, b.end_at AS batch_end_at,
          p.full_name AS patient_name, p.username AS patient_username
        FROM neuropsych_records r
        JOIN neuropsych_tests t ON t.id = r.test_id
        LEFT JOIN assessment_publish_item_records pir ON pir.id = r.publish_item_record_id
        LEFT JOIN assessment_publish_batches b ON b.id = pir.batch_id
        LEFT JOIN profiles p ON p.id = r.user_id
        WHERE r.id = :id
        """ + userClause + " LIMIT 1", params);
    if (record == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "神经心理测评记录不存在");
    }
    return record;
  }

  private Map<String, Object> loadRecordDetail(String recordId, String userId) {
    return loadRecordHeader(recordId, userId);
  }

  private List<Map<String, Object>> queryRecords(String where, Map<String, Object> params, boolean detail) {
    return query("""
        SELECT r.*, t.code AS test_code, t.title AS test_title, t.description AS test_description, t.dimension,
          t.clinical_meaning, t.estimated_minutes, t.source_path, t.config_json,
          b.title AS batch_title,
          p.full_name AS patient_name, p.username AS patient_username
        FROM neuropsych_records r
        JOIN neuropsych_tests t ON t.id = r.test_id
        LEFT JOIN assessment_publish_item_records pir ON pir.id = r.publish_item_record_id
        LEFT JOIN assessment_publish_batches b ON b.id = pir.batch_id
        LEFT JOIN profiles p ON p.id = r.user_id
        """ + where + " ORDER BY r.created_at DESC", params);
  }

  private void assertNotExpired(Map<String, Object> record) {
    Object endAt = record.get("batch_end_at");
    if (endAt instanceof Timestamp timestamp && timestamp.toInstant().isBefore(Instant.now())) {
      jdbcTemplate.update("UPDATE neuropsych_records SET status = 'expired' WHERE id = :id", new MapSqlParameterSource("id", record.get("id")));
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评任务已过期");
    }
    if (endAt instanceof String text && !text.isBlank()) {
      try {
        if (Instant.parse(text).isBefore(Instant.now())) {
          jdbcTemplate.update("UPDATE neuropsych_records SET status = 'expired' WHERE id = :id", new MapSqlParameterSource("id", record.get("id")));
          throw new ApiException(HttpStatus.BAD_REQUEST, "该测评任务已过期");
        }
      } catch (ApiException ex) {
        throw ex;
      } catch (Exception ignored) {
      }
    }
  }

  private List<String> validPatientIds(List<String> userIds) {
    if (userIds.isEmpty()) {
      return List.of();
    }
    return query("SELECT id FROM profiles WHERE role = 'user' AND id IN (:ids)", Map.of("ids", userIds))
        .stream()
        .map(row -> string(row.get("id")))
        .toList();
  }

  private AuthUser requireStaff(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可操作");
    }
    return user;
  }

  private List<Map<String, Object>> query(String sql, Map<String, Object> params) {
    return jdbcTemplate.query(sql, new MapSqlParameterSource(params), new ColumnMapRowMapper())
        .stream()
        .map(this::normalizeRow)
        .toList();
  }

  private Map<String, Object> one(String sql, Map<String, Object> params) {
    List<Map<String, Object>> rows = query(sql, params);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private Map<String, Object> normalizeRow(Map<String, Object> row) {
    Map<String, Object> result = new LinkedHashMap<>();
    for (Map.Entry<String, Object> entry : row.entrySet()) {
      String key = entry.getKey().toLowerCase();
      Object value = entry.getValue();
      if (value instanceof Timestamp timestamp) {
        result.put(key, timestamp.toInstant().toString());
      } else if (key.endsWith("_json") || "report".equals(key) || "recipient_scope".equals(key)) {
        result.put(key, parseJsonField(value));
      } else {
        result.put(key, value);
      }
    }
    return result;
  }

  private Object parseJsonField(Object value) {
    if (value instanceof String json && !json.isBlank()) {
      try {
        return objectMapper.readValue(json, new TypeReference<Object>() {});
      } catch (JsonProcessingException ignored) {
        return value;
      }
    }
    return value;
  }

  @SuppressWarnings("unchecked")
  private Map<String, Object> map(Object value) {
    return value instanceof Map<?, ?> source ? (Map<String, Object>) source : new LinkedHashMap<>();
  }

  private void addEqFilter(List<String> clauses, Map<String, Object> params, Map<String, Object> filters, String key, String column) {
    Object value = filters == null ? null : filters.get(key);
    if (value != null && !String.valueOf(value).isBlank()) {
      clauses.add(column + " = :" + key);
      params.put(key, value);
    }
  }

  private Object firstNonNull(Object... values) {
    for (Object value : values) {
      if (value != null) {
        return value;
      }
    }
    return null;
  }

  private String requiredString(Map<String, Object> payload, String key, String message) {
    String value = string(payload.get(key));
    if (value.isBlank()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, message);
    }
    return value;
  }

  private List<String> stringList(Object value) {
    if (value instanceof List<?> list) {
      return list.stream().map(this::string).filter(item -> !item.isBlank()).toList();
    }
    if (value instanceof String text && !text.isBlank()) {
      return List.of(text.split(",")).stream().map(String::trim).filter(item -> !item.isBlank()).toList();
    }
    return List.of();
  }

  private Timestamp timestamp(Object value) {
    if (value == null || string(value).isBlank()) {
      return null;
    }
    try {
      return Timestamp.from(Instant.parse(string(value)));
    } catch (Exception ignored) {
      return null;
    }
  }

  private String toJson(Object value) {
    try {
      return objectMapper.writeValueAsString(value == null ? Map.of() : value);
    } catch (JsonProcessingException ex) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "JSON 序列化失败");
    }
  }

  private String normalizeStatus(String status) {
    return "stopped".equals(status) ? "stopped" : "active";
  }

  private String nullableString(Object value) {
    String text = string(value);
    return text.isBlank() ? null : text;
  }

  private String string(Object value) {
    return string(value, "");
  }

  private String string(Object value, String fallback) {
    return value == null ? fallback : String.valueOf(value).trim();
  }

  private boolean bool(Object value, boolean fallback) {
    if (value instanceof Boolean bool) {
      return bool;
    }
    return value == null ? fallback : Boolean.parseBoolean(String.valueOf(value));
  }

  private int intValue(Object value, int fallback) {
    if (value instanceof Number number) {
      return number.intValue();
    }
    try {
      return value == null || string(value).isBlank() ? fallback : Integer.parseInt(string(value));
    } catch (NumberFormatException ignored) {
      return fallback;
    }
  }

  private int warningToRisk(String warning) {
    return switch (string(warning, "none")) {
      case "high" -> 3;
      case "middle" -> 2;
      case "low" -> 1;
      default -> 0;
    };
  }

  private String uuid() {
    return UUID.randomUUID().toString();
  }
}
