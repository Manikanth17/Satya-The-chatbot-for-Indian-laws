package com.satya.backend;

import java.util.List;
import java.util.Map;

import jakarta.validation.Valid;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class PublicController {

    private final ChatService chatService;
    private final CanonicalStore store;
    private final AiGateway gateway;

    public PublicController(
            ChatService chatService,
            CanonicalStore store,
            AiGateway gateway
    ) {
        this.chatService = chatService;
        this.store = store;
        this.gateway = gateway;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of(
                "status", "ok",
                "service", "satya-backend",
                "gateway_mode", gateway.mode()
        );
    }

    @PostMapping("/chat")
    public Contract.ChatResponse chat(
            @Valid @RequestBody Contract.ChatRequest request
    ) {
        return chatService.chat(request.question());
    }

    @GetMapping("/sources")
    public Contract.SourceLibrary sources() {
        String revision = store.activeRevision();

        return new Contract.SourceLibrary(
                "real",
                revision,
                revision == null ? List.of() : store.sources(revision)
        );
    }

    @GetMapping("/sources/{documentId}")
    public Contract.Source source(
            @PathVariable String documentId
    ) {
        return store.source(requiredRevision(), documentId);
    }

    @GetMapping("/paragraphs/{paragraphId}")
    public Contract.Evidence paragraph(
            @PathVariable String paragraphId
    ) {
        return store.paragraph(requiredRevision(), paragraphId);
    }

    private String requiredRevision() {
        String revision = store.activeRevision();

        if (revision == null) {
            throw new ApiFailure(
                    404,
                    "CORPUS_NOT_CONFIGURED",
                    "No reviewed corpus revision is configured.",
                    false
            );
        }

        return revision;
    }
}