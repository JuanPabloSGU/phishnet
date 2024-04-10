FROM --platform=$BUILDPLATFORM node:18.19-alpine as build

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY package.json ./
COPY yarn.lock ./
RUN yarn install
COPY . ./
RUN yarn build

# production environment
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html/
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# Default port exposure
EXPOSE 80
RUN apk add bash
# Copy .env file and shell script to container
WORKDIR /usr/share/nginx/html/
# Start Nginx server
CMD ["/bin/bash", "-c", "nginx -g \"daemon off;\""]


