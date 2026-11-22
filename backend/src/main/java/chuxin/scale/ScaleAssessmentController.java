package chuxin.scale;

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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/scale-assessments")
public class ScaleAssessmentController {

  private final ScaleAssessmentService service;
  private final ScaleHuaxinyunImportService huaxinyunImportService;

  public ScaleAssessmentController(
      ScaleAssessmentService service,
      ScaleHuaxinyunImportService huaxinyunImportService) {
    this.service = service;
    this.huaxinyunImportService = huaxinyunImportService;
  }

  @GetMapping("/surveys")
  public Map<String, Object> listSurveys(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listSurveys(principal(authentication)));
  }

  @PostMapping("/surveys")
  public Map<String, Object> createSurvey(@RequestBody Map<String, Object> payload, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createSurvey(payload, principal(authentication)));
  }

  @GetMapping("/surveys/{surveyId}")
  public Map<String, Object> getSurvey(@PathVariable String surveyId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getSurvey(surveyId, principal(authentication)));
  }

  @GetMapping("/free-surveys")
  public Map<String, Object> listFreeSurveys(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listFreeSurveys(principal(authentication)));
  }

  @PutMapping("/surveys/{surveyId}")
  public Map<String, Object> updateSurvey(
      @PathVariable String surveyId,
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.updateSurvey(surveyId, payload, principal(authentication)));
  }

  @PutMapping("/surveys/reorder")
  public Map<String, Object> reorderSurveys(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.reorderSurveys(payload, principal(authentication)));
  }

  @DeleteMapping("/surveys/{surveyId}")
  public Map<String, Object> deleteSurvey(@PathVariable String surveyId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.deleteSurvey(surveyId, principal(authentication)));
  }

  @PostMapping("/surveys/{surveyId}/publish")
  public Map<String, Object> publishSurvey(@PathVariable String surveyId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.publishSurvey(surveyId, principal(authentication)));
  }

  @PostMapping("/surveys/{surveyId}/clone")
  public Map<String, Object> cloneSurvey(@PathVariable String surveyId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.cloneSurvey(surveyId, principal(authentication)));
  }

  @PostMapping("/import/huaxinyun")
  public Map<String, Object> importHuaxinyun(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(huaxinyunImportService.importSurveys(payload, principal(authentication)));
  }

  @GetMapping("/distribution-plans")
  public Map<String, Object> listDistributionPlans(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listDistributionPlans(principal(authentication)));
  }

  @PostMapping("/distribution-plans")
  public Map<String, Object> createDistributionPlan(
      @RequestBody Map<String, Object> payload,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.createDistributionPlan(payload, principal(authentication)));
  }

  @GetMapping("/distribution-plans/{planId}")
  public Map<String, Object> getDistributionPlan(@PathVariable String planId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getDistributionPlan(planId, principal(authentication)));
  }

  @PostMapping("/distribution-plans/{planId}/stop")
  public Map<String, Object> stopDistributionPlan(@PathVariable String planId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.stopDistributionPlan(planId, principal(authentication)));
  }

  @GetMapping("/results")
  public Map<String, Object> listResults(
      @RequestParam(required = false) String survey_id,
      @RequestParam(required = false) String user_id,
      @RequestParam(required = false) String status,
      @RequestParam(required = false) String calc_status,
      @RequestParam(required = false) String warning_level,
      Authentication authentication) {
    return ResponseBodyBuilder.ok(service.listResults(
        Map.of(
            "survey_id", survey_id == null ? "" : survey_id,
            "user_id", user_id == null ? "" : user_id,
            "status", status == null ? "" : status,
            "calc_status", calc_status == null ? "" : calc_status,
            "warning_level", warning_level == null ? "" : warning_level
        ),
        principal(authentication)
    ));
  }

  @GetMapping("/results/{recordId}")
  public Map<String, Object> getResult(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getResult(recordId, principal(authentication)));
  }

  @PostMapping("/results/{recordId}/recalculate")
  public Map<String, Object> recalculate(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.recalculateRecord(recordId, principal(authentication)));
  }

  @GetMapping("/results/export")
  public Map<String, Object> exportResults(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.exportResults(Map.of(), false, principal(authentication)));
  }

  @GetMapping("/results/export-unfinished")
  public Map<String, Object> exportUnfinished(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.exportResults(Map.of(), true, principal(authentication)));
  }

  @GetMapping("/answers/template")
  public Map<String, Object> answerTemplate(Authentication authentication) {
    service.exportResults(Map.of(), true, principal(authentication));
    return ResponseBodyBuilder.ok(Map.of(
        "filename", "scale-answer-template.csv",
        "content", "record_id,question_id,question_type,my_answer\n"
    ));
  }

  @PostMapping("/answers/import")
  public Map<String, Object> importAnswers(@RequestBody Map<String, Object> payload, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.importAnswers(payload, principal(authentication)));
  }

  @GetMapping("/my-records")
  public Map<String, Object> myRecords(Authentication authentication) {
    return ResponseBodyBuilder.ok(service.myRecords(principal(authentication)));
  }

  @PostMapping("/free/{surveyCode}/start")
  public Map<String, Object> startFree(@PathVariable String surveyCode, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.startFreeRecord(surveyCode, principal(authentication)));
  }

  @GetMapping("/records/{recordId}")
  public Map<String, Object> getMyRecord(@PathVariable String recordId, Authentication authentication) {
    return ResponseBodyBuilder.ok(service.getMyRecord(recordId, principal(authentication)));
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
    return ResponseBodyBuilder.ok(service.getMyRecord(recordId, principal(authentication)));
  }

  private AuthUser principal(Authentication authentication) {
    return authentication != null && authentication.getPrincipal() instanceof AuthUser authUser ? authUser : null;
  }
}
