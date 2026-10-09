# Worldsmith: one container serves the page at / and the API under /api/* (same origin, no CORS).
#   docker build -t worldsmith .
#   docker run -p 8765:8765 -e GEMINI_API_KEY=... worldsmith
# The key is only ever an environment variable at run time; it is never copied into the image.

# 1) three.js and CodeMirror from the lockfile (node is only needed here)
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# 2) inline them into the page: dist/page.html and dist/test.html
FROM python:3.11-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN python build.py

# 3) runtime: Python standard library only, no pip install
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8765 \
    LLM_PROVIDER=gemini \
    RATE_LIMIT_PER_MIN=10
WORKDIR /app
COPY server/ ./server/
COPY shared/ ./shared/
COPY content/ ./content/
COPY --from=build /app/dist ./dist
RUN useradd --system --uid 10001 app && mkdir -p server/logs && chown app server/logs
USER app
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT','8765'), timeout=4)"
CMD ["python", "server/app.py"]
