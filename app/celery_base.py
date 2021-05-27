import re
import os.path
from celery import Celery, chain
from gensim.models import KeyedVectors
import celery
from docker_logs import get_logger
import requests
import time
import json
from reddit_post import RedditPost
from dataclasses_serialization.bson import BSONSerializer
from datetime import datetime
import math
import influxdb
import pymongo
import numpy as np

influxDB_client = influxdb.client.InfluxDBClient(host='influxdb', port=8086, username='root', password='root')
influxDB_client.create_database('reddit_new')
influxDB_client.switch_database('reddit_new')

myclient = pymongo.MongoClient("mongodb://userr:userr@database:27017/")
db = myclient['reddit']
col = db["subreddit_v1"]


TIME_PERIOD = 5
logging = get_logger("task")
logging.propagate = False


app = Celery()
app.conf.update({'task_routes':
                       {
                           'embedding': {'queue': 'emb_queue'},
                           'getData': {'queue': 'scraping_queues'},
                           'save_to_db': {'queue': 'db_queue'},
                           'getDataSpliter': {'queue': 'tasks_splitter_queue'}
                       }})


@app.task(bind=True)
def save_to_db(self, data):
    if len(data) > 0:
        col.insert_many(data)
    logging.info('{} posts inserted to db'.format(len(data)))


filename = '../GoogleNews-vectors-negative300-SLIM.bin'
x = time.time()
#model = None
model = KeyedVectors.load_word2vec_format(filename, binary=True)
logging.info('loading word2vec '+ str(time.time()-x)+'s')

@app.task(bind=True, name='example')
def example(self):
    logging.info("example")


@app.task(bind=True, name='task')  
def task(self, param):  
    logging.info(f"Celery task executed with param: {param}")
    return f"Result of task for param {param}"


def to_dataclass(data):
    try:
        reddit = RedditPost(title=data['title'], url=data['url'], author=data['author'],
                        subreddit=data['subreddit'], text=data['selftext'],
                        num_votes=data['score'], nfsw=data['over_18'],
                        num_comm=data['num_comments'])
    except:
        return BSONSerializer.serialize(None)
    return BSONSerializer.serialize(reddit)


def publish_metrics(list_of_reddit_post, duration):
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    json_body = [
        {
            "measurement": "scrapping_worker",
            "tags": {
                "WorkerId": celery._state.current_task
            },
            "time": current_time,
            "fields": {
                "amount": len(list_of_reddit_post),
                "duration": duration
            }
        }
    ]

    for post in list_of_reddit_post:
        #print(type(post))
        if post is not None:
            if post['text'] is not None:
                length = len(post['text'])
            else:
                length = 0
            title_len = len(post['title'])
            tag = post['subreddit']
            post_metrics=dict()
            post_metrics['measurement'] = "reddit_post"
            post_metrics['tags'] = {"subreddit":tag}
            post_metrics['time'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            post_metrics['fields'] = {"post_length": length, "title_length": title_len}
            json_body.append(post_metrics)
    influxDB_client.write_points(json_body)


@app.task(bind=True)
def getData(self, after=None, before=None, subreddit=None, metrics=True):
    start_time = time.time()
    url_tmp = 'https://api.pushshift.io/reddit/search/submission/?sort_type=created_utc&size=100&'
    if after:
        url_tmp = url_tmp + 'after=' + str(after) + '&'
    if before:
        url_tmp = url_tmp + 'before=' + str(before) + '&'
    if subreddit:
        url_tmp = url_tmp + 'subreddit=' + str(subreddit)
    logging.info(url_tmp)
    r = requests.get(url_tmp)
    data = '{}'
    text = r.text
    try:
        data = json.loads(text)
    except:
        logging.warning("Error: " + url_tmp)
        logging.warning(text)
        return []
    logging.info('Downloaded submissions: ' + str(len(data['data'])))
    subData = [to_dataclass(d) for d in data['data']]
    duration = time.time() - start_time
    if metrics:
        publish_metrics(subData, duration)
    return subData


@app.task(bind=True, name='embedding')
def embedding(self, subData):
    data = [BSONSerializer.deserialize(RedditPost, post) for post in subData if post is not None]
    orginal_size = len(data)
    data = [post for post in data if (post.text != '[removed]' and post.text != '[deleted]')]

    for i, post in enumerate(data):
        vectors = [model[word].tolist() for word in re.sub('[^A-Za-z0-9 ]+', '', post.title + "\n" +post.text).split()
                   if word in model.vocab]
        #logging.info(vectors)
        if len(vectors)==0:
            vectors = None
            #logging.info(data[i])
        else:
            vectors = list(np.mean(vectors, axis=0))
            #print(type(vectors))
        data[i].text_emb = vectors

    data = [post for post in data if post.text_emb is not None]
    logging.info("embedded {} posts. Deleted {} post (deleted/removed)".format(len(data), orginal_size-len(data)))
    return BSONSerializer.serialize(data)


@app.task(bind=True, name='getDataSpliter')
def getDataSpliter(self, subreddit=None, time_period=TIME_PERIOD):
    #if not os.path.exists("tmp.txt"):
    #    print("create file")
    #    file = open("tmp.txt", "w+")
    #    file.write(str(math.ceil(datetime.utcnow().timestamp()) - 3600))
    #    file.close()
    #with open("tmp.txt", "r") as file:
    #    before = float(file.readline())
    #    after = before-time_period*4
    #    # 15 min
    #    print(before)
    #with open("tmp.txt", "w+") as file:
    #    file.write(str(after))

    #start = int(after)
    #before = int(before)
    before = math.ceil(datetime.utcnow().timestamp()) - 3600
    after = before - time_period
    start = after

    while start <= before:
        if start + time_period < before:
            task = chain(
                getData.s(after=start, before=start + time_period, subreddit=subreddit).set(queue='scraping_queues'),
                embedding.s().set(queue='emb_queue'),
                save_to_db.s().set(queue='db_queue')
            ).apply_async()
        else:
            task = chain(
                getData.s(after=start, before=start + time_period, subreddit=subreddit),
                embedding.s().set(queue='emb_queue'),
                save_to_db.s().set(queue='db_queue')
            ).apply_async()
        start = start + time_period




app.conf.beat_schedule = {
    "get_all": {
        "task": "getDataSpliter",
        "schedule": TIME_PERIOD
    }
}