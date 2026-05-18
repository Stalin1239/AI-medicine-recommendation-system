FROM nginx:alpine

# Remove default nginx configurations
RUN rm /etc/nginx/conf.d/default.conf

# Copy static assets to nginx html serving directory
COPY static /usr/share/nginx/html/static

# Copy modern routing Nginx reverse-proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for front-facing client request routing
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
