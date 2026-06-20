FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev --fetch-retries=5 --fetch-retry-maxtimeout=120000

COPY . .

ENV DATA_DIR=/app/data
ENV PORT=5858

EXPOSE 5858

CMD ["npm", "start"]
