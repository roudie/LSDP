from pyspark.sql.functions import expr


def getData(spark_session, data_x_name, data_y_name):
    data = spark_session.sql('select {}, {} from subreddit'.format(data_x_name, data_y_name))
    if data_x_name=="text_emb":
        data = data.select([expr('features[' + str(x) + ']') for x in range(0, 300)] + [data.subreddit])
    return data