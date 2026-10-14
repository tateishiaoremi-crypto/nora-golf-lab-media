# nora_golf_lab — Meta Instagram API initial setup

Updated: 2026-10-14. Publishing code uses Meta Graph API **v26.0**.
The project uses **Instagram API with Facebook Login** (not Instagram Login), because
the Instagram professional account was previously connected to a Facebook Page.

## What is already done
- Public photos/videos are already hosted in this GitHub repository.
- A mixed photo/video carousel publisher exists at `scripts/publish_instagram_carousel.py`.
- A GitHub Action exists at `.github/workflows/instagram-carousel.yml`.
- A draft 2026-10-10 Menard Aoyama carousel was successfully checked (with **no publication**).
- A nonpublishing auth test is available at `.github/workflows/verify-instagram-connection.yml`.
- The destination Instagram account is **nora_golf_lab**: ID `17841428397719857`.

## The only unavoidable account-holder steps

1. **Log in to Meta for Developers once** at https://developers.facebook.com/apps/
   using the Meta/Facebook account that manages your linked Instagram professional account.
   First check if you already own an app. Otherwise select **Create App** and
   use `Nora Golf Lab` as the app name. Depending on the current dashboard,
   use the Instagram content-management use case or **Other / Business** app path.
   Select the **Instagram API with Facebook Login** integration, not Instagram Login
   (which uses a different API host/token/scope set).

2. **Grant publishing access to your own account.** In
   https://developers.facebook.com/tools/explorer/ select your newly created app,
   select Graph API **v26.0**, request a **User Access Token** with:
   - `pages_show_list`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`

   Authorize the Facebook Page connected to **nora_golf_lab**. If the app is in
   development mode, make sure the person authorizing has an app admin/developer
   role and has the required Page/Instagram permissions.

3. **Obtain a durable Page Access Token.** Do not save the short-lived token
   from Graph API Explorer directly into GitHub as the final production token.
   First extend/exchange your User Access Token to a long-lived User token,
   using Meta's official Graph API token flow. Using that token, call

   `GET /me/accounts?fields=id,name,access_token,instagram_business_account`

   and choose the Facebook Page whose `instagram_business_account.id` corresponds
   to `17841428397719857` (**nora_golf_lab**). Copy that Page's
   `access_token`, not the short-lived User token. Token lifetime depends on
   Meta account/app settings; it may expire or be revoked, so reauthorization
   should be monitored. Never send a token or App Secret into ChatGPT.

4. **Save the token securely once** at
   https://github.com/tateishiaoremi-crypto/nora-golf-lab-media/settings/secrets/actions
   → **New repository secret**:
   - Secret name: `INSTAGRAM_GRAPH_TOKEN`
   - Secret value: the authorized **Page Access Token**

   Do **not** store it in code, manifest, README, images or chat.

5. **Run a no-publication connection check.** Once the secret has been saved,
   from this chat the assistant can trigger
   `.github/workflows/verify-instagram-connection.yml` by updating
   `connection-check/verify.txt`; or in GitHub Actions manually select
   **Verify Meta Instagram connection → Run workflow**.
   The test confirms account ID and username, and creates a temporary
   image media container, but intentionally **never calls media_publish**.

6. **Review before first real publication.** The first 2026-10-10 carousel is
   currently a **draft**, not approved. Its source JPEGs are 1080×1350 (4:5);
   its swing video is 720×1280 (9:16). Confirm how that video is framed for a
   4:5 carousel; check audio sync, the full video's app/watermark cleanup, exact
   numbers, people, caption and order. Only after explicit approval switch the
   manifest's `status` to `approved`, which triggers the publishing Action.

## Automatic operation after the initial step
1. User supplies files and copy direction in ChatGPT.
2. Edited media is uploaded to this GitHub repository.
3. ChatGPT verifies media and sends a preview for explicit publication approval.
4. Approved manifest is committed; GitHub Action calls Meta's Graph API.
5. Successful publication records `instagram-published.json` with its media ID.

The account owner will only need to sign in again when permissions/tokens are
invalidated, expire or require renewal, or Meta requests an account check.
The user may need to authorize additional scope if we later add analytics,
Stories or other features; these are separate from the mixed carousel setup.

**Windsor.ai should remain connected until the API has successfully
published and verified the needed post types.**

## Reference
- https://www.postman.com/meta/instagram/folder/u4g5a2a/instagram-api-with-facebook-login
- https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- https://developers.facebook.com/docs/graph-api/guides/explorer/
- https://developers.facebook.com/docs/graph-api/changelog/versions/
