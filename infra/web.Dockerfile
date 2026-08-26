FROM oven/bun:1.3

WORKDIR /app

COPY apps/web/package.json apps/web/bun.lock ./
RUN bun install --frozen-lockfile

COPY apps/web ./

EXPOSE 5173
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]

