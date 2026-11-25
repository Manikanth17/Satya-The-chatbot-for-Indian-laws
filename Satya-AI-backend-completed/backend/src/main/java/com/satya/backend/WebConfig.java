package com.satya.backend;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;

import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final String[] allowedOrigins;
    private final String demoToken;

    public WebConfig(Environment environment) {
        allowedOrigins = Arrays.stream(
                        environment.getRequiredProperty(
                                "satya.frontend.allowed-origins"
                        ).split(",", -1)
                )
                .map(String::strip)
                .map(WebConfig::validateOrigin)
                .distinct()
                .toArray(String[]::new);

        demoToken = environment.getProperty("satya.demo-token", "");

        String bindAddress = environment.getProperty(
                "server.address",
                "127.0.0.1"
        );

        boolean loopback =
                "127.0.0.1".equals(bindAddress)
                || "::1".equals(bindAddress)
                || "localhost".equalsIgnoreCase(bindAddress);

        if ((!loopback || !demoToken.isEmpty())
                && demoToken.length() < 32) {
            throw new IllegalStateException(
                    "Configure SATYA_DEMO_TOKEN with at least 32 characters "
                    + "before enabling non-loopback access."
            );
        }

        if (demoToken.contains("\r") || demoToken.contains("\n")) {
            throw new IllegalStateException("Invalid demo token.");
        }
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOrigins)
                .allowedMethods("GET", "POST")
                .allowedHeaders(
                        "Accept",
                        "Content-Type",
                        "X-Demo-Token"
                )
                .allowCredentials(false)
                .maxAge(600);
    }

    @Bean
    public FilterRegistrationBean<OncePerRequestFilter> demoAccessFilter(
            ObjectMapper mapper
    ) {
        OncePerRequestFilter filter = new OncePerRequestFilter() {
            @Override
            protected void doFilterInternal(
                    HttpServletRequest request,
                    HttpServletResponse response,
                    FilterChain chain
            ) throws ServletException, IOException {
                response.setHeader("X-Content-Type-Options", "nosniff");
                response.setHeader("Cache-Control", "no-store");

                boolean preflight =
                        "OPTIONS".equalsIgnoreCase(request.getMethod());

                if (!preflight && !demoToken.isEmpty()) {
                    String supplied = request.getHeader("X-Demo-Token");

                    boolean authorized =
                            supplied != null
                            && MessageDigest.isEqual(
                                    demoToken.getBytes(StandardCharsets.UTF_8),
                                    supplied.getBytes(StandardCharsets.UTF_8)
                            );

                    if (!authorized) {
                        response.setStatus(401);
                        response.setContentType("application/json");
                        mapper.writeValue(
                                response.getOutputStream(),
                                new Contract.ApiError(
                                        "error",
                                        "UNAUTHORIZED",
                                        "A valid demo access token is required.",
                                        false
                                )
                        );
                        return;
                    }
                }

                chain.doFilter(request, response);
            }
        };

        FilterRegistrationBean<OncePerRequestFilter> registration =
                new FilterRegistrationBean<>(filter);

        registration.setOrder(10);
        registration.addUrlPatterns("/api/*");

        return registration;
    }

    private static String validateOrigin(String value) {
        try {
            URI origin = URI.create(value);

            boolean scheme =
                    "http".equalsIgnoreCase(origin.getScheme())
                    || "https".equalsIgnoreCase(origin.getScheme());

            boolean noPath =
                    origin.getRawPath() == null
                    || origin.getRawPath().isEmpty();

            int port = origin.getPort();

            if (value.isBlank()
                    || value.contains("*")
                    || !scheme
                    || origin.getHost() == null
                    || origin.getRawUserInfo() != null
                    || origin.getRawQuery() != null
                    || origin.getRawFragment() != null
                    || !noPath
                    || !(port == -1 || (port >= 1 && port <= 65535))) {
                throw new IllegalArgumentException();
            }

            return value;
        } catch (IllegalArgumentException exception) {
            throw new IllegalStateException(
                    "Allowed frontend origins must be exact HTTP or HTTPS "
                    + "origins without paths, trailing slashes, or wildcards."
            );
        }
    }
}