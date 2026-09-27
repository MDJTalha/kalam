# Worker application boundary

The worker now executes bounded background operations for the LMS:
- Course due-date reminder automation.
- Compliance automation and notifications.
- Notification email delivery.
- Notification webhook delivery with retry state.
- Scheduled report generation and delivery.
- Deterministic one-shot execution through `run.py --once` for local evidence and operations checks.

The worker uses the API domain models/services through an explicit import boundary. Production deployment should run it as a separate long-lived worker process/container with monitoring and restart policy.
