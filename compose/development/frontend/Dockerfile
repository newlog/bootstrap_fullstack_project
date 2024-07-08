FROM node:14
WORKDIR /app
COPY ./frontend/post_publisher/package.json ./frontend/post_publisher/package-lock.json ./
RUN npm install
COPY ./frontend/post_publisher .
RUN npm run build
RUN npm install -g serve
EXPOSE 3000