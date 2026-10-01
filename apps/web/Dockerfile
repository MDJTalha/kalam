FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci --ignore-scripts --include=dev

FROM node:24-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY apps/web/tsconfig.json apps/web/tsconfig.json
COPY apps/web/next.config.ts apps/web/next.config.ts
COPY apps/web/eslint.config.mjs apps/web/eslint.config.mjs
COPY apps/web/public apps/web/public
COPY apps/web/src apps/web/src
WORKDIR /app/apps/web
ARG API_ORIGIN=http://localhost:8000
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ENV API_ORIGIN=$API_ORIGIN
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run typecheck
RUN npm run lint
RUN npm run build -- --webpack

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Bind to all container interfaces so the local healthcheck and gateway can
# reach the standalone server instead of Docker's generated container hostname.
ENV HOSTNAME=0.0.0.0
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
RUN chown -R nextjs:nodejs /app
USER nextjs
WORKDIR /app/apps/web
EXPOSE 3000
CMD ["node", "server.js"]
