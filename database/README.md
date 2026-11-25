# SATYA AI - Database Setup

This folder contains the local MySQL environment for SATYA AI.

## Technology
- MySQL 8.4
- Docker Compose
- Spring Boot integration through Spring Data JPA
- Flyway migrations managed by the backend

## 1. Configure the root `.env`

Place these variables in the `.env` file at the project root:

```env
MYSQL_DATABASE=satya_ai
MYSQL_USER=satya_user
MYSQL_PASSWORD=replace_with_a_strong_password
MYSQL_ROOT_PASSWORD=replace_with_a_different_strong_password
MYSQL_PORT=3306
```

Do not commit `.env` to Git.

## 2. Start MySQL

Run this command from the project root:

```bash
docker compose --env-file .env -f database/docker-compose.yml up -d
```

## 3. Check the container

```bash
docker ps
```

The container should be named `satya-mysql`.

## 4. Stop MySQL

```bash
docker compose -f database/docker-compose.yml down
```

## 5. Delete the database volume

WARNING: This permanently deletes the database data.

```bash
docker compose -f database/docker-compose.yml down -v
```

## Schema and migrations

This folder only provisions the MySQL server. Database tables should be created and updated through Flyway migration files in:

`backend/src/main/resources/db/migration/`

Do not maintain a second, competing copy of the application schema here.
