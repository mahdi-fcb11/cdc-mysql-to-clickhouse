# cdc-mysql-to-clickhouse

[![Python 3.9](https://img.shields.io/badge/Python-3.9-green.svg)](https://shields.io/)

This is a practice project to understand how to configure a mysql and clickhouse database, and use kafka connect with debezium and jdbc to capture data changes in mysql and sink the data into clickhouse database.

## How it works



## Project layout

The project contains 4 main directories. 
CDC contains docker-compose file for kafka, kafka connect, schema registry, and kafka-ui. 
Database directory contains a python code to generate random data for our mysql database. 
This directory also contains a docker-compose file for mysql and clickhouse.
Spark directory contains a docker-compose file for spark-master and spark-worker. This directory also contains a code that connects spark to kafka.
Utils contains python codes that can be used in other codes.

```text
├── CDC
│   └── docker-compose.yaml   <- kafka, kafka connect, kafka-ui, schema-registry
├── Database
│   ├── generator.py          <- code for generating random data for mysql
│   └── docker-compose.yaml   <- mysql and clickhouse
├── Spark
│   ├── spark.py              <- connecting spark to kafka
│   └── docker-compose.yaml   <- kafka-master and kafka-worker
├── Utils
│   ├── db_connection.py      <- class for connecting to mysql db
│   └── logger.py             <- function for showing logs
└── volumes                   <- mounted volumes for docker services
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


### Creating users table in mysql

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

### Clickhouse tables

After connecting mysql to kafka, the main kafka connect topic contains queries that were used to create the tables in mysql database.
We use a query translator to translate every query of mysql into clickhouse queries.
We call users table in clickhouse prd_users and it can be created using the following command.

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

#### MySQL engine table

In order to move past data from users to prd_users, we create a table in clickhouse with mysql engine.
This table connects to users table in our mysql database, but it does not save the data on its disk.

```clickhouse
CREATE TABLE product.users (
    `id` Int64, 
    `name` String, 
    `birthdate` Nullable(Int32), 
    `email` Nullable(String), 
    `address` Nullable(String), 
    `created_at` DateTime64(3, 'Asia/Tehran'), 
    `updated_at` Nullable(DateTime64(3, 'Asia/Tehran'))
) ENGINE = MySQL('mysql:3306', 'product', 'users', 'root', '[HIDDEN]')
```

Then the following query will be used to save the past data from mysql engine table into prd_users. 

```clickhouse
INSERT INTO default.prd_users 
SELECT  *, 'false' FROM dw.users WHERE id < ["id from which we started kafka connect"]
```

## Deduplicate

running infinitely

```clickhouse
optimize table prd_users partition [part_name] final deduplicate by id
```
