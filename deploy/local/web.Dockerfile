FROM node:22-bookworm-slim AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY . .
RUN VITE_APP_BASE=/chuxin-vue/ npm run build

FROM nginx:1.28-alpine
COPY --from=build /src/dist/ /usr/share/nginx/html/chuxin-vue/
