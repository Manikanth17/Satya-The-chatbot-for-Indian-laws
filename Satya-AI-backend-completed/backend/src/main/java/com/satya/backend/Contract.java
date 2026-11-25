package com.satya.backend;

import java.util.List;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public final class Contract {

    public static final String DISCLAIMER =
            "Informational assistance, not legal advice.";

    public static final String CHAT_SCHEMA = "satya-chat-v1";
    public static final String BUNDLE_SCHEMA = "satya-evidence-v1";

    private Contract() {
    }

    public record ChatRequest(
            @NotBlank
            @Size(max = 2000)
            String question
    ) {
    }

    public record AiRequest(
            String schema_version,
            String question,
            String corpus_revision
    ) {
    }

    public record SupportingQuote(
            String evidence_id,
            String quote
    ) {
    }

    public record AiClaim(
            String claim_id,
            String text,
            List<SupportingQuote> supporting_quotes,
            String support_assessment
    ) {
    }

    public record AiResult(
            String schema_version,
            String corpus_revision,
            String status,
            List<AiClaim> claims,
            int unanswered_count
    ) {
    }

    public record DisplayClaim(
            String claim_id,
            String text,
            List<SupportingQuote> supporting_quotes
    ) {
    }

    public record Source(
            String document_id,
            String corpus_revision,
            String document_title,
            String official_source_url,
            String sha256,
            int pdf_page_count,
            boolean reviewed
    ) {
    }

    public record Evidence(
            String paragraph_id,
            String document_id,
            String corpus_revision,
            String document_title,
            int pdf_page_number,
            String printed_page_label,
            String original_section_label,
            String original_paragraph_label,
            String derived_locator,
            String exact_text,
            String official_source_url,
            boolean synthetic
    ) {
    }

    public record EvidenceBundle(
            String schema_version,
            String corpus_revision,
            boolean extraction_reviewed,
            List<Source> documents,
            List<Evidence> paragraphs
    ) {
    }

    public record ChatResponse(
            String schema_version,
            String status,
            String mode,
            String corpus_revision,
            String evidence_label,
            String message,
            List<DisplayClaim> claims,
            List<Evidence> evidence,
            int unanswered_count,
            String notice,
            String disclaimer
    ) {
    }

    public record SourceLibrary(
            String mode,
            String corpus_revision,
            List<Source> sources
    ) {
    }

    public record ApiError(
            String status,
            String code,
            String message,
            boolean retryable
    ) {
    }
}