package chuxin.assessmenttasks;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import chuxin.interventiontasks.InterventionTaskService;
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
public class AssessmentPublishTaskService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;
  private final InterventionTaskService interventionTaskService;

  public AssessmentPublishTaskService(
      NamedParameterJdbcTemplate jdbcTemplate,
      ObjectMapper objectMapper,
      InterventionTaskService interventionTaskService) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
    this.interventionTaskService = interventionTaskService;
  }

  public List<Map<String, Object>> listTasks(AuthUser authUser) {
    requireStaff(authUser);
    return query("""
        SELECT b.*,
          (SELECT COUNT(*) FROM assessment_publish_items i WHERE i.batch_id = b.id) AS item_count,
          (SELECT COUNT(*) FROM assessment_publish_assignees a WHERE a.batch_id = b.id) AS assignee_count,
          (SELECT COUNT(*) FROM assessment_publish_assignees a WHERE a.batch_id = b.id AND a.status = 'completed') AS completed_count
        FROM assessment_publish_batches b
        ORDER BY b.created_at DESC
        """, Map.of());
  }

  public Map<String, Object> getTask(String taskId, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> task = loadTask(taskId);
    task.put("items", query("SELECT * FROM assessment_publish_items WHERE batch_id = :id ORDER BY order_no", Map.of("id", taskId)));
    task.put("assignees", queryAssignees(taskId));
    return task;
  }

  @Transactional
  public Map<String, Object> createTask(Map<String, Object> payload, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    String taskId = uuid();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO assessment_publish_batches (
          id, title, description, status, start_at, end_at, recipient_type, recipient_scope, created_by, created_at, updated_at
        ) VALUES (
          :id, :title, :description, 'draft', :startAt, :endAt, 'users', CAST(:scope AS JSON), :createdBy, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", taskId)
            .addValue("title", requiredString(payload, "title", "请填写发布测评任务标题"))
            .addValue("description", nullableString(payload.get("description")))
            .addValue("startAt", timestamp(payload.get("start_at")))
            .addValue("endAt", timestamp(payload.get("end_at")))
            .addValue("scope", toJson(recipientScope(payload)))
            .addValue("createdBy", staff.id())
            .addValue("now", Timestamp.from(now)));
    replaceItems(taskId, list(payload.get("items")), now);
    return getTask(taskId, authUser);
  }

  @Transactional
  public Map<String, Object> updateTask(String taskId, Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> existing = loadTask(taskId);
    if (!"draft".equals(existing.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "只能编辑草稿测评任务");
    }
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE assessment_publish_batches
        SET title = :title,
            description = :description,
            start_at = :startAt,
            end_at = :endAt,
            recipient_scope = CAST(:scope AS JSON),
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", taskId)
            .addValue("title", requiredString(payload, "title", "请填写发布测评任务标题"))
            .addValue("description", nullableString(payload.get("description")))
            .addValue("startAt", timestamp(payload.get("start_at")))
            .addValue("endAt", timestamp(payload.get("end_at")))
            .addValue("scope", toJson(recipientScope(payload)))
            .addValue("now", Timestamp.from(now)));
    replaceItems(taskId, list(payload.get("items")), now);
    return getTask(taskId, authUser);
  }

  @Transactional
  public Map<String, Object> publishTask(String taskId, AuthUser authUser) {
    AuthUser staff = requireStaff(authUser);
    Map<String, Object> task = loadTask(taskId);
    if ("active".equals(task.get("status"))) {
      return getTask(taskId, authUser);
    }
    if (!"draft".equals(task.get("status"))) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评任务不能发布");
    }
    List<Map<String, Object>> items = query("SELECT * FROM assessment_publish_items WHERE batch_id = :id ORDER BY order_no", Map.of("id", taskId));
    if (items.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请至少添加一个测评项目");
    }
    for (Map<String, Object> item : items) {
      if (!List.of("scale", "neuropsych", "dialogue_scale", "voice", "expression").contains(string(item.get("item_type")))) {
        throw new ApiException(HttpStatus.BAD_REQUEST, "该测评类型暂未开发，不能发布: " + item.get("title"));
      }
    }
    Map<String, Object> scope = map(task.get("recipient_scope"));
    List<String> userIds = resolveRecipientUserIds(scope);
    List<String> validUsers = validPatientIds(userIds);
    if (validUsers.isEmpty() || validUsers.size() != userIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请选择有效患者");
    }
    Instant now = Instant.now();
    String scalePlanId = createScalePlanIfNeeded(task, items, validUsers, staff, now);
    jdbcTemplate.update("""
        UPDATE assessment_publish_batches
        SET status = 'active', published_at = :now, updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource().addValue("id", taskId).addValue("now", Timestamp.from(now)));
    for (String userId : validUsers) {
      String assigneeId = uuid();
      jdbcTemplate.update("""
          INSERT INTO assessment_publish_assignees (id, batch_id, user_id, status, created_at, updated_at)
          VALUES (:id, :batchId, :userId, 'pending', :now, :now)
          """,
          new MapSqlParameterSource()
              .addValue("id", assigneeId)
              .addValue("batchId", taskId)
              .addValue("userId", userId)
              .addValue("now", Timestamp.from(now)));
      for (Map<String, Object> item : items) {
        createItemRecord(taskId, assigneeId, userId, item, scalePlanId, now);
      }
    }
    return getTask(taskId, authUser);
  }

  @Transactional
  public Map<String, Object> stopTask(String taskId, AuthUser authUser) {
    requireStaff(authUser);
    jdbcTemplate.update("""
        UPDATE assessment_publish_batches SET status = 'stopped', updated_at = :now WHERE id = :id
        """, new MapSqlParameterSource().addValue("id", taskId).addValue("now", Timestamp.from(Instant.now())));
    jdbcTemplate.update("""
        UPDATE assessment_publish_item_records
        SET status = 'cancelled', updated_at = :now
        WHERE batch_id = :id AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource().addValue("id", taskId).addValue("now", Timestamp.from(Instant.now())));
    jdbcTemplate.update("""
        UPDATE assessment_publish_assignees
        SET status = 'cancelled', updated_at = :now
        WHERE batch_id = :id AND status IN ('pending','in_progress')
        """, new MapSqlParameterSource().addValue("id", taskId).addValue("now", Timestamp.from(Instant.now())));
    return getTask(taskId, authUser);
  }

  public Map<String, Object> materials(AuthUser authUser) {
    requireStaff(authUser);
    return Map.of(
        "scale", query("SELECT id, title, code, survey_type, status FROM scale_surveys WHERE status = 'published' ORDER BY updated_at DESC", Map.of()),
        "neuropsych", query("SELECT id, code, title, dimension, estimated_minutes, status FROM neuropsych_tests WHERE status = 'active' ORDER BY estimated_minutes, created_at", Map.of()),
        "reserved", List.of(
            Map.of("type", "dialogue_scale", "title", "对话式心理健康评估", "enabled", true),
            Map.of("type", "voice", "title", "语音识别", "enabled", true),
            Map.of("type", "expression", "title", "表情评估", "enabled", true),
            Map.of("type", "multimodal_baseline", "title", "多模态基线", "enabled", false)
        )
    );
  }

  @Transactional
  public Map<String, Object> assignDefaultTaskToUser(String userId) {
    if (userId == null || userId.isBlank()) {
      return Map.of("assigned", false, "reason", "empty_user");
    }
    Map<String, Object> task = one("""
        SELECT * FROM assessment_publish_batches
        WHERE batch_type = 'auto_default'
          AND template_code = 'default_forensic_risk_screening'
          AND auto_assign_enabled = TRUE
          AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
        """, Map.of());
    if (task == null) {
      return Map.of("assigned", false, "reason", "template_disabled");
    }
    String taskId = string(task.get("id"));
    Map<String, Object> existing = one("""
        SELECT id FROM assessment_publish_assignees WHERE batch_id = :batchId AND user_id = :userId LIMIT 1
        """, Map.of("batchId", taskId, "userId", userId));
    if (existing != null) {
      return Map.of("assigned", false, "reason", "already_assigned", "assigneeId", existing.get("id"));
    }
    List<Map<String, Object>> items = query("""
        SELECT * FROM assessment_publish_items
        WHERE batch_id = :batchId AND status = 'enabled'
        ORDER BY order_no
        """, Map.of("batchId", taskId));
    if (items.isEmpty()) {
      return Map.of("assigned", false, "reason", "template_empty");
    }
    Instant now = Instant.now();
    String assigneeId = uuid();
    jdbcTemplate.update("""
        INSERT INTO assessment_publish_assignees (id, batch_id, user_id, status, created_at, updated_at)
        VALUES (:id, :batchId, :userId, 'pending', :now, :now)
        """,
        new MapSqlParameterSource()
            .addValue("id", assigneeId)
            .addValue("batchId", taskId)
            .addValue("userId", userId)
            .addValue("now", Timestamp.from(now)));
    String scalePlanId = createScalePlanIfNeeded(task, items, List.of(userId), null, now);
    for (Map<String, Object> item : items) {
      createItemRecord(taskId, assigneeId, userId, item, scalePlanId, now);
    }
    return Map.of("assigned", true, "assigneeId", assigneeId, "taskId", taskId);
  }

  public Map<String, Object> getMyTaskDetail(String assigneeId, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> assignee = one("""
        SELECT a.*, b.title AS batch_title, b.description AS batch_description, b.batch_type,
               b.template_code, b.start_at, b.end_at
        FROM assessment_publish_assignees a
        JOIN assessment_publish_batches b ON b.id = a.batch_id
        WHERE a.id = :id AND a.user_id = :userId
        LIMIT 1
        """, Map.of("id", assigneeId, "userId", user.id()));
    if (assignee == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "测评任务不存在");
    }
    assignee.put("items", enrichItemRecords(queryItemRecords(assigneeId)));
    assignee.put("package_report", loadPackageReport(assigneeId, user.id()));
    return assignee;
  }

  @Transactional
  public Map<String, Object> startItem(String itemRecordId, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> itemRecord = loadMyItemRecord(itemRecordId, user.id());
    String itemType = string(itemRecord.get("item_type"));
    if (List.of("scale", "neuropsych").contains(itemType)) {
      return itemRecord;
    }
    if (!List.of("dialogue_scale", "voice", "expression").contains(itemType)) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评类型暂未开放");
    }
    Instant now = Instant.now();
    ensureModuleRecord(itemRecord, now);
    jdbcTemplate.update("""
        UPDATE assessment_publish_item_records
        SET status = 'in_progress',
            started_at = COALESCE(started_at, :now),
            updated_at = :now
        WHERE id = :id AND user_id = :userId AND status IN ('pending','in_progress')
        """,
        new MapSqlParameterSource()
            .addValue("id", itemRecordId)
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now)));
    jdbcTemplate.update("""
        UPDATE assessment_task_module_records
        SET status = 'in_progress',
            started_at = COALESCE(started_at, :now),
            updated_at = :now
        WHERE item_record_id = :id AND user_id = :userId AND status IN ('pending','in_progress')
        """,
        new MapSqlParameterSource()
            .addValue("id", itemRecordId)
            .addValue("userId", user.id())
            .addValue("now", Timestamp.from(now)));
    refreshAssigneeById(string(itemRecord.get("assignee_id")), now);
    return getMyTaskDetail(string(itemRecord.get("assignee_id")), user);
  }

  @Transactional
  public Map<String, Object> submitModuleItem(String itemRecordId, Map<String, Object> payload, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> itemRecord = loadMyItemRecord(itemRecordId, user.id());
    String itemType = string(itemRecord.get("item_type"));
    if (!List.of("dialogue_scale", "voice", "expression").contains(itemType)) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "该测评项目不支持通用提交");
    }
    Instant now = Instant.now();
    String moduleRecordId = ensureModuleRecord(itemRecord, now);
    Object rawData = firstNonNull(payload.get("rawData"), payload.get("raw_data_json"), payload.get("data"), Map.of());
    Object metrics = firstNonNull(payload.get("metrics"), payload.get("metrics_json"), Map.of());
    Map<String, Object> report = buildModuleReport(itemType, itemRecord, rawData, metrics, map(payload.get("report")));
    String warning = string(report.get("riskLevel"), string(report.get("warningLevel"), "none"));
    jdbcTemplate.update("""
        UPDATE assessment_task_module_records
        SET status = 'completed',
            raw_data_json = CAST(:rawData AS JSON),
            metrics_json = CAST(:metrics AS JSON),
            report = CAST(:report AS JSON),
            warning_level = :warning,
            started_at = COALESCE(started_at, :now),
            completed_at = :now,
            updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", moduleRecordId)
            .addValue("userId", user.id())
            .addValue("rawData", toJson(rawData))
            .addValue("metrics", toJson(metrics))
            .addValue("report", toJson(report))
            .addValue("warning", normalizeWarning(warning))
            .addValue("now", Timestamp.from(now)));
    jdbcTemplate.update("""
        UPDATE assessment_publish_item_records
        SET status = 'completed',
            report = CAST(:report AS JSON),
            warning_level = :warning,
            started_at = COALESCE(started_at, :now),
            completed_at = :now,
            result_ref_table = 'assessment_task_module_records',
            result_ref_id = :moduleRecordId,
            updated_at = :now
        WHERE id = :id AND user_id = :userId
        """,
        new MapSqlParameterSource()
            .addValue("id", itemRecordId)
            .addValue("userId", user.id())
            .addValue("moduleRecordId", moduleRecordId)
            .addValue("report", toJson(report))
            .addValue("warning", normalizeWarning(warning))
            .addValue("now", Timestamp.from(now)));
    refreshAssigneeById(string(itemRecord.get("assignee_id")), now);
    maybeBuildPackageReport(string(itemRecord.get("assignee_id")), user.id());
    return getMyTaskDetail(string(itemRecord.get("assignee_id")), user);
  }

  @Transactional
  public Map<String, Object> buildPackageReport(String assigneeId, AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    Map<String, Object> assignee = getMyTaskDetail(assigneeId, user);
    return buildAndSyncPackageReport(assignee, user.id());
  }

  public Map<String, Object> getDefaultTemplate(AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> template = one("""
        SELECT * FROM assessment_publish_batches
        WHERE batch_type = 'auto_default' AND template_code = 'default_forensic_risk_screening'
        ORDER BY created_at DESC LIMIT 1
        """, Map.of());
    if (template == null) {
      return Map.of();
    }
    template.put("items", query("""
        SELECT * FROM assessment_publish_items WHERE batch_id = :id ORDER BY order_no
        """, Map.of("id", template.get("id"))));
    return template;
  }

  @Transactional
  public Map<String, Object> updateDefaultTemplate(Map<String, Object> payload, AuthUser authUser) {
    requireStaff(authUser);
    Map<String, Object> template = one("""
        SELECT * FROM assessment_publish_batches
        WHERE batch_type = 'auto_default' AND template_code = 'default_forensic_risk_screening'
        ORDER BY created_at DESC LIMIT 1
        """, Map.of());
    if (template == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "默认测评模板不存在");
    }
    Instant now = Instant.now();
    jdbcTemplate.update("""
        UPDATE assessment_publish_batches
        SET title = :title,
            description = :description,
            auto_assign_enabled = :enabled,
            status = :status,
            updated_at = :now
        WHERE id = :id
        """,
        new MapSqlParameterSource()
            .addValue("id", template.get("id"))
            .addValue("title", string(payload.get("title"), string(template.get("title"))))
            .addValue("description", nullableString(firstNonNull(payload.get("description"), template.get("description"))))
            .addValue("enabled", bool(payload.get("auto_assign_enabled"), bool(template.get("auto_assign_enabled"), true)))
            .addValue("status", bool(payload.get("auto_assign_enabled"), true) ? "active" : "stopped")
            .addValue("now", Timestamp.from(now)));
    if (payload.containsKey("items")) {
      replaceItems(string(template.get("id")), list(payload.get("items")), now);
    }
    return getDefaultTemplate(authUser);
  }

  public List<Map<String, Object>> myTasks(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    List<Map<String, Object>> assignees = query("""
        SELECT a.*, b.title AS batch_title, b.description AS batch_description, b.start_at, b.end_at
        FROM assessment_publish_assignees a
        JOIN assessment_publish_batches b ON b.id = a.batch_id
        WHERE a.user_id = :userId AND b.status = 'active'
        ORDER BY a.created_at DESC
        """, Map.of("userId", user.id()));
    for (Map<String, Object> assignee : assignees) {
      assignee.put("items", query("""
          SELECT r.*, i.title, i.required, i.order_no, i.target_id
          FROM assessment_publish_item_records r
          JOIN assessment_publish_items i ON i.id = r.item_id
          WHERE r.assignee_id = :id
          ORDER BY i.order_no
          """, Map.of("id", assignee.get("id"))));
    }
    return assignees;
  }

  private void replaceItems(String taskId, List<Map<String, Object>> items, Instant now) {
    jdbcTemplate.update("DELETE FROM assessment_publish_items WHERE batch_id = :id", new MapSqlParameterSource("id", taskId));
    int order = 1;
    for (Map<String, Object> item : items) {
      String type = string(item.get("item_type"), string(item.get("type")));
      if (type.isBlank()) {
        continue;
      }
      jdbcTemplate.update("""
          INSERT INTO assessment_publish_items (
            id, batch_id, item_type, target_id, title, required, order_no, config_json, status, created_at
          ) VALUES (
            :id, :batchId, :type, :targetId, :title, :required, :orderNo, CAST(:configJson AS JSON), :status, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", uuid())
              .addValue("batchId", taskId)
              .addValue("type", type)
              .addValue("targetId", nullableString(firstNonNull(item.get("target_id"), item.get("targetId"))))
              .addValue("title", requiredString(item, "title", "请填写测评项目名称"))
              .addValue("required", bool(item.get("required"), true))
              .addValue("orderNo", intValue(item.get("order_no"), order++))
              .addValue("configJson", toJson(firstNonNull(item.get("config_json"), Map.of())))
              .addValue("status", string(item.get("status"), "enabled"))
              .addValue("now", Timestamp.from(now)));
    }
  }

  private String createScalePlanIfNeeded(
      Map<String, Object> task,
      List<Map<String, Object>> items,
      List<String> userIds,
      AuthUser staff,
      Instant now) {
    List<String> surveyIds = items.stream()
        .filter(item -> "scale".equals(item.get("item_type")))
        .map(item -> string(item.get("target_id")))
        .filter(id -> !id.isBlank())
        .toList();
    if (surveyIds.isEmpty()) {
      return "";
    }
    List<Map<String, Object>> published = query("SELECT id FROM scale_surveys WHERE id IN (:ids) AND status = 'published'", Map.of("ids", surveyIds));
    if (published.size() != surveyIds.size()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "只能发布已发布量表");
    }
    String planId = uuid();
    jdbcTemplate.update("""
        INSERT INTO scale_distribution_plans (
          id, title, assessment_category, survey_ids, recipient_type, recipient_scope, start_at, end_at, status, created_by, created_at, updated_at
        ) VALUES (
          :id, :title, 'scale', CAST(:surveyIds AS JSON), 'users', CAST(:scope AS JSON), :startAt, :endAt, 'active', :createdBy, :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", planId)
            .addValue("title", task.get("title"))
            .addValue("surveyIds", toJson(surveyIds))
            .addValue("scope", toJson(Map.of("user_ids", userIds)))
            .addValue("startAt", task.get("start_at") instanceof Timestamp timestamp ? timestamp : timestamp(task.get("start_at")))
            .addValue("endAt", task.get("end_at") instanceof Timestamp timestamp ? timestamp : timestamp(task.get("end_at")))
            .addValue("createdBy", staff == null ? null : staff.id())
            .addValue("now", Timestamp.from(now)));
    return planId;
  }

  private void createItemRecord(
      String taskId,
      String assigneeId,
      String userId,
      Map<String, Object> item,
      String scalePlanId,
      Instant now) {
    String itemRecordId = uuid();
    String itemType = string(item.get("item_type"));
    jdbcTemplate.update("""
        INSERT INTO assessment_publish_item_records (
          id, assignee_id, batch_id, item_id, user_id, item_type, status, created_at, updated_at
        ) VALUES (
          :id, :assigneeId, :batchId, :itemId, :userId, :itemType, 'pending', :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", itemRecordId)
            .addValue("assigneeId", assigneeId)
            .addValue("batchId", taskId)
            .addValue("itemId", item.get("id"))
            .addValue("userId", userId)
            .addValue("itemType", itemType)
            .addValue("now", Timestamp.from(now)));
    if ("scale".equals(itemType)) {
      String recordId = uuid();
      jdbcTemplate.update("""
          INSERT INTO scale_distribution_records (
            id, plan_id, survey_id, user_id, assessment_category, status, calc_status, sent_at, created_at, updated_at
          ) VALUES (
            :id, :planId, :surveyId, :userId, 'scale', 'pending', 'none', :now, :now, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("planId", scalePlanId)
              .addValue("surveyId", item.get("target_id"))
              .addValue("userId", userId)
              .addValue("now", Timestamp.from(now)));
      linkItemRecord(itemRecordId, "scale_distribution_records", recordId);
    } else if ("neuropsych".equals(itemType)) {
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
      linkItemRecord(itemRecordId, "neuropsych_records", recordId);
    } else if (List.of("dialogue_scale", "voice", "expression").contains(itemType)) {
      String recordId = uuid();
      jdbcTemplate.update("""
          INSERT INTO assessment_task_module_records (
            id, item_record_id, user_id, module_type, status, created_at, updated_at
          ) VALUES (
            :id, :itemRecordId, :userId, :moduleType, 'pending', :now, :now
          )
          """,
          new MapSqlParameterSource()
              .addValue("id", recordId)
              .addValue("itemRecordId", itemRecordId)
              .addValue("userId", userId)
              .addValue("moduleType", itemType)
              .addValue("now", Timestamp.from(now)));
      linkItemRecord(itemRecordId, "assessment_task_module_records", recordId);
    } else {
      jdbcTemplate.update("""
          UPDATE assessment_publish_item_records
          SET status = 'unsupported', updated_at = :now
          WHERE id = :id
          """,
          new MapSqlParameterSource().addValue("id", itemRecordId).addValue("now", Timestamp.from(now)));
    }
  }

  private void linkItemRecord(String itemRecordId, String table, String recordId) {
    jdbcTemplate.update("""
        UPDATE assessment_publish_item_records
        SET result_ref_table = :tableName, result_ref_id = :recordId
        WHERE id = :itemRecordId
        """,
        new MapSqlParameterSource()
            .addValue("tableName", table)
            .addValue("recordId", recordId)
            .addValue("itemRecordId", itemRecordId));
  }

  private List<Map<String, Object>> queryItemRecords(String assigneeId) {
    return query("""
        SELECT r.*, i.title, i.required, i.order_no, i.target_id, i.config_json
        FROM assessment_publish_item_records r
        JOIN assessment_publish_items i ON i.id = r.item_id
        WHERE r.assignee_id = :id
        ORDER BY i.order_no
        """, Map.of("id", assigneeId));
  }

  private List<Map<String, Object>> enrichItemRecords(List<Map<String, Object>> itemRecords) {
    List<Map<String, Object>> result = new ArrayList<>();
    for (Map<String, Object> item : itemRecords) {
      Map<String, Object> enriched = new LinkedHashMap<>(item);
      String table = string(item.get("result_ref_table"));
      String refId = string(item.get("result_ref_id"));
      if ("scale_distribution_records".equals(table) && !refId.isBlank()) {
        enriched.put("result", one("""
            SELECT r.*, s.title AS survey_title, s.code AS survey_code, s.survey_json
            FROM scale_distribution_records r
            LEFT JOIN scale_surveys s ON s.id = r.survey_id
            WHERE r.id = :id
            """, Map.of("id", refId)));
      } else if ("neuropsych_records".equals(table) && !refId.isBlank()) {
        enriched.put("result", one("""
            SELECT r.*, t.code AS test_code, t.title AS test_title, t.dimension, t.source_path, t.config_json
            FROM neuropsych_records r
            LEFT JOIN neuropsych_tests t ON t.id = r.test_id
            WHERE r.id = :id
            """, Map.of("id", refId)));
      } else if ("assessment_task_module_records".equals(table) && !refId.isBlank()) {
        enriched.put("result", one("SELECT * FROM assessment_task_module_records WHERE id = :id", Map.of("id", refId)));
      }
      result.add(enriched);
    }
    return result;
  }

  private Map<String, Object> loadMyItemRecord(String itemRecordId, String userId) {
    Map<String, Object> itemRecord = one("""
        SELECT r.*, i.title, i.required, i.order_no, i.target_id, i.config_json
        FROM assessment_publish_item_records r
        JOIN assessment_publish_items i ON i.id = r.item_id
        JOIN assessment_publish_batches b ON b.id = r.batch_id
        WHERE r.id = :id AND r.user_id = :userId AND b.status = 'active'
        LIMIT 1
        """, Map.of("id", itemRecordId, "userId", userId));
    if (itemRecord == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "测评项目不存在或已停止");
    }
    return itemRecord;
  }

  private String ensureModuleRecord(Map<String, Object> itemRecord, Instant now) {
    String refId = string(itemRecord.get("result_ref_id"));
    if ("assessment_task_module_records".equals(itemRecord.get("result_ref_table")) && !refId.isBlank()) {
      return refId;
    }
    Map<String, Object> existing = one("""
        SELECT id FROM assessment_task_module_records WHERE item_record_id = :id LIMIT 1
        """, Map.of("id", itemRecord.get("id")));
    if (existing != null) {
      String id = string(existing.get("id"));
      linkItemRecord(string(itemRecord.get("id")), "assessment_task_module_records", id);
      return id;
    }
    String id = uuid();
    jdbcTemplate.update("""
        INSERT INTO assessment_task_module_records (
          id, item_record_id, user_id, module_type, status, created_at, updated_at
        ) VALUES (
          :id, :itemRecordId, :userId, :moduleType, 'pending', :now, :now
        )
        """,
        new MapSqlParameterSource()
            .addValue("id", id)
            .addValue("itemRecordId", itemRecord.get("id"))
            .addValue("userId", itemRecord.get("user_id"))
            .addValue("moduleType", itemRecord.get("item_type"))
            .addValue("now", Timestamp.from(now)));
    linkItemRecord(string(itemRecord.get("id")), "assessment_task_module_records", id);
    return id;
  }

  private Map<String, Object> buildModuleReport(
      String itemType,
      Map<String, Object> itemRecord,
      Object rawData,
      Object metrics,
      Map<String, Object> providedReport) {
    if (!providedReport.isEmpty()) {
      return new LinkedHashMap<>(providedReport);
    }
    Map<String, Object> metricMap = map(metrics);
    Map<String, Object> rawMap = map(rawData);
    int score = intValue(firstNonNull(metricMap.get("score"), rawMap.get("score")), 20);
    String warning = score >= 75 ? "high" : score >= 55 ? "middle" : score >= 35 ? "low" : "none";
    String title = string(itemRecord.get("title"));
    String summary = switch (itemType) {
      case "dialogue_scale" -> "对话式心理健康评估已完成，系统已记录压力、冲动控制和情绪状态线索。";
      case "voice" -> "语音识别已完成，系统已记录转写文本、语速、停顿和情绪波动线索。";
      case "expression" -> "表情评估已完成，系统已记录面部情绪分布和负性情绪线索。";
      default -> title + "已完成。";
    };
    List<Map<String, Object>> metricCards = new ArrayList<>();
    metricCards.add(Map.of("label", "风险分", "value", score, "unit", "分", "tone", warningTone(warning)));
    Object text = firstNonNull(rawMap.get("text"), rawMap.get("transcript"), rawMap.get("summary"));
    if (text != null && !string(text).isBlank()) {
      metricCards.add(Map.of("label", "文本摘要", "value", string(text).length() > 28 ? string(text).substring(0, 28) + "..." : string(text), "unit", "", "tone", "slate"));
    }
    return new LinkedHashMap<>(Map.of(
        "title", title,
        "moduleType", itemType,
        "summary", summary,
        "score", score,
        "riskLevel", warning,
        "warningLevel", warning,
        "metricCards", metricCards,
        "feedbackCards", List.of(Map.of(
            "title", "结果反馈",
            "level", warning,
            "conclusion", summary,
            "suggestion", "请结合其他测评模块综合查看，如结果提示中高风险，建议联系专业人员进一步访谈。"
        )),
        "completedAt", Instant.now().toString()
    ));
  }

  private Object loadPackageReport(String assigneeId, String userId) {
    Map<String, Object> assessment = one("""
        SELECT id, user_id, assessment_type, risk_level, score, report, created_at, updated_at
        FROM assessments
        WHERE user_id = :userId
          AND assessment_type = 'assessment_package_report'
          AND JSON_UNQUOTE(JSON_EXTRACT(report, '$.packageData.assigneeId')) = :assigneeId
        ORDER BY created_at DESC
        LIMIT 1
        """, Map.of("userId", userId, "assigneeId", assigneeId));
    return assessment == null ? null : assessment;
  }

  private void maybeBuildPackageReport(String assigneeId, String userId) {
    List<Map<String, Object>> items = queryItemRecords(assigneeId);
    if (!items.isEmpty() && items.stream().allMatch(item -> "completed".equals(item.get("status")) || "unsupported".equals(item.get("status")))) {
      Map<String, Object> assignee = one("""
          SELECT a.*, b.title AS batch_title, b.description AS batch_description
          FROM assessment_publish_assignees a
          JOIN assessment_publish_batches b ON b.id = a.batch_id
          WHERE a.id = :id AND a.user_id = :userId
          LIMIT 1
          """, Map.of("id", assigneeId, "userId", userId));
      if (assignee != null) {
        assignee.put("items", enrichItemRecords(items));
        buildAndSyncPackageReport(assignee, userId);
      }
    }
  }

  private Map<String, Object> buildAndSyncPackageReport(Map<String, Object> assignee, String userId) {
    List<Map<String, Object>> items = list(assignee.get("items"));
    if (items.isEmpty()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "测评任务没有项目");
    }
    int totalRequired = (int) items.stream().filter(item -> bool(item.get("required"), true)).count();
    int completedRequired = (int) items.stream()
        .filter(item -> bool(item.get("required"), true))
        .filter(item -> "completed".equals(item.get("status")) || "unsupported".equals(item.get("status")))
        .count();
    if (completedRequired < totalRequired) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "请完成全部必做测评后再生成总报告");
    }
    List<Map<String, Object>> sections = buildReportSections(items);
    Map<String, Object> moduleReports = collectModuleReports(items);
    Map<String, Double> weights = Map.of(
        "scale", 0.30,
        "neuropsych", 0.25,
        "dialogue_scale", 0.20,
        "voice", 0.10,
        "expression", 0.15
    );
    double weighted = 0;
    double usedWeight = 0;
    String highestWarning = "none";
    for (Map<String, Object> section : sections) {
      String type = string(section.get("type"));
      double weight = weights.getOrDefault(type, 0.0);
      int scoreValue = intValue(section.get("score"), extractReportScore(section));
      weighted += scoreValue * weight;
      usedWeight += weight;
      highestWarning = higherWarning(highestWarning, string(section.get("riskLevel")));
    }
    int score = usedWeight <= 0 ? 0 : (int) Math.round(weighted / usedWeight);
    String warning = higherWarning(scoreToWarning(score), highestWarning);
    String taskTitle = string(assignee.get("batch_title"), "测评任务报告");
    boolean initialScreening = "auto_default".equals(assignee.get("batch_type")) ||
        "default_forensic_risk_screening".equals(assignee.get("template_code")) ||
        taskTitle.contains("职务犯罪");
    Map<String, Object> overall = new LinkedHashMap<>();
    overall.put("score", score);
    overall.put("riskLevel", warning);
    overall.put("label", warningLabel(warning));
    overall.put("summary", buildOverallSummary(taskTitle, sections, warning));
    overall.put("patientConclusion", buildPatientConclusion(sections, warning));
    overall.put("doctorConclusion", buildDoctorConclusion(sections, warning, score));
    Map<String, Object> report = new LinkedHashMap<>();
    report.put("packageData", Map.of(
        "assigneeId", assignee.get("id"),
        "batchId", assignee.get("batch_id"),
        "title", taskTitle,
        "reportTitle", initialScreening ? "职务犯罪初筛总报告" : "测评任务报告",
        "taskType", initialScreening ? "initial_screening" : "assessment_task",
        "completedItems", completedRequired,
        "totalItems", totalRequired,
        "generatedAt", Instant.now().toString()
    ));
    report.put("scaleData", moduleReports.getOrDefault("scale", Map.of()));
    report.put("neuropsychData", moduleReports.getOrDefault("neuropsych", Map.of()));
    report.put("dialogueData", moduleReports.getOrDefault("dialogue_scale", Map.of()));
    report.put("voiceData", moduleReports.getOrDefault("voice", Map.of()));
    report.put("expressionData", moduleReports.getOrDefault("expression", Map.of()));
    report.put("sections", sections);
    report.put("overall", overall);
    report.put("weights", weights);
    report.put("advice", buildPackageAdvice(warning));
    String assessmentId = syncPackageAssessment(userId, string(assignee.get("id")), score, warning, report);
    syncPackageRiskAlert(userId, assessmentId, score, warning, report);
    if (initialScreening) {
      try {
        interventionTaskService.assignDefaultByAssessment(assessmentId, userId);
      } catch (Exception ignored) {
        // 干预计划自动生成不能影响测评报告生成；医生端可手动补发。
      }
    }
    return Map.of("assessmentId", assessmentId, "report", report);
  }

  private List<Map<String, Object>> buildReportSections(List<Map<String, Object>> items) {
    Map<String, List<Map<String, Object>>> grouped = new LinkedHashMap<>();
    for (Map<String, Object> item : items) {
      Object report = extractItemReport(item);
      if (report == null) {
        continue;
      }
      String type = string(item.get("item_type"));
      grouped.computeIfAbsent(type, ignored -> new ArrayList<>()).add(normalizeReportItem(item, report));
    }

    List<Map<String, Object>> sections = new ArrayList<>();
    for (Map.Entry<String, List<Map<String, Object>>> entry : grouped.entrySet()) {
      String type = entry.getKey();
      List<Map<String, Object>> sectionItems = entry.getValue();
      int score = (int) Math.round(sectionItems.stream().mapToInt(item -> intValue(item.get("score"), 0)).average().orElse(0));
      String warning = sectionItems.stream()
          .map(item -> string(item.get("riskLevel")))
          .reduce("none", this::higherWarning);
      Map<String, Object> section = new LinkedHashMap<>();
      section.put("type", type);
      section.put("title", moduleLabel(type));
      section.put("score", score);
      section.put("riskLevel", warning);
      section.put("label", warningLabel(warning));
      section.put("summary", buildSectionSummary(type, sectionItems, warning));
      section.put("items", sectionItems);
      section.put("order", moduleOrder(type));
      sections.add(section);
    }
    sections.sort((left, right) -> Integer.compare(intValue(left.get("order"), 99), intValue(right.get("order"), 99)));
    return sections;
  }

  private Map<String, Object> normalizeReportItem(Map<String, Object> item, Object reportObject) {
    Map<String, Object> report = map(reportObject);
    String type = string(item.get("item_type"));
    String title = firstText(
        item.get("title"),
        report.get("surveyTitle"),
        report.get("testTitle"),
        report.get("title"),
        report.get("name"),
        moduleLabel(type));
    int score = extractReportScore(report);
    String warning = extractReportWarning(report, score);
    Map<String, Object> normalized = new LinkedHashMap<>();
    normalized.put("id", string(item.get("id")));
    normalized.put("type", type);
    normalized.put("title", title);
    normalized.put("score", score);
    normalized.put("riskLevel", warning);
    normalized.put("label", warningLabel(warning));
    normalized.put("summary", extractReportSummary(type, title, report));
    normalized.put("keyFindings", extractKeyFindings(type, report));
    normalized.put("suggestions", extractSuggestions(type, report));
    normalized.put("metrics", extractReportMetrics(type, report));
    normalized.put("completedAt", firstText(item.get("completed_at"), report.get("completedAt"), Instant.now().toString()));
    normalized.put("sourceReport", report);
    return normalized;
  }

  private String extractReportSummary(String type, String title, Map<String, Object> report) {
    String direct = firstText(
        report.get("summary"),
        report.get("conclusion"),
        report.get("analysis_report"),
        report.get("content"),
        map(report.get("overall")).get("summary"));
    if (!direct.isBlank()) {
      return direct;
    }
    if ("scale".equals(type)) {
      List<Map<String, Object>> dimensions = list(report.get("dimensions"));
      if (!dimensions.isEmpty()) {
        String conclusion = dimensions.stream()
            .map(dimension -> firstText(dimension.get("conclusion"), dimension.get("name")))
            .filter(text -> !text.isBlank())
            .findFirst()
            .orElse("");
        if (!conclusion.isBlank()) {
          return conclusion;
        }
      }
      return title + "已完成，系统已根据量表计分规则生成结果。";
    }
    if ("neuropsych".equals(type)) {
      List<Map<String, Object>> cards = list(report.get("feedbackCards"));
      if (!cards.isEmpty()) {
        return firstText(cards.getFirst().get("conclusion"), cards.getFirst().get("title"), title + "已完成。");
      }
      return title + "已完成，系统已记录关键行为指标。";
    }
    return title + "已完成。";
  }

  private List<String> extractKeyFindings(String type, Map<String, Object> report) {
    List<String> findings = new ArrayList<>();
    if ("scale".equals(type)) {
      for (Map<String, Object> dimension : list(report.get("dimensions"))) {
        String name = firstText(dimension.get("name"), dimension.get("label"), "维度");
        String score = firstText(dimension.get("standardScore"), dimension.get("rawScore"), dimension.get("score"));
        String conclusion = firstText(dimension.get("conclusion"));
        findings.add(score.isBlank() ? name + "：" + conclusion : name + "：" + score + "分" + (conclusion.isBlank() ? "" : "，" + conclusion));
      }
    } else if ("neuropsych".equals(type)) {
      for (Map<String, Object> card : list(report.get("feedbackCards"))) {
        String title = firstText(card.get("title"), "指标反馈");
        String conclusion = firstText(card.get("conclusion"), card.get("subtitle"));
        findings.add(title + (conclusion.isBlank() ? "" : "：" + conclusion));
      }
      if (findings.isEmpty()) {
        Map<String, Object> metrics = map(firstNonNull(report.get("metrics"), report.get("metrics_json")));
        for (Map.Entry<String, Object> entry : metrics.entrySet()) {
          if (findings.size() >= 4) break;
          findings.add(entry.getKey() + "：" + string(entry.getValue()));
        }
      }
    } else {
      List<Map<String, Object>> cards = list(report.get("metricCards"));
      for (Map<String, Object> card : cards) {
        findings.add(firstText(card.get("label"), "指标") + "：" + firstText(card.get("value"), card.get("summary")));
      }
    }
    return findings.stream().filter(text -> !text.isBlank() && !text.endsWith("：")).limit(5).toList();
  }

  private List<String> extractSuggestions(String type, Map<String, Object> report) {
    List<String> suggestions = new ArrayList<>();
    for (Map<String, Object> dimension : list(report.get("dimensions"))) {
      String suggestion = firstText(dimension.get("suggestion"));
      if (!suggestion.isBlank()) suggestions.add(suggestion);
    }
    for (Map<String, Object> card : list(report.get("feedbackCards"))) {
      String suggestion = firstText(card.get("suggestion"));
      if (!suggestion.isBlank()) suggestions.add(suggestion);
    }
    String direct = firstText(report.get("suggestion"), report.get("advice"), report.get("recommendation"));
    if (!direct.isBlank()) suggestions.add(direct);
    if (suggestions.isEmpty()) {
      suggestions.add(switch (type) {
        case "scale" -> "建议结合量表维度结果进行自我观察，如近期压力明显升高，可主动联系专业人员进一步沟通。";
        case "neuropsych" -> "建议结合当日状态理解实验表现，避免将单次结果视为诊断结论。";
        case "dialogue_scale" -> "建议保留近期压力与冲动控制记录，必要时与医生进一步讨论。";
        case "voice" -> "建议结合睡眠、压力和情绪变化理解语音线索。";
        case "expression" -> "建议结合主观感受理解表情线索，持续观察负性情绪变化。";
        default -> "建议结合其他测评模块综合理解本次结果。";
      });
    }
    return suggestions.stream().filter(text -> !text.isBlank()).distinct().limit(4).toList();
  }

  private Map<String, Object> extractReportMetrics(String type, Map<String, Object> report) {
    Map<String, Object> metrics = new LinkedHashMap<>();
    metrics.put("score", extractReportScore(report));
    metrics.put("riskLevel", extractReportWarning(report, extractReportScore(report)));
    if ("scale".equals(type)) {
      metrics.put("totalScore", firstNonNull(report.get("totalScore"), report.get("score")));
      metrics.put("dimensionCount", list(report.get("dimensions")).size());
    } else if ("neuropsych".equals(type)) {
      metrics.putAll(map(firstNonNull(report.get("metrics"), report.get("metrics_json"))));
    } else {
      metrics.putAll(map(report.get("metrics")));
      for (Map<String, Object> card : list(report.get("metricCards"))) {
        String label = firstText(card.get("label"));
        if (!label.isBlank()) {
          metrics.put(label, card.get("value"));
        }
      }
    }
    return metrics;
  }

  private Map<String, Object> collectModuleReports(List<Map<String, Object>> items) {
    Map<String, List<Object>> grouped = new LinkedHashMap<>();
    for (Map<String, Object> item : items) {
      String type = string(item.get("item_type"));
      Object report = extractItemReport(item);
      if (report == null) {
        continue;
      }
      grouped.computeIfAbsent(type, ignored -> new ArrayList<>()).add(report);
    }
    Map<String, Object> result = new LinkedHashMap<>();
    for (Map.Entry<String, List<Object>> entry : grouped.entrySet()) {
      List<Object> reports = entry.getValue();
      if (reports.size() == 1) {
        result.put(entry.getKey(), reports.getFirst());
      } else {
        int score = (int) Math.round(reports.stream().mapToInt(this::extractReportScore).average().orElse(0));
        result.put(entry.getKey(), Map.of(
            "score", score,
            "riskLevel", score >= 75 ? "high" : score >= 55 ? "middle" : score >= 35 ? "low" : "none",
            "reports", reports
        ));
      }
    }
    return result;
  }

  private Object extractItemReport(Map<String, Object> item) {
    Object direct = item.get("report");
    if (direct != null) {
      return direct;
    }
    Object result = item.get("result");
    if (result instanceof Map<?, ?> map) {
      return map.containsKey("report") ? map.get("report") : result;
    }
    return null;
  }

  private int extractReportScore(Object value) {
    if (value instanceof Map<?, ?> map) {
      Object score = firstNonNull(map.get("score"), map.get("totalScore"), map.get("risk_score"));
      int numeric = intValue(score, -1);
      if (numeric >= 0) {
        return Math.min(100, numeric);
      }
      Object warning = firstNonNull(map.get("riskLevel"), map.get("warningLevel"), map.get("warning_level"));
      return switch (normalizeWarning(string(warning))) {
        case "high" -> 85;
        case "middle" -> 62;
        case "low" -> 38;
        default -> 18;
      };
    }
    return 0;
  }

  private String syncPackageAssessment(String userId, String assigneeId, int score, String warning, Map<String, Object> report) {
    Map<String, Object> existing = one("""
        SELECT id FROM assessments
        WHERE user_id = :userId
          AND assessment_type = 'assessment_package_report'
          AND JSON_UNQUOTE(JSON_EXTRACT(report, '$.packageData.assigneeId')) = :assigneeId
        ORDER BY created_at DESC
        LIMIT 1
        """, Map.of("userId", userId, "assigneeId", assigneeId));
    String id = existing == null ? uuid() : string(existing.get("id"));
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", id)
        .addValue("userId", userId)
        .addValue("score", score)
        .addValue("riskLevel", warningToRisk10(warning, score))
        .addValue("report", toJson(report))
        .addValue("now", Timestamp.from(Instant.now()));
    if (existing == null) {
      jdbcTemplate.update("""
          INSERT INTO assessments (
            id, user_id, assessment_type, conversation_history, ai_analysis, risk_level, score, report, created_at, updated_at
          ) VALUES (
            :id, :userId, 'assessment_package_report', CAST('[]' AS JSON), CAST('{}' AS JSON),
            :riskLevel, :score, CAST(:report AS JSON), :now, :now
          )
          """, params);
    } else {
      jdbcTemplate.update("""
          UPDATE assessments
          SET risk_level = :riskLevel,
              score = :score,
              report = CAST(:report AS JSON),
              updated_at = :now
          WHERE id = :id
          """, params);
    }
    return id;
  }

  private void syncPackageRiskAlert(String userId, String assessmentId, int score, String warning, Map<String, Object> report) {
    int risk = warningToRisk10(warning, score);
    if (risk < 6) {
      return;
    }
    Map<String, Object> existing = one("""
        SELECT id FROM risk_alerts WHERE data_source = 'assessment_package_report' AND source_id = :sourceId LIMIT 1
        """, Map.of("sourceId", assessmentId));
    MapSqlParameterSource params = new MapSqlParameterSource()
        .addValue("id", existing == null ? uuid() : existing.get("id"))
        .addValue("patientId", userId)
        .addValue("risk", risk)
        .addValue("description", string(map(report.get("overall")).get("summary"), "五段式测评包提示风险"))
        .addValue("sourceId", assessmentId)
        .addValue("now", Timestamp.from(Instant.now()));
    if (existing == null) {
      jdbcTemplate.update("""
          INSERT INTO risk_alerts (
            id, patient_id, alert_type, risk_level, description, data_source, source_id, is_handled, created_at
          ) VALUES (
            :id, :patientId, '综合测评报告预警', :risk, :description, 'assessment_package_report', :sourceId, FALSE, :now
          )
          """, params);
    } else {
      jdbcTemplate.update("""
          UPDATE risk_alerts
          SET risk_level = :risk, description = :description, is_handled = FALSE
          WHERE id = :id
          """, params);
    }
  }

  private void refreshAssigneeById(String assigneeId, Instant now) {
    if (assigneeId.isBlank()) {
      return;
    }
    List<Map<String, Object>> siblings = query("SELECT status FROM assessment_publish_item_records WHERE assignee_id = :id", Map.of("id", assigneeId));
    boolean completed = !siblings.isEmpty() && siblings.stream().allMatch(row -> "completed".equals(row.get("status")) || "unsupported".equals(row.get("status")));
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
            .addValue("now", Timestamp.from(now)));
  }

  private String normalizeWarning(String warning) {
    return switch (string(warning)) {
      case "high" -> "high";
      case "middle", "medium" -> "middle";
      case "low" -> "low";
      default -> "none";
    };
  }

  private String warningLabel(String warning) {
    return switch (normalizeWarning(warning)) {
      case "high" -> "高风险";
      case "middle" -> "中风险";
      case "low" -> "低风险";
      default -> "低风险";
    };
  }

  private String warningTone(String warning) {
    return switch (normalizeWarning(warning)) {
      case "high" -> "rose";
      case "middle" -> "amber";
      case "low" -> "emerald";
      default -> "slate";
    };
  }

  private String buildPackageAdvice(String warning) {
    return switch (normalizeWarning(warning)) {
      case "high" -> "综合结果提示较高风险，建议医生尽快进行人工访谈和风险复核。";
      case "middle" -> "综合结果提示需要持续关注，建议结合个案背景进行随访观察。";
      case "low" -> "综合结果提示轻度风险信号，建议保持观察并按需复测。";
      default -> "综合结果暂未提示明显风险，请保持规律作息并完成后续随访。";
    };
  }

  private String moduleLabel(String type) {
    return switch (type) {
      case "scale" -> "量表测评";
      case "neuropsych" -> "神经心理测验";
      case "dialogue_scale" -> "对话式心理健康评估";
      case "voice" -> "语音识别";
      case "expression" -> "表情评估";
      case "multimodal_baseline" -> "多模态基线";
      default -> "测评项目";
    };
  }

  private int moduleOrder(String type) {
    return switch (type) {
      case "scale" -> 10;
      case "neuropsych" -> 20;
      case "dialogue_scale" -> 30;
      case "voice" -> 40;
      case "expression" -> 50;
      case "multimodal_baseline" -> 60;
      default -> 99;
    };
  }

  private String scoreToWarning(int score) {
    if (score >= 75) return "high";
    if (score >= 55) return "middle";
    if (score >= 35) return "low";
    return "none";
  }

  private String higherWarning(String left, String right) {
    return warningRank(right) > warningRank(left) ? normalizeWarning(right) : normalizeWarning(left);
  }

  private int warningRank(String warning) {
    return switch (normalizeWarning(warning)) {
      case "high" -> 3;
      case "middle" -> 2;
      case "low" -> 1;
      default -> 0;
    };
  }

  private String extractReportWarning(Map<String, Object> report, int score) {
    String warning = string(firstNonNull(report.get("riskLevel"), report.get("warningLevel"), report.get("warning_level")));
    if (!warning.isBlank()) {
      return normalizeWarning(warning);
    }
    return scoreToWarning(score);
  }

  private String buildOverallSummary(String taskTitle, List<Map<String, Object>> sections, String warning) {
    String sectionNames = sections.stream()
        .map(section -> string(section.get("title")))
        .filter(text -> !text.isBlank())
        .distinct()
        .toList()
        .stream()
        .reduce((left, right) -> left + "、" + right)
        .orElse("各项测评");
    return taskTitle + "已完成。系统综合" + sectionNames + "结果，当前总体提示为" + warningLabel(warning) + "。";
  }

  private String buildPatientConclusion(List<Map<String, Object>> sections, String warning) {
    String prefix = switch (normalizeWarning(warning)) {
      case "high" -> "本次结果提示需要重点关注的风险信号。";
      case "middle" -> "本次结果提示存在需要持续观察的风险信号。";
      case "low" -> "本次结果提示存在轻度波动或低水平风险信号。";
      default -> "本次结果暂未提示明显风险信号。";
    };
    String focus = sections.stream()
        .filter(section -> warningRank(string(section.get("riskLevel"))) >= 2)
        .map(section -> string(section.get("title")))
        .distinct()
        .toList()
        .stream()
        .reduce((left, right) -> left + "、" + right)
        .orElse("");
    if (!focus.isBlank()) {
      return prefix + " 主要关注模块包括：" + focus + "。结果仅用于筛查和随访参考，不等同于临床诊断。";
    }
    return prefix + " 结果仅用于筛查和随访参考，不等同于临床诊断。";
  }

  private String buildDoctorConclusion(List<Map<String, Object>> sections, String warning, int score) {
    long highCount = sections.stream().filter(section -> "high".equals(normalizeWarning(string(section.get("riskLevel"))))).count();
    long middleCount = sections.stream().filter(section -> "middle".equals(normalizeWarning(string(section.get("riskLevel"))))).count();
    return "任务报告综合分 " + score + "，总体" + warningLabel(warning) + "。中高风险模块数：" + (highCount + middleCount)
        + "。建议结合访谈、既往资料和现场观察进行人工复核。";
  }

  private String buildSectionSummary(String type, List<Map<String, Object>> items, String warning) {
    String label = moduleLabel(type);
    if (items.size() == 1) {
      return string(items.getFirst().get("summary"), label + "已完成。");
    }
    return label + "共完成 " + items.size() + " 项，综合提示为" + warningLabel(warning) + "。";
  }

  private int warningToRisk10(String warning, int score) {
    return switch (normalizeWarning(warning)) {
      case "high" -> Math.max(8, Math.min(10, (int) Math.ceil(score / 10.0)));
      case "middle" -> Math.max(6, Math.min(7, (int) Math.ceil(score / 10.0)));
      case "low" -> Math.max(3, Math.min(5, (int) Math.ceil(score / 10.0)));
      default -> Math.max(1, Math.min(2, (int) Math.ceil(score / 10.0)));
    };
  }

  private Map<String, Object> loadTask(String taskId) {
    Map<String, Object> task = one("SELECT * FROM assessment_publish_batches WHERE id = :id", Map.of("id", taskId));
    if (task == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "发布测评任务不存在");
    }
    return task;
  }

  private List<Map<String, Object>> queryAssignees(String taskId) {
    List<Map<String, Object>> assignees = query("""
        SELECT a.*, p.full_name AS patient_name, p.username AS patient_username
        FROM assessment_publish_assignees a
        LEFT JOIN profiles p ON p.id = a.user_id
        WHERE a.batch_id = :id
        ORDER BY a.created_at DESC
        """, Map.of("id", taskId));
    for (Map<String, Object> assignee : assignees) {
      assignee.put("items", query("""
          SELECT r.*, i.title, i.required, i.order_no, i.target_id
          FROM assessment_publish_item_records r
          JOIN assessment_publish_items i ON i.id = r.item_id
          WHERE r.assignee_id = :id
          ORDER BY i.order_no
          """, Map.of("id", assignee.get("id"))));
    }
    return assignees;
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

  private AuthUser requireStaff(AuthUser authUser) {
    AuthUser user = requireUser(authUser);
    if (!user.isStaff()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅医生或管理员可操作");
    }
    return user;
  }

  private AuthUser requireUser(AuthUser authUser) {
    if (authUser == null) {
      throw new ApiException(HttpStatus.UNAUTHORIZED, "请先登录");
    }
    return authUser;
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
      } else if (key.endsWith("_json") || "recipient_scope".equals(key) || "report".equals(key)) {
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
    return value instanceof Map<?, ?> source ? (Map<String, Object>) source : Map.of();
  }

  @SuppressWarnings("unchecked")
  private List<Map<String, Object>> list(Object value) {
    return value instanceof List<?> source ? (List<Map<String, Object>>) source : List.of();
  }

  private Object firstNonNull(Object... values) {
    for (Object value : values) {
      if (value != null) {
        return value;
      }
    }
    return null;
  }

  private String firstText(Object... values) {
    for (Object value : values) {
      String text = string(value);
      if (!text.isBlank()) {
        return text;
      }
    }
    return "";
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

  private String uuid() {
    return UUID.randomUUID().toString();
  }
}
