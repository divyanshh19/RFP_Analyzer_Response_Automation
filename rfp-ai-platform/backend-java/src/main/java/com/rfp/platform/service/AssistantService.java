package com.rfp.platform.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;

@Service
public class AssistantService {

    private final AiServiceClient aiServiceClient;

    @Autowired
    public AssistantService(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    public Map<String, Object> chat(UUID projectId, String message) {
        return aiServiceClient.chatWithCopilot(projectId, message);
    }

    public Map<String, Object> getHistory(UUID projectId) {
        return aiServiceClient.getChatHistory(projectId);
    }
}
