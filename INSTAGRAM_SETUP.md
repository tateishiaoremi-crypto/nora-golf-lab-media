# nora_golf_lab — Instagram Login API setup

## Confirmed current state
- Meta app **Nora Golf Lab** created in Meta Developers.
- The **Instagramでメッセージとコンテンツを管理** use case is installed.
- Instagram Login selected; `instagram_business_basic` and `instagram_business_content_publish` have been added and show “テスト準備完了”.
- GitHub publishing and verification scripts now use **`graph.instagram.com/v26.0`** and authenticate the actual Instagram Login user by `GET /me?fields=id,username`.
- Mixed media draft is at `posts/2026-10-10-menard/instagram-carousel.json`. It remains **draft**, and no post has been sent from GitHub.
- Meta access token has **not** yet been registered with GitHub.

## Next UI steps (account-holder action)

1. In Meta Developers, open **Nora Golf Lab → ユースケース → InstagramログインによるAPI設定**.
2. Section **2. アクセストークンを生成する** → **アカウントを追加**.
3. Log in to the Instagram professional account **nora_golf_lab** and approve the connection. If Meta asks for an Instagram tester role, add that account under the app's Roles and accept the invitation on Instagram before continuing.
4. Generate an **Instagram user access token** for nora_golf_lab using this setup page. This is an **Instagram Login token**, NOT a Facebook Page token. Don't paste it into ChatGPT or public GitHub code.
5. For long-term operation, exchange the short-lived Instagram token for a **long-lived Instagram user token** using Meta's Instagram Login token endpoint and your **Instagram App Secret**. The short-lived token alone is not appropriate for unattended publishing; long-lived tokens typically last about 60 days and require renewal before expiry.
6. Open the repository's [GitHub Actions secrets](https://github.com/tateishiaoremi-crypto/nora-golf-lab-media/settings/secrets/actions), add **New repository secret**:
   - **Name**: `INSTAGRAM_GRAPH_TOKEN`
   - **Value**: the long-lived Instagram **user** token
7. Once it has been securely stored, run **Verify Meta Instagram connection** in GitHub Actions or tell ChatGPT `トークンを登録しました` to initiate the no-publication connection test.

Do not send Instagram passwords, access tokens, App Secrets or full authentication callback URLs to ChatGPT. If taking screenshots, mask those fields.

## Approved posting workflow
- Draft manifest changes run format/safety preflight only.
- Only explicitly approved posts are published by `.github/workflows/instagram-carousel.yml`.
- 2026-10-10 draft: images 1080x1350 (4:5); video 720x1280 (9:16) — review video framing before publication. Confirm exact score, caption, audio sync, watermark removal throughout the video and all Instagram UI safe zones.
- A successful post writes an `instagram-published.json` receipt to reduce duplicate posting risks.
- Keep Windsor.ai connected until the new Meta API publishing path has successfully published the formats you need.
- The current code only handles mixed carousels; image/reel/stories flows must be migrated and tested separately.

## References
- [Meta Instagram API official Postman documentation](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api)
- [Meta Instagram Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login)
- [Meta Instagram Login content publishing](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing)
