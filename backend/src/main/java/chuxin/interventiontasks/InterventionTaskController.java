package chuxin.interventiontasks;

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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/intervention-tasks")
public class InterventionTaskController {

  private final InterventionTaskService service;

  public InterventionTaskController(InterventionTaskService service) {
    this.service = service;
  }

  @GetMapping("/materials")
  public Map<String, Object> materials(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.materials(principal(authentication)));
  }

  @GetMapping("/templates")
  public Map<String, Object> templates(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.templates(principal(authentication)));
  }

  @PutMapping("/templates/{templateId}")
  public Map<String, Object> updateTemplate(
      @PathVariable String templateId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateTemplate(templateId, payload, principal(authentication)));
  }

  @GetMapping
  public Map<String, Object> listTasks(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listTasks(principal(authentication)));
  }

  @PostMapping
  public Map<String, Object> createTask(@RequestBody Map<String, Object> payload, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createTask(payload, principal(authentication)));
  }

  @GetMapping("/{batchId}")
  public Map<String, Object> getTask(@PathVariable String batchId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getTask(batchId, principal(authentication)));
  }

  @PutMapping("/{batchId}")
  public Map<String, Object> updateTask(
      @PathVariable String batchId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateTask(batchId, payload, principal(authentication)));
  }

  @PostMapping("/{batchId}/publish")
  public Map<String, Object> publishTask(@PathVariable String batchId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.publishTask(batchId, principal(authentication)));
  }

  @PostMapping("/{batchId}/stop")
  public Map<String, Object> stopTask(@PathVariable String batchId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.stopTask(batchId, principal(authentication)));
  }

  @PostMapping("/auto-assign/{assessmentId}")
  public Map<String, Object> autoAssign(@PathVariable String assessmentId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.assignDefaultByAssessment(assessmentId, principal(authentication)));
  }

  @PostMapping("/defaults/backfill")
  public Map<String, Object> backfillDefaults(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.backfillDefaultInterventions(principal(authentication)));
  }

  @GetMapping("/users/{userId}/plan")
  public Map<String, Object> userPlan(@PathVariable String userId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.userPlanForDoctor(userId, principal(authentication)));
  }

  @GetMapping("/my")
  public Map<String, Object> myTasks(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myTasks(principal(authentication)));
  }

  @GetMapping("/my/today")
  public Map<String, Object> myToday(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myToday(principal(authentication)));
  }

  @GetMapping("/my/plan")
  public Map<String, Object> myPlan(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myPlan(principal(authentication)));
  }

  @GetMapping("/my/calendar")
  public Map<String, Object> calendar(
      @RequestParam(required = false) String start,
      @RequestParam(required = false) String end,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.calendar(start, end, principal(authentication)));
  }

  @GetMapping("/my/calendar/{date}")
  public Map<String, Object> calendarDate(@PathVariable String date, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.calendarDate(date, principal(authentication)));
  }

  @PostMapping("/items/{recordId}/start")
  public Map<String, Object> startItem(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.startItem(recordId, principal(authentication)));
  }

  @PostMapping("/items/{recordId}/complete")
  public Map<String, Object> completeItem(
      @PathVariable String recordId,
      @RequestBody(required = false) Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.completeItem(recordId, payload, principal(authentication)));
  }

  @PostMapping("/my/mood/complete-today")
  public Map<String, Object> completeTodayMood(
      @RequestBody(required = false) Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.completeTodayMood(payload, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
