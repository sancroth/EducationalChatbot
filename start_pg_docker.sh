docker stop postgres-chatbot && docker rm postgres-chatbot
docker stop pgadmin-chatbot && docker rm pgadmin-chatbot

docker run -d \
	--name postgres-chatbot \
        -p 5432:5432 \
	-e POSTGRES_PASSWORD=mysecretpassword \
	-e PGDATA=/var/lib/postgresql/data/pgdata \
	-v $(pwd)/pg_data:/var/lib/postgresql/data \
	postgres

docker run -p 8081:80    \
    --name pgadmin-chatbot \
    -e 'PGADMIN_DEFAULT_EMAIL=sancroth@gmail.com' \
    -e 'PGADMIN_DEFAULT_PASSWORD=mysupersecret' \
    -d dpage/pgadmin4
