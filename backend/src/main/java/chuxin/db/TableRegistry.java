package chuxin.db;

import chuxin.common.ApiException;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
public class TableRegistry {

  private final Map<String, TableMetadata> tables = Map.ofEntries(
      Map.entry("profiles", metadata("profiles", set(
          "id", "username", "email", "phone", "wechat", "role", "department_id", "avatar_url", "full_name", "gender",
          "birth_date", "bio", "background_url", "selected_background", "created_at", "updated_at"))),
      Map.entry("departments", metadata("departments", set(
          "id", "name", "description", "status", "created_at", "updated_at"))),
      Map.entry("emotion_diaries", metadata("emotion_diaries", set(
          "id", "user_id", "diary_date", "emotion_level", "title", "content", "tags", "image_urls", "voice_url",
          "ai_analysis", "created_at", "updated_at"), set("tags", "image_urls", "ai_analysis"))),
      Map.entry("assessments", metadata("assessments", set(
          "id", "user_id", "assessment_type", "conversation_history", "text_input", "voice_input_url", "image_input_url",
          "video_input_url", "ai_analysis", "risk_level", "score", "report", "created_at", "updated_at"),
          set("conversation_history", "ai_analysis", "report"))),
      Map.entry("wearable_data", metadata("wearable_data", set(
          "id", "user_id", "record_date", "heart_rate", "sleep_hours", "sleep_quality", "steps", "calories",
          "stress_level", "blood_oxygen", "temperature", "data_json", "created_at"), set("data_json"))),
      Map.entry("healing_contents", metadata("healing_contents", set(
          "id", "title", "description", "category", "content_type", "content_url", "duration", "thumbnail_url",
          "author", "tags", "is_active", "view_count", "like_count", "created_at", "updated_at"), set("tags"))),
      Map.entry("user_healing_records", metadata("user_healing_records", set(
          "id", "user_id", "healing_content_id", "duration_seconds", "completed", "created_at"))),
      Map.entry("community_posts", metadata("community_posts", set(
          "id", "user_id", "anonymous_name", "anonymous_nickname", "title", "content", "category_id", "tags",
          "like_count", "comment_count", "is_pinned", "is_hidden", "is_recovery_story", "is_featured", "created_at", "updated_at"),
          set("tags"))),
      Map.entry("community_comments", metadata("community_comments", set(
          "id", "post_id", "user_id", "anonymous_name", "content", "like_count", "created_at"))),
      Map.entry("post_likes", metadata("post_likes", set("id", "post_id", "user_id", "created_at"))),
      Map.entry("meditation_sessions", metadata("meditation_sessions", set(
          "id", "user_id", "content_id", "duration", "completed", "mood_before", "mood_after", "notes", "created_at", "updated_at"))),
      Map.entry("user_favorites", metadata("user_favorites", set("id", "user_id", "content_id", "created_at"))),
      Map.entry("post_categories", metadata("post_categories", set("id", "name", "description", "icon", "color", "created_at"))),
      Map.entry("doctor_patients", metadata("doctor_patients", set(
          "id", "doctor_id", "patient_id", "status", "notes", "created_at", "updated_at"))),
      Map.entry("risk_alerts", metadata("risk_alerts", set(
          "id", "patient_id", "alert_type", "risk_level", "description", "data_source", "source_id", "is_handled",
          "handled_by", "handled_at", "notes", "created_at"))),
      Map.entry("knowledge_base", metadata("knowledge_base", set(
          "id", "title", "content", "category", "tags", "content_type", "file_url", "file_name", "file_size",
          "file_mime_type", "is_active", "created_by", "created_at", "updated_at"), set("tags"))),
      Map.entry("doctor_verification_codes", metadata("doctor_verification_codes", set(
          "id", "code", "is_permanent", "is_used", "used_by", "used_at", "created_by", "created_at", "notes"))),
      Map.entry("scale_surveys", metadata("scale_surveys", set(
          "id", "code", "title", "description", "cover_url", "survey_type", "status", "self_test_enabled",
          "survey_json", "version", "created_by", "published_at", "created_at", "updated_at"), set("survey_json"))),
      Map.entry("scale_questions", metadata("scale_questions", set(
          "id", "survey_id", "question_type", "stem", "media_url", "order_no", "required", "created_at", "updated_at"))),
      Map.entry("scale_options", metadata("scale_options", set(
          "id", "question_id", "option_no", "label", "value", "order_no", "media_url", "created_at", "updated_at"))),
      Map.entry("scale_dimensions", metadata("scale_dimensions", set(
          "id", "survey_id", "name", "code", "num", "raw_score_formula", "standard_score_formula",
          "show_in_full_report", "show_in_user_report", "show_chart", "created_at", "updated_at"))),
      Map.entry("scale_result_definitions", metadata("scale_result_definitions", set(
          "id", "dimension_id", "condition_expression", "conclusion", "suggestion", "warning_level",
          "order_no", "created_at", "updated_at"))),
      Map.entry("scale_distribution_plans", metadata("scale_distribution_plans", set(
          "id", "title", "assessment_category", "survey_ids", "recipient_type", "recipient_scope", "cover_url",
          "start_at", "end_at", "status", "created_by", "created_at", "updated_at"), set("survey_ids", "recipient_scope"))),
      Map.entry("scale_distribution_records", metadata("scale_distribution_records", set(
          "id", "plan_id", "survey_id", "user_id", "assessment_category", "source_type", "status", "calc_status", "calc_error",
          "sent_at", "started_at", "completed_at", "answer_duration_sec", "answers_json", "total_score",
          "warning_level", "report", "assessment_id", "created_at", "updated_at"), set("answers_json", "report"))),
      Map.entry("scale_answers", metadata("scale_answers", set(
          "id", "record_id", "survey_id", "question_id", "question_type", "my_answer", "answer_text",
          "option_no", "score", "created_at"))),
      Map.entry("scale_record_dimensions", metadata("scale_record_dimensions", set(
          "id", "record_id", "dimension_id", "dimension_name", "dimension_code", "raw_score", "standard_score",
          "conclusion", "suggestion", "warning_level", "created_at"))),
      Map.entry("neuropsych_tests", metadata("neuropsych_tests", set(
          "id", "code", "title", "description", "dimension", "clinical_meaning", "estimated_minutes",
          "source_path", "runner_type", "status", "self_test_enabled", "config_json", "metric_schema_json",
          "scoring_version", "created_by", "created_at", "updated_at"), set("config_json", "metric_schema_json"))),
      Map.entry("neuropsych_records", metadata("neuropsych_records", set(
          "id", "test_id", "user_id", "source_type", "publish_item_record_id", "status", "calc_status",
          "calc_error", "started_at", "completed_at", "duration_ms", "raw_data_json", "metrics_json", "report",
          "warning_level", "assessment_id", "created_at", "updated_at"),
          set("raw_data_json", "metrics_json", "report"))),
      Map.entry("assessment_publish_batches", metadata("assessment_publish_batches", set(
          "id", "title", "description", "status", "start_at", "end_at", "recipient_type", "recipient_scope",
          "created_by", "published_at", "created_at", "updated_at"), set("recipient_scope"))),
      Map.entry("assessment_publish_items", metadata("assessment_publish_items", set(
          "id", "batch_id", "item_type", "target_id", "title", "required", "order_no", "config_json",
          "status", "created_at"), set("config_json"))),
      Map.entry("assessment_publish_assignees", metadata("assessment_publish_assignees", set(
          "id", "batch_id", "user_id", "status", "started_at", "completed_at", "created_at", "updated_at"))),
      Map.entry("assessment_publish_item_records", metadata("assessment_publish_item_records", set(
          "id", "assignee_id", "batch_id", "item_id", "user_id", "item_type", "status", "result_ref_table",
          "result_ref_id", "started_at", "completed_at", "created_at", "updated_at"))),
      Map.entry("intervention_materials", metadata("intervention_materials", set(
          "id", "code", "title", "description", "category", "subtype", "target_ref_table", "target_ref_id",
          "route_path", "duration_sec", "completion_mode", "tags", "config_json", "is_active", "created_at", "updated_at"),
          set("tags", "config_json"))),
      Map.entry("intervention_plan_templates", metadata("intervention_plan_templates", set(
          "id", "code", "title", "risk_level", "description", "duration_days", "daily_required_count",
          "auto_assign_enabled", "status", "created_by", "created_at", "updated_at"))),
      Map.entry("intervention_plan_template_items", metadata("intervention_plan_template_items", set(
          "id", "template_id", "material_id", "title", "frequency_type", "required_count", "duration_sec",
          "order_no", "required", "config_json", "created_at"), set("config_json"))),
      Map.entry("intervention_publish_batches", metadata("intervention_publish_batches", set(
          "id", "batch_type", "template_id", "source_assessment_id", "title", "description", "risk_level",
          "duration_days", "daily_required_count", "status", "start_date", "end_date", "recipient_type",
          "recipient_scope", "created_by", "published_at", "created_at", "updated_at"), set("recipient_scope"))),
      Map.entry("intervention_publish_items", metadata("intervention_publish_items", set(
          "id", "batch_id", "material_id", "item_type", "subtype", "title", "route_path", "required",
          "frequency_type", "required_count", "duration_sec", "completion_mode", "order_no", "config_json",
          "status", "created_at"), set("config_json"))),
      Map.entry("intervention_publish_assignees", metadata("intervention_publish_assignees", set(
          "id", "batch_id", "user_id", "source_assessment_id", "status", "start_date", "end_date",
          "completed_days", "total_completed_count", "last_completed_at", "created_at", "updated_at"))),
      Map.entry("intervention_item_records", metadata("intervention_item_records", set(
          "id", "assignee_id", "batch_id", "item_id", "material_id", "user_id", "plan_date", "status",
          "source_ref_table", "source_ref_id", "duration_seconds", "completion_note", "summary_json",
          "started_at", "completed_at", "created_at", "updated_at"), set("summary_json"))),
      Map.entry("intervention_daily_summaries", metadata("intervention_daily_summaries", set(
          "id", "assignee_id", "user_id", "summary_date", "completed_count", "required_count", "mood_level",
          "summary_text", "details_json", "created_at", "updated_at"), set("details_json")))
  );

  public TableMetadata get(String table) {
    TableMetadata metadata = tables.get(table);
    if (metadata == null) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "不支持的数据表: " + table);
    }
    return metadata;
  }

  private static TableMetadata metadata(String table, Set<String> columns) {
    return new TableMetadata(table, columns, Set.of(), Set.of("created_at"), List.of("created_at desc"));
  }

  private static TableMetadata metadata(String table, Set<String> columns, Set<String> jsonColumns) {
    return new TableMetadata(table, columns, jsonColumns, Set.of("created_at"), List.of("created_at desc"));
  }

  private static Set<String> set(String... values) {
    return Set.of(values);
  }
}
