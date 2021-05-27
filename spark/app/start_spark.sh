pyspark --packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.0 \
        --conf "spark.mongodb.output.uri=mongodb://userr:userr@database:27017/reddit.subreddit_v1" \
        < spark.py