package com.satya.backend;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface EvidenceRepository
        extends JpaRepository<EvidenceRecord, String> {

    Optional<EvidenceRecord>
    findByCorpusRevisionAndRecordKindAndExternalId(
            String corpusRevision,
            String recordKind,
            String externalId
    );

    List<EvidenceRecord>
    findByCorpusRevisionAndRecordKindOrderByExternalIdAsc(
            String corpusRevision,
            String recordKind
    );

    boolean existsByCorpusRevisionAndRecordKind(
            String corpusRevision,
            String recordKind
    );

    boolean existsByBundleSha256(String bundleSha256);
}