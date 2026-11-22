package chuxin.assessmenttasks;

import chuxin.auth.AuthUser;
import chuxin.common.ResponseBodyBuilder;
import java.util.Map;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/assessment-publish-tasks")
public class AssessmentPublishTaskController {

  private final AssessmentPublishTaskService service;

  public AssessmentPublishTaskController(AssessmentPublishTaskService service) {
    this.service = service;
  }

  @GetMapping
  public Map<String, Object> listTasks(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listTasks(principal(authentication)));
  }

  @PostMapping
  public Map<String, Object> createTask(@RequestBody Map<String, Object> payload, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createTask(payload, principal(authentication)));
  }

  @GetMapping("/{taskId}")
  public Map<String, Object> getTask(@PathVariable String taskId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getTask(taskId, principal(authentication)));
  }

  @PutMapping("/{taskId}")
  public Map<String, Object> updateTask(
      @PathVariable String taskId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateTask(taskId, payload, principal(authentication)));
  }

  @PostMapping("/{taskId}/publish")
  public Map<String, Object> publishTask(@PathVariable String taskId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.publishTask(taskId, principal(authentication)));
  }

  @PostMapping("/{taskId}/stop")
  public Map<String, Object> stopTask(@PathVariable String taskId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.stopTask(taskId, principal(authentication)));
  }

  @GetMapping("/materials")
  public Map<String, Object> materials(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.materials(principal(authentication)));
  }

  @GetMapping("/my")
  public Map<String, Object> myTasks(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myTasks(principal(authentication)));
  }

  @GetMapping("/my/{assigneeId}")
  public Map<String, Object> myTaskDetail(@PathVariable String assigneeId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getMyTaskDetail(assigneeId, principal(authentication)));
  }

  @PostMapping("/items/{itemRecordId}/start")
  public Map<String, Object> startItem(@PathVariable String itemRecordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.startItem(itemRecordId, principal(authentication)));
  }

  @PostMapping("/items/{itemRecordId}/submit")
  public Map<String, Object> submitItem(
      @PathVariable String itemRecordId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.submitModuleItem(itemRecordId, payload, principal(authentication)));
  }

  @GetMapping("/my/{assigneeId}/report")
  public Map<String, Object> packageReport(@PathVariable String assigneeId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.buildPackageReport(assigneeId, principal(authentication)));
  }

  @GetMapping("/default-template")
  public Map<String, Object> defaultTemplate(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getDefaultTemplate(principal(authentication)));
  }

  @PutMapping("/default-template")
  public Map<String, Object> updateDefaultTemplate(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateDefaultTemplate(payload, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
