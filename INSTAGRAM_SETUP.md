# Instagram direct publishing setup — nora_golf_lab

## Current status (2026-10-14)
- GitHub Actions draft preflight: **passed**, including video/audio-track inspection.
- Instagram account connected to Windsor.ai: `nora_golf_lab` (Instagram user ID `17841428397719857`).
- Windsor.ai's available carousel action supports **images only**, not mixed photos/videos.
- Mixed media is handled here by the Instagram Graph API directly.
- **No Meta access token has been added to GitHub Actions yet. No mixed carousel has been published.**

## One-time human permission step (never send passwords or access tokens in chat)
1. Sign in to [Meta for Developers](https://developers.facebook.com/apps/) and use/create a Meta app with Instagram content publishing. The Instagram Professional account must be connected to a Facebook Page if using **Instagram API with Facebook Login**. A Facebook Page named "Nora Golf Lab" has previously been discussed; check that it is the linked Page.
2. Grant the app publishing access for your Instagram account. For the Facebook Login route, obtain permissions `pages_show_list`, `pages_read_engagement`, `instagram_basic`, and `instagram_content_publish`. Use an authorized **Page Access Token** associated with the connected Instagram professional account. To inspect linked Page tokens/accounts, the official route is `/me/accounts?fields=name,access_token,instagram_business_account`. Where eligible, use the appropriate long-lived credential; expiration/revocation can still require renewal.
3. Sign in to [this repository's GitHub Actions secrets settings](https://github.com/tateishiaoremi-crypto/nora-golf-lab-media/settings/secrets/actions), choose **New repository secret**, and add exactly:
   - Name: `INSTAGRAM_GRAPH_TOKEN`
   - Value: the authorized Page Access Token from the Meta setup.
   Never add it to a source file, README, manifest, or chat.
4. Once saved, update `posts/.../instagram-carousel.json` to `"status": "approved"` **only after the user explicitly approves the final media, order and caption**. The commit triggers the GitHub Action and publishes. No new login per post while the credential remains valid.

**Important:** The user cannot delegate granting Meta account access to ChatGPT: initial authorization requires the account owner's action. The rest of the workflow can be managed through GitHub and this chat.

## Workflow
- Script: `scripts/publish_instagram_carousel.py`
- Action: `.github/workflows/instagram-carousel.yml`
- Media: public GitHub-hosted images and videos; every URL is pinned to its source commit.
- An edited manifest in **draft** state runs preflight only.
- An **approved** manifest checks the Meta token belongs to `nora_golf_lab`, creates and waits for image/video containers, creates the mixed carousel and publishes.
- Success records `instagram-published.json` to prevent accidental duplicate posting.
- Failed actions should be inspected before retrying. If a publish succeeded but saving the receipt failed, inspect Instagram before any retry to avoid duplicates.

## Non-negotiable editorial checks BEFORE switching to approved
- Verify exact score, captions, people and desired slide order.
- Videos must have original audio correctly synchronized with the visual impact.
- Ensure SmoothSwing/application watermarks are removed from the **entire video** and covers.
- Check 4:5 carousel presentation, video frame cropping, text safe zones and visual quality.
- Use a dedicated non-black cover / first slide. Carousel videos do not necessarily use Reel cover_url behavior.
- Keep captions and any #bkndr usage consistent with nora_golf_lab policy.

## API references (official Meta)
- [Meta Instagram API collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
- [Meta for Developers](https://developers.facebook.com/documentation/instagram-platform/content-publishing/)
