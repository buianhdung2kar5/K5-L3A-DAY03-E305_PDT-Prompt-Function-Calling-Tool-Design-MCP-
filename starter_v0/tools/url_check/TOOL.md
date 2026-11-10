---
name: url_check
track: team
kind: local
provider: none (static string analysis, never opens the URL)
requires_env: []
inputs: [url]
outputs: [verdict, safe, reasons, warnings]
side_effect: false
---
# url_check

Inspects a URL string and reports whether it looks safe. It does not open the page.

Flags as `suspicious`: scheme other than http/https, host that is a raw IP address, `@` (userinfo) before the host, punycode (`xn--`) host, and hosts that imitate a well-known brand (for example `paypa1.com` or `paypal.com.evil.io`). A string that is not a full URL returns `invalid`.
Adds `warnings` (still `safe`) for URL shorteners, many subdomains, non-standard ports and very long URLs.

This is a heuristic, not a guarantee: `safe` means no red flag was found in the string, not that the site is trustworthy.
