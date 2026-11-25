package com.satya.backend;

import java.util.List;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class ChatServiceTest {

    @Test
    void mockResultIsExplicitlySynthetic() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(true);
        when(gateway.ask("Question", "synthetic-v1"))
                .thenReturn(SyntheticFixture.result());

        Contract.ChatResponse response =
                new ChatService(gateway, store).chat("Question");

        assertEquals("answered", response.status());
        assertEquals("synthetic", response.mode());
        assertEquals("synthetic-v1", response.corpus_revision());
        assertEquals(1, response.claims().size());
        assertEquals(1, response.evidence().size());
        assertNull(response.evidence().getFirst().official_source_url());
        assertTrue(response.notice().startsWith("SYNTHETIC"));
        assertEquals(Contract.DISCLAIMER, response.disclaimer());

        verifyNoInteractions(store);
    }

    @Test
    void missingCorpusRefusesWithoutCallingPython() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn(null);

        Contract.ChatResponse response =
                new ChatService(gateway, store).chat("Question");

        assertEquals("refusal", response.status());
        assertEquals("real", response.mode());
        assertEquals("Insufficient evidence", response.evidence_label());
        assertTrue(response.claims().isEmpty());
        assertTrue(response.evidence().isEmpty());
        assertNull(response.corpus_revision());

        verify(gateway, never()).ask(anyString(), anyString());
    }

    @Test
    void mismatchedRevisionIsRejected() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "different-revision",
                        "answered",
                        List.of(supportedClaim("claim-1")),
                        0
                ));

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_INVALID_RESPONSE", failure.code());
        assertEquals(502, failure.httpStatus());
    }

    @Test
    void unresolvedCitationIsRejected() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "answered",
                        List.of(supportedClaim("claim-1")),
                        0
                ));

        when(store.paragraph("corpus-v1", "paragraph-1"))
                .thenThrow(new ApiFailure(
                        404,
                        "SOURCE_NOT_FOUND",
                        "Not found.",
                        false
                ));

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_INVALID_RESPONSE", failure.code());
        assertEquals(502, failure.httpStatus());
    }

    @Test
    void nonmatchingQuoteIsRejected() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        Contract.AiClaim claim = new Contract.AiClaim(
                "claim-1",
                "Invented text.",
                List.of(
                        new Contract.SupportingQuote(
                                "paragraph-1",
                                "Invented text."
                        )
                ),
                "supported"
        );

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "answered",
                        List.of(claim),
                        0
                ));

        when(store.paragraph("corpus-v1", "paragraph-1"))
                .thenReturn(evidence());

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_INVALID_RESPONSE", failure.code());
    }

    @Test
    void uncertainClaimIsRemovedAndAnswerBecomesPartial() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        Contract.AiClaim uncertain = new Contract.AiClaim(
                "claim-2",
                "Uncertain sentence.",
                List.of(),
                "uncertain"
        );

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "answered",
                        List.of(supportedClaim("claim-1"), uncertain),
                        0
                ));

        when(store.paragraph("corpus-v1", "paragraph-1"))
                .thenReturn(evidence());

        Contract.ChatResponse response =
                new ChatService(gateway, store).chat("Question");

        assertEquals("partial", response.status());
        assertEquals("Partially supported", response.evidence_label());
        assertEquals(1, response.claims().size());
        assertEquals("claim-1", response.claims().getFirst().claim_id());
        assertEquals(1, response.evidence().size());
        assertEquals(1, response.unanswered_count());
    }

    @Test
    void allUnsupportedClaimsBecomeRefusal() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        Contract.AiClaim unsupported = new Contract.AiClaim(
                "claim-1",
                "Unsupported sentence.",
                List.of(),
                "unsupported"
        );

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "answered",
                        List.of(unsupported),
                        0
                ));

        Contract.ChatResponse response =
                new ChatService(gateway, store).chat("Question");

        assertEquals("refusal", response.status());
        assertEquals("Insufficient evidence", response.evidence_label());
        assertTrue(response.claims().isEmpty());
        assertTrue(response.evidence().isEmpty());
        assertEquals(1, response.unanswered_count());
    }

    @Test
    void duplicateClaimIdsAreRejected() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "answered",
                        List.of(
                                supportedClaim("duplicate"),
                                supportedClaim("duplicate")
                        ),
                        0
                ));

        when(store.paragraph("corpus-v1", "paragraph-1"))
                .thenReturn(evidence());

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_INVALID_RESPONSE", failure.code());
    }

    @Test
    void clarificationContainsNoClaims() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "clarification",
                        List.of(),
                        0
                ));

        Contract.ChatResponse response =
                new ChatService(gateway, store).chat("Question");

        assertEquals("clarification", response.status());
        assertTrue(response.claims().isEmpty());
        assertTrue(response.evidence().isEmpty());
    }

    @Test
    void conflictRequiresAtLeastTwoSupportedClaims() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenReturn(result(
                        "corpus-v1",
                        "conflict",
                        List.of(supportedClaim("claim-1")),
                        0
                ));

        when(store.paragraph("corpus-v1", "paragraph-1"))
                .thenReturn(evidence());

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_INVALID_RESPONSE", failure.code());
    }

    @Test
    void gatewayFailureRemainsTechnicalError() {
        AiGateway gateway = mock(AiGateway.class);
        CanonicalStore store = mock(CanonicalStore.class);

        when(gateway.isMock()).thenReturn(false);
        when(store.activeRevision()).thenReturn("corpus-v1");

        when(gateway.ask("Question", "corpus-v1"))
                .thenThrow(new ApiFailure(
                        502,
                        "AI_SERVICE_ERROR",
                        "Request failed.",
                        true
                ));

        ApiFailure failure = assertThrows(
                ApiFailure.class,
                () -> new ChatService(gateway, store).chat("Question")
        );

        assertEquals("AI_SERVICE_ERROR", failure.code());
        assertEquals(502, failure.httpStatus());
        assertTrue(failure.retryable());
    }

    private static Contract.AiResult result(
            String revision,
            String status,
            List<Contract.AiClaim> claims,
            int unansweredCount
    ) {
        return new Contract.AiResult(
                Contract.CHAT_SCHEMA,
                revision,
                status,
                claims,
                unansweredCount
        );
    }

    private static Contract.AiClaim supportedClaim(String id) {
        return new Contract.AiClaim(
                id,
                "Exact supporting sentence.",
                List.of(
                        new Contract.SupportingQuote(
                                "paragraph-1",
                                "Exact supporting sentence."
                        )
                ),
                "supported"
        );
    }

    private static Contract.Evidence evidence() {
        // Invented unit-test evidence; never import as a legal corpus.
        return new Contract.Evidence(
                "paragraph-1",
                "document-1",
                "corpus-v1",
                "UNIT TEST FIXTURE",
                1,
                null,
                null,
                null,
                "Extracted paragraph 1 on PDF page 1.",
                "Exact supporting sentence.",
                "https://example.invalid/test.pdf",
                false
        );
    }
}