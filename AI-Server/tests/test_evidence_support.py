from app.verification.evidence_support import assess_claim_support


def test_direct_textual_support():
    evidence = {
        "exact_text": (
            "An application fee of rupees ten "
            "shall accompany the application."
        )
    }

    result = assess_claim_support(
        "An application fee of rupees ten shall accompany the application.",
        evidence,
    )

    assert result == "supported"


def test_irrelevant_evidence_is_unsupported():
    evidence = {
        "exact_text": (
            "Postal charges exceeding fifty rupees "
            "shall be paid by the applicant."
        )
    }

    result = assess_claim_support(
        "The photocopying fee is two rupees per page.",
        evidence,
    )

    assert result == "unsupported"


def test_numeric_mismatch_is_uncertain():
    evidence = {
        "exact_text": "The application fee shall be rupees ten."
    }

    result = assess_claim_support(
        "The application fee shall be rupees twenty.",
        evidence,
    )

    assert result == "uncertain"


def test_negation_mismatch_is_uncertain():
    evidence = {
        "exact_text": "The authority shall provide the information."
    }

    result = assess_claim_support(
        "The authority shall not provide the information.",
        evidence,
    )

    assert result == "uncertain"


def test_paraphrased_claim_is_uncertain():
    evidence = {
        "exact_text": (
            "The application fee shall be rupees ten."
        )
    }

    result = assess_claim_support(
        "Applicants must pay ten rupees to submit an application.",
        evidence,
    )

    assert result == "uncertain"