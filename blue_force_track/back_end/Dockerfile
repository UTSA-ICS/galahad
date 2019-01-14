FROM node:11

COPY src /src
COPY galahad-config /galahad-config
RUN cd /src && npm install

EXPOSE 3000

CMD cd /src && node index.js
