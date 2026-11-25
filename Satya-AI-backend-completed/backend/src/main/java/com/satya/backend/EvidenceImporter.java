package com.satya.backend;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class EvidenceImporter {

    private static final long MAX_BUNDLE_BYTES = 30_000_000;

    private final EvidenceRepository repository;
    private final ObjectMapper mapper;
    private final Set<String> allowedHosts;

    public EvidenceImporter(
            EvidenceRepository repository,
            ObjectMapper mapper,
            Environment environment
    ) {
        this.repository = repository;
        this.mapper = mapper;

        allowedHosts = new HashSet<>(
                Arrays.stream(
                                environment.getRequiredProperty(
                                        "satya.corpus.allowed-hosts"
                                ).split(",")
                        )
                        .map(String::strip)
                        .map(String::toLowerCase)
                        .filter(value -> !value.isEmpty())
                        .toList()
        );
    }

    @Transactional
    public void importFile(Path path) {
        try {
            require(Files.isRegularFile(path), "Bundle file is missing.");

            long size = Files.size(path);
            require(
                    size > 0 && size <= MAX_BUNDLE_BYTES,
                    "Bundle must be nonempty and at most 30 MB."
            );

            byte[] bytes;
            try (var input = Files.newInputStream(path)) {
                bytes = input.readNBytes((int) MAX_BUNDLE_BYTES + 1);
            }

            require(
                    bytes.length <= MAX_BUNDLE_BYTES,
                    "Bundle exceeds the permitted size."
            );

            String rawJson = strictUtf8(bytes);
            Contract.EvidenceBundle bundle =
                    mapper.readValue(rawJson, Contract.EvidenceBundle.class);

            validate(bundle);

            String bundleHash = sha256(bytes);
            String revision = bundle.corpus_revision();

            require(
                    !repository.existsByCorpusRevisionAndRecordKind(
                            revision,
                            "bundle"
                    ),
                    "This corpus revision has already been imported."
            );

            require(
                    !repository.existsByBundleSha256(bundleHash),
                    "This exact evidence bundle has already been imported."
            );

            List<EvidenceRecord> records = new ArrayList<>();

            records.add(record(
                    revision,
                    "bundle",
                    revision,
                    rawJson,
                    bundleHash
            ));

            for (Contract.Source document : bundle.documents()) {
                records.add(record(
                        revision,
                        "document",
                        document.document_id(),
                        mapper.writeValueAsString(document),
                        null
                ));
            }

            for (Contract.Evidence paragraph : bundle.paragraphs()) {
                records.add(record(
                        revision,
                        "paragraph",
                        paragraph.paragraph_id(),
                        mapper.writeValueAsString(paragraph),
                        null
                ));
            }

            repository.saveAll(records);
            repository.flush();
        } catch (IOException exception) {
            throw new ApiFailure(
                    400,
                    "INVALID_EVIDENCE_BUNDLE",
                    "The evidence bundle could not be read or parsed.",
                    false
            );
        }
    }

    private void validate(Contract.EvidenceBundle bundle) {
        require(bundle != null, "Bundle is missing.");
        require(
                Contract.BUNDLE_SCHEMA.equals(bundle.schema_version()),
                "Unsupported evidence-bundle schema."
        );

        require(identifier(bundle.corpus_revision()), "Invalid revision.");
        require(
                !"synthetic-v1".equals(bundle.corpus_revision()),
                "Synthetic fixtures cannot be imported as a legal corpus."
        );

        require(
                bundle.extraction_reviewed(),
                "Extraction warnings and paragraphs must be reviewed."
        );

        require(
                bundle.documents() != null
                && bundle.documents().size() >= 3
                && bundle.documents().size() <= 5,
                "The reviewed corpus must contain 3–5 documents."
        );

        require(
                bundle.paragraphs() != null
                && !bundle.paragraphs().isEmpty()
                && bundle.paragraphs().size() <= 20_000,
                "Invalid paragraph collection."
        );

        Map<String, Contract.Source> documents = new HashMap<>();
        Set<String> documentHashes = new HashSet<>();
        Set<String> documentUrls = new HashSet<>();

        for (Contract.Source document : bundle.documents()) {
            require(document != null, "Null document.");
            require(identifier(document.document_id()), "Invalid document ID.");
            require(
                    bundle.corpus_revision().equals(document.corpus_revision()),
                    "Document revision mismatch."
            );

            require(
                    text(document.document_title(), 1000),
                    "Invalid document title."
            );

            require(document.reviewed(), "Document has not been reviewed.");
            require(
                    document.pdf_page_count() >= 1,
                    "Invalid PDF page count."
            );

            require(
                    document.sha256() != null
                    && document.sha256().matches("[0-9a-f]{64}"),
                    "Invalid PDF SHA-256."
            );

            require(
                    officialUrl(document.official_source_url()),
                    "Document source is outside the reviewed host allowlist."
            );

            require(
                    documents.putIfAbsent(
                            document.document_id(),
                            document
                    ) == null,
                    "Duplicate document ID."
            );

            require(
                    documentHashes.add(document.sha256()),
                    "Duplicate PDF hash."
            );

            require(
                    documentUrls.add(document.official_source_url()),
                    "Duplicate official document URL."
            );
        }

        Set<String> paragraphIds = new HashSet<>();
        Set<String> documentsWithParagraphs = new HashSet<>();

        for (Contract.Evidence paragraph : bundle.paragraphs()) {
            require(paragraph != null, "Null paragraph.");
            require(
                    identifier(paragraph.paragraph_id()),
                    "Invalid paragraph ID."
            );
            require(
                    paragraphIds.add(paragraph.paragraph_id()),
                    "Duplicate paragraph ID."
            );

            Contract.Source document = documents.get(paragraph.document_id());
            require(document != null, "Paragraph document is unresolved.");

            require(
                    bundle.corpus_revision().equals(paragraph.corpus_revision()),
                    "Paragraph revision mismatch."
            );

            require(!paragraph.synthetic(), "Synthetic paragraph rejected.");

            require(
                    document.document_title().equals(paragraph.document_title()),
                    "Paragraph title differs from its document."
            );

            require(
                    document.official_source_url()
                            .equals(paragraph.official_source_url()),
                    "Paragraph source URL differs from its document."
            );

            require(
                    paragraph.pdf_page_number() >= 1
                    && paragraph.pdf_page_number() <= document.pdf_page_count(),
                    "Paragraph PDF page is out of range."
            );

            require(
                    text(paragraph.derived_locator(), 1000),
                    "Missing paragraph locator."
            );

            require(
                    text(paragraph.exact_text(), 100_000),
                    "Invalid exact paragraph text."
            );

            require(
                    optionalText(paragraph.printed_page_label()),
                    "Invalid printed page label."
            );

            require(
                    optionalText(paragraph.original_section_label()),
                    "Invalid section label."
            );

            require(
                    optionalText(paragraph.original_paragraph_label()),
                    "Invalid original paragraph label."
            );

            documentsWithParagraphs.add(paragraph.document_id());
        }

        require(
                documentsWithParagraphs.equals(documents.keySet()),
                "Every imported document must contain reviewed paragraphs."
        );
    }

    private boolean officialUrl(String value) {
        try {
            if (value == null || value.length() > 4000) {
                return false;
            }

            URI url = URI.create(value);

            return "https".equalsIgnoreCase(url.getScheme())
                    && url.getHost() != null
                    && allowedHosts.contains(url.getHost().toLowerCase())
                    && url.getRawUserInfo() == null
                    && url.getRawFragment() == null
                    && (url.getPort() == -1 || url.getPort() == 443);
        } catch (IllegalArgumentException exception) {
            return false;
        }
    }

    private EvidenceRecord record(
            String revision,
            String kind,
            String externalId,
            String payload,
            String bundleHash
    ) {
        String identity = revision + "\n" + kind + "\n" + externalId;

        return new EvidenceRecord(
                sha256(identity.getBytes(StandardCharsets.UTF_8)),
                revision,
                kind,
                externalId,
                payload,
                bundleHash
        );
    }

    private String strictUtf8(byte[] bytes)
            throws CharacterCodingException {
        return StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(bytes))
                .toString();
    }

    private String sha256(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(bytes)
            );
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable.");
        }
    }

    private boolean identifier(String value) {
        return value != null
                && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,159}");
    }

    private boolean text(String value, int maximumLength) {
        return value != null
                && !value.isBlank()
                && value.length() <= maximumLength;
    }

    private boolean optionalText(String value) {
        return value == null || text(value, 1000);
    }

    private void require(boolean condition, String message) {
        if (!condition) {
            throw new ApiFailure(
                    400,
                    "INVALID_EVIDENCE_BUNDLE",
                    message,
                    false
            );
        }
    }
}