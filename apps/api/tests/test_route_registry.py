"""Database-free guards for API route compatibility and accidental duplicates."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.routes.sessions import SessionCreate
from app.main import app


def _openapi_operations() -> dict[tuple[str, str], dict[str, object]]:
    paths = app.openapi()["paths"]
    return {
        (method.upper(), path): operation
        for path, path_item in paths.items()
        for method, operation in path_item.items()
        if method in {"get", "post", "put", "patch", "delete", "head", "options"}
    }


def test_openapi_operation_ids_are_unique() -> None:
    operation_ids = [
        operation["operationId"]
        for operation in _openapi_operations().values()
        if "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))


def test_saas_finance_query_routes_remain_registered() -> None:
    operations = _openapi_operations()
    expected = {
        ("GET", "/api/v1/saas/crm/finance/overview"): "finance_overview",
        ("GET", "/api/v1/saas/crm/page/invoices"): "paged_invoices",
        ("GET", "/api/v1/saas/crm/page/payments"): "paged_payments",
    }

    for operation, endpoint_name in expected.items():
        assert operations[operation]["operationId"].startswith(f"{endpoint_name}_")


def test_saas_finance_crud_routes_have_one_active_owner() -> None:
    operations = _openapi_operations()
    expected = {
        ("GET", "/api/v1/saas/crm/contracts"): "list_contracts",
        ("POST", "/api/v1/saas/crm/contracts"): "create_contract",
        ("PATCH", "/api/v1/saas/crm/contracts/{contract_id}"): "update_contract",
        ("GET", "/api/v1/saas/crm/invoices"): "list_invoices",
        ("POST", "/api/v1/saas/crm/invoices"): "create_invoice",
        ("PATCH", "/api/v1/saas/crm/invoices/{invoice_id}"): "update_invoice",
        ("GET", "/api/v1/saas/crm/payments"): "list_payments",
        ("POST", "/api/v1/saas/crm/payments"): "create_payment",
        ("PATCH", "/api/v1/saas/crm/payments/{payment_id}"): "update_payment",
    }

    for operation, endpoint_name in expected.items():
        assert operations[operation]["operationId"].startswith(f"{endpoint_name}_")


def test_password_reset_compatibility_paths_remain_available() -> None:
    operations = _openapi_operations()
    assert ("POST", "/api/v1/auth/forgot-password") in operations
    assert ("POST", "/api/v1/auth/password-reset/request") in operations
    assert ("POST", "/api/v1/auth/reset-password") in operations
    assert ("POST", "/api/v1/auth/password-reset/confirm") in operations


def test_platform_incident_lifecycle_routes_are_registered() -> None:
    operations = _openapi_operations()
    expected = {
        ("GET", "/api/v1/support/developer/incidents"),
        ("POST", "/api/v1/support/developer/incidents"),
        ("PATCH", "/api/v1/support/developer/incidents/{incident_id}"),
    }
    assert expected <= operations.keys()


def test_tenant_knowledge_base_routes_are_registered() -> None:
    operations = _openapi_operations()
    expected = {
        ("GET", "/api/v1/support/knowledge"),
        ("GET", "/api/v1/support/knowledge/{article_id}"),
        ("POST", "/api/v1/support/admin/knowledge"),
        ("PATCH", "/api/v1/support/admin/knowledge/{article_id}"),
    }
    assert expected <= operations.keys()


def test_live_session_times_require_timezone_and_positive_duration() -> None:
    base = {
        "course_id": str(uuid4()),
        "title": "Instructor-led session",
        "starts_at": "2031-07-01T10:00:00Z",
        "ends_at": "2031-07-01T11:00:00Z",
    }
    assert SessionCreate.model_validate(base).ends_at > SessionCreate.model_validate(base).starts_at

    with pytest.raises(ValidationError, match="must include a timezone"):
        SessionCreate.model_validate({**base, "starts_at": "2031-07-01T10:00:00"})
    with pytest.raises(ValidationError, match="must be later"):
        SessionCreate.model_validate({**base, "ends_at": "2031-07-01T09:00:00Z"})
