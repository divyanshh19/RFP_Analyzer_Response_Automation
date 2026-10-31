package com.rfp.platform.service;

import com.rfp.platform.dto.CopilotChatRequestDto;
import com.rfp.platform.dto.HumanReviewRequestDto;
import com.rfp.platform.dto.WorkflowStartRequestDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.UUID;

@Service
public class AiServiceClient {

    private final RestClient restClient;

    @Autowired
    public AiServiceClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public Map<String, Object> startWorkflow(UUID projectId, UUID documentId) {
        WorkflowStartRequestDto req = new WorkflowStartRequestDto();
        req.setDocumentId(documentId);

        return restClient.post()
                .uri("/workflow/{projectId}/start", projectId)
                .body(req)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> getWorkflowStatus(UUID projectId) {
        return restClient.get()
                .uri("/workflow/{projectId}/status", projectId)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> getComplianceReport(UUID projectId) {
        return restClient.get()
                .uri("/workflow/{projectId}/compliance", projectId)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> getProposalDraft(UUID projectId) {
        return restClient.get()
                .uri("/workflow/{projectId}/proposal", projectId)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> submitReview(UUID projectId, String action, String feedback) {
        HumanReviewRequestDto req = new HumanReviewRequestDto();
        req.setAction(action);
        req.setFeedback(feedback);

        return restClient.post()
                .uri("/workflow/{projectId}/review", projectId)
                .body(req)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> chatWithCopilot(UUID projectId, String message) {
        CopilotChatRequestDto req = new CopilotChatRequestDto();
        req.setProjectId(projectId);
        req.setMessage(message);

        return restClient.post()
                .uri("/assistant/chat")
                .body(req)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> getChatHistory(UUID projectId) {
        return restClient.get()
                .uri("/assistant/{projectId}/history", projectId)
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }
}
