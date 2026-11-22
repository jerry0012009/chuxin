package chuxin.functions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import chuxin.config.OpenRouterProperties;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import chuxin.common.ApiException;

@Service
public class AiService {

  private final OpenRouterProperties properties;
  private final ObjectMapper objectMapper;
  private final HttpClient httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(20)).build();

  public AiService(OpenRouterProperties properties, ObjectMapper objectMapper) {
    this.properties = properties;
    this.objectMapper = objectMapper;
  }

  public Map<String, Object> chatCompletion(Map<String, Object> payload) {
    return callTextModel((List<Map<String, Object>>) payload.get("messages"), 512);
  }

  public Map<String, Object> multimodalAnalysis(Map<String, Object> payload) {
    return callVisionModel((List<Map<String, Object>>) payload.get("messages"), 256);
  }

  public Map<String, Object> speechRecognition(Map<String, Object> payload) {
    requireOpenRouterApiKey();

    Map<String, Object> inputAudio = payload.get("input_audio") instanceof Map<?, ?> map
        ? (Map<String, Object>) map
        : Map.of(
            "data", payload.getOrDefault("speech", ""),
            "format", payload.getOrDefault("format", "wav")
        );
    String audioData = String.valueOf(inputAudio.getOrDefault("data", ""));
    String format = String.valueOf(inputAudio.getOrDefault("format", "wav"));
    if (audioData.isBlank()) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "缺少音频数据");
    }

    return callTranscriptionModel(Map.of(
        "model", payload.getOrDefault("model", properties.getTranscriptionModel()),
        "input_audio", Map.of("data", stripDataUrlPrefix(audioData), "format", format)
    ));
  }

  public Map<String, Object> ragRetrieval(Map<String, Object> payload) {
    String query = String.valueOf(payload.getOrDefault("query", ""));
    String assessmentType = String.valueOf(payload.getOrDefault("assessment_type", "PHQ-9"));
    return Map.of(
        "choices", List.of(Map.of("message", Map.of("content", "请继续描述你的情况，我会结合当前评估维度进一步了解你。"))),
        "knowledge_used", 0,
        "assessment_type", assessmentType,
        "query", query
    );
  }

  public Map<String, Object> multimodalFusion(Map<String, Object> payload) {
    String context = toJson(payload);
    return callTextModel(List.of(
        Map.of(
            "role", "system",
            "content", String.join("\n",
                "你是初心的多模态心理评估融合助手。",
                "必须基于输入的量表、语音、图像/面部等真实模块结果做融合分析，不得补造缺失模块。",
                "只返回 JSON，不要 Markdown。",
                "JSON schema: {\"success\":true,\"fused_score\":0,\"risk_level\":0,\"symptoms\":{\"情绪低落\":0,\"兴趣丧失\":0,\"精力下降\":0},\"recommendations\":[\"...\"],\"detailed_report\":\"中文综合结论\"}",
                "fused_score 为 0-100，risk_level 为 0-10。"
            )
        ),
        Map.of("role", "user", "content", context)
    ), 768);
  }

  private Map<String, Object> callTextModel(List<Map<String, Object>> messages, int maxTokens) {
    return callModel(properties.getTextModel(), messages, maxTokens);
  }

  private Map<String, Object> callVisionModel(List<Map<String, Object>> messages, int maxTokens) {
    return callModel(properties.getVisionModel(), messages, maxTokens);
  }

  private Map<String, Object> callModel(String model, List<Map<String, Object>> messages, int maxTokens) {
    requireOpenRouterApiKey();
    try {
      String body = objectMapper.writeValueAsString(Map.of(
          "model", model,
          "messages", messages,
          "stream", false,
          "max_tokens", maxTokens
      ));
      HttpRequest request = HttpRequest.newBuilder()
          .uri(URI.create("https://openrouter.ai/api/v1/chat/completions"))
          .header("Authorization", "Bearer " + properties.getApiKey())
          .header("Content-Type", "application/json")
          .header("HTTP-Referer", properties.getSiteUrl())
          .header("X-Title", properties.getAppName())
          .timeout(Duration.ofSeconds(90))
          .POST(HttpRequest.BodyPublishers.ofString(body))
          .build();
      HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      if (response.statusCode() < 200 || response.statusCode() >= 300) {
        throw new ApiException(HttpStatus.BAD_GATEWAY, resolveUpstreamError(response.body()));
      }
      JsonNode jsonNode = objectMapper.readTree(response.body());
      return objectMapper.convertValue(jsonNode, Map.class);
    } catch (IOException | InterruptedException e) {
      if (e instanceof InterruptedException) {
        Thread.currentThread().interrupt();
      }
      throw new ApiException(HttpStatus.BAD_GATEWAY, "AI 服务暂时不可用，请稍后重试。");
    }
  }

  private Map<String, Object> callTranscriptionModel(Map<String, Object> payload) {
    String lastError = "语音识别服务暂时不可用，请稍后重试。";
    for (int attempt = 0; attempt < 3; attempt++) {
      try {
        String body = objectMapper.writeValueAsString(Map.of(
            "model", payload.get("model"),
            "input_audio", payload.get("input_audio")
        ));
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://openrouter.ai/api/v1/audio/transcriptions"))
            .header("Authorization", "Bearer " + properties.getApiKey())
            .header("Content-Type", "application/json")
            .header("HTTP-Referer", properties.getSiteUrl())
            .header("X-Title", properties.getAppName())
            .timeout(Duration.ofSeconds(90))
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 200 && response.statusCode() < 300) {
          JsonNode jsonNode = objectMapper.readTree(response.body());
          String text = jsonNode.path("text").asText("");
          if (text.isBlank()) {
            text = jsonNode.path("choices").path(0).path("message").path("content").asText("");
          }
          return Map.of("text", text == null ? "" : text.trim());
        }
        lastError = resolveUpstreamError(response.body());
        if (response.statusCode() < 500 || attempt == 2) {
          break;
        }
      } catch (IOException e) {
        lastError = "语音识别服务暂时不可用，请稍后重试。";
      } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw new ApiException(HttpStatus.BAD_GATEWAY, "语音识别服务暂时不可用，请稍后重试。");
      }
      try {
        Thread.sleep(600L * (attempt + 1));
      } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        throw new ApiException(HttpStatus.BAD_GATEWAY, "语音识别服务暂时不可用，请稍后重试。");
      }
    }
    throw new ApiException(HttpStatus.BAD_GATEWAY,
        "Internal Server Error".equalsIgnoreCase(lastError) ? "语音识别服务暂时拥堵，请稍后重试。" : lastError);
  }

  private void requireOpenRouterApiKey() {
    if (properties.getApiKey() == null || properties.getApiKey().isBlank()) {
      throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "OPENROUTER_API_KEY 未配置");
    }
  }

  private String resolveUpstreamError(String body) {
    if (body == null || body.isBlank()) {
      return "AI 服务返回空错误";
    }
    try {
      JsonNode jsonNode = objectMapper.readTree(body);
      String error = jsonNode.path("error").isTextual()
          ? jsonNode.path("error").asText()
          : jsonNode.path("error").path("message").asText("");
      return error == null || error.isBlank() ? body : error;
    } catch (IOException ignored) {
      return body;
    }
  }

  private String stripDataUrlPrefix(String audioData) {
    int commaIndex = audioData.indexOf(',');
    if (audioData.startsWith("data:audio/") && commaIndex >= 0) {
      return audioData.substring(commaIndex + 1);
    }
    return audioData;
  }

  private String toJson(Object value) {
    try {
      return objectMapper.writeValueAsString(value);
    } catch (IOException e) {
      throw new ApiException(HttpStatus.BAD_REQUEST, "融合分析参数格式错误");
    }
  }
}
