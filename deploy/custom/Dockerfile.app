FROM node:20-alpine AS builder
WORKDIR /src
RUN corepack enable

COPY web ./web

WORKDIR /src/web
RUN pnpm install --frozen-lockfile
RUN pnpm --filter panda-wiki-app build

FROM node:20-alpine AS runner
WORKDIR /app
RUN corepack enable
COPY --from=builder /src/web /app/web

WORKDIR /app/web/app
ENV NODE_ENV=production
EXPOSE 3010
CMD ["sh", "-c", "pnpm start -p 3010"]
