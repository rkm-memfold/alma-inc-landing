# PostHog setup

The production homepage contains the PostHog JavaScript snippet and event
tracking. The project token and US Cloud ingestion host are configured.

## Browser storage

The site uses `persistence: "memory"`, so PostHog does not store analytics data
in cookies, local storage, or session storage. Do not enable cookieless server
hash mode for this site because it strips IP data before PostHog can perform
GeoIP enrichment.

## Captured data

- Pageviews and pageleaves on `alma.inc`
- Clicks on links and buttons
- `waitlist_form_submitted` without the submitted email address
- `social_x_clicked`
- `social_instagram_clicked`
- `social_linkedin_clicked`

The email input is excluded from autocapture and masked in session replay.
Replay starts for every production session, overriding sampling and trigger
rules. Dead-click capture, input-change autocapture, and person profile creation
for anonymous visitors are disabled. Analytics also stays disabled on localhost
and other non-production hosts.

Country enrichment requires IP data capture in PostHog. Under **Settings >
Project > Privacy**, keep **Discard client IP data** disabled. PostHog uses the
address for GeoIP enrichment; geography is only available for new events after
cookieless server hash mode is removed.

## Verification

After the token and host are configured, deploy the page and open PostHog's
Live events view. Visit `https://alma.inc/`, submit a test email, and open one
social link. Confirm the pageview and both custom event names appear.

Official references:

- https://posthog.com/docs/libraries/js
- https://posthog.com/docs/libraries/js/config
- https://posthog.com/docs/product-analytics/autocapture
- https://posthog.com/docs/privacy/data-collection
- https://posthog.com/docs/session-replay/privacy
- https://posthog.com/docs/web-analytics/installation/html-snippet
