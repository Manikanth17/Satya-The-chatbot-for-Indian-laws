package com.satya.backend;

import org.springframework.dao.DataAccessException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ApiFailure.class)
    public ResponseEntity<Contract.ApiError> apiFailure(
            ApiFailure exception
    ) {
        return response(
                exception.httpStatus(),
                exception.code(),
                exception.getMessage(),
                exception.retryable()
        );
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Contract.ApiError> invalidQuestion(
            MethodArgumentNotValidException exception
    ) {
        return response(
                400,
                "INVALID_QUESTION",
                "Provide a nonblank question of at most 2000 characters.",
                false
        );
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Contract.ApiError> invalidJson(
            HttpMessageNotReadableException exception
    ) {
        return response(
                400,
                "INVALID_REQUEST",
                "The request JSON is invalid or contains unsupported fields.",
                false
        );
    }

    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<Contract.ApiError> databaseFailure(
            DataAccessException exception
    ) {
        return response(
                503,
                "DATABASE_UNAVAILABLE",
                "The evidence database could not complete the request.",
                true
        );
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Contract.ApiError> httpFailure(
            ResponseStatusException exception
    ) {
        return response(
                exception.getStatusCode().value(),
                "HTTP_REQUEST_ERROR",
                "The requested operation could not be completed.",
                false
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Contract.ApiError> unexpectedFailure(
            Exception exception
    ) {
        return response(
                500,
                "INTERNAL_ERROR",
                "An unexpected technical error occurred.",
                false
        );
    }

    private ResponseEntity<Contract.ApiError> response(
            int status,
            String code,
            String message,
            boolean retryable
    ) {
        return ResponseEntity.status(status).body(
                new Contract.ApiError(
                        "error",
                        code,
                        message,
                        retryable
                )
        );
    }
}