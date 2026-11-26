package com.satya.backend;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import org.hibernate.annotations.Immutable;

@Entity
@Immutable
@Table(name = "canonical_record")
public class EvidenceRecord {

    @Id
    @Column(
        name = "record_key",
        columnDefinition = "CHAR(64)",
        nullable = false
    )
    private String recordKey;

    @Column(name = "corpus_revision", length = 160, nullable = false)
    private String corpusRevision;

    @Column(name = "record_kind", length = 16, nullable = false)
    private String recordKind;

    @Column(name = "external_id", length = 160, nullable = false)
    private String externalId;

    @Column(name = "payload", columnDefinition = "LONGTEXT", nullable = false)
    private String payload;

    @Column(
        name = "bundle_sha256",
        columnDefinition = "CHAR(64)"
    )
    private String bundleSha256;

    protected EvidenceRecord() {
    }

    public EvidenceRecord(
            String recordKey,
            String corpusRevision,
            String recordKind,
            String externalId,
            String payload,
            String bundleSha256
    ) {
        this.recordKey = recordKey;
        this.corpusRevision = corpusRevision;
        this.recordKind = recordKind;
        this.externalId = externalId;
        this.payload = payload;
        this.bundleSha256 = bundleSha256;
    }

    public String payload() {
        return payload;
    }
}