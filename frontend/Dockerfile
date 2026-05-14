FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --ignore-scripts --omit=optional

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npx", "--yes", "serve@14.2.4", "-l", "3000", "dist"]
