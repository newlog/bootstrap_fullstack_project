# Stage 1: Build the React application
FROM node:14 as build

WORKDIR /app

COPY ./frontend/post_publisher/package.json frontend/post_publisher/package-lock.json ./

RUN npm install

COPY ./frontend/post_publisher .

RUN npm run build

# Stage 2: Serve the React application with Nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

COPY compose/production/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
