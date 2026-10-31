package com.rfp.platform.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    @Value("${ai.service.url:http://localhost:8000/api}")
    private String aiServiceUrl;

    @Bean
    public RestClient aiServiceClient() {
        return RestClient.builder()
                .baseUrl(aiServiceUrl)
                .defaultHeader("Accept", "application/json")
                .defaultHeader("Content-Type", "application/json")
                .build();
    }
}
