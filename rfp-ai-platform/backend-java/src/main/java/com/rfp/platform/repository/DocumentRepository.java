package com.rfp.platform.repository;

import com.rfp.platform.entity.DocumentEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DocumentRepository extends JpaRepository<DocumentEntity, UUID> {
    List<DocumentEntity> findByRfpProjectId(UUID rfpProjectId);
    Optional<DocumentEntity> findFirstByRfpProjectIdAndDocumentTypeOrderByCreatedAtDesc(UUID rfpProjectId, String documentType);
}
