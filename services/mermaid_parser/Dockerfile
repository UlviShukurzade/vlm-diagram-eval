# Pinned by digest for reproducibility: node:22.22.0-alpine (Node v22.22.0)
FROM node@sha256:e4bf2a82ad0a4037d28035ae71529873c069b13eb0455466ae0bc13363826e34

WORKDIR /app

# npm ci installs strictly from package-lock.json (mermaid 11.12.2, 240 pinned deps)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY index.cjs .

EXPOSE 8000
CMD ["npm", "start"]
