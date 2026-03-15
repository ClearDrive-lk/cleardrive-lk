# Cloudflare WAF Assets

This folder contains source-controlled assets for `CD-93`.

Files:

- `waf-config.template.json`
  Cloudflare WAF rule template covering:
  - OWASP managed rules
  - SQL injection blocking
  - XSS blocking
  - path traversal blocking
  - admin route protection
  - rate limits
  - bot management defaults

What this does not do:

- create a Cloudflare account
- add a zone/domain
- change nameservers
- apply rules automatically to a live Cloudflare zone

Those steps still require Cloudflare dashboard/API credentials and a real zone.

Suggested rollout:

1. Create/verify the `cleardrive.lk` zone in Cloudflare.
2. Enable the managed OWASP ruleset from the Cloudflare dashboard.
3. Recreate the custom and rate-limit rules from `waf-config.template.json`.
4. Enable bot management or Super Bot Fight Mode as allowed by your plan.
5. Run the local verification script:
   `python backend/scripts/test_waf_attacks.py --base-url https://cleardrive.lk`

Expected result:

- normal baseline requests should not be blocked
- SQLi/XSS/path-traversal probes should be blocked or challenged
- login brute-force simulation should trigger edge mitigation
