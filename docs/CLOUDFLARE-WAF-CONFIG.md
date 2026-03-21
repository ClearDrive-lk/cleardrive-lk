# Cloudflare WAF Configuration

## Overview

ClearDrive uses Cloudflare WAF for edge security protection.

## Active Rules

### 1. OWASP ModSecurity Core Ruleset

- Status: Enabled
- Sensitivity: Medium
- Protects: SQL Injection, XSS, RCE, LFI, RFI

### 2. Custom WAF Rules

- SQL Injection Protection
- XSS Protection
- Path Traversal Protection
- Admin Panel Protection (GeoIP restriction)
- API Security

### 3. Rate Limiting

- Global: 100 req/10s per IP
- Login: 5 req/60s per IP
- Registration: 3 req/hour per IP
- API: 60 req/60s per IP+UA

### 4. Bot Protection

- Bot Fight Mode: Enabled
- Bad bots blocked automatically
- Verified bots (Google, Bing) allowed

## Testing

### Test SQL Injection Protection

```bash
curl "https://cleardrive.lk/search?q=' or 1=1--"
# Expected: 403 Forbidden
```

### Test Rate Limiting

```bash
for i in {1..10}; do
  curl -X POST https://cleardrive.lk/api/v1/auth/login
done
# Expected: 429 after 5 attempts
```

## Monitoring

Dashboard: https://dash.cloudflare.com

- Security -> Events (view blocked requests)
- Analytics -> Security (threat statistics)

## Emergency Procedures

### Under DDoS Attack

1. Security -> Settings
2. Security Level: I'm Under Attack!
3. All visitors get JavaScript challenge
4. Return to Medium after attack subsides

### False Positives

1. Security -> Events
2. Find blocked request
3. Click request -> View details
4. Add exception if legitimate:
   - Managed Rules -> Configure
   - Add exception for specific rule

## Contacts

- Primary: admin@cleardrive.lk
- Cloudflare Support: https://support.cloudflare.com
