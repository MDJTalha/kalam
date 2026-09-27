# ADR-002 — Backend Stack

Status: Accepted
Date: 2026-09-24

## Decision
Use Python with FastAPI, Pydantic-style validation and SQLAlchemy for the API/application layer.

## Why
- Typed request/response contracts.
- OpenAPI generated from the API application.
- Async database and external I/O support.
- Mature ecosystem for security, testing and data processing.

## Alternatives
Node/NestJS and Django were considered; the current team/project baseline favors FastAPI for the modular API boundary.

## Consequences
Business authorization and domain rules remain centralized in the API. Static typing, linting, migration checks and integration tests are required CI evidence.