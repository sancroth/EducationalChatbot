docker stop chatbot-nginx && docker rm chatbot-nginx && docker run -d \
    -p 8888:8888 \
    -p 8889:8889 \
    -v ./public/:/usr/share/nginx/html \
    --name chatbot-nginx \
    chatbot-nginx:latest
