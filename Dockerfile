FROM python

RUN curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "mysql-connector",
      "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "database.hostname": "localhost",
            "database.port": "3306",
            "database.user": "debezium",
            "database.password": "dbz",
            "database.server.id": "42",
            "database.server.name": "demo",
            "database.history.kafka.bootstrap.servers": "localhost:9092",
            "database.history.kafka.topic": "dbhistory.demo" ,
            "include.schema.changes": "true"
       }
    }'