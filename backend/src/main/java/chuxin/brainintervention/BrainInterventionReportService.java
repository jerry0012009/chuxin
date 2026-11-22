package chuxin.brainintervention;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthService;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.math.BigDecimal;
import java.sql.Timestamp;
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
public class BrainInterventionReportService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;
  private final AuthService authService;

  public BrainInterventionReportService(
      NamedParameterJdbcTemplate jdbcTemplate,
      ObjectMapper objectMapper,
      AuthService authService) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
    this.authService = authService;
  }

  @Transactional
  public Map<String, Object> createReport(Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    String userId = string(firstNonNull(payload.get("user_id"), user.id()), user.id());
    if (!user.isStaff() && !user.id().equals(userId)) {
      throw new ApiException(HttpStatus.FORBIDDEN, "无权为其他用户创建训练报告");
    }
    if (user.isStaff() && !canAccessPatient(user, userId)) {
      throw new ApiException(HttpStatus.FORBIDDEN, "无权为该用户创建训练报告");
    }

    Map<String, Object> profile = loadProfile(userId);
    String reportId = uuid();
    Instant now = Instant.now();
    Instant startedAt = instant(payload.get("started_at"), now);
    Instant endedAt = instant(payload.get("ended_at"), now);
    int durationSec = intValue(payload.get("duration_sec"), Math.max(0, (int) (endedAt.getEpochSecond() - startedAt.getEpochSecond())));
    String protocolKey = normalizeProtocol(string(payload.get("protocol_key"), "alpha_uptraining"));
    String taskName = string(payload.get("task_name"), taskName(protocolKey));
    String taskType = normalizeTaskType(string(payload.get("task_type"), "neurofeedback"));
    String status = normalizeStatus(string(payload.get("status"), "completed"));
    Map<String, Object> metrics = map(firstNonNull(payload.get("metrics_json"), payload.get("metrics")));
    Object curve = firstNonNull(payload.get("curve_json"), payload.get("curve"));
    Object config = firstNonNull(payload.get("config_json"), payload.get("config"));
    Double avgScore = doubleValue(firstNonNull(payload.get("avg_score"), metrics.get("avgFeedback")));
    Double maxScore = doubleValue(firstNonNull(payload.get("max_score"), metrics.get("maxFeedback")));
    Double mainScore = doubleValue(firstNonNull(payload.get("main_score"), avgScore));
    Integer stableDuration = integerValue(firstNonNull(payload.get("stable_duration_sec"), metrics.get("stableDurationSec")));
    Double signalQuality = doubleValue(firstNonNull(payload.get("signal_quality_avg"), metrics.get("signalQualityAvg")));
    Double artifactRatio = doubleValue(firstNonNull(payload.get("artifact_ratio"), metrics.get("artifactRatio")));
    String summary = nullableString(firstNonNull(payload.get("summary"), buildSummary(protocolKey, avgScore, maxScore, stableDuration)));
    String suggestion = nullableString(firstNonNull(payload.get("suggestion"), buildSuggestion(avgScore, stableDuration)));

    jdbcTemplate.update("""
        INSERT INTO brain_intervention_reports (
          id, user_id, user_name, doctor_id, report_type, task_type, task_name, protocol_key,
          started_at, ended_at, duration_sec, status, main_score, avg_score, max_score,
          stable_duration_sec, signal_quality_avg, artifact_ratio, summary, suggestion,
          metrics_json, curve_json, config_json, created_at, updated_at
        ) VALUES (
          :id, :userId, :userName, :doctorId, :reportType, :taskType, :taskName, :protocolKey,
          :startedAt, :endedAt, :durationSec, :status, :mainScore, :avgScore, :maxScore,
          :stableDurationSec, :signalQualityAvg, :artifactRatio, :summary, :suggestion,
          CAST(:metricsJson AS JSON), CAST(:curveJson AS JSON), CAST(:configJson AS JSON), :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", reportId)
            .addValue("userId", userId)
            .addValue("userName", displayName(profile, user.username()))
            .addValue("doctorId", resolveDoctorId(user, userId))
            .addValue("reportType", "brain_intervention")
            .addValue("taskType", taskType)
            .addValue("taskName", taskName)
            .addValue("protocolKey", protocolKey)
            .addValue("startedAt", Timestamp.from(startedAt))
            .addValue("endedAt", Timestamp.from(endedAt))
            .addValue("durationSec", durationSec)
            .addValue("status", status)
            .addValue("mainScore", decimal(mainScore))
            .addValue("avgScore", decimal(avgScore))
            .addValue("maxScore", decimal(maxScore))
            .addValue("stableDurationSec", stableDuration)
            .addValue("signalQualityAvg", decimal(signalQuality))
            .addValue("artifactRatio", decimal(artifactRatio))
            .addValue("summary", summary)
            .addValue("suggestion", suggestion)
            .addValue("metricsJson", toJson(metrics))
            .addValue("curveJson", toJson(curve == null ? Map.of() : curve))
            .addValue("configJson", toJson(config == null ? Map.of() : config))
            .addValue("now", Timestamp.from(now)));
    return loadReport(reportId, user);
  }

  public List<Map<String, Object>> myReports(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    return queryReports("WHERE r.user_id = :userId", Map.of("userId", user.id()), 100);
  }

  public Map<String, Object> getMyReport(String reportId, AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    Map<String, Object> report = oneReport("WHERE r.id = :id AND r.user_id = :userId", Map.of("id", reportId, "userId", user.id()));
    if (report == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "训练报告不存在");
    }
    return report;
  }

  public List<Map<String, Object>> listReports(Map<String, Object> filters, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    List<String> clauses = new ArrayList<>();
    Map<String, Object> params = new LinkedHashMap<>();
    addScopeClause(clauses, params, staff);
    addEqFilter(clauses, params, filters, "user_id", "r.user_id");
    addEqFilter(clauses, params, filters, "report_type", "r.report_type");
    addEqFilter(clauses, params, filters, "task_type", "r.task_type");
    addEqFilter(clauses, params, filters, "protocol_key", "r.protocol_key");
    addDateFilter(clauses, params, filters, "started_from", "r.started_at", ">=");
    addDateFilter(clauses, params, filters, "started_to", "r.started_at", "<=");
    return queryReports("WHERE " + String.join(" AND ", clauses), params, intValue(filters == null ? null : filters.get("limit"), 200));
  }

  public Map<String, Object> getReport(String reportId, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    Map<String, Object> report = oneReport("WHERE r.id = :id", Map.of("id", reportId));
    if (report == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "训练报告不存在");
    }
    if (!canAccessPatient(staff, string(report.get("user_id")))) {
      throw new ApiException(HttpStatus.FORBIDDEN, "无权查看该用户训练报告");
    }
    return report;
  }

  private Map<String, Object> loadReport(String reportId, AuthUser user) {
    if (user.isStaff()) {
      return getReport(reportId, user);
    }
    return getMyReport(reportId, user);
  }

  private List<Map<String, Object>> queryReports(String where, Map<String, ?> params, int limit) {
    return query("""
        SELECT r.*,
          p.username AS patient_username,
          p.full_name AS patient_full_name,
          p.department_id AS patient_department_id,
          d.name AS patient_department_name
        FROM brain_intervention_reports r
        LEFT JOIN profiles p ON p.id = r.user_id
        LEFT JOIN departments d ON d.id = p.department_id
        """ + where + " ORDER BY r.started_at DESC, r.created_at DESC LIMIT :limit",
        withLimit(params, Math.min(500, Math.max(1, limit))));
  }

  private Map<String, Object> oneReport(String where, Map<String, ?> params) {
    List<Map<String, Object>> rows = queryReports(where, params, 1);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private void addScopeClause(List<String> clauses, Map<String, Object> params, AuthUser staff) {
    if ("doctor".equals(staff.role())) {
      clauses.add("""
          EXISTS (
            SELECT 1 FROM doctor_patients dp
            WHERE dp.doctor_id = :doctorScopeId
              AND dp.patient_id = r.user_id
              AND dp.status = 'active'
          )
          """);
      params.put("doctorScopeId", staff.id());
    } else {
      clauses.add("1 = 1");
    }
  }

  private boolean canAccessPatient(AuthUser staff, String patientId) {
    if (!staff.isStaff()) {
      return staff.id().equals(patientId);
    }
    if (!"doctor".equals(staff.role())) {
      return true;
    }
    Integer count = jdbcTemplate.queryForObject("""
        SELECT COUNT(*) FROM doctor_patients
        WHERE doctor_id = :doctorId AND patient_id = :patientId AND status = 'active'
        """,
        new MapSqlParameterSource()
            .addValue("doctorId", staff.id())
            .addValue("patientId", patientId),
        Integer.class);
    return count != null && count > 0;
  }

  private String resolveDoctorId(AuthUser user, String patientId) {
    if ("doctor".equals(user.role())) {
      return user.id();
    }
    Map<String, Object> row = one("""
        SELECT doctor_id FROM doctor_patients
        WHERE patient_id = :patientId AND status = 'active'
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
        """, Map.of("patientId", patientId));
    return row == null ? null : string(row.get("doctor_id"));
  }

  private Map<String, Object> loadProfile(String userId) {
    Map<String, Object> profile = one("SELECT id, username, full_name, role FROM profiles WHERE id = :id LIMIT 1", Map.of("id", userId));
    if (profile == null || !"user".equals(profile.get("role"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "训练报告用户不存在");
    }
    return profile;
  }

  private AuthUser requireStaff(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可查看用户训练报告");
    }
    return user;
  }

  private String displayName(Map<String, Object> profile, String fallback) {
    String fullName = string(profile.get("full_name"));
    return fullName.isBlank() ? string(profile.get("username"), fallback) : fullName;
  }

  private String buildSummary(String protocolKey, Double avgScore, Double maxScore, Integer stableDuration) {
    String metric = taskMetricLabel(protocolKey);
    if (avgScore == null && maxScore == null) {
      return metric + "神经反馈训练已完成，当前记录用于回顾训练过程。";
    }
    String avg = avgScore == null ? "--" : String.format("%.1f", avgScore);
    String max = maxScore == null ? "--" : String.format("%.1f", maxScore);
    int stable = stableDuration == null ? 0 : stableDuration;
    return metric + "神经反馈训练已完成，平均反馈值 " + avg + "，最高反馈值 " + max + "，稳定达标约 " + stable + " 秒。";
  }

  private String buildSuggestion(Double avgScore, Integer stableDuration) {
    if (avgScore == null) {
      return "建议保持稳定坐姿和规律练习，后续可结合信号质量记录观察训练趋势。";
    }
    int stable = stableDuration == null ? 0 : stableDuration;
    if (avgScore >= 65 && stable >= 20) {
      return "本次训练过程较稳定。建议保持当前节奏，后续关注多次训练的趋势变化。";
    }
    if (avgScore >= 50) {
      return "本次训练已有一定稳定性。建议下次继续减少眨眼、咬牙和身体动作，保持舒适专注。";
    }
    return "本次反馈值偏低。建议优先确认电极佩戴和信号质量，并采用较短时长、低压力的练习。";
  }

  private String taskName(String protocolKey) {
    return switch (protocolKey) {
      case "meditation_biosignal_monitor" -> "脑机交互冥想";
      case "theta_training" -> "Theta Training";
      case "beta_training" -> "Beta Training";
      case "smr_training" -> "SMR Training";
      case "theta_beta_ratio" -> "Theta-Beta Ratio Training";
      default -> "Alpha Uptraining";
    };
  }

  private String taskMetricLabel(String protocolKey) {
    return switch (protocolKey) {
      case "meditation_biosignal_monitor" -> "脑机交互冥想";
      case "theta_training" -> "Theta";
      case "beta_training" -> "Beta";
      case "smr_training" -> "SMR";
      case "theta_beta_ratio" -> "Theta/Beta Ratio";
      default -> "Alpha";
    };
  }

  private void addEqFilter(List<String> clauses, Map<String, Object> params, Map<String, Object> filters, String key, String column) {
    Object value = filters == null ? null : filters.get(key);
    if (value != null && !string(value).isBlank()) {
      clauses.add(column + " = :" + key);
      params.put(key, value);
    }
  }

  private void addDateFilter(List<String> clauses, Map<String, Object> params, Map<String, Object> filters, String key, String column, String op) {
    Object value = filters == null ? null : filters.get(key);
    Timestamp timestamp = timestamp(value);
    if (timestamp != null) {
      clauses.add(column + " " + op + " :" + key);
      params.put(key, timestamp);
    }
  }

  private List<Map<String, Object>> query(String sql, Map<String, ?> params) {
    return jdbcTemplate.query(sql, new MapSqlParameterSource(params), new ColumnMapRowMapper())
        .stream()
        .map(this::normalizeRow)
        .toList();
  }

  private Map<String, Object> one(String sql, Map<String, ?> params) {
    List<Map<String, Object>> rows = query(sql, params);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private Map<String, Object> withLimit(Map<String, ?> params, int limit) {
    Map<String, Object> result = new LinkedHashMap<>(params);
    result.put("limit", limit);
    return result;
  }

  private Map<String, Object> normalizeRow(Map<String, Object> row) {
    Map<String, Object> result = new LinkedHashMap<>();
    for (Map.Entry<String, Object> entry : row.entrySet()) {
      String key = entry.getKey().toLowerCase();
      Object value = entry.getValue();
      if (value instanceof Timestamp timestamp) {
        result.put(key, timestamp.toInstant().toString());
      } else if (value instanceof BigDecimal decimal) {
        result.put(key, decimal.doubleValue());
      } else if (key.endsWith("_json")) {
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

  private Object firstNonNull(Object... values) {
    for (Object value : values) {
      if (value != null) {
        return value;
      }
    }
    return null;
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

  private Instant instant(Object value, Instant fallback) {
    Timestamp timestamp = timestamp(value);
    return timestamp == null ? fallback : timestamp.toInstant();
  }

  private String toJson(Object value) {
    try {
      return objectMapper.writeValueAsString(value == null ? Map.of() : value);
    } catch (JsonProcessingException ex) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "训练报告 JSON 序列化失败");
    }
  }

  private BigDecimal decimal(Double value) {
    return value == null ? null : BigDecimal.valueOf(value);
  }

  private Double doubleValue(Object value) {
    if (value instanceof Number number) {
      return number.doubleValue();
    }
    try {
      String text = string(value);
      return text.isBlank() ? null : Double.parseDouble(text);
    } catch (NumberFormatException ignored) {
      return null;
    }
  }

  private Integer integerValue(Object value) {
    if (value instanceof Number number) {
      return number.intValue();
    }
    try {
      String text = string(value);
      return text.isBlank() ? null : Integer.parseInt(text);
    } catch (NumberFormatException ignored) {
      return null;
    }
  }

  private int intValue(Object value, int fallback) {
    Integer parsed = integerValue(value);
    return parsed == null ? fallback : parsed;
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

  private String normalizeStatus(String status) {
    return switch (status) {
      case "interrupted" -> "interrupted";
      case "invalid" -> "invalid";
      default -> "completed";
    };
  }

  private String normalizeTaskType(String taskType) {
    return switch (taskType) {
      case "ssvep", "p300", "smr", "relaxation", "attention_training", "meditation_biosignal_monitor" -> taskType;
      default -> "neurofeedback";
    };
  }

  private String normalizeProtocol(String protocolKey) {
    return switch (protocolKey) {
      case "theta_training", "beta_training", "smr_training", "theta_beta_ratio", "meditation_biosignal_monitor" -> protocolKey;
      default -> "alpha_uptraining";
    };
  }

  private String uuid() {
    return UUID.randomUUID().toString();
  }
}
