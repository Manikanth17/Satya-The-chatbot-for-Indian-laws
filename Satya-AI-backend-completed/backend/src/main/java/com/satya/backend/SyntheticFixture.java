package com.satya.backend;

import java.util.List;

public final class SyntheticFixture {

    public static final String REVISION = "synthetic-v1";

    private static final String PARAGRAPH_ID =
            "synthetic-doc-001-p001-para001";

    private static final String TEXT =
            "In this synthetic test scenario, the example application "
            + "fee is 10 test credits.";

    private SyntheticFixture() {
    }

    public static Contract.Evidence evidence() {
        return new Contract.Evidence(
                PARAGRAPH_ID,
                "synthetic-doc-001",
                REVISION,
                "SYNTHETIC FIXTURE — Example Application",
                1,
                null,
                null,
                null,
                "Extracted paragraph 1 on PDF page 1.",
                TEXT,
                null,
                true
        );
    }

    public static Contract.AiResult result() {
        return new Contract.AiResult(
                Contract.CHAT_SCHEMA,
                REVISION,
                "answered",
                List.of(
                        new Contract.AiClaim(
                                "synthetic-claim-001",
                                TEXT,
                                List.of(
                                        new Contract.SupportingQuote(
                                                PARAGRAPH_ID,
                                                TEXT
                                        )
                                ),
                                "supported"
                        )
                ),
                0
        );
    }
}