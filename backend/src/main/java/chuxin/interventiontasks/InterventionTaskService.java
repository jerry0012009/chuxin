package chuxin.interventiontasks;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.sql.Date;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.ColumnMapRowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class InterventionTaskService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;

  public InterventionTaskService(NamedParameterJdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
  }

  public Map<String, Object> materials(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    String where = user.isStaff() ? "" : " WHERE is_active = TRUE";
    List<Map<String, Object>> rows = query("""
        SELECT * FROM intervention_materials
        %s
        ORDER BY FIELD(category, 'mood','meditation','knowledge','game','brain_intervention'), title
        """.formatted(where), Map.of());
    Map<String, List<Map<String, Object>>> grouped = rows.stream()
        .collect(Collectors.groupingBy(row -> string(row.get("category")), LinkedHashMap::new, Collectors.toList()));
    grouped.put("all", rows);
    return new LinkedHashMap<>(grouped);
  }

  public List<Map<String, Object>> templates(AuthUser authUser) {
    requireStaff(authUser);
    List<Map<String, Object>> rows = query("""
        SELECT * FROM intervention_plan_templates
        ORDER BY FIELD(risk_level, 'low','middle','high')
        """, Map.of());
    rows.forEach(template -> template.put("items", templateItems(string(template.get("id")))));
    return rows;
  }

  @Transactional
  public Map<String, Object> updateTemplate(String templateId, Map<String, Object> payload, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    Map<String, Object> template = loadTemplate(templateId);
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE intervention_plan_templates
        SET title = :title,
            description = :description,
            duration_days = :durationDays,
            daily_required_count = :dailyRequiredCount,
            auto_assign_enabled = :autoAssignEnabled,
            status = :status,
            created_by = COALESCE(created_by, :createdBy),
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", templateId)
            .addValue("title", string(payload.get("title"), string(template.get("title"))))
            .addValue("description", nullableString(firstNonNull(payload.get("description"), template.get("description"))))
            .addValue("durationDays", intValue(payload.get("duration_days"), intValue(template.get("duration_days"), 7)))
            .addValue("dailyRequiredCount", intValue(payload.get("daily_required_count"), intValue(template.get("daily_required_count"), 1)))
            .addValue("autoAssignEnabled", bool(payload.get("auto_assign_enabled"), bool(template.get("auto_assign_enabled"), true)))
            .addValue("status", string(payload.get("status"), string(template.get("status"), "active")))
            .addValue("createdBy", staff.id())
            .addValue("now", Timestamp.from(now)));
    if (payload.containsKey("items")) {
      replaceTemplateItems(templateId, list(payload.get("items")), now);
    }
    return loadTemplateWithItems(templateId);
  }

  public List<Map<String, Object>> listTasks(AuthUser authUser) {
    requireStaff(authUser);
    expireOverdueAssignees();
    return query("""
        SELECT b.*,
          (SELECT COUNT(*) FROM intervention_publish_items i WHERE i.batch_id = b.id) AS item_count,
          (SELECT COUNT(*) FROM intervention_publish_assignees a WHERE a.batch_id = b.id) AS assignee_count,
          (SELECT COUNT(*) FROM intervention_publish_assignees a WHERE a.batch_id = b.id AND a.status IN ('completed','expired')) AS finished_count,
          (SELECT COALESCE(ROUND(AVG(a.total_completed_count), 0), 0) FROM intervention_publish_assignees a WHERE a.batch_id = b.id) AS average_completed_count
        FROM intervention_publish_batches b
        ORDER BY b.created_at DESC
        """, Map.of());
  }

  public Map<String, Object> getTask(String batchId, AuthUser authUser) {
    requireStaff(authUser);
    expireOverdueAssignees();
    Map<String, Object> task = loadTask(batchId);
    task.put("items", publishItems(batchId));
    task.put("assignees", query("""
        SELECT a.*, p.full_name AS patient_name, p.username AS patient_username,
          (SELECT COUNT(*) FROM intervention_item_records r WHERE r.assignee_id = a.id AND r.status = 'completed') AS completed_item_count,
          (SELECT COUNT(*) FROM intervention_item_records r WHERE r.assignee_id = a.id) AS generated_item_count
        FROM intervention_publish_assignees a
        LEFT JOIN profiles p ON p.id = a.user_id
        WHERE a.batch_id = :batchId
        ORDER BY a.created_at DESC
        """, Map.of("batchId", batchId)));
    return task;
  }

  @Transactional
  public Map<String, Object> createTask(Map<String, Object> payload, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    String batchId = uuid();
    Instant now = Instant.now();
    int durationDays = intValue(payload.get("duration_days"), 7);
    LocalDate start = localDate(payload.get("start_date"), LocalDate.now(ZoneOffset.UTC));
    LocalDate end = start.plusDays(Math.max(1, durationDays) - 1L);
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_batches (
          id, batch_type, title, description, risk_level, duration_days, daily_required_count, status,
          start_date, end_date, recipient_type, recipient_scope, created_by, created_at, updated_at
        ) VALUES (
          :id, 'manual', :title, :description, :riskLevel, :durationDays, :dailyRequiredCount, 'draft',
          :startDate, :endDate, 'users', CAST(:scope AS JSON), :createdBy, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("title", requiredString(payload, "title", "请填写发布干预任务标题"))
            .addValue("description", nullableString(payload.get("description")))
            .addValue("riskLevel", nullableString(payload.get("risk_level")))
            .addValue("durationDays", durationDays)
            .addValue("dailyRequiredCount", intValue(payload.get("daily_required_count"), 1))
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("scope", toJson(recipientScope(payload)))
            .addValue("createdBy", staff.id())
            .addValue("now", Timestamp.from(now)));
    replacePublishItems(batchId, list(payload.get("items")), now);
    return getTask(batchId, authUser);
  }

  @Transactional
  public Map<String, Object> updateTask(String batchId, Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> task = loadTask(batchId);
    if (!"draft".equals(task.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "只能编辑草稿干预任务");
    }
    int durationDays = intValue(payload.get("duration_days"), intValue(task.get("duration_days"), 7));
    LocalDate start = localDate(payload.get("start_date"), localDate(task.get("start_date"), LocalDate.now(ZoneOffset.UTC)));
    LocalDate end = start.plusDays(Math.max(1, durationDays) - 1L);
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE intervention_publish_batches
        SET title = :title,
            description = :description,
            risk_level = :riskLevel,
            duration_days = :durationDays,
            daily_required_count = :dailyRequiredCount,
            start_date = :startDate,
            end_date = :endDate,
            recipient_scope = CAST(:scope AS JSON),
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("title", requiredString(payload, "title", "请填写发布干预任务标题"))
            .addValue("description", nullableString(payload.get("description")))
            .addValue("riskLevel", nullableString(payload.get("risk_level")))
            .addValue("durationDays", durationDays)
            .addValue("dailyRequiredCount", intValue(payload.get("daily_required_count"), intValue(task.get("daily_required_count"), 1)))
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("scope", toJson(recipientScope(payload)))
            .addValue("now", Timestamp.from(now)));
    replacePublishItems(batchId, list(payload.get("items")), now);
    return getTask(batchId, authUser);
  }

  @Transactional
  public Map<String, Object> publishTask(String batchId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> task = loadTask(batchId);
    if ("active".equals(task.get("status"))) {
      return getTask(batchId, authUser);
    }
    if (!"draft".equals(task.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该干预任务不能发布");
    }
    List<Map<String, Object>> items = publishItems(batchId);
    if (items.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请至少添加一个干预项目");
    }
    List<String> userIds = resolveRecipientUserIds(map(task.get("recipient_scope")));
    List<String> validUsers = validPatientIds(userIds);
    if (validUsers.isEmpty() || validUsers.size() != userIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择有效患者");
    }
    Instant now = Instant.now();
    LocalDate start = localDate(task.get("start_date"), LocalDate.now(ZoneOffset.UTC));
    LocalDate end = localDate(task.get("end_date"), start.plusDays(Math.max(1, intValue(task.get("duration_days"), 7)) - 1L));
    jdbcTemplate.update("""
        UPDATE intervention_publish_batches
        SET status = 'active', start_date = :startDate, end_date = :endDate, published_at = :now, updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("now", Timestamp.from(now)));
    for (String userId : validUsers) {
      jdbcTemplate.update("""
          INSERT IGNORE INTO intervention_publish_assignees (
            id, batch_id, user_id, status, start_date, end_date, created_at, updated_at
          ) VALUES (
            :id, :batchId, :userId, 'pending', :startDate, :endDate, :now, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", uuid())
              .addValue("batchId", batchId)
              .addValue("userId", userId)
              .addValue("startDate", Date.valueOf(start))
              .addValue("endDate", Date.valueOf(end))
              .addValue("now", Timestamp.from(now)));
    }
    return getTask(batchId, authUser);
  }

  @Transactional
  public Map<String, Object> stopTask(String batchId, AuthUser authUser) {
    requireStaff(authUser);
    Instant now = Instant.now();
    jdbcTemplate.update("UPDATE intervention_publish_batches SET status = 'stopped', updated_at = :now WHERE id = :id",
        new MapSqlParameterSource().addValue("id", batchId).addValue("now", Timestamp.from(now)));
    jdbcTemplate.update("""
        UPDATE intervention_publish_assignees
        SET status = 'cancelled', updated_at = :now
        WHERE batch_id = :id AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource().addValue("id", batchId).addValue("now", Timestamp.from(now)));
    jdbcTemplate.update("""
        UPDATE intervention_item_records
        SET status = 'cancelled', updated_at = :now
        WHERE batch_id = :id AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource().addValue("id", batchId).addValue("now", Timestamp.from(now)));
    return getTask(batchId, authUser);
  }

  public List<Map<String, Object>> myTasks(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    ensureDefaultInterventionForUser(user.id());
    expireOverdueAssignees(user.id());
    List<Map<String, Object>> rows = query("""
        SELECT a.*, b.title AS batch_title, b.description AS batch_description, b.risk_level,
               b.duration_days, b.daily_required_count, b.batch_type, b.source_assessment_id
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.user_id = :userId AND b.status IN ('active','completed')
        ORDER BY a.created_at DESC
        """, Map.of("userId", user.id()));
    rows.forEach(row -> row.put("items", publishItems(string(row.get("batch_id")))));
    return rows;
  }

  public Map<String, Object> userPlanForDoctor(String userId, AuthUser authUser) {
    requireStaff(authUser);
    expireOverdueAssignees(userId);
    List<Map<String, Object>> rows = query("""
        SELECT a.*, b.title AS batch_title, b.description AS batch_description, b.risk_level,
               b.duration_days, b.daily_required_count, b.batch_type, b.source_assessment_id
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.user_id = :userId
        ORDER BY a.created_at DESC
        """, Map.of("userId", userId));
    for (Map<String, Object> row : rows) {
      String assigneeId = string(row.get("id"));
      row.put("items", publishItems(string(row.get("batch_id"))));
      row.put("summaries", query("""
          SELECT * FROM intervention_daily_summaries
          WHERE assignee_id = :assigneeId
          ORDER BY summary_date DESC
          LIMIT 14
          """, Map.of("assigneeId", assigneeId)));
      row.put("records", query("""
          SELECT r.*, i.title, i.item_type
          FROM intervention_item_records r
          JOIN intervention_publish_items i ON i.id = r.item_id
          WHERE r.assignee_id = :assigneeId
          ORDER BY r.plan_date DESC, i.order_no
          LIMIT 80
          """, Map.of("assigneeId", assigneeId)));
    }
    return Map.of("plans", rows);
  }

  @Transactional
  public Map<String, Object> myToday(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    LocalDate today = LocalDate.now(ZoneOffset.UTC);
    ensureDefaultInterventionForUser(user.id());
    expireOverdueAssignees(user.id());
    ensureRecordsForDate(user.id(), today);
    List<Map<String, Object>> records = recordsForDate(user.id(), today);
    List<Map<String, Object>> merged = mergeTodayRecords(records);
    return Map.of(
        "date", today.toString(),
        "tasks", merged,
        "summary", summarizeTodayRecords(records, merged)
    );
  }

  @Transactional
  public Map<String, Object> myPlan(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    LocalDate today = LocalDate.now(ZoneOffset.UTC);
    ensureDefaultInterventionForUser(user.id());
    ensureRecordsForDate(user.id(), today);
    List<Map<String, Object>> plans = myTasks(user);
    LocalDate start = today.withDayOfMonth(1);
    LocalDate end = start.plusMonths(1).minusDays(1);
    return Map.of(
        "plans", plans,
        "today", myToday(user),
        "calendar", calendar(start.toString(), end.toString(), user)
    );
  }

  @Transactional
  public Map<String, Object> startItem(String recordId, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> record = loadMyRecord(recordId, user.id());
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE intervention_item_records
        SET status = CASE WHEN status = 'pending' THEN 'in_progress' ELSE status END,
            started_at = COALESCE(started_at, :now),
            updated_at = :now
        WHERE id = :id AND user_id = :userId AND status IN ('pending','in_progress','completed')
        """,
        new MapSqlParameterSource()
            .addValue("id", recordId)
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now)));
    refreshAssignee(string(record.get("assignee_id")));
    return loadMyRecord(recordId, user.id());
  }

  @Transactional
  public Map<String, Object> completeItem(String recordId, Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> record = loadMyRecord(recordId, user.id());
    return completeRecordsByMaterial(
        user.id(),
        localDate(record.get("plan_date"), LocalDate.now(ZoneOffset.UTC)),
        string(record.get("material_id")),
        firstText(payload == null ? null : payload.get("source_ref_table")),
        firstText(payload == null ? null : payload.get("source_ref_id")),
        intValue(payload == null ? null : payload.get("duration_seconds"), intValue(record.get("duration_sec"), 10)),
        map(payload == null ? null : payload.get("summary_json"))
    );
  }

  @Transactional
  public Map<String, Object> completeTodayMood(Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    LocalDate today = LocalDate.now(ZoneOffset.UTC);
    ensureDefaultInterventionForUser(user.id());
    ensureRecordsForDate(user.id(), today);
    List<Map<String, Object>> moodRecords = query("""
        SELECT r.* FROM intervention_item_records r
        JOIN intervention_publish_items i ON i.id = r.item_id
        WHERE r.user_id = :userId AND r.plan_date = :today AND i.item_type = 'mood'
          AND r.status IN ('pending','in_progress')
        """, Map.of("userId", user.id(), "today", Date.valueOf(today)));
    if (moodRecords.isEmpty()) {
      return Map.of("completed", false, "reason", "no_pending_mood_task");
    }
    String materialId = string(moodRecords.getFirst().get("material_id"));
    return completeRecordsByMaterial(
        user.id(),
        today,
        materialId,
        firstText(payload == null ? null : payload.get("source_ref_table"), "emotion_diaries"),
        firstText(payload == null ? null : payload.get("source_ref_id")),
        0,
        map(payload == null ? null : payload.get("summary_json"))
    );
  }

  public List<Map<String, Object>> calendar(String start, String end, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    ensureDefaultInterventionForUser(user.id());
    LocalDate now = LocalDate.now(ZoneOffset.UTC);
    LocalDate startDate = localDate(start, now.withDayOfMonth(1));
    LocalDate endDate = localDate(end, startDate.plusMonths(1).minusDays(1));
    return query("""
        SELECT s.*
        FROM intervention_daily_summaries s
        WHERE s.user_id = :userId AND s.summary_date BETWEEN :startDate AND :endDate
        ORDER BY s.summary_date
        """, Map.of("userId", user.id(), "startDate", Date.valueOf(startDate), "endDate", Date.valueOf(endDate)));
  }

  public Map<String, Object> calendarDate(String date, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    ensureDefaultInterventionForUser(user.id());
    LocalDate target = localDate(date, LocalDate.now(ZoneOffset.UTC));
    List<Map<String, Object>> records = recordsForDate(user.id(), target);
    List<Map<String, Object>> summaries = query("""
        SELECT * FROM intervention_daily_summaries
        WHERE user_id = :userId AND summary_date = :date
        ORDER BY created_at DESC
        """, Map.of("userId", user.id(), "date", Date.valueOf(target)));
    return Map.of(
        "date", target.toString(),
        "items", records,
        "tasks", mergeTodayRecords(records),
        "summaries", summaries
    );
  }

  @Transactional
  public Map<String, Object> assignDefaultByAssessment(String assessmentId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> assessment = one("SELECT * FROM assessments WHERE id = :id LIMIT 1", Map.of("id", assessmentId));
    if (assessment == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "初筛报告不存在");
    }
    return assignDefaultByAssessment(assessmentId, string(assessment.get("user_id")));
  }

  @Transactional
  public Map<String, Object> assignDefaultByAssessment(String assessmentId, String userId) {
    if (assessmentId == null || assessmentId.isBlank() || userId == null || userId.isBlank()) {
      return Map.of("assigned", false, "reason", "empty_assessment_or_user");
    }
    Map<String, Object> existing = one("""
        SELECT id, batch_id FROM intervention_publish_assignees
        WHERE user_id = :userId AND source_assessment_id = :assessmentId
        LIMIT 1
        """, Map.of("userId", userId, "assessmentId", assessmentId));
    if (existing != null) {
      return Map.of("assigned", false, "reason", "already_assigned", "assigneeId", existing.get("id"), "batchId", existing.get("batch_id"));
    }
    Map<String, Object> assessment = one("SELECT * FROM assessments WHERE id = :id AND user_id = :userId LIMIT 1", Map.of("id", assessmentId, "userId", userId));
    if (assessment == null) {
      return Map.of("assigned", false, "reason", "assessment_not_found");
    }
    String risk = riskFromAssessment(assessment);
    if ("none".equals(risk)) {
      return assignBaselinePlan(userId, assessmentId, "no_risk_screening_report");
    }
    Map<String, Object> template = one("""
        SELECT * FROM intervention_plan_templates
        WHERE risk_level = :risk AND auto_assign_enabled = TRUE AND status = 'active'
        ORDER BY updated_at DESC
        LIMIT 1
        """, Map.of("risk", risk));
    if (template == null) {
      return Map.of("assigned", false, "reason", "template_disabled", "riskLevel", risk);
    }
    List<Map<String, Object>> items = templateItems(string(template.get("id")));
    if (items.isEmpty()) {
      return Map.of("assigned", false, "reason", "template_empty", "riskLevel", risk);
    }
    Instant now = Instant.now();
    LocalDate start = LocalDate.now(ZoneOffset.UTC);
    int durationDays = intValue(template.get("duration_days"), 7);
    LocalDate end = start.plusDays(Math.max(1, durationDays) - 1L);
    String batchId = uuid();
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_batches (
          id, batch_type, template_id, source_assessment_id, title, description, risk_level, duration_days,
          daily_required_count, status, start_date, end_date, recipient_type, recipient_scope, published_at, created_at, updated_at
        ) VALUES (
          :id, 'auto_after_screening', :templateId, :assessmentId, :title, :description, :risk, :durationDays,
          :dailyRequiredCount, 'active', :startDate, :endDate, 'users', CAST(:scope AS JSON), :now, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("templateId", template.get("id"))
            .addValue("assessmentId", assessmentId)
            .addValue("title", template.get("title"))
            .addValue("description", template.get("description"))
            .addValue("risk", risk)
            .addValue("durationDays", durationDays)
            .addValue("dailyRequiredCount", intValue(template.get("daily_required_count"), 1))
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("scope", toJson(Map.of("user_ids", List.of(userId))))
            .addValue("now", Timestamp.from(now)));
    copyTemplateItemsToBatch(batchId, items, now);
    String assigneeId = uuid();
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_assignees (
          id, batch_id, user_id, source_assessment_id, status, start_date, end_date, created_at, updated_at
        ) VALUES (
          :id, :batchId, :userId, :assessmentId, 'pending', :startDate, :endDate, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", assigneeId)
            .addValue("batchId", batchId)
            .addValue("userId", userId)
            .addValue("assessmentId", assessmentId)
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("now", Timestamp.from(now)));
    return Map.of("assigned", true, "riskLevel", risk, "assigneeId", assigneeId, "batchId", batchId);
  }

  @Transactional
  public Map<String, Object> backfillDefaultInterventions(AuthUser authUser) {
    requireStaff(authUser);
    List<Map<String, Object>> users = query("""
        SELECT u.id, u.username
        FROM users u
        JOIN profiles p ON p.id = u.id
        WHERE u.role = 'user' AND COALESCE(u.status, 'active') = 'active'
        ORDER BY u.created_at DESC
        """, Map.of());
    int assigned = 0;
    int skipped = 0;
    List<Map<String, Object>> results = new ArrayList<>();
    for (Map<String, Object> row : users) {
      Map<String, Object> result = ensureDefaultInterventionForUser(string(row.get("id")));
      Map<String, Object> item = new LinkedHashMap<>(result);
      item.put("userId", row.get("id"));
      item.put("username", row.get("username"));
      results.add(item);
      if (bool(result.get("assigned"), false)) {
        assigned += 1;
      } else {
        skipped += 1;
      }
    }
    return Map.of(
        "total", users.size(),
        "assigned", assigned,
        "skipped", skipped,
        "results", results
    );
  }

  @Transactional
  public Map<String, Object> ensureDefaultInterventionForUser(String userId) {
    if (userId == null || userId.isBlank()) {
      return Map.of("assigned", false, "reason", "empty_user");
    }
    Map<String, Object> latestScreening = one("""
        SELECT *
        FROM assessments
        WHERE user_id = :userId
          AND assessment_type = 'assessment_package_report'
          AND JSON_UNQUOTE(JSON_EXTRACT(report, '$.packageData.taskType')) = 'initial_screening'
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
        """, Map.of("userId", userId));
    if (latestScreening != null) {
      return assignDefaultByAssessment(string(latestScreening.get("id")), userId);
    }
    return assignBaselinePlan(userId, null, "no_initial_screening_report");
  }

  private Map<String, Object> assignBaselinePlan(String userId, String sourceAssessmentId, String reason) {
    if (userId == null || userId.isBlank()) {
      return Map.of("assigned", false, "reason", "empty_user");
    }
    if (sourceAssessmentId != null && !sourceAssessmentId.isBlank()) {
      Map<String, Object> existing = one("""
          SELECT id, batch_id FROM intervention_publish_assignees
          WHERE user_id = :userId AND source_assessment_id = :sourceAssessmentId
          LIMIT 1
          """, Map.of("userId", userId, "sourceAssessmentId", sourceAssessmentId));
      if (existing != null) {
        return Map.of("assigned", false, "reason", "already_assigned", "assigneeId", existing.get("id"), "batchId", existing.get("batch_id"));
      }
    } else {
      Map<String, Object> existing = one("""
          SELECT a.id, a.batch_id
          FROM intervention_publish_assignees a
          JOIN intervention_publish_batches b ON b.id = a.batch_id
          WHERE a.user_id = :userId AND b.batch_type = 'auto_baseline'
          LIMIT 1
          """, Map.of("userId", userId));
      if (existing != null) {
        return Map.of("assigned", false, "reason", "baseline_already_assigned", "assigneeId", existing.get("id"), "batchId", existing.get("batch_id"));
      }
    }
    List<String> materialIds = List.of(
        "10000000-0000-0000-0000-000000000001",
        "10000000-0000-0000-0000-000000000002"
    );
    List<Map<String, Object>> materials = new ArrayList<>();
    for (String materialId : materialIds) {
      materials.add(loadMaterial(materialId));
    }
    Instant now = Instant.now();
    LocalDate start = LocalDate.now(ZoneOffset.UTC);
    LocalDate end = start.plusDays(2);
    String batchId = uuid();
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_batches (
          id, batch_type, source_assessment_id, title, description, risk_level, duration_days,
          daily_required_count, status, start_date, end_date, recipient_type, recipient_scope,
          published_at, created_at, updated_at
        ) VALUES (
          :id, 'auto_baseline', :sourceAssessmentId, :title, :description, 'low', 3,
          1, 'active', :startDate, :endDate, 'users', CAST(:scope AS JSON),
          :now, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", batchId)
            .addValue("sourceAssessmentId", nullableString(sourceAssessmentId))
            .addValue("title", "基础稳定关怀计划")
            .addValue("description", "初筛未完成或暂无风险时自动发放的轻量干预：记录心情并完成短时呼吸放松。")
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("scope", toJson(Map.of("user_ids", List.of(userId), "reason", reason)))
            .addValue("now", Timestamp.from(now)));
    int order = 1;
    for (Map<String, Object> material : materials) {
      Map<String, Object> item = new LinkedHashMap<>();
      item.put("title", material.get("title"));
      item.put("required", true);
      item.put("frequency_type", "daily");
      item.put("required_count", 1);
      item.put("duration_sec", material.get("duration_sec"));
      item.put("config_json", Map.of("baseline", true));
      insertPublishItem(batchId, material, item, order++, now);
    }
    String assigneeId = uuid();
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_assignees (
          id, batch_id, user_id, source_assessment_id, status, start_date, end_date, created_at, updated_at
        ) VALUES (
          :id, :batchId, :userId, :sourceAssessmentId, 'pending', :startDate, :endDate, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", assigneeId)
            .addValue("batchId", batchId)
            .addValue("userId", userId)
            .addValue("sourceAssessmentId", nullableString(sourceAssessmentId))
            .addValue("startDate", Date.valueOf(start))
            .addValue("endDate", Date.valueOf(end))
            .addValue("now", Timestamp.from(now)));
    Map<String, Object> result = new LinkedHashMap<>();
    result.put("assigned", true);
    result.put("riskLevel", "none");
    result.put("reason", reason);
    result.put("assigneeId", assigneeId);
    result.put("batchId", batchId);
    return result;
  }

  private void replaceTemplateItems(String templateId, List<Map<String, Object>> items, Instant now) {
    jdbcTemplate.update("DELETE FROM intervention_plan_template_items WHERE template_id = :id", new MapSqlParameterSource("id", templateId));
    int order = 1;
    for (Map<String, Object> item : items) {
      Map<String, Object> material = loadMaterial(firstText(item.get("material_id"), item.get("id")));
      jdbcTemplate.update("""
          INSERT INTO intervention_plan_template_items (
            id, template_id, material_id, title, frequency_type, required_count, duration_sec, order_no, required, config_json, created_at
          ) VALUES (
            :id, :templateId, :materialId, :title, :frequencyType, :requiredCount, :durationSec, :orderNo, :required, CAST(:configJson AS JSON), :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", uuid())
              .addValue("templateId", templateId)
              .addValue("materialId", material.get("id"))
              .addValue("title", firstText(item.get("title"), material.get("title")))
              .addValue("frequencyType", firstText(item.get("frequency_type"), "daily"))
              .addValue("requiredCount", intValue(item.get("required_count"), 1))
              .addValue("durationSec", intValue(item.get("duration_sec"), intValue(material.get("duration_sec"), 10)))
              .addValue("orderNo", intValue(item.get("order_no"), order++))
              .addValue("required", bool(item.get("required"), true))
              .addValue("configJson", toJson(firstNonNull(item.get("config_json"), Map.of())))
              .addValue("now", Timestamp.from(now)));
    }
  }

  private void replacePublishItems(String batchId, List<Map<String, Object>> items, Instant now) {
    jdbcTemplate.update("DELETE FROM intervention_publish_items WHERE batch_id = :id", new MapSqlParameterSource("id", batchId));
    int order = 1;
    for (Map<String, Object> item : items) {
      Map<String, Object> material = loadMaterial(firstText(item.get("material_id"), item.get("id")));
      insertPublishItem(batchId, material, item, order++, now);
    }
  }

  private void copyTemplateItemsToBatch(String batchId, List<Map<String, Object>> items, Instant now) {
    int order = 1;
    for (Map<String, Object> item : items) {
      insertPublishItem(batchId, item, item, order++, now);
    }
  }

  private void insertPublishItem(String batchId, Map<String, Object> material, Map<String, Object> item, int order, Instant now) {
    jdbcTemplate.update("""
        INSERT INTO intervention_publish_items (
          id, batch_id, material_id, item_type, subtype, title, route_path, required, frequency_type,
          required_count, duration_sec, completion_mode, order_no, config_json, status, created_at
        ) VALUES (
          :id, :batchId, :materialId, :itemType, :subtype, :title, :routePath, :required, :frequencyType,
          :requiredCount, :durationSec, :completionMode, :orderNo, CAST(:configJson AS JSON), 'enabled', :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", uuid())
            .addValue("batchId", batchId)
            .addValue("materialId", material.get("material_id") == null ? material.get("id") : material.get("material_id"))
            .addValue("itemType", firstText(material.get("category"), material.get("item_type")))
            .addValue("subtype", nullableString(firstNonNull(material.get("subtype"), item.get("subtype"))))
            .addValue("title", firstText(item.get("title"), material.get("title")))
            .addValue("routePath", firstText(material.get("route_path"), item.get("route_path"), "/healing"))
            .addValue("required", bool(item.get("required"), true))
            .addValue("frequencyType", firstText(item.get("frequency_type"), "daily"))
            .addValue("requiredCount", intValue(item.get("required_count"), 1))
            .addValue("durationSec", intValue(item.get("duration_sec"), intValue(material.get("duration_sec"), 10)))
            .addValue("completionMode", firstText(material.get("completion_mode"), item.get("completion_mode"), "countdown"))
            .addValue("orderNo", intValue(item.get("order_no"), order))
            .addValue("configJson", toJson(firstNonNull(item.get("config_json"), material.get("config_json"), Map.of())))
            .addValue("now", Timestamp.from(now)));
  }

  private void ensureRecordsForDate(String userId, LocalDate date) {
    List<Map<String, Object>> assignees = query("""
        SELECT a.*, b.daily_required_count, b.duration_days
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.user_id = :userId AND b.status = 'active'
          AND a.status IN ('pending','in_progress')
          AND :date BETWEEN a.start_date AND a.end_date
        """, Map.of("userId", userId, "date", Date.valueOf(date)));
    Instant now = Instant.now();
    for (Map<String, Object> assignee : assignees) {
      List<Map<String, Object>> items = selectDailyItems(publishItems(string(assignee.get("batch_id"))), assignee, date);
      List<String> selectedItemIds = items.stream().map(item -> string(item.get("id"))).toList();
      if (!selectedItemIds.isEmpty()) {
        jdbcTemplate.update("""
            UPDATE intervention_item_records
            SET status = 'cancelled', updated_at = :now
            WHERE assignee_id = :assigneeId AND plan_date = :planDate
              AND item_id NOT IN (:itemIds)
              AND status IN ('pending','in_progress')
            """,
            new MapSqlParameterSource()
                .addValue("assigneeId", assignee.get("id"))
                .addValue("planDate", Date.valueOf(date))
                .addValue("itemIds", selectedItemIds)
                .addValue("now", Timestamp.from(now)));
      }
      for (Map<String, Object> item : items) {
        jdbcTemplate.update("""
            INSERT IGNORE INTO intervention_item_records (
              id, assignee_id, batch_id, item_id, material_id, user_id, plan_date, status, created_at, updated_at
            ) VALUES (
              :id, :assigneeId, :batchId, :itemId, :materialId, :userId, :planDate, 'pending', :now, :now
            )
            """,
            new MapSqlParameterSource()
                .addValue("id", uuid())
                .addValue("assigneeId", assignee.get("id"))
                .addValue("batchId", assignee.get("batch_id"))
                .addValue("itemId", item.get("id"))
                .addValue("materialId", item.get("material_id"))
                .addValue("userId", userId)
                .addValue("planDate", Date.valueOf(date))
                .addValue("now", Timestamp.from(now)));
      }
      refreshDailySummary(string(assignee.get("id")), date);
      refreshAssignee(string(assignee.get("id")));
    }
  }

  private void expireOverdueAssignees() {
    expireOverdueAssignees(null);
  }

  private void expireOverdueAssignees(String userId) {
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("today", Date.valueOf(LocalDate.now(ZoneOffset.UTC)))
        .addValue("now", Timestamp.from(Instant.now()));
    String userClause = "";
    if (userId != null && !userId.isBlank()) {
      userClause = " AND user_id = :userId";
      params.addValue("userId", userId);
    }
    List<Map<String, Object>> expired = query("""
        SELECT id, batch_id FROM intervention_publish_assignees
        WHERE status IN ('pending','in_progress') AND end_date < :today
        %s
        """.formatted(userClause), params.getValues());
    if (expired.isEmpty()) return;
    jdbcTemplate.update("""
        UPDATE intervention_publish_assignees
        SET status = 'expired', updated_at = :now
        WHERE id IN (:ids)
        """, new MapSqlParameterSource()
            .addValue("ids", expired.stream().map(row -> string(row.get("id"))).toList())
            .addValue("now", params.getValue("now")));
    jdbcTemplate.update("""
        UPDATE intervention_item_records
        SET status = 'expired', updated_at = :now
        WHERE assignee_id IN (:ids) AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource()
            .addValue("ids", expired.stream().map(row -> string(row.get("id"))).toList())
            .addValue("now", params.getValue("now")));
    for (Map<String, Object> row : expired) {
      syncFinishAlert(string(row.get("id")), "expired");
      refreshBatch(string(row.get("batch_id")));
    }
  }

  private List<Map<String, Object>> selectDailyItems(List<Map<String, Object>> items, Map<String, Object> assignee, LocalDate date) {
    if (items.isEmpty()) return items;
    int dailyCount = Math.max(1, intValue(assignee.get("daily_required_count"), 1));
    if (items.size() <= dailyCount) return items;
    String seed = string(assignee.get("id")) + "|" + date;
    return items.stream()
        .sorted(Comparator.comparingInt(item -> Math.floorMod((seed + "|" + item.get("id")).hashCode(), Integer.MAX_VALUE)))
        .limit(dailyCount)
        .toList();
  }

  private Map<String, Object> completeRecordsByMaterial(
      String userId,
      LocalDate date,
      String materialId,
      String sourceTable,
      String sourceId,
      int durationSeconds,
      Map<String, Object> summary) {
    List<Map<String, Object>> records = query("""
        SELECT * FROM intervention_item_records
        WHERE user_id = :userId AND plan_date = :date AND material_id = :materialId
          AND status IN ('pending','in_progress','completed')
        """, Map.of("userId", userId, "date", Date.valueOf(date), "materialId", materialId));
    if (records.isEmpty()) {
      throw new ApiException(HttpStatus.NOT_FOUND, "干预任务不存在或已结束");
    }
    Instant now = Instant.now();
    List<String> ids = records.stream().map(row -> string(row.get("id"))).toList();
    List<String> assigneeIds = records.stream().map(row -> string(row.get("assignee_id"))).distinct().toList();
    jdbcTemplate.update("""
        UPDATE intervention_item_records
        SET status = 'completed',
            source_ref_table = :sourceTable,
            source_ref_id = :sourceId,
            duration_seconds = :durationSeconds,
            summary_json = CAST(:summary AS JSON),
            started_at = COALESCE(started_at, :now),
            completed_at = COALESCE(completed_at, :now),
            updated_at = :now
        WHERE id IN (:ids)
        """,
        new MapSqlParameterSource()
            .addValue("ids", ids)
            .addValue("sourceTable", nullableString(sourceTable))
            .addValue("sourceId", nullableString(sourceId))
            .addValue("durationSeconds", Math.max(0, durationSeconds))
            .addValue("summary", toJson(summary.isEmpty() ? Map.of("completedAt", now.toString()) : summary))
            .addValue("now", Timestamp.from(now)));
    for (String assigneeId : assigneeIds) {
      refreshDailySummary(assigneeId, date);
      refreshAssignee(assigneeId);
    }
    return Map.of(
        "completed", true,
        "recordIds", ids,
        "tasks", mergeTodayRecords(recordsForDate(userId, date))
    );
  }

  private void refreshDailySummary(String assigneeId, LocalDate date) {
    Map<String, Object> assignee = one("""
        SELECT a.*, b.daily_required_count
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.id = :id
        LIMIT 1
        """, Map.of("id", assigneeId));
    if (assignee == null) return;
    List<Map<String, Object>> records = query("""
        SELECT r.*, i.title, i.item_type
        FROM intervention_item_records r
        JOIN intervention_publish_items i ON i.id = r.item_id
        WHERE r.assignee_id = :assigneeId AND r.plan_date = :date
        ORDER BY i.order_no
        """, Map.of("assigneeId", assigneeId, "date", Date.valueOf(date)));
    int target = Math.min(Math.max(1, intValue(assignee.get("daily_required_count"), 1)), records.size());
    int completed = Math.min((int) records.stream().filter(row -> "completed".equals(row.get("status"))).count(), target);
    String summaryText = completed >= target
        ? "今日干预目标已完成，建议保持稳定节奏。"
        : "今日还有干预项目待完成，可从任务中心继续进入。";
    String mood = records.stream()
        .filter(row -> "mood".equals(row.get("item_type")) && "completed".equals(row.get("status")))
        .findFirst()
        .map(row -> string(map(row.get("summary_json")).get("mood")))
        .orElse(null);
    jdbcTemplate.update("""
        INSERT INTO intervention_daily_summaries (
          id, assignee_id, user_id, summary_date, completed_count, required_count, mood_level, summary_text, details_json, created_at, updated_at
        ) VALUES (
          :id, :assigneeId, :userId, :date, :completed, :required, :mood, :summaryText, CAST(:details AS JSON), :now, :now
        )
        ON DUPLICATE KEY UPDATE
          completed_count = VALUES(completed_count),
          required_count = VALUES(required_count),
          mood_level = VALUES(mood_level),
          summary_text = VALUES(summary_text),
          details_json = VALUES(details_json),
          updated_at = VALUES(updated_at)
        """,
        new MapSqlParameterSource()
            .addValue("id", uuid())
            .addValue("assigneeId", assigneeId)
            .addValue("userId", assignee.get("user_id"))
            .addValue("date", Date.valueOf(date))
            .addValue("completed", completed)
            .addValue("required", target)
            .addValue("mood", mood)
            .addValue("summaryText", summaryText)
            .addValue("details", toJson(records))
            .addValue("now", Timestamp.from(Instant.now())));
  }

  private void refreshAssignee(String assigneeId) {
    if (assigneeId == null || assigneeId.isBlank()) return;
    Map<String, Object> assignee = one("""
        SELECT a.*, b.duration_days
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.id = :id
        LIMIT 1
        """, Map.of("id", assigneeId));
    if (assignee == null) return;
    List<Map<String, Object>> summaries = query("""
        SELECT * FROM intervention_daily_summaries WHERE assignee_id = :id
        """, Map.of("id", assigneeId));
    int completedDays = (int) summaries.stream()
        .filter(row -> intValue(row.get("completed_count"), 0) >= Math.max(0, intValue(row.get("required_count"), 0)))
        .count();
    int totalCompleted = summaries.stream().mapToInt(row -> intValue(row.get("completed_count"), 0)).sum();
    LocalDate end = localDate(assignee.get("end_date"), LocalDate.now(ZoneOffset.UTC));
    boolean expired = LocalDate.now(ZoneOffset.UTC).isAfter(end);
    boolean completed = completedDays >= Math.max(1, intValue(assignee.get("duration_days"), intValue(assignee.get("completed_days"), 0)));
    boolean started = totalCompleted > 0 || summaries.stream().anyMatch(row -> intValue(row.get("completed_count"), 0) > 0);
    String status = completed ? "completed" : expired ? "expired" : started ? "in_progress" : "pending";
    jdbcTemplate.update("""
        UPDATE intervention_publish_assignees
        SET status = :status,
            completed_days = :completedDays,
            total_completed_count = :totalCompleted,
            last_completed_at = CASE WHEN :totalCompleted > 0 THEN COALESCE(last_completed_at, :now) ELSE last_completed_at END,
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", assigneeId)
            .addValue("status", status)
            .addValue("completedDays", completedDays)
            .addValue("totalCompleted", totalCompleted)
            .addValue("now", Timestamp.from(Instant.now())));
    if ("completed".equals(status) || "expired".equals(status)) {
      syncFinishAlert(assigneeId, status);
    }
    refreshBatch(string(assignee.get("batch_id")));
  }

  private void refreshBatch(String batchId) {
    Map<String, Object> open = one("""
        SELECT id FROM intervention_publish_assignees
        WHERE batch_id = :batchId AND status IN ('pending','in_progress')
        LIMIT 1
        """, Map.of("batchId", batchId));
    if (open == null) {
      jdbcTemplate.update("""
          UPDATE intervention_publish_batches
          SET status = CASE WHEN status = 'active' THEN 'completed' ELSE status END,
              updated_at = :now
          WHERE id = :batchId
          """, new MapSqlParameterSource().addValue("batchId", batchId).addValue("now", Timestamp.from(Instant.now())));
    }
  }

  private void syncFinishAlert(String assigneeId, String status) {
    Map<String, Object> data = one("""
        SELECT a.*, b.title, b.risk_level
        FROM intervention_publish_assignees a
        JOIN intervention_publish_batches b ON b.id = a.batch_id
        WHERE a.id = :id
        LIMIT 1
        """, Map.of("id", assigneeId));
    if (data == null) return;
    Map<String, Object> existing = one("""
        SELECT id FROM risk_alerts WHERE data_source = 'intervention_task' AND source_id = :sourceId LIMIT 1
        """, Map.of("sourceId", assigneeId));
    String description = "completed".equals(status)
        ? "干预任务已完成，建议医生复查完成质量并决定是否继续随访。"
        : "干预周期已结束，建议医生查看完成率并决定是否重新发布计划。";
    int risk = switch (string(data.get("risk_level"))) {
      case "high" -> 8;
      case "middle" -> 6;
      default -> 4;
    };
    if (existing == null) {
      jdbcTemplate.update("""
          INSERT INTO risk_alerts (
            id, patient_id, alert_type, risk_level, description, data_source, source_id, is_handled, created_at
          ) VALUES (
            :id, :patientId, '干预任务结束提醒', :risk, :description, 'intervention_task', :sourceId, FALSE, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", uuid())
              .addValue("patientId", data.get("user_id"))
              .addValue("risk", risk)
              .addValue("description", description)
              .addValue("sourceId", assigneeId)
              .addValue("now", Timestamp.from(Instant.now())));
    }
  }

  private List<Map<String, Object>> mergeTodayRecords(List<Map<String, Object>> records) {
    Map<String, Map<String, Object>> grouped = new LinkedHashMap<>();
    for (Map<String, Object> record : records) {
      String key = string(record.get("material_id")) + "|" + string(record.get("plan_date"));
      Map<String, Object> current = grouped.computeIfAbsent(key, ignored -> new LinkedHashMap<>(record));
      List<String> ids = stringList(current.get("record_ids"));
      ids.add(string(record.get("id")));
      current.put("record_ids", ids);
      if (!"completed".equals(record.get("status"))) {
        current.put("status", record.get("status"));
        current.put("id", record.get("id"));
      }
      current.put("navigation_path", buildNavigationPath(current));
    }
    return new ArrayList<>(grouped.values());
  }

  private String buildNavigationPath(Map<String, Object> record) {
    String route = string(record.get("route_path"), "/healing");
    String separator = route.contains("?") ? "&" : "?";
    return route + separator
        + "interventionRecordId=" + record.get("id")
        + "&interventionAssigneeId=" + record.get("assignee_id")
        + "&materialId=" + record.get("material_id")
        + (string(record.get("target_ref_id")).isBlank() ? "" : "&targetRefId=" + record.get("target_ref_id"))
        + "&duration=" + intValue(record.get("duration_sec"), 10)
        + "&returnTo=/assessment-tasks";
  }

  private Map<String, Object> summarizeTodayRecords(List<Map<String, Object>> records, List<Map<String, Object>> merged) {
    Map<String, List<Map<String, Object>>> byAssignee = records.stream()
        .collect(Collectors.groupingBy(row -> string(row.get("assignee_id")), LinkedHashMap::new, Collectors.toList()));
    int targetTotal = 0;
    int completedTarget = 0;
    int requiredTotal = 0;
    int optionalTotal = 0;
    for (List<Map<String, Object>> group : byAssignee.values()) {
      int requiredItems = group.size();
      int planTarget = Math.max(1, intValue(group.getFirst().get("daily_required_count"), 1));
      int effectiveTarget = Math.min(planTarget, requiredItems);
      int completedRequired = (int) group.stream().filter(row -> "completed".equals(row.get("status"))).count();
      targetTotal += effectiveTarget;
      completedTarget += Math.min(completedRequired, effectiveTarget);
      requiredTotal += requiredItems;
    }
    int itemTotal = merged.size();
    int itemCompleted = (int) merged.stream().filter(row -> "completed".equals(row.get("status"))).count();
    return Map.of(
        "total", itemTotal,
        "completed", itemCompleted,
        "pending", Math.max(0, itemTotal - itemCompleted),
        "itemTotal", itemTotal,
        "itemCompleted", itemCompleted,
        "requiredTotal", requiredTotal,
        "optionalTotal", optionalTotal,
        "planTargetTotal", targetTotal,
        "planCompletedTotal", completedTarget
    );
  }

  private List<Map<String, Object>> recordsForDate(String userId, LocalDate date) {
    return query("""
        SELECT r.*, i.title, i.item_type, i.route_path, i.frequency_type, i.required_count, i.duration_sec,
               i.completion_mode, i.required, i.order_no, i.config_json,
               b.title AS batch_title, b.risk_level, b.daily_required_count,
               m.description AS material_description, m.subtype, m.target_ref_table, m.target_ref_id,
               m.tags AS material_tags
        FROM intervention_item_records r
        JOIN intervention_publish_items i ON i.id = r.item_id
        JOIN intervention_publish_batches b ON b.id = r.batch_id
        JOIN intervention_materials m ON m.id = r.material_id
        WHERE r.user_id = :userId AND r.plan_date = :date
          AND r.status NOT IN ('cancelled','expired')
        ORDER BY FIELD(i.item_type, 'mood','meditation','knowledge','game','brain_intervention'), i.order_no
        """, Map.of("userId", userId, "date", Date.valueOf(date)));
  }

  private List<Map<String, Object>> templateItems(String templateId) {
    return query("""
        SELECT ti.*, m.code, m.description AS material_description, m.category, m.subtype, m.target_ref_table,
               m.target_ref_id, m.route_path, m.completion_mode, m.tags, m.config_json AS material_config_json
        FROM intervention_plan_template_items ti
        JOIN intervention_materials m ON m.id = ti.material_id
        WHERE ti.template_id = :templateId
        ORDER BY ti.order_no
        """, Map.of("templateId", templateId));
  }

  private List<Map<String, Object>> publishItems(String batchId) {
    return query("""
        SELECT i.*, m.code, m.description AS material_description, m.target_ref_table, m.target_ref_id,
               m.tags, m.config_json AS material_config_json
        FROM intervention_publish_items i
        JOIN intervention_materials m ON m.id = i.material_id
        WHERE i.batch_id = :batchId AND i.status = 'enabled'
        ORDER BY i.order_no
        """, Map.of("batchId", batchId));
  }

  private Map<String, Object> loadTemplateWithItems(String templateId) {
    Map<String, Object> template = loadTemplate(templateId);
    template.put("items", templateItems(templateId));
    return template;
  }

  private Map<String, Object> loadTemplate(String templateId) {
    Map<String, Object> row = one("SELECT * FROM intervention_plan_templates WHERE id = :id LIMIT 1", Map.of("id", templateId));
    if (row == null) throw new ApiException(HttpStatus.NOT_FOUND, "干预方案模板不存在");
    return row;
  }

  private Map<String, Object> loadTask(String batchId) {
    Map<String, Object> row = one("SELECT * FROM intervention_publish_batches WHERE id = :id LIMIT 1", Map.of("id", batchId));
    if (row == null) throw new ApiException(HttpStatus.NOT_FOUND, "干预任务不存在");
    return row;
  }

  private Map<String, Object> loadMaterial(String materialId) {
    if (materialId == null || materialId.isBlank()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择干预素材");
    }
    Map<String, Object> row = one("SELECT * FROM intervention_materials WHERE id = :id AND is_active = TRUE LIMIT 1", Map.of("id", materialId));
    if (row == null) throw new ApiException(HttpStatus.BAD_REQUEST, "干预素材不存在或已停用");
    return row;
  }

  private Map<String, Object> loadMyRecord(String recordId, String userId) {
    Map<String, Object> row = one("""
        SELECT r.*, i.title, i.item_type, i.route_path, i.duration_sec, i.completion_mode, i.config_json,
               b.status AS batch_status
        FROM intervention_item_records r
        JOIN intervention_publish_items i ON i.id = r.item_id
        JOIN intervention_publish_batches b ON b.id = r.batch_id
        WHERE r.id = :id AND r.user_id = :userId AND b.status = 'active'
        LIMIT 1
        """, Map.of("id", recordId, "userId", userId));
    if (row == null) throw new ApiException(HttpStatus.NOT_FOUND, "干预项目不存在或已结束");
    return row;
  }

  private List<String> validPatientIds(List<String> userIds) {
    if (userIds == null || userIds.isEmpty()) return List.of();
    return query("""
        SELECT id FROM profiles WHERE role = 'user' AND id IN (:ids)
        """, Map.of("ids", userIds)).stream().map(row -> string(row.get("id"))).toList();
  }

  private Map<String, Object> recipientScope(Map<String, Object> payload) {
    return Map.of(
        "user_ids", stringList(firstNonNull(payload.get("user_ids"), payload.get("recipient_user_ids"))),
        "department_ids", stringList(firstNonNull(payload.get("department_ids"), payload.get("recipient_department_ids"))));
  }

  private List<String> resolveRecipientUserIds(Map<String, Object> scope) {
    List<String> ids = new ArrayList<>(stringList(scope.get("user_ids")));
    List<String> departmentIds = stringList(scope.get("department_ids"));
    if (!departmentIds.isEmpty()) {
      ids.addAll(query("""
          SELECT id FROM profiles
          WHERE role = 'user' AND department_id IN (:departmentIds)
          """, Map.of("departmentIds", departmentIds)).stream().map(row -> string(row.get("id"))).toList());
    }
    return ids.stream().filter(id -> !id.isBlank()).distinct().toList();
  }

  private String riskFromAssessment(Map<String, Object> assessment) {
    Map<String, Object> report = map(assessment.get("report"));
    String warning = string(map(report.get("overall")).get("riskLevel"));
    if (!warning.isBlank()) return normalizeRisk(warning);
    int score = intValue(firstNonNull(map(report.get("overall")).get("score"), assessment.get("score")), intValue(assessment.get("risk_level"), 0) * 10);
    if (score >= 75) return "high";
    if (score >= 45) return "middle";
    return "low";
  }

  private String normalizeRisk(String value) {
    return switch (string(value)) {
      case "high" -> "high";
      case "middle", "medium" -> "middle";
      case "none", "no", "normal" -> "none";
      default -> "low";
    };
  }

  private AuthUser requireUser(AuthUser user) {
    if (user == null) {
      throw new ApiException(HttpStatus.UNAUTHORIZED, "请先登录");
    }
    return user;
  }

  private AuthUser requireStaff(AuthUser user) {
    user = requireUser(user);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可操作");
    }
    return user;
  }

  private List<Map<String, Object>> query(String sql, Map<String, ?> params) {
    return jdbcTemplate.query(sql, new MapSqlParameterSource(params), new ColumnMapRowMapper())
        .stream().map(this::normalizeRow).collect(Collectors.toCollection(ArrayList::new));
  }

  private Map<String, Object> one(String sql, Map<String, ?> params) {
    List<Map<String, Object>> rows = query(sql, params);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private Map<String, Object> normalizeRow(Map<String, Object> row) {
    Map<String, Object> normalized = new LinkedHashMap<>();
    for (Map.Entry<String, Object> entry : row.entrySet()) {
      String key = entry.getKey().toLowerCase();
      Object value = entry.getValue();
      if (value instanceof Timestamp timestamp) {
        normalized.put(key, timestamp.toInstant().toString());
      } else if (value instanceof Date date) {
        normalized.put(key, date.toString());
      } else if (value instanceof String text && isJsonColumn(key) && !text.isBlank()) {
        try {
          normalized.put(key, objectMapper.readValue(text, new TypeReference<Object>() {}));
        } catch (JsonProcessingException ignored) {
          normalized.put(key, value);
        }
      } else {
        normalized.put(key, value);
      }
    }
    return normalized;
  }

  private boolean isJsonColumn(String key) {
    return key.endsWith("json") || key.endsWith("_json") || "tags".equals(key) || "recipient_scope".equals(key)
        || "summary_json".equals(key) || "details_json".equals(key) || "config_json".equals(key)
        || "material_config_json".equals(key);
  }

  private String toJson(Object value) {
    try {
      return objectMapper.writeValueAsString(value == null ? Map.of() : value);
    } catch (JsonProcessingException e) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "JSON 序列化失败");
    }
  }

  private Map<String, Object> map(Object value) {
    if (value instanceof Map<?, ?> raw) {
      Map<String, Object> result = new LinkedHashMap<>();
      raw.forEach((key, item) -> result.put(String.valueOf(key), item));
      return result;
    }
    if (value instanceof String text && !text.isBlank()) {
      try {
        return objectMapper.readValue(text, new TypeReference<Map<String, Object>>() {});
      } catch (JsonProcessingException ignored) {
      }
    }
    return new LinkedHashMap<>();
  }

  private List<Map<String, Object>> list(Object value) {
    if (value instanceof List<?> raw) {
      return raw.stream().filter(Map.class::isInstance).map(Map.class::cast).map(this::map).toList();
    }
    return List.of();
  }

  private List<String> stringList(Object value) {
    if (value instanceof Collection<?> collection) {
      return collection.stream().map(this::string).filter(item -> !item.isBlank()).distinct().toList();
    }
    if (value instanceof String text && !text.isBlank()) {
      return List.of(text);
    }
    return new ArrayList<>();
  }

  private Object firstNonNull(Object... values) {
    for (Object value : values) {
      if (value != null) return value;
    }
    return null;
  }

  private String firstText(Object... values) {
    for (Object value : values) {
      String text = string(value);
      if (!text.isBlank()) return text;
    }
    return "";
  }

  private String string(Object value) {
    return value == null ? "" : String.valueOf(value);
  }

  private String string(Object value, String fallback) {
    String text = string(value);
    return text.isBlank() ? fallback : text;
  }

  private String nullableString(Object value) {
    String text = string(value);
    return text.isBlank() ? null : text;
  }

  private String requiredString(Map<String, Object> payload, String key, String message) {
    String text = string(payload.get(key));
    if (text.isBlank()) throw new ApiException(HttpStatus.BAD_REQUEST, message);
    return text;
  }

  private int intValue(Object value, int fallback) {
    if (value instanceof Number number) return number.intValue();
    try {
      return value == null ? fallback : Integer.parseInt(String.valueOf(value));
    } catch (NumberFormatException ignored) {
      return fallback;
    }
  }

  private boolean bool(Object value, boolean fallback) {
    if (value instanceof Boolean b) return b;
    if (value instanceof Number number) return number.intValue() != 0;
    if (value instanceof String text) {
      if ("true".equalsIgnoreCase(text) || "1".equals(text)) return true;
      if ("false".equalsIgnoreCase(text) || "0".equals(text)) return false;
    }
    return fallback;
  }

  private LocalDate localDate(Object value, LocalDate fallback) {
    if (value instanceof Date date) return date.toLocalDate();
    if (value instanceof java.util.Date date) return date.toInstant().atZone(ZoneOffset.UTC).toLocalDate();
    String text = string(value);
    if (!text.isBlank()) {
      try {
        return LocalDate.parse(text.length() > 10 ? text.substring(0, 10) : text);
      } catch (Exception ignored) {
      }
    }
    return fallback;
  }

  private String uuid() {
    return UUID.randomUUID().toString();
  }
}
