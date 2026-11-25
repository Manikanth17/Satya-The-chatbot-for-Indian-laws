// package test.java.com.satya.backend;

// import com.fasterxml.jackson.databind.JsonNode;
// import com.fasterxml.jackson.databind.ObjectMapper;
// import com.fasterxml.jackson.databind.json.JsonMapper;

// import jakarta.validation.Validation;

// import org.junit.jupiter.api.Test;

// import static org.junit.jupiter.api.Assertions.*;

// class ContractTest {

//     private final ObjectMapper mapper = JsonMapper.builder().build();

//     @Test
//     void internalRequestUsesAgreedFieldNames() throws Exception {
//         Contract.AiRequest request = new Contract.AiRequest(
//                 Contract.CHAT_SCHEMA,
//                 "Question",
//                 "corpus-v1"
//         );

//         JsonNode json = mapper.readTree(
//                 mapper.writeValueAsString(request)
//         );

//         assertEquals("satya-chat-v1", json.get("schema_version").asText());
//         assertEquals("corpus-v1", json.get("corpus_revision").asText());
//         assertFalse(json.has("schemaVersion"));
//     }

//     @Test
//     void aiResultRoundTripPreservesFields() throws Exception {
//         Contract.AiResult original = SyntheticFixture.result();

//         Contract.AiResult decoded = mapper.readValue(
//                 mapper.writeValueAsString(original),
//                 Contract.AiResult.class
//         );

//         assertEquals(original, decoded);
//     }

//     @Test
//     void evidencePreservesWhitespace() throws Exception {
//         String exactText = "First line.\n\n  Second line.\t";

//         Contract.Evidence evidence = new Contract.Evidence(
//                 "paragraph-1",
//                 "document-1",
//                 "test-v1",
//                 "UNIT TEST FIXTURE",
//                 1,
//                 null,
//                 null,
//                 null,
//                 "Extracted paragraph 1 on PDF page 1.",
//                 exactText,
//                 null,
//                 true
//         );

//         Contract.Evidence decoded = mapper.readValue(
//                 mapper.writeValueAsString(evidence),
//                 Contract.Evidence.class
//         );

//         assertEquals(exactText, decoded.exact_text());
//         assertNull(decoded.official_source_url());
//     }

//     @Test
//     void syntheticEvidenceHasNoOfficialLink() throws Exception {
//         JsonNode json = mapper.readTree(
//                 mapper.writeValueAsString(SyntheticFixture.evidence())
//         );

//         assertTrue(json.get("synthetic").asBoolean());
//         assertTrue(json.get("official_source_url").isNull());
//     }

//     @Test
//     void questionValidationRejectsBlankAndOversizedInputs() {
//         try (var factory = Validation.buildDefaultValidatorFactory()) {
//             var validator = factory.getValidator();

//             assertFalse(
//                     validator.validate(
//                             new Contract.ChatRequest("   ")
//                     ).isEmpty()
//             );

//             assertFalse(
//                     validator.validate(
//                             new Contract.ChatRequest("x".repeat(2001))
//                     ).isEmpty()
//             );

//             assertTrue(
//                     validator.validate(
//                             new Contract.ChatRequest("Valid question.")
//                     ).isEmpty()
//             );
//         }
//     }

//     @Test
//     void technicalErrorIsNotAnEvidenceRefusal() throws Exception {
//         Contract.ApiError error = new Contract.ApiError(
//                 "error",
//                 "AI_SERVICE_ERROR",
//                 "Request failed.",
//                 true
//         );

//         JsonNode json = mapper.read


package com.satya.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;

import jakarta.validation.Validation;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ContractTest {

    private final ObjectMapper mapper = JsonMapper.builder().build();

    @Test
    void internalRequestUsesAgreedFieldNames() throws Exception {
        Contract.AiRequest request = new Contract.AiRequest(
                Contract.CHAT_SCHEMA,
                "Question",
                "corpus-v1"
        );

        JsonNode json = mapper.readTree(
                mapper.writeValueAsString(request)
        );

        assertEquals("satya-chat-v1", json.get("schema_version").asText());
        assertEquals("corpus-v1", json.get("corpus_revision").asText());
        assertFalse(json.has("schemaVersion"));
    }

    @Test
    void aiResultRoundTripPreservesFields() throws Exception {
        Contract.AiResult original = SyntheticFixture.result();

        Contract.AiResult decoded = mapper.readValue(
                mapper.writeValueAsString(original),
                Contract.AiResult.class
        );

        assertEquals(original, decoded);
    }

    @Test
    void evidencePreservesWhitespace() throws Exception {
        String exactText = "First line.\n\n  Second line.\t";

        Contract.Evidence evidence = new Contract.Evidence(
                "paragraph-1",
                "document-1",
                "test-v1",
                "UNIT TEST FIXTURE",
                1,
                null,
                null,
                null,
                "Extracted paragraph 1 on PDF page 1.",
                exactText,
                null,
                true
        );

        Contract.Evidence decoded = mapper.readValue(
                mapper.writeValueAsString(evidence),
                Contract.Evidence.class
        );

        assertEquals(exactText, decoded.exact_text());
        assertNull(decoded.official_source_url());
    }

    @Test
    void syntheticEvidenceHasNoOfficialLink() throws Exception {
        JsonNode json = mapper.readTree(
                mapper.writeValueAsString(SyntheticFixture.evidence())
        );

        assertTrue(json.get("synthetic").asBoolean());
        assertTrue(json.get("official_source_url").isNull());
    }

    @Test
    void questionValidationRejectsBlankAndOversizedInputs() {
        try (var factory = Validation.buildDefaultValidatorFactory()) {
            var validator = factory.getValidator();

            assertFalse(
                    validator.validate(
                            new Contract.ChatRequest("   ")
                    ).isEmpty()
            );

            assertFalse(
                    validator.validate(
                            new Contract.ChatRequest("x".repeat(2001))
                    ).isEmpty()
            );

            assertTrue(
                    validator.validate(
                            new Contract.ChatRequest("Valid question.")
                    ).isEmpty()
            );
        }
    }

    @Test
    void technicalErrorIsNotAnEvidenceRefusal() throws Exception {
        Contract.ApiError error = new Contract.ApiError(
                "error",
                "AI_SERVICE_ERROR",
                "Request failed.",
                true
        );

        JsonNode json = mapper.readTree(
                mapper.writeValueAsString(error)
        );

        assertEquals("error", json.get("status").asText());
        assertEquals("AI_SERVICE_ERROR", json.get("code").asText());
        assertEquals("Request failed.", json.get("message").asText());
        assertTrue(json.get("retryable").asBoolean());

        assertNotEquals("INSUFFICIENT_EVIDENCE", json.get("code").asText());
    }
}