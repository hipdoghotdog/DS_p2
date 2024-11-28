# Use Nginx as the base image
FROM nginx:alpine

# Copy the static files (HTML, JS, CSS) to the default Nginx directory
#COPY static/index.html /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/

# Expose port 80 for Nginx
EXPOSE 80

# Default command to run Nginx
CMD ["nginx", "-g", "daemon off;"]