# 猎鹰 Falcon AI · 前端镜像（Next.js 14 standalone 多阶段构建）

# ---- Stage 1: deps（缓存 node_modules） ----
FROM node:20-alpine AS deps
WORKDIR /app

# Alpine 下部分原生依赖需要 libc6-compat
# 配置 Alpine 国内镜像源（阿里云）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk add --no-cache libc6-compat

# 配置 npm 国内镜像源（阿里云）
RUN npm config set registry https://registry.npmmirror.com

COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund


# ---- Stage 2: builder ----
FROM node:20-alpine AS builder
WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build


# ---- Stage 3: runner（只保留 standalone 最小产物） ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# public 静态资源
COPY --from=builder /app/public ./public
# standalone 自带最小 node_modules + server.js
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# 构建时产出的 static 资源
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000 >/dev/null 2>&1 || exit 1

CMD ["node", "server.js"]
