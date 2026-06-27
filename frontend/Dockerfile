FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server (Phase 0/1). Production build uses `npm run build` + a static host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
