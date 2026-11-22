package chuxin.brainintervention;

import chuxin.auth.AuthUser;
import chuxin.common.ResponseBodyBuilder;
import java.util.Map;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/brain-intervention-reports")
public class BrainInterventionReportController {

  private final BrainInterventionReportService service;

  public BrainInterventionReportController(BrainInterventionReportService service) {
    this.service = service;
  }

  @PostMapping
  public Map<String, Object> createReport(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createReport(payload, principal(authentication)));
  }

  @GetMapping("/my")
  public Map<String, Object> myReports(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myReports(principal(authentication)));
  }

  @GetMapping("/my/{reportId}")
  public Map<String, Object> getMyReport(@PathVariable String reportId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getMyReport(reportId, principal(authentication)));
  }

  @GetMapping
  public Map<String, Object> listReports(
      @RequestParam(required = false) String user_id,
      @RequestParam(required = false) String report_type,
      @RequestParam(required = false) String task_type,
      @RequestParam(required = false) String protocol_key,
      @RequestParam(required = false) String started_from,
      @RequestParam(required = false) String started_to,
      @RequestParam(required = false) Integer limit,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listReports(
        Map.of(
            "user_id", user_id == null ? "" : user_id,
            "report_type", report_type == null ? "" : report_type,
            "task_type", task_type == null ? "" : task_type,
            "protocol_key", protocol_key == null ? "" : protocol_key,
            "started_from", started_from == null ? "" : started_from,
            "started_to", started_to == null ? "" : started_to,
            "limit", limit == null ? 200 : limit
        ),
        principal(authentication)));
  }

  @GetMapping("/{reportId}")
  public Map<String, Object> getReport(@PathVariable String reportId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getReport(reportId, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
