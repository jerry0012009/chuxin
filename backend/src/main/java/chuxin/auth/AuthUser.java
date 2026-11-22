package chuxin.auth;

public record AuthUser(
    String id,
    String username,
    String email,
    String role
) {

  public boolean isStaff() {
    return "doctor".equals(role) || "admin".equals(role) || "super_admin".equals(role);
  }

  public boolean isAdmin() {
    return "admin".equals(role);
  }

  public boolean isSuperAdmin() {
    return "super_admin".equals(role);
  }
}
