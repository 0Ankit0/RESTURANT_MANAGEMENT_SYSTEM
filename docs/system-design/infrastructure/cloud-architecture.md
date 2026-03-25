# Cloud Architecture - Restaurant Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Guest touchpoints and web hosting | CloudFront + S3 / Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Messaging | Amazon SQS / EventBridge |
| Reporting store | Redshift / RDS replica / analytics warehouse |
| Object storage | Amazon S3 |
| Notifications | Amazon SES / SNS |
| Monitoring | CloudWatch + OpenTelemetry |
| Identity federation | IAM Identity Center / external IdP |

## Architecture Notes

- Use separate production and non-production environments to isolate financial and operational data.
- Preserve backups for orders, settlements, stock ledgers, and audit logs with clearly documented recovery procedures.
- Device-heavy branches may require local print/KDS gateways or connection-health monitoring even in a cloud-first design.
