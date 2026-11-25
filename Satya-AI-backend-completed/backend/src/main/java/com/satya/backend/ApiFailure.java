package com.satya.backend;

public final class ApiFailure extends RuntimeException {

    private final int httpStatus;
    private final String code;
    private final boolean retryable;

    public ApiFailure(
            int httpStatus,
            String code,
            String message,
            boolean retryable
    ) {
        super(message);
        this.httpStatus = httpStatus;
        this.code = code;
        this.retryable = retryable;
    }

    public int httpStatus() {
        return httpStatus;
    }

    public String code() {
        return code;
    }

    public boolean retryable() {
        return retryable;
    }

    public static ApiFailure invalidAiResponse() {
        return new ApiFailure(
                502,
                "AI_INVALID_RESPONSE",
                "The AI response failed integrity checks and was not displayed.",
                false
        );
    }
}