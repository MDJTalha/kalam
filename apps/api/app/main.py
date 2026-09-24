from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.request_context import request_id_context
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.assessments import router as assessments_router
from app.api.routes.certificates import router as certificates_router
from app.api.routes.compliance import router as compliance_router
from app.api.routes.skills import router as skills_router
from app.api.routes.reports import router as reports_router
from app.api.routes.people import router as people_router
from app.api.routes.admin import router as admin_router
from app.api.routes.programs import router as programs_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.development import router as development_router
from app.api.routes.search import router as search_router
from app.api.routes.files import router as files_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.interop import router as interop_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Enterprise Corporate Learning Management System API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[host.strip() for host in settings.allowed_hosts.split(",") if host.strip()],
)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    request_id_token = request_id_context.set(request_id)

    try:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("Origin")
            if origin and origin != settings.web_origin:
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "Origin not allowed"},
                )
                response.headers["X-Request-ID"] = request_id
                return response

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.app_env != "development" and settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    finally:
        request_id_context.reset(request_id_token)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(courses_router, prefix="/api/v1/courses", tags=["learning"])
app.include_router(assessments_router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(certificates_router, prefix="/api/v1/certificates", tags=["certificates"])
app.include_router(compliance_router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(people_router, prefix="/api/v1/people", tags=["people"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["administration"])
app.include_router(programs_router, prefix="/api/v1/programs", tags=["programs"])
app.include_router(sessions_router, prefix="/api/v1/sessions", tags=["live-learning"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(development_router, prefix="/api/v1/development", tags=["development"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(interop_router, prefix="/api/v1/interop", tags=["interoperability"])
