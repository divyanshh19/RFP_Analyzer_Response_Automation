package com.rfp.platform.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "documents")
public class DocumentEntity {

    @Id
    @Column(name = "id", nullable = false)
    private UUID id;

    @Column(name = "rfp_project_id")
    private UUID rfpProjectId;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "file_type", length = 50)
    private String fileType;

    @Column(name = "file_path", columnDefinition = "TEXT")
    private String filePath;

    @Column(name = "document_type", length = 50)
    private String documentType;

    @Column(name = "processing_status", length = 50)
    private String processingStatus = "PENDING";

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public DocumentEntity() {
        if (this.id == null) {
            this.id = UUID.randomUUID();
        }
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getRfpProjectId() { return rfpProjectId; }
    public void setRfpProjectId(UUID rfpProjectId) { this.rfpProjectId = rfpProjectId; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getFileType() { return fileType; }
    public void setFileType(String fileType) { this.fileType = fileType; }

    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }

    public String getDocumentType() { return documentType; }
    public void setDocumentType(String documentType) { this.documentType = documentType; }

    public String getProcessingStatus() { return processingStatus; }
    public void setProcessingStatus(String processingStatus) { this.processingStatus = processingStatus; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
