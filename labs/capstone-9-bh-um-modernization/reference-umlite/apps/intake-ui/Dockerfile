# Multi-stage build for the Angular intake UI (Phase 6 / Track 6, M30).
# Stage 1 builds the static bundle; stage 2 serves it with nginx → tiny image, no Node at runtime.

# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build           # ng build → dist/intake-ui/browser

# --- runtime stage ---
FROM nginx:1.27-alpine AS runtime
# Angular 18 (application builder) emits to dist/<project>/browser
COPY --from=build /app/dist/intake-ui/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
