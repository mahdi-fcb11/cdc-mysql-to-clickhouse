# cdc-mysql-to-clickhouse

[![Python 3.9](https://img.shields.io/badge/Python-3.9-green.svg)](https://shields.io/)

This is a practice project to understand how to configure a mysql and clickhouse database, and use kafka connect with debezium and jdbc to capture data changes in mysql and sink the data into clickhouse database.

## How it works

This project starts with creating mysql and clickhouse databases. Next we generate fake data in our mysql database in users table.
Then kafka is used to start a stream of data movement from mysql into clickhouse. 
Finally, data in clickhouse will be deduplicated.

### Databases

MySQL database represents our OLTP database, and is the primary base of our data. A generator code is used to insert random data in this database.
This database only has one table which is called users and is in product schema. Data model for users table is later discussed.

Users table can be created with following query.

```mysql
-- product.users definition

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `birthdate` date DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

Clickhouse represents our OLAP database. Users table in MySQL is transferred into prd_user in Clickhouse. 
prd_users uses the ReplacingMergeTree engine in clickhouse that has background process to remove duplicates with the same sorting key. 
The problem with this deduplication is that it occurs during merge in an unknown time.
Therefore, optimizing tables or handling duplicates in queries is a must for clickhouse.

prd_users in clickhouse is created using the following query.

```clickhouse
CREATE TABLE default.prd_users (
    id Int64, 
    name String, 
    birthdate Nullable(Int32), 
    email Nullable(String), 
    address Nullable(String), 
    created_at DateTime64(3, 'Asia/Tehran'), 
    updated_at Nullable(DateTime64(3, 'Asia/Tehran')), 
    __deleted String
) ENGINE = ReplacingMergeTree PARTITION BY toYYYYMM(created_at) ORDER BY id SETTINGS index_granularity = 8192;
```

The docker-compose file in Database folder is a way for configuring MySQL and Clickhouse databases.

### Ingestion

We want to move our data from MySQL to Clickhouse. In order to do so, two steps are followed. 

#### 1. MySQL Engine

In the first step we use MySQL engine in Clickhouse to create table called product.users. The query is as follows.

```clickhouse
CREATE TABLE product.users (
    `id` Int64, 
    `name` String, 
    `birthdate` Nullable(Int32), 
    `email` Nullable(String), 
    `address` Nullable(String), 
    `created_at` DateTime64(3, 'Asia/Tehran'), 
    `updated_at` Nullable(DateTime64(3, 'Asia/Tehran')),
    `__deleted` String
) ENGINE = MySQL('mysql:3306', 'product', 'users', 'root', 'pass')
```

This table does not load the data into Clickhouse disk. So we have to insert data from this table to our prd_users table.
So we can have our past data from before ingestion in a fast way. 

```clickhouse
INSERT INTO default.prd_users 
SELECT  *, 'false' as __deleted FROM product.users WHERE id < ["id from which we started kafka connect"]
```

#### 2. Kafka Streaming

In the second step we have to start a stream process using kafka to insert every incoming data into Clickhouse. 
For this purpose we use kafka connect. Kafka and Kafka connect configurations can be found in docker-compose in Ingestion folder.
Besides, we use schema registry to validate our schema in confluent platform. The integration between kafka connect and schema registry can also be found in Ingestion docker-compose.
We also use [provectus kafka-ui](https://github.com/provectus/kafka-ui) for communicating with kafka.

We use two connectors to build a stream process between our databases. First connector is a Debezium Source Connector that gets everything from MySQL database.
Plugins for this connector can be found in [connect_plugins](https://github.com/mahsa-fathi/cdc-mysql-to-clickhouse/tree/master/volumes/connect_plugins). Source connector can be created using the following POST method.

```shell
curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "mycnc",
      "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "snapshot.mode": "schema_only",
            "database.hostname": "localhost",
            "database.port": "3306",
            "database.user": "root",
            "database.password": "pass",
            "database.server.id": "100",
            "database.include.list": "product",
            "table.incluse.list": "users",
            "topic.creation.default.partitions": 3,
            "topic.creation.default.replication.factor": 1,
            "topic.prefix": "prd",
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
```
- schema_only for snapshot.mode is used. This mode capture data changes from MySQL binlog, But gets every change in schema and tables from the beginning.
- transforms.unwrap.type is set to io.debezium.transforms.ExtractNewRecordState. This is a type of unwrapping incoming data from MySQL. 
    ```json
    {
      "[column]": {
        "[type]": "[]"
      }
    }
    ```
- transforms.unwrap.delete.handling.mode is set to rewrite. This will add a column by the name of __deleted is a string either true or false.
- transforms.unwrap.drop.tombstones is set to true. This will avoid creating null messages in kafka after a delete query in MySQL. 

This connector will capture every change from the starting time of connector and send it to the topic of prd.product.users.
Now we need another connector to sink the captured data in prd_users. The sink connector can be created using the following POST method.
This connector uses a JDBC sink connector.

```shell
curl -i -X POST -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/ \
    -d '{
      "name": "clicksink",
      "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "topics": "cdc.product.users",
            "table.name.format": "prd_users",
            "connection.url": "jdbc:clickhouse://localhost:8123/default",
            "connection.user": "root",
            "connection.password": "pass",
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
    }'
```

- This connector uses a timestamp transformer. This is because incoming timestamp data from MySQL is in a format unrecognizable by clickhouse. It will transform timestamp with the format of "yyyy-MM-dd'T'HH:mm:ss'Z'" into unix.

### Management

Clickhouse will not handle delete and update in a synchronous manner. Using ReplacingMergeTree engine or other similar engines, will not handle delete and update queries synchronously. 
The problem is that we can never now when this engine will merge the tables. Therefore, we will always have duplicates in our table.
This problem can be handled in query. Using FINAL keyword at the end of every query will assure a deduplicated result, but the problem with using raw FINAL is that it takes a lot of time to be executed.
Actually, there are many ways to handle deduplication in Clickhouse. Clickhouse documentation gives us a complete guide on [deduplication strategies](https://clickhouse.com/docs/en/guides/developer/deduplication).
Alternatively, [Altinity blog](https://altinity.com/blog/2020/4/14/handling-real-time-updates-in-clickhouse/) gives us a good guidance on deduplication. 

Our method for handling deduplication can be used for small and medium size tables. In this method we use OPTIMIZE queries on users table based on our partition. 
Earlier, we created the prd_users table with ReplacingMergeTree and partitioned this table by created_at monthly. We know that created_at will never be updated for any user, 
and we can group our users using this column. This will make our optimizing much faster and much more efficient. 
So we can run a code infinitely to optimize our table by partition using the following query.

```clickhouse
OPTIMIZE TABLE default.prd_users PARTITION ID 'partition_id' FINAL
```

### Spark (in progress)

This folder contains a docker-compose with spark-master and spark-worker. The python code in this folder creates a connection between spark and kafka in order to get data from prd.product.users.
The code can be run using the following command.

```shell
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.4 spark.py
```

Further manipulation of data using spark will be added.

## Project layout

The project contains 4 main directories. 
CDC contains docker-compose file for kafka, kafka connect, schema registry, and kafka-ui. 
Database directory contains a python code to generate random data for our mysql database. 
This directory also contains a docker-compose file for mysql and clickhouse.
Spark directory contains a docker-compose file for spark-master and spark-worker. This directory also contains a code that connects spark to kafka.
Utils contains python codes that can be used in other codes.

```text
├── Database
│   ├── generator.py          <- code for generating random data for mysql
│   └── docker-compose.yaml   <- mysql and clickhouse
├── Ingestion
│   └── docker-compose.yaml   <- kafka, kafka connect, kafka-ui, schema-registry
├── Management
│   └── main.py               <- Deduplicating data in clickhouse
├── Spark
│   ├── spark.py              <- connecting spark to kafka
│   └── docker-compose.yaml   <- kafka-master and kafka-worker
├── Utils
│   ├── db_connection.py      <- class for connecting to mysql or clickhouse
│   └── logger.py             <- function for showing logs
└── volumes 
    ├── connect_plugins       <- plugins for kafka connect
    └── update_run.sh         <- function for using kraft
```

## Data Model

In mysql database (product) we have only one table called users. Users table data model is as follows.

| Name       | Type         | Optional |
|------------|--------------|----------|
| id         | Bigint       | False    |
| name       | Varchar(100) | False    |
| birthdate  | Date         | True     |
| email      | Varchar(100) | True     |
| address    | Varchar(100) | True     |
| created_at | datetime     | False    |
| updated_at | timestamp    | False    |

## Author

[Mahsa Fathi](https://www.linkedin.com/in/mahsa-fathi-68216112b/), Data Engineer
