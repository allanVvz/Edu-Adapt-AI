FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

# NODE_TLS_REJECT_UNAUTHORIZED=0 apenas para o npm install (rede corporativa/proxy)
RUN NODE_TLS_REJECT_UNAUTHORIZED=0 npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
