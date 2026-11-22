package chuxin.neuropsych;

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
@RequestMapping("/api/neuropsych-assessments")
public class NeuropsychAssessmentController {

  private final NeuropsychAssessmentService service;

  public NeuropsychAssessmentController(NeuropsychAssessmentService service) {
    this.service = service;
  }

  @GetMapping("/tests")
  public Map<String, Object> listTests(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listTests(principal(authentication)));
  }

  @GetMapping("/free-tests")
  public Map<String, Object> listFreeTests(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listFreeTests(principal(authentication)));
  }

  @PutMapping("/tests/{testId}")
  public Map<String, Object> updateTest(
      @PathVariable String testId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateTest(testId, payload, principal(authentication)));
  }

  @PostMapping("/distribution-plans")
  public Map<String, Object> createDistributionPlan(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createDistributionPlan(payload, principal(authentication)));
  }

  @GetMapping("/results")
  public Map<String, Object> listResults(
      @RequestParam(required = false) String test_id,
      @RequestParam(required = false) String user_id,
      @RequestParam(required = false) String status,
      @RequestParam(required = false) String calc_status,
      @RequestParam(required = false) String warning_level,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listResults(
        Map.of(
            "test_id", test_id == null ? "" : test_id,
            "user_id", user_id == null ? "" : user_id,
            "status", status == null ? "" : status,
            "calc_status", calc_status == null ? "" : calc_status,
            "warning_level", warning_level == null ? "" : warning_level
        ),
        principal(authentication)));
  }

  @GetMapping("/results/{recordId}")
  public Map<String, Object> getResult(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getResult(recordId, principal(authentication)));
  }

  @PostMapping("/results/{recordId}/recalculate")
  public Map<String, Object> recalculate(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.recalculateRecord(recordId, principal(authentication)));
  }

  @GetMapping("/my-records")
  public Map<String, Object> myRecords(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myRecords(principal(authentication)));
  }

  @PostMapping("/free/{testCode}/start")
  public Map<String, Object> startFree(@PathVariable String testCode, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.startFreeRecord(testCode, principal(authentication)));
  }

  @PostMapping("/records/{recordId}/start")
  public Map<String, Object> startRecord(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.startRecord(recordId, principal(authentication)));
  }

  @PostMapping("/records/{recordId}/submit")
  public Map<String, Object> submitRecord(
      @PathVariable String recordId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.submitRecord(recordId, payload, principal(authentication)));
  }

  @GetMapping("/records/{recordId}/report")
  public Map<String, Object> getMyReport(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getMyReport(recordId, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
