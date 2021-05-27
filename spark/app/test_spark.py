from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.sql.functions import expr
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

#conf = SparkConf().setAppName('appName').setMaster('local')
#conf.set("spark.debug.maxToStringFields", 10000)
#conf.set("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.11:2.3.2")
sc = SparkContext( )
print(sc.version)
print(":S")

spark = SparkSession \
    .builder \
    .master('local') \
    .appName('Spark_app') \
    .config('spark.mongodb.input.uri', 'mongodb://userr:userr@127.0.0.1:27017/reddit.subreddit_v1') \
    .config("spark.mongodb.output.uri", 'mongodb://userr:userr@127.0.0.1:27017/reddit.subreddit_v1') \
    .getOrCreate()
#spark.conf.set("spark.sql.debug.maxToStringFields", 305)

data_frame_reader = spark.read.format('com.mongodb.spark.sql.DefaultSource').load()
data_frame_reader.printSchema()
