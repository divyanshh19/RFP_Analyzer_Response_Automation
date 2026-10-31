package com.rfp.platform.dto;

import java.util.UUID;

public class WorkflowStartRequestDto {
    private UUID documentId;

    public UUID getDocumentId() { return documentId; }
    public void setDocumentId(UUID documentId) { this.documentId = documentId; }
}
