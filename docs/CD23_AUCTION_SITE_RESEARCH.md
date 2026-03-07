# CD-23.1 Research: Target Auction Sites

## Scope
This document captures the target sources evaluated for CD-23 and the safe implementation approach used in the backend scraper.

## Evaluated Sources
1. `https://www.ramadbk.com`
- Reason: Public Japanese used-vehicle listing pages with structured card data.
- Risk: Layout changes can break selectors.
- Mitigation: Selector-flexible parser + Selenium fallback.

2. `https://auctions.yahoo.co.jp` (not implemented)
- Reason: Large vehicle marketplace.
- Risk: ToS/anti-bot constraints and dynamic rendering.
- Decision: Deferred until explicit legal approval and compliance review.

3. `https://www.ussnet.co.jp` (not implemented)
- Reason: Japanese auction ecosystem relevance.
- Risk: Access controls and commercial restrictions.
- Decision: Deferred.

4. `https://www.beforward.jp` (not implemented)
- Reason: Public listing-style inventory pages.
- Risk: Scraping policy and structural changes.
- Decision: Deferred until compliance validation.

## Compliance Guardrails
1. Respect `robots.txt` and Terms of Service before enabling a new source.
2. Do not bypass CAPTCHAs, auth walls, or anti-bot controls.
3. Rate-limit requests and keep request volume low.
4. Collect only public vehicle listing attributes required by CD-23.

## Implementation Decision
CD-23 uses a hybrid source strategy:
1. Try live scraping via `requests + BeautifulSoup`.
2. Fallback to Selenium page-source fetch for dynamic pages.
3. If scraping fails, fallback to static dataset (`static_vehicles.json`, then `vehicles.json`).
4. Use mock scraper as runtime backup when live scraping returns no rows.
