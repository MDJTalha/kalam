FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci --ignore-scripts --include=dev --fetch-retries=5 --fetch-retry-factor=2 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000

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

# Package a host/CI-prebuilt Next standalone artifact when the Docker builder
# cannot run the full webpack build within its memory budget.
FROM deps AS prebuilt-runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ARG PREBUILT_DIST_DIR=.next
ENV NEXT_DIST_DIR=${PREBUILT_DIST_DIR}
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY apps/web/public ./apps/web/public
COPY apps/web/${PREBUILT_DIST_DIR}/standalone ./
COPY apps/web/${PREBUILT_DIST_DIR}/static ./apps/web/${PREBUILT_DIST_DIR}/static
USER nextjs
WORKDIR /app/apps/web
EXPOSE 3000
CMD ["node", "server.js"]

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
