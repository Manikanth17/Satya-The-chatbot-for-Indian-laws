# SATYA backend – corrected build package

This package preserves the existing backend design and fixes the build-blocking Java package declarations and Maven compiler include configuration.

## Requirements
- JDK 21
- Maven 3.9+
- MySQL 8+

## 1. Create the database
Run in MySQL:

```sql
CREATE DATABASE satya_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 2. Configure environment (PowerShell)
Run these in the same PowerShell terminal before starting the backend:

```powershell
$env:SATYA_DB_URL="jdbc:mysql://localhost:3306/satya_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Kolkata"
$env:SATYA_DB_USERNAME="root"
$env:SATYA_DB_PASSWORD="YOUR_MYSQL_PASSWORD"
$env:SATYA_AI_MODE="mock"
$env:SATYA_ALLOWED_FRONTEND_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"
```

Use the MySQL password you created during installation. Do not commit credentials to Git.

## 3. Run

```powershell
cd backend
mvn clean test
mvn spring-boot:run
```

Backend health endpoint:

`http://127.0.0.1:8080/api/health`

## 4. Important mode distinction
`SATYA_AI_MODE=mock` returns the repository's synthetic test fixture. It is not real legal information and must not be presented as legal guidance.

To call the Python service, set:

```powershell
$env:SATYA_AI_MODE="python"
$env:SATYA_AI_BASE_URL="http://127.0.0.1:8000"
$env:SATYA_INTERNAL_TOKEN="replace-with-a-long-random-secret-at-least-32-characters"
```

The Python service in the current repository is still a scaffold and must implement the expected `satya-chat-v1` response contract before this mode can answer real questions.

## 5. Import a reviewed evidence bundle
The importer expects a JSON bundle matching `Contract.EvidenceBundle` and the validation rules in `EvidenceImporter`. The bundle must use schema `satya-evidence-v1`, contain 3–5 reviewed documents, and include reviewed paragraph records. Configure `SATYA_CORPUS_REVISION` to the exact revision after import.

Example offline import:

```powershell
$env:SATYA_IMPORT_FILE="C:\path\to\reviewed-bundle.json"
$env:SATYA_CORPUS_REVISION="your-corpus-revision"
mvn spring-boot:run -Dspring-boot.run.arguments="--spring.main.web-application-type=none"
```

Importing a bundle does not establish that its legal content is current or authoritative. Verify documents and effective dates before use.

## API
- `GET /api/health`
- `POST /api/chat` with `{ "question": "..." }`
- `GET /api/sources`
- `GET /api/sources/{documentId}`
- `GET /api/paragraphs/{paragraphId}`

The backend validates AI response structure and evidence references. This is not a substitute for legal review or independent validation of the model's legal interpretation.
