package com.satya.backend;

import java.util.List;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class CanonicalStore {

    private final EvidenceRepository repository;
    private final ObjectMapper mapper;
    private final String configuredRevision;

    public CanonicalStore(
            EvidenceRepository repository,
            ObjectMapper mapper,
            Environment environment
    ) {
        this.repository = repository;
        this.mapper = mapper;
        configuredRevision = environment.getProperty(
                "satya.corpus.revision",
                ""
        ).strip();
    }

    public String activeRevision() {
        if (configuredRevision.isEmpty()) {
            return null;
        }

        if (!repository.existsByCorpusRevisionAndRecordKind(
                configuredRevision,
                "bundle"
        )) {
            throw new ApiFailure(
                    503,
                    "CORPUS_NOT_AVAILABLE",
                    "The configured corpus revision has not been imported.",
                    false
            );
        }

        return configuredRevision;
    }

    public List<Contract.Source> sources(String revision) {
        return repository
                .findByCorpusRevisionAndRecordKindOrderByExternalIdAsc(
                        revision,
                        "document"
                )
                .stream()
                .map(record -> decode(record, Contract.Source.class))
                .toList();
    }

    public Contract.Source source(String revision, String documentId) {
        EvidenceRecord record = repository
                .findByCorpusRevisionAndRecordKindAndExternalId(
                        revision,
                        "document",
                        documentId
                )
                .orElseThrow(() -> notFound("Document"));

        return decode(record, Contract.Source.class);
    }

    public Contract.Evidence paragraph(String revision, String paragraphId) {
        EvidenceRecord record = repository
                .findByCorpusRevisionAndRecordKindAndExternalId(
                        revision,
                        "paragraph",
                        paragraphId
                )
                .orElseThrow(() -> notFound("Paragraph"));

        return decode(record, Contract.Evidence.class);
    }

    private <T> T decode(EvidenceRecord record, Class<T> type) {
        try {
            return mapper.readValue(record.payload(), type);
        } catch (JsonProcessingException exception) {
            throw new ApiFailure(
                    500,
                    "EVIDENCE_STORAGE_ERROR",
                    "Stored canonical evidence could not be read.",
                    false
            );
        }
    }

    private ApiFailure notFound(String type) {
        return new ApiFailure(
                404,
                "SOURCE_NOT_FOUND",
                type + " was not found in the configured corpus revision.",
                false
        );
    }
}