package com.satya.backend;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.springframework.stereotype.Service;

@Service
public class ChatService {

    private static final Set<String> STATUSES = Set.of(
            "answered",
            "partial",
            "clarification",
            "refusal",
            "conflict"
    );

    private static final Set<String> ASSESSMENTS = Set.of(
            "supported",
            "unsupported",
            "uncertain"
    );

    private final AiGateway gateway;
    private final CanonicalStore store;

    public ChatService(AiGateway gateway, CanonicalStore store) {
        this.gateway = gateway;
        this.store = store;
    }

    public Contract.ChatResponse chat(String question) {
        boolean synthetic = gateway.isMock();

        String revision = synthetic
                ? SyntheticFixture.REVISION
                : store.activeRevision();

        if (revision == null) {
            return response(
                    "refusal",
                    false,
                    null,
                    List.of(),
                    List.of(),
                    0
            );
        }

        Contract.AiResult result = gateway.ask(question, revision);

        return validateAndCompose(result, revision, synthetic);
    }

    private Contract.ChatResponse validateAndCompose(
            Contract.AiResult result,
            String revision,
            boolean synthetic
    ) {
        require(result != null);
        require(Contract.CHAT_SCHEMA.equals(result.schema_version()));
        require(revision.equals(result.corpus_revision()));
        require(STATUSES.contains(result.status()));
        require(result.claims() != null);
        require(result.claims().size() <= 12);
        require(result.unanswered_count() >= 0);
        require(result.unanswered_count() <= 100);

        if ("refusal".equals(result.status())
                || "clarification".equals(result.status())) {
            require(result.claims().isEmpty());

            return response(
                    result.status(),
                    synthetic,
                    revision,
                    List.of(),
                    List.of(),
                    result.unanswered_count()
            );
        }

        require(!result.claims().isEmpty());

        List<Contract.DisplayClaim> displayedClaims = new ArrayList<>();
        Map<String, Contract.Evidence> displayedEvidence =
                new LinkedHashMap<>();

        Set<String> claimIds = new HashSet<>();
        int removedClaims = 0;

        for (Contract.AiClaim claim : result.claims()) {
            require(claim != null);
            require(identifier(claim.claim_id()));
            require(claimIds.add(claim.claim_id()));
            require(text(claim.text(), 2000));
            require(ASSESSMENTS.contains(claim.support_assessment()));

            if (!"supported".equals(claim.support_assessment())) {
                removedClaims++;
                continue;
            }

            require(claim.supporting_quotes() != null);
            require(!claim.supporting_quotes().isEmpty());
            require(claim.supporting_quotes().size() <= 8);

            Set<String> quoteIdentities = new HashSet<>();
            Map<String, Contract.Evidence> claimEvidence =
                    new LinkedHashMap<>();

            for (Contract.SupportingQuote quote : claim.supporting_quotes()) {
                require(quote != null);
                require(identifier(quote.evidence_id()));
                require(text(quote.quote(), 100_000));
                require(
                        quoteIdentities.add(
                                quote.evidence_id() + "\n" + quote.quote()
                        )
                );

                Contract.Evidence evidence =
                        resolveEvidence(revision, quote.evidence_id(), synthetic);

                require(revision.equals(evidence.corpus_revision()));
                require(evidence.synthetic() == synthetic);
                require(evidence.exact_text().contains(quote.quote()));

                if (synthetic) {
                    require(claim.text().equals(quote.quote()));
                    require(evidence.official_source_url() == null);
                } else {
                    require(evidence.official_source_url() != null);
                }

                claimEvidence.put(evidence.paragraph_id(), evidence);
            }

            displayedClaims.add(
                    new Contract.DisplayClaim(
                            claim.claim_id(),
                            claim.text(),
                            List.copyOf(claim.supporting_quotes())
                    )
            );

            displayedEvidence.putAll(claimEvidence);
        }

        int unansweredCount = result.unanswered_count() + removedClaims;
        String status = result.status();

        if (displayedClaims.isEmpty()) {
            status = "refusal";
        } else if ("conflict".equals(status)) {
            // A conflict response must retain at least two supported claims.
            require(displayedClaims.size() >= 2);
        } else if ("partial".equals(status)
                || unansweredCount > 0) {
            status = "partial";
        } else {
            status = "answered";
        }

        return response(
                status,
                synthetic,
                revision,
                List.copyOf(displayedClaims),
                List.copyOf(displayedEvidence.values()),
                unansweredCount
        );
    }

    private Contract.Evidence resolveEvidence(
            String revision,
            String paragraphId,
            boolean synthetic
    ) {
        if (synthetic) {
            Contract.Evidence fixture = SyntheticFixture.evidence();
            require(fixture.paragraph_id().equals(paragraphId));
            return fixture;
        }

        try {
            return store.paragraph(revision, paragraphId);
        } catch (ApiFailure exception) {
            if (exception.httpStatus() == 404) {
                throw ApiFailure.invalidAiResponse();
            }
            throw exception;
        }
    }

    private Contract.ChatResponse response(
            String status,
            boolean synthetic,
            String revision,
            List<Contract.DisplayClaim> claims,
            List<Contract.Evidence> evidence,
            int unansweredCount
    ) {
        String label = switch (status) {
            case "answered" -> "Supported by retrieved sources";
            case "partial" -> "Partially supported";
            case "conflict" -> "Conflicting evidence";
            default -> "Insufficient evidence";
        };

        String message = switch (status) {
            case "answered" ->
                    "The displayed claims have supporting evidence.";
            case "partial" ->
                    "Only supported claims are shown. Some requested points remain unsupported.";
            case "clarification" ->
                    "Please narrow your question to one specific issue within the reviewed topic.";
            case "conflict" ->
                    "The retrieved sources contain conflicting evidence. No definitive resolution is supplied.";
            default ->
                    "There is insufficient evidence in the available corpus to answer.";
        };

        String notice = synthetic
                ? "SYNTHETIC TEST DATA — not law or policy."
                : "Answers are limited to the reviewed corpus. "
                  + "Model-based support checks are fallible. "
                  + "Absence from this corpus does not prove a provision does not exist.";

        return new Contract.ChatResponse(
                Contract.CHAT_SCHEMA,
                status,
                synthetic ? "synthetic" : "real",
                revision,
                label,
                message,
                claims,
                evidence,
                unansweredCount,
                notice,
                Contract.DISCLAIMER
        );
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

    private void require(boolean condition) {
        if (!condition) {
            throw ApiFailure.invalidAiResponse();
        }
    }
}