# Corporate LMS — QA and Test Strategy

Version: 0.1

## 1. Quality objective

Quality means proving that the system behaves correctly, securely and predictably under realistic business conditions.

## 2. Test levels

### Unit
- Domain rules
- Validation
- Calculations
- Policy functions
- Status transitions

### Integration
- API + database
- Authorization + database
- File storage
- Notifications
- Jobs
- Integrations

### E2E
- Login
- Enrollment
- Learning
- Assessment
- Certification
- Compliance
- Manager workflow
- Admin workflow

### Security
- Authentication abuse
- Authorization bypass
- IDOR/BOLA
- injection
- file upload abuse
- rate limiting
- session abuse
- tenant isolation

### Accessibility
- automated checks
- keyboard checks
- screen-reader spot checks
- focus/order checks

### Performance
- API latency
- database query performance
- concurrent user scenarios
- bulk import
- report generation
- job throughput

## 3. Test data

Seeded data must:
- be clearly marked DEMO
- cover every role
- cover multiple departments
- cover active/inactive records
- cover overdue/complete learners
- cover failed/passed assessments
- cover expiring certificates
- cover exceptions
- cover realistic reporting cases

## 4. Critical workflows

1. Create tenant
2. Create user
3. Assign role
4. Create course
5. Publish course
6. Enroll learner
7. Complete learning
8. Submit assessment
9. Issue certificate
10. Verify certificate
11. Create compliance requirement
12. Assign requirement
13. Trigger reminder
14. Trigger overdue escalation
15. Record skill evidence
16. Export report
17. Audit privileged action

## 5. Regression rule

Every defect that reaches QA and is fixed should gain a regression test when technically appropriate.

## 6. Evidence

Release evidence should include:
- test summary
- failed/passed counts
- critical defects
- security review
- accessibility review
- migration result
- backup/restore result
- deployment result

## 7. Quality gates

### Gate 1
No broken core startup path.

### Gate 2
Authentication and tenant isolation pass.

### Gate 3
Learning journey passes end-to-end.

### Gate 4
Assessment/certification passes.

### Gate 5
Compliance/reporting passes.

### Gate 6
Security/accessibility/performance evidence passes.

### Gate 7
Production release checklist passes.

## 8. Release ready

- Critical defects: 0
- High-risk unresolved security defects: 0
- Core E2E suite: pass
- Tenant isolation suite: pass
- Database migration checks: pass
- Backup/restore test: pass
- Accessibility baseline: pass
- Observability: verified
- Documentation: updated
- Rollback procedure: tested

