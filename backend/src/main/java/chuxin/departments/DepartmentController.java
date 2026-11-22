package chuxin.departments;

import chuxin.auth.AuthUser;
import chuxin.common.ResponseBodyBuilder;
import java.util.Map;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/departments")
public class DepartmentController {

  private final DepartmentService service;

  public DepartmentController(DepartmentService service) {
    this.service = service;
  }

  @GetMapping
  public Map<String, Object> list(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.list(principal(authentication)));
  }

  @PostMapping
  public Map<String, Object> create(@RequestBody Map<String, Object> payload, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.create(payload, principal(authentication)));
  }

  @PutMapping("/{id}")
  public Map<String, Object> update(
      @PathVariable String id,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.update(id, payload, principal(authentication)));
  }

  @DeleteMapping("/{id}")
  public Map<String, Object> delete(@PathVariable String id, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.delete(id, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
