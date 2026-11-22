package chuxin.departments;

import chuxin.auth.AuthService;
import chuxin.auth.AuthUser;
import chuxin.common.ApiException;
import java.sql.Timestamp;
import java.time.Instant;
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
public class DepartmentService {

  private final NamedParameterJdbcTemplate jdbcTemplate;
  private final AuthService authService;

  public DepartmentService(NamedParameterJdbcTemplate jdbcTemplate, AuthService authService) {
    this.jdbcTemplate = jdbcTemplate;
    this.authService = authService;
  }

  public List<Map<String, Object>> list(AuthUser authUser) {
    boolean superAdmin = authUser != null && authUser.isSuperAdmin();
    String where = superAdmin ? "" : "WHERE status = 'active'";
    return jdbcTemplate.query("""
        SELECT d.*,
          (SELECT COUNT(*) FROM profiles p WHERE p.department_id = d.id AND p.role = 'user') AS user_count
        FROM departments d
        %s
        ORDER BY d.created_at DESC
        """.formatted(where), new MapSqlParameterSource(), new ColumnMapRowMapper());
  }

  @Transactional
  public Map<String, Object> create(Map<String, Object> payload, AuthUser authUser) {
    requireSuperAdmin(authUser);
    String id = UUID.randomUUID().toString();
    Instant now = Instant.now();
    jdbcTemplate.update("""
        INSERT INTO departments (id, name, description, status, created_at, updated_at)
        VALUES (:id, :name, :description, :status, :now, :now)
        """, new MapSqlParameterSource()
        .addValue("id", id)
        .addValue("name", required(payload.get("name"), "请填写部门名称"))
        .addValue("description", nullable(payload.get("description")))
        .addValue("status", status(payload.get("status")))
        .addValue("now", Timestamp.from(now)));
    return get(id);
  }

  @Transactional
  public Map<String, Object> update(String id, Map<String, Object> payload, AuthUser authUser) {
    requireSuperAdmin(authUser);
    jdbcTemplate.update("""
        UPDATE departments
        SET name = :name, description = :description, status = :status, updated_at = :now
        WHERE id = :id
        """, new MapSqlParameterSource()
        .addValue("id", id)
        .addValue("name", required(payload.get("name"), "请填写部门名称"))
        .addValue("description", nullable(payload.get("description")))
        .addValue("status", status(payload.get("status")))
        .addValue("now", Timestamp.from(Instant.now())));
    return get(id);
  }

  @Transactional
  public Map<String, Object> delete(String id, AuthUser authUser) {
    requireSuperAdmin(authUser);
    jdbcTemplate.update("""
        UPDATE departments SET status = 'inactive', updated_at = :now WHERE id = :id
        """, new MapSqlParameterSource().addValue("id", id).addValue("now", Timestamp.from(Instant.now())));
    return Map.of("deleted", true, "id", id);
  }

  private Map<String, Object> get(String id) {
    Map<String, Object> row = jdbcTemplate.query("""
        SELECT d.*,
          (SELECT COUNT(*) FROM profiles p WHERE p.department_id = d.id AND p.role = 'user') AS user_count
        FROM departments d
        WHERE d.id = :id
        LIMIT 1
        """, new MapSqlParameterSource().addValue("id", id), rs -> rs.next() ? new ColumnMapRowMapper().mapRow(rs, 1) : null);
    if (row == null) {
      throw new ApiException(HttpStatus.NOT_FOUND, "部门不存在");
    }
    return row;
  }

  private AuthUser requireSuperAdmin(AuthUser authUser) {
    AuthUser user = authService.requireUser(authUser);
    if (!user.isSuperAdmin()) {
      throw new ApiException(HttpStatus.FORBIDDEN, "仅超级管理员可操作部门");
    }
    return user;
  }

  private String required(Object value, String message) {
    String text = value == null ? "" : String.valueOf(value).trim();
    if (text.isBlank()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, message);
    }
    return text;
  }

  private String nullable(Object value) {
    String text = value == null ? "" : String.valueOf(value).trim();
    return text.isBlank() ? null : text;
  }

  private String status(Object value) {
    return "inactive".equals(String.valueOf(value)) ? "inactive" : "active";
  }
}
