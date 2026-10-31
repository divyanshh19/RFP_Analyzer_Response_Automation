package com.rfp.platform.dto;

import java.util.UUID;

public class CopilotChatRequestDto {
    private UUID projectId;
    private String message;

    public UUID getProjectId() { return projectId; }
    public void setProjectId(UUID projectId) { this.projectId = projectId; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
