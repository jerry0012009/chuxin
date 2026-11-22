package chuxin.functions;

import chuxin.common.ResponseBodyBuilder;
import java.util.Map;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@ConditionalOnProperty(name = "app.optional-endpoints-enabled", havingValue = "true", matchIfMissing = true)
@RequestMapping("/api/functions")
public class FunctionController {

  private final AiService aiService;

  public FunctionController(AiService aiService) {
    this.aiService = aiService;
  }

  @PostMapping("/{name}")
  public Map<String, Object> invoke(@PathVariable String name, @RequestBody Map<String, Object> payload) {
    return switch (name) {
      case "chat-completion" -> ResponseBodyBuilder.ok(aiService.chatCompletion(payload));
      case "multimodal-analysis" -> ResponseBodyBuilder.ok(aiService.multimodalAnalysis(payload));
      case "speech-recognition" -> ResponseBodyBuilder.ok(aiService.speechRecognition(payload));
      case "rag-retrieval" -> ResponseBodyBuilder.ok(aiService.ragRetrieval(payload));
      case "multimodal-fusion" -> ResponseBodyBuilder.ok(aiService.multimodalFusion(payload));
      default -> Map.of("error", "Unsupported function: " + name);
    };
  }
}
