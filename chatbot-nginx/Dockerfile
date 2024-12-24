FROM nginx:latest

COPY sites.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY public/ /usr/share/nginx/html

COPY entrypoint.sh /entrypoint.sh
COPY .htpasswd /etc/nginx/.htpasswd

RUN chmod +x /entrypoint.sh &&\
    mkdir /var/run/nginx &&\
    chown -R nginx:nginx /usr/share/nginx/html &&\
    chown nginx:nginx /etc/nginx/conf.d/default.conf /var/run/nginx/ /var/cache/nginx /var/cache/nginx
   
USER nginx

EXPOSE 8888

ENTRYPOINT ["/entrypoint.sh"]