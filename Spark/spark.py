from pyspark.sql import SparkSession

spark = (SparkSession.builder.appName("test-spark").master("spark://localhost:7077").getOrCreate())

spark.sparkContext.setLogLevel('WARN')

# connection to kafka stream
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
