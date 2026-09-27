# Corporate LMS — Architecture and Critical Sequences

Version: 0.1
Status: Phase 0 baseline

## 1. Logical architecture
```mermaid
flowchart LR
  U[Browser] --> W[Next.js Web]
  W --> A[FastAPI API]
  A --> D[(PostgreSQL)]
  A --> R[(Redis-compatible jobs/cache)]
  A --> F[Object Storage]
  A --> E[Integration Adapters]
  A --> X[xAPI/LTI/SCORM/cmi5 boundaries]
  A --> AU[Audit Service]
  A --> N[Notification Worker]
```

## 2. Login / session sequence
```mermaid
sequenceDiagram
  actor User
  User->>Web: submit credentials
  Web->>API: POST /api/v1/auth/login
  API->>DB: load tenant/user/roles
  API->>API: verify password + lockout policy
  API->>DB: persist session record
  API-->>Web: authenticated session cookie
  Web->>API: authenticated request
  API->>DB: resolve user + tenant
  API-->>Web: tenant-scoped response
```

## 3. Tenant-scoped read
```mermaid
sequenceDiagram
  actor User
  User->>Web: open protected resource
  Web->>API: request with session
  API->>API: authenticate + authorize
  API->>DB: query with tenant boundary
  DB-->>API: matching tenant records
  API-->>Web: response
```

## 4. Learning completion
```mermaid
sequenceDiagram
  actor Learner
  Learner->>Web: open course
  Web->>API: get course + enrollment
  API->>DB: load course/progress
  Learner->>Web: complete lesson
  Web->>API: POST completion
  API->>DB: persist LessonProgress
  API->>DB: update Enrollment
  API-->>Web: durable completion state
```

## 5. Assessment and certificate
```mermaid
sequenceDiagram
  actor Learner
  Learner->>API: start/submit assessment
  API->>DB: load questions without answer keys
  API->>API: score using server-side answer keys
  API->>DB: persist AssessmentAttempt
  alt passed + course complete
    API->>DB: persist Certificate
  end
  API-->>Learner: result/credential status
```

## 6. Compliance evidence
```mermaid
sequenceDiagram
  actor Admin
  Admin->>API: define/assign requirement
  API->>DB: persist requirement + assignment
  actor Learner
  Learner->>API: submit evidence
  API->>DB: persist evidence
  actor Reviewer
  Reviewer->>API: verify evidence
  API->>DB: persist verifier + timestamp
  API->>DB: update compliance state
```

## 7. File lifecycle
```mermaid
flowchart LR
  Upload --> Validate[Validate MIME/size/name]
  Validate --> Scan[Malware-scan boundary]
  Scan --> Store[Private storage]
  Store --> Meta[(File metadata)]
  Meta --> Download[Authorized download]
```

These diagrams are normative at Phase 0; implementation changes require architecture/ADR review where the trust boundary changes.