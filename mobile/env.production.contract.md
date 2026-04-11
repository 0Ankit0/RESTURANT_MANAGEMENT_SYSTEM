# Mobile production environment contract (`mobile/.env.production`)

## Required runtime variables

| Variable | Purpose | Secret handling |
| --- | --- | --- |
| `BASE_URL` | Backend API base URL used by the mobile app. | Non-secret; set directly in env file. |
| `WEBSITE_URL` | Public website/frontend base URL sent during payment initiation. | Non-secret; set directly in env file. |
| `PAYMENT_RETURN_URL_BASE` | Payment callback base URL (for example `https://app.example.com/payment-callback`) used for return redirects and WebView callback interception. | Non-secret; set directly in env file. |

## Notes

- `PAYMENT_RETURN_URL_BASE` must be configured for payment initiation to succeed; the mobile app now fails fast when missing.
- Do not place backend secrets in mobile env files.
