import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, \
    FloatType
import pyspark
import os

spark = (SparkSession.builder.appName("test-spark").master("spark://192.168.1.147:7077").getOrCreate())
# spark = (SparkSession.builder.appName("test-spark_4").master("local[*]").getOrCreate())
# Spark session & context
spark.sparkContext.setLogLevel('WARN')

df = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "localhost:9092") \
  .option("subscribe", "cdc.product.users") \
  .option("startingOffsets", "earliest") \
  .load()

df.printSchema()

df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

df.writeStream.format("console").outputMode("append").start().awaitTermination()
