



import logging
import time
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.ai import router as ai_router
from app.api.routes.assessments import router as assessments_router
from app.api.routes.auth import router as auth_router
from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.capability_assessments import (
    router as capability_assessments_router,
)
from app.api.routes.capability_domain import router as capability_domain_router
from app.api.routes.capability_gap import router as capability_gap_router
from app.api.routes.capability_risk import router as capability_risk_router
from app.api.routes.certificates import router as certificates_router
from app.api.routes.compliance import router as compliance_router
from app.api.routes.courses import router as courses_router
from app.api.routes.development import router as development_router
from app.api.routes.development_execution import router as development_execution_router
from app.api.routes.development_intelligence import (
    router as development_intelligence_router,
)
from app.api.routes.equivalencies import router as equivalencies_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.files import router as files_router
from app.api.routes.health import router as health_router
from app.api.routes.integrations import router as integrations_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.interop import router as interop_router
from app.api.routes.marketing import router as marketing_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.organization import router as organization_router
from app.api.routes.people import router as people_router
from app.api.routes.programs import router as programs_router
from app.api.routes.report_library import router as report_library_router
from app.api.routes.reports import router as reports_router
from app.api.routes.saas_commercial import router as saas_commercial_router
from app.api.routes.saas_finance import finance_overview, paged_invoices, paged_payments
from app.api.routes.search import router as search_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.skills import router as skills_router
from app.api.routes.support import router as support_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.request_context import request_id_context

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(message)s")
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
)
logger = structlog.get_logger("corplms.api")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Enterprise Corporate Learning Management System API",
    docs_url="/docs" if settings.api_docs_enabled else None,
    redoc_url="/redoc" if settings.api_docs_enabled else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled else None,
)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "health": "/api/v1/health",
        "docs": "/docs" if settings.api_docs_enabled else None,
    }

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
    started = time.perf_counter()
    status_code = 500

    try:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("Origin")
            if origin and origin != settings.web_origin:
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "Origin not allowed"},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.app_env != "development" and settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    finally:
        log = logger.debug if request.url.path in {
            "/api/v1/health",
            "/api/v1/health/live",
            "/api/v1/health/ready",
        } else logger.info
        log(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
            client_host=request.client.host if request.client else None,
        )
        request_id_context.reset(request_id_token)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(equivalencies_router, prefix="/api/v1/courses/equivalencies", tags=["learning"])
app.include_router(courses_router, prefix="/api/v1/courses", tags=["learning"])
app.include_router(assessments_router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(certificates_router, prefix="/api/v1/certificates", tags=["certificates"])
app.include_router(compliance_router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(capabilities_router, prefix="/api/v1/capabilities", tags=["capabilities"])
app.include_router(capability_domain_router, prefix="/api/v1/capability-domain", tags=["capability-domain"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["capability-evidence"])
app.include_router(capability_assessments_router, prefix="/api/v1/capability-assessments", tags=["capability-assessments"])
app.include_router(capability_gap_router, prefix="/api/v1/capability-gaps", tags=["capability-gaps"])
app.include_router(capability_risk_router, prefix="/api/v1/capability-risks", tags=["capability-risks"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(report_library_router, prefix="/api/v1/reports", tags=["report-library"])
app.include_router(people_router, prefix="/api/v1/people", tags=["people"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["administration"])
app.include_router(organization_router, prefix="/api/v1/organization", tags=["organization"])
app.include_router(programs_router, prefix="/api/v1/programs", tags=["programs"])
app.include_router(sessions_router, prefix="/api/v1/sessions", tags=["live-learning"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(support_router, prefix="/api/v1/support", tags=["support"])
app.include_router(development_router, prefix="/api/v1/development", tags=["development"])
app.include_router(development_intelligence_router, prefix="/api/v1/development", tags=["development-intelligence"])
app.include_router(development_execution_router, prefix="/api/v1/development/interventions", tags=["development-execution"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
app.include_router(integrations_router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(interop_router, prefix="/api/v1/interop", tags=["interoperability"])
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["governed-ai"])
app.include_router(marketing_router, prefix="/api/v1/marketing", tags=["marketing"])
app.include_router(saas_commercial_router, prefix="/api/v1/saas", tags=["saas-commercial"])
app.add_api_route("/api/v1/saas/crm/finance/overview", finance_overview, methods=["GET"], tags=["saas-finance"])
app.add_api_route("/api/v1/saas/crm/page/invoices", paged_invoices, methods=["GET"], tags=["saas-finance"])
app.add_api_route("/api/v1/saas/crm/page/payments", paged_payments, methods=["GET"], tags=["saas-finance"])
