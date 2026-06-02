FROM node:20-alpine

WORKDIR /app

COPY cdp-proxy.js ./cdp-proxy.js

EXPOSE 3456

CMD ["node", "cdp-proxy.js"]
