package com.satya.backend;

import java.net.URI;
import java.net.http.HttpClient;
import java.time.Duration;

import org.springframework.core.env.Environment;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
public class AiGateway {

    private final String mode;
    private final Environment environment;
    private final RestClient client;

    public AiGateway(Environment environment) {
        this.environment = environment;
        mode = environment.getRequiredProperty("satya.ai.mode");

        if (!"mock".equals(mode) && !"python".equals(mode)) {
            throw new IllegalStateException(
                    "SATYA_AI_MODE must be mock or python."
            );
        }

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();

        JdkClientHttpRequestFactory requestFactory =
                new JdkClientHttpRequestFactory(httpClient);

        requestFactory.setReadTimeout(Duration.ofSeconds(60));

        client = RestClient.builder()
                .requestFactory(requestFactory)
                .build();
    }

    public boolean isMock() {
        return "mock".equals(mode);
    }

    public String mode() {
        return mode;
    }

    public Contract.AiResult ask(String question, String revision) {
        if (isMock()) {
            return SyntheticFixture.result();
        }

        URI endpoint = configuredEndpoint();
        String token = environment.getProperty("satya.ai.internal-token", "");

        if (token.length() < 32
                || token.contains("\r")
                || token.contains("\n")) {
            throw configurationError();
        }

        try {
            Contract.AiResult result = client.post()
                    .uri(endpoint)
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .header("X-Internal-Token", token)
                    .body(
                            new Contract.AiRequest(
                                    Contract.CHAT_SCHEMA,
                                    question,
                                    revision
                            )
                    )
                    .retrieve()
                    .body(Contract.AiResult.class);

            if (result == null) {
                throw ApiFailure.invalidAiResponse();
            }

            return result;
        } catch (RestClientException exception) {
            throw new ApiFailure(
                    502,
                    "AI_SERVICE_ERROR",
                    "The AI service request failed. No answer was displayed.",
                    true
            );
        }
    }

    private URI configuredEndpoint() {
        try {
            URI base = URI.create(
                    environment.getProperty("satya.ai.base-url", "").strip()
            );

            boolean scheme =
                    "http".equalsIgnoreCase(base.getScheme())
                    || "https".equalsIgnoreCase(base.getScheme());

            boolean path =
                    base.getRawPath() == null
                    || base.getRawPath().isEmpty()
                    || "/".equals(base.getRawPath());

            int port = base.getPort();

            if (!scheme
                    || base.getHost() == null
                    || base.getRawUserInfo() != null
                    || base.getRawQuery() != null
                    || base.getRawFragment() != null
                    || !path
                    || !(port == -1 || (port >= 1 && port <= 65535))) {
                throw configurationError();
            }

            return base.resolve("/internal/chat");
        } catch (IllegalArgumentException exception) {
            throw configurationError();
        }
    }

    private ApiFailure configurationError() {
        return new ApiFailure(
                503,
                "AI_GATEWAY_NOT_CONFIGURED",
                "The internal AI gateway is not configured correctly.",
                false
        );
    }
}