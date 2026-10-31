package com.rfp.platform.controller;

import com.rfp.platform.dto.CopilotChatRequestDto;
import com.rfp.platform.service.AssistantService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/assistant")
public class AssistantController {

    private final AssistantService assistantService;

    @Autowired
    public AssistantController(AssistantService assistantService) {
        this.assistantService = assistantService;
    }

    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody CopilotChatRequestDto request) {
        return ResponseEntity.ok(assistantService.chat(request.getProjectId(), request.getMessage()));
    }

    @GetMapping("/{projectId}/history")
    public ResponseEntity<Map<String, Object>> getHistory(@PathVariable UUID projectId) {
        return ResponseEntity.ok(assistantService.getHistory(projectId));
    }
}
