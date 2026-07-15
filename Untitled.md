FACTS.md را به روز کن

Phase 1 تایید است

-------

CONSULTANT'S APPROVAL & COMMAND FOR PHASE 2:

Excellent work on Phase 1. The Draft PR was perfect. The human admin has successfully executed the manual cutover (export, merge, .env update on the VPS, Flowise restoration, and FACTS.md update). We are now officially authorizing you to proceed to Phase 2.

---------------------------------------------------------

YOUR IMMEDIATE TASK: EXECUTE PHASE 2 ONLY

---------------------------------------------------------

PHASE 2: Astro Backend - Cloudflare-Compatible GIS Session Cookie API (HMR-Astro repo)

CONTEXT:

HMR-Astro is deployed on Cloudflare Pages (Edge runtime/V8 isolates). Standard Node.js crypto modules (like `google-auth-library` or `jsonwebtoken`) will fail in this environment. We MUST use lightweight, Edge-compatible libraries like `jose` to verify the Google JWT and mint our own session cookie.

Instructions for Phase 2:

1. Access the `HMR-Astro` repository.

2. Add `jose` to `package.json` dependencies if not already present.

3. Create a new auth endpoint for login (e.g., `src/pages/api/auth/login.ts`).

4. This endpoint must strictly do the following:

a. Receive the raw Google credential (JWT) from the client's POST request (from the GIS login).

b. Verify the Google JWT using `jose` against Google's public JWKS (`[https://www.googleapis.com/oauth2/v3/certs](https://www.googleapis.com/oauth2/v3/certs)`). Validate that the `aud` matches our `GOOGLE_CLIENT_ID`.

c. Extract the `sub` (Google user ID), `email`, `name`, and `picture`.

d. Mint a new Custom Session JWT using `jose`, signed with a new environment variable `SESSION_SECRET`, containing the extracted user payload.

e. Set this custom JWT as an `HttpOnly`, `Secure`, `SameSite=Lax`, and `Path=/` cookie on the Astro response.

5. Ensure `SESSION_SECRET` and `GOOGLE_CLIENT_ID` are documented in `.env.example` with empty values.

6. Open a Draft PR in `HMR-Astro` containing these exact changes.

REQUIRED OUTPUT FROM YOU NOW (Phase 2 Execution Report):

Please generate a report formatted exactly like this:

[PHASE 2 REPORT]

- Astro Backend Changes: [Briefly explain the API endpoint logic and Cloudflare edge-compatibility]

- Security Status: [Confirm HttpOnly cookie attributes and JWT verification logic]

- PR Status: [Confirm the Draft PR creation in HMR-Astro]

- Next Steps Readiness: Ready for Consultant Approval for Phase 3 (Astro Middleware).