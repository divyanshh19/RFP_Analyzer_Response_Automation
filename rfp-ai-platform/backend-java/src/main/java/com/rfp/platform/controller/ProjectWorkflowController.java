package com.rfp.platform.controller;

import com.rfp.platform.dto.HumanReviewRequestDto;
import com.rfp.platform.dto.WorkflowStartRequestDto;
import com.rfp.platform.entity.ProjectEntity;
import com.rfp.platform.service.ProjectWorkflowService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects")
public class ProjectWorkflowController {

    private final ProjectWorkflowService workflowService;

    @Autowired
    public ProjectWorkflowController(ProjectWorkflowService workflowService) {
        this.workflowService = workflowService;
    }

    @GetMapping
    public ResponseEntity<List<ProjectEntity>> listProjects() {
        return ResponseEntity.ok(workflowService.listProjects());
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProjectEntity> getProject(@PathVariable UUID id) {
        return workflowService.getProject(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}/workflow/start")
    public ResponseEntity<Map<String, Object>> startWorkflow(
            @PathVariable UUID id,
            @RequestBody(required = false) WorkflowStartRequestDto request
    ) {
        UUID docId = (request != null) ? request.getDocumentId() : null;
        return ResponseEntity.ok(workflowService.startWorkflow(id, docId));
    }

    @GetMapping("/{id}/workflow/status")
    public ResponseEntity<Map<String, Object>> getWorkflowStatus(@PathVariable UUID id) {
        return ResponseEntity.ok(workflowService.getWorkflowStatus(id));
    }

    @GetMapping("/{id}/compliance")
    public ResponseEntity<Map<String, Object>> getComplianceReport(@PathVariable UUID id) {
        return ResponseEntity.ok(workflowService.getComplianceReport(id));
    }

    @GetMapping("/{id}/evidence")
    public ResponseEntity<Map<String, Object>> getEvidenceMapping(@PathVariable UUID id) {
        Map<String, Object> comp = workflowService.getComplianceReport(id);
        return ResponseEntity.ok(comp);
    }

    @PostMapping("/{id}/review")
    public ResponseEntity<Map<String, Object>> submitReview(
            @PathVariable UUID id,
            @RequestBody HumanReviewRequestDto reviewRequest
    ) {
        return ResponseEntity.ok(workflowService.submitReview(
                id,
                reviewRequest.getAction(),
                reviewRequest.getFeedback()
        ));
    }

    @GetMapping("/{id}/proposal")
    public ResponseEntity<Map<String, Object>> getProposal(@PathVariable UUID id) {
        return ResponseEntity.ok(workflowService.getProposal(id));
    }
}
