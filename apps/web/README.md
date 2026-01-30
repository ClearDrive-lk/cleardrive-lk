This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel (monorepo)

This app lives in `apps/web`. To avoid **404 NOT_FOUND** on Vercel:

1. In [Vercel Dashboard](https://vercel.com/dashboard) → your project → **Settings** → **General**
2. Under **Root Directory**, click **Edit**, set to **`apps/web`**, and Save
3. **Redeploy** the project (Deployments → ⋮ on latest → Redeploy)

If Root Directory is left at the repo root, Vercel won’t find the Next.js app and will return 404.

Then deploy via the [Vercel Platform](https://vercel.com/new) or [Next.js deployment docs](https://nextjs.org/docs/app/building-your-application/deploying).
