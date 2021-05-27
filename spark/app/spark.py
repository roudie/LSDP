from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.sql.functions import expr
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from prepare_data import getData

conf = SparkConf().setAppName('appName').setMaster('local')
#conf.set("spark.debug.maxToStringFields", 10000)
conf.set("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.0")
sc = SparkContext(conf=conf)
print(sc.version)
print(":S")

MONGODB_CONECTION_STR = "mongodb://userr:userr@localhost:27017/reddit.subreddit_v1?authSource=admin"

spark = SparkSession \
    .builder \
    .appName("myApp") \
    .config('spark.mongodb.input.uri', MONGODB_CONECTION_STR).getOrCreate()
    #.config('spark.mongodb.input.database', 'reddit') \
    #.config('spark.mongodb.input.collection', 'subreddit_v1') \


df = spark.read.format("mongo").option("uri", MONGODB_CONECTION_STR).load()
#df = spark.read.format("mongo").load()
df.printSchema()
df.createOrReplaceTempView("subreddit")


data = spark.sql('select text_emb, subreddit, nfsw from subreddit')
data.printSchema()

data = data.withColumnRenamed("text_emb", "features")

subreddit_data = data.select([expr('features[' +str(x)+ ']') for x in range(0, 300)] + [data.subreddit])

train_data, test_data = subreddit_data.randomSplit([.8, .2], seed=1000)

indexer = StringIndexer(inputCol="subreddit", outputCol="subred")
vec_assemb = VectorAssembler(inputCols=["features[{}]".format(i) for i in range(300)], outputCol='features')
lr = LogisticRegression(maxIter=10, regParam=0.3, elasticNetParam=0.8)

subreddit_tree = DecisionTreeClassifier(labelCol="subred")
subreddit_pipeline = Pipeline(stages = [indexer, vec_assemb, subreddit_tree])
subreddit_model = subreddit_pipeline.fit(train_data)

subreddit_pred_train =subreddit_model.transform(train_data)
subreddit_pred_test =subreddit_model.transform(test_data)

subred_evaluation = MulticlassClassificationEvaluator(
    labelCol="subred", predictionCol="prediction", metricName="f1")
f1_test = subred_evaluation.evaluate(subreddit_pred_test)
f1_train = subred_evaluation.evaluate(subreddit_pred_train)

print("test subreddit f1", f1_test)
print("train subreddit f1", f1_train)