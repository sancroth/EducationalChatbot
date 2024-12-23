#!/bin/bash

export $(cat .env | xargs)

if [[ -z "$NGINX_SERVER" || -z "$RASA_SERVER" || -z "$AUTH_SERVER" ]]; then
  echo "Error: NGINX_SERVER or RASA_SERVER environment variable is not set."
  exit 1
fi

echo "Replacing placeholders"
find /usr/share/nginx/html -type f -name "*.html" -exec sed -i "s|__NGINX_SERVER__|$NGINX_SERVER|g" {} \;
find /usr/share/nginx/html -type f -name "*.html" -exec sed -i "s|__RASA_SERVER__|$RASA_SERVER|g" {} \;
find /usr/share/nginx/html -type f -name "*.html" -exec sed -i "s|__AUTH_SERVER__|$AUTH_SERVER|g" {} \;
find /usr/share/nginx/html -type f -name "*.js" -exec sed -i "s|__NGINX_SERVER__|$NGINX_SERVER|g" {} \;
find /usr/share/nginx/html -type f -name "*.js" -exec sed -i "s|__AUTH_SERVER__|$AUTH_SERVER|g" {} \;

# Start nginx
echo "Starting nginx..."
exec nginx -g "daemon off;"