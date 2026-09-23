FROM postgres:17-alpine
COPY init.sh /docker-entrypoint-initdb.d/init.sh
RUN chmod 0644 /docker-entrypoint-initdb.d/init.sh
