package com.rfp.platform.service;

import com.rfp.platform.entity.DocumentEntity;
import com.rfp.platform.entity.ProjectEntity;
import com.rfp.platform.repository.DocumentRepository;
import com.rfp.platform.repository.ProjectRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class ProjectWorkflowService {

    private final ProjectRepository projectRepository;
    private final DocumentRepository documentRepository;
    private final AiServiceClient aiServiceClient;

    @Autowired
    public ProjectWorkflowService(
            ProjectRepository projectRepository,
            DocumentRepository documentRepository,
            AiServiceClient aiServiceClient
    ) {
        this.projectRepository = projectRepository;
        this.documentRepository = documentRepository;
        this.aiServiceClient = aiServiceClient;
    }

    public List<ProjectEntity> listProjects() {
        return projectRepository.findAll();
    }

    public Optional<ProjectEntity> getProject(UUID projectId) {
        return projectRepository.findById(projectId);
    }

    public ProjectEntity createProject(String name, String description) {
        ProjectEntity p = new ProjectEntity();
        p.setName(name);
        p.setDescription(description);
        p.setStatus("DRAFT");
        return projectRepository.save(p);
    }

    public Map<String, Object> startWorkflow(UUID projectId, UUID documentId) {
        // Resolve document if not explicitly passed
        if (documentId == null) {
            Optional<DocumentEntity> doc = documentRepository
                    .findFirstByRfpProjectIdAndDocumentTypeOrderByCreatedAtDesc(projectId, "RFP");
            if (doc.isPresent()) {
                documentId = doc.get().getId();
            }
        }

        Map<String, Object> res = aiServiceClient.startWorkflow(projectId, documentId);

        // Update project status
        projectRepository.findById(projectId).ifPresent(p -> {
            p.setStatus("PROCESSING");
            projectRepository.save(p);
        });

        return res;
    }

    public Map<String, Object> getWorkflowStatus(UUID projectId) {
        return aiServiceClient.getWorkflowStatus(projectId);
    }

    public Map<String, Object> getComplianceReport(UUID projectId) {
        return aiServiceClient.getComplianceReport(projectId);
    }

    public Map<String, Object> getProposal(UUID projectId) {
        return aiServiceClient.getProposalDraft(projectId);
    }

    public Map<String, Object> submitReview(UUID projectId, String action, String feedback) {
        Map<String, Object> res = aiServiceClient.submitReview(projectId, action, feedback);

        projectRepository.findById(projectId).ifPresent(p -> {
            if ("APPROVED".equalsIgnoreCase(action)) {
                p.setStatus("COMPLETED");
            } else if ("REVISE".equalsIgnoreCase(action)) {
                p.setStatus("REVISION");
            } else {
                p.setStatus("REJECTED");
            }
            projectRepository.save(p);
        });

        return res;
    }
}
