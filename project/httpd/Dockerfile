FROM node:alpine

RUN npm install -g http-server
WORKDIR /site
EXPOSE  8080

CMD ["http-server", "--cors", "-p8080", "/site"]
