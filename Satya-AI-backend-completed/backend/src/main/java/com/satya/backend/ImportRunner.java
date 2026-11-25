package com.satya.backend;

import java.nio.file.Path;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

@Component
public class ImportRunner implements ApplicationRunner {

    private final EvidenceImporter importer;
    private final Environment environment;
    private final ConfigurableApplicationContext context;

    public ImportRunner(
            EvidenceImporter importer,
            Environment environment,
            ConfigurableApplicationContext context
    ) {
        this.importer = importer;
        this.environment = environment;
        this.context = context;
    }

    @Override
    public void run(ApplicationArguments arguments) {
        String file = environment.getProperty("satya.import-file", "").strip();

        if (file.isEmpty()) {
            return;
        }

        if (environment.getProperty(
                "spring.main.web-application-type",
                ""
        ).equalsIgnoreCase("none")) {
            importer.importFile(Path.of(file));
            System.out.println("Canonical evidence bundle imported.");
            int exitCode = SpringApplication.exit(context, () -> 0);
            System.exit(exitCode);
            return;
        }

        throw new IllegalStateException(
                "Evidence import requires offline mode: "
                + "spring.main.web-application-type=none"
        );
    }
}