# Corporate LMS — Security, Privacy and Compliance Baseline

Version: 0.1

## 1. Objective

The LMS must be built with security and governance as engineering requirements, not post-development polish.

This document defines readiness targets. It does not claim certification or legal compliance.

## 2. Security references

Primary engineering references:
- OWASP Application Security Verification Standard (ASVS)
- OWASP secure coding guidance
- W3C WCAG 2.2
- NIST AI Risk Management Framework and Generative AI Profile for AI features

## 3. Identity security

Requirements:
- strong password hashing
- brute-force/rate-limit protection
- secure password reset
- short-lived reset tokens
- session invalidation
- suspicious sign-in logging
- optional MFA
- optional SSO

## 4. Authorization security

Test:
- tenant boundary
- role boundary
- manager boundary
- instructor boundary
- learner boundary
- report boundary
- file boundary
- API boundary

Unauthorized access must fail closed.

## 5. Data protection

Classify:
- account data
- employee profile data
- learning records
- assessment results
- compliance records
- audit records
- uploaded documents
- AI interaction data

Collect only required data.

## 6. Privacy controls

Architecture should support:
- privacy notice
- purpose limitation
- retention
- deletion/anonymization where legally appropriate
- data export
- access request workflow
- tenant-configurable retention
- processor/subprocessor records

Legal language must be reviewed for actual markets before commercialization.

## 7. Auditability

Audit privileged actions including:
- user/role changes
- permission changes
- course publication
- assessment result changes
- certificate issuance/revocation
- compliance requirement changes
- exports
- integration changes
- AI policy/configuration changes

## 8. AI governance

For AI features:
- identify use case
- identify data sources
- define allowed users
- define prohibited use
- log model/prompt versions
- evaluate quality
- evaluate privacy
- provide human review for consequential outputs
- retain evidence needed for incident analysis

Do not use AI as an invisible employment decision engine.

## 9. Secure development lifecycle

Every release should include:
- dependency scanning
- secret scanning
- static analysis
- unit tests
- integration tests
- authorization tests
- security regression tests
- vulnerability review
- release checklist

## 10. Incident readiness

Maintain runbooks for:
- credential compromise
- tenant isolation failure
- unauthorized file exposure
- data corruption
- database outage
- object storage outage
- notification provider failure
- AI provider outage
- suspicious automated activity

## 11. Accessibility

Target WCAG 2.2 AA.

Test:
- keyboard access
- focus
- forms
- errors
- headings/landmarks
- contrast
- labels
- tables
- dialogs
- media alternatives
- responsive text/layout

## 12. Compliance positioning

The product may be designed to support customers with their own regulatory or certification obligations.

The product must not claim:
- ISO certification
- SOC 2 certification
- legal compliance
- regulatory approval

unless the relevant assessment/certification has actually been completed.

## 13. Security release blockers

Production release is blocked by:
- critical authentication bypass
- critical authorization bypass
- cross-tenant data exposure
- exploitable remote code execution
- exposed secrets
- critical injection defect
- unverified production migrations
- untested restore path for required production data
