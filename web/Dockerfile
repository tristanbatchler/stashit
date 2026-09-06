FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS openapi

WORKDIR /api

COPY api/pyproject.toml api/uv.lock api/README.md ./
COPY api/src ./src

RUN uv sync --frozen --no-dev

RUN --mount=type=secret,id=settings,target=/.env \
    uv run python -c "from api.main import app; import json; open('/openapi.json', 'w').write(json.dumps(app.openapi()))" \
    && echo "===== GENERATED OPENAPI =====" \
    && cat /openapi.json \
    && echo "===== END GENERATED OPENAPI ====="


FROM node:24-bookworm-slim AS build

WORKDIR /app

COPY web/package.json web/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY web/ ./

COPY --from=openapi /openapi.json ./openapi.json

RUN npm run gen-types

RUN npm run build


FROM node:24-bookworm-slim AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules

EXPOSE 3000

CMD ["node", "build"]
