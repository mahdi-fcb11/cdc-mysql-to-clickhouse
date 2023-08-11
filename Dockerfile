FROM python3.9

RUN curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "mycnc1",
      "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "snapshot.mode": "schema_only",
            "database.hostname": "mysql",
            "database.port": "3306",
            "database.user": "root",
            "database.password": "mysqlpass",
            "database.server.id": "104",
            "database.include.list": "product",
            "table.incluse.list": "users",
            "topic.creation.default.partitions": 3,
            "topic.creation.default.replication.factor": 1,
            "topic.prefix": "cdc",
            "schema.history.internal.kafka.topic": "schema.change",
            "schema.history.internal.kafka.bootstrap.servers": "broker:29092",
            "schema.name.adjustment.mode": "avro",
            "include.schema.changes": "true",
            "drop.tombstones":"false",
            "tasks.max": "1",
            "transforms": "unwrap",
            "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
            "transforms.unwrap.drop.tombstones": "true",
            "transforms.unwrap.delete.handling.mode": "rewrite"
       }
    }'

 RUN curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "clicksink",
      "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "topics": "cdc.product.users",
            "table.name.format": "prd_users",
            "connection.url": "jdbc:clickhouse://clickhouse:8123/default",
            "connection.user": "root",
            "connection.password": "clickpass",
            "tasks.max":"1",
            "auto.create": "false",
            "auto.evolve": "false",
            "insert.mode": "insert",
            "pk.fields": "id",
            "delete.enabled":"false",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "io.confluent.connect.avro.AvroConverter",
            "value.converter.schemas.enable": "true",
            "value.converter.schema.registry.url": "http://schema-registry:8081",
            "transforms": "TimestampConverter",
            "transforms.TimestampConverter.type": "org.apache.kafka.connect.transforms.TimestampConverter$Value",
            "transforms.TimestampConverter.field": "updated_at",
            "transforms.TimestampConverter.format": "yyyy-MM-dd'T'HH:mm:ss'Z'",
            "transforms.TimestampConverter.target.type": "unix"
        }
    }
    '

RUN spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.4 spark.py