CREATE TABLE canonical_record (
    record_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    corpus_revision VARCHAR(160)
        CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    record_kind VARCHAR(16)
        CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    external_id VARCHAR(160)
        CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    payload LONGTEXT
        CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    bundle_sha256 CHAR(64)
        CHARACTER SET ascii COLLATE ascii_bin NULL,

    PRIMARY KEY (record_key),

    CONSTRAINT uq_canonical_identity
        UNIQUE (corpus_revision, record_kind, external_id),

    CONSTRAINT uq_bundle_hash
        UNIQUE (bundle_sha256),

    CONSTRAINT chk_record_kind
        CHECK (record_kind IN ('bundle', 'document', 'paragraph')),

    CONSTRAINT chk_payload_json
        CHECK (JSON_VALID(payload)),

    INDEX idx_corpus_kind (corpus_revision, record_kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;