package com.rfp.platform.dto;

public class HumanReviewRequestDto {
    private String action; // APPROVED, REVISE, REJECTED
    private String feedback;

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }

    public String getFeedback() { return feedback; }
    public void setFeedback(String feedback) { this.feedback = feedback; }
}
