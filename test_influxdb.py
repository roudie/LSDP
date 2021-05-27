import pymongo
import json

if __name__ == '__main__':
    client = pymongo.MongoClient("mongodb://userr:userr@localhost:27017/")
    d = dict((db, [collection for collection in client[db].collection_names()])
             for db in client.database_names())
    print(json.dumps(d))
    with client:
        collection = client.reddit
        subreddits = collection.subreddit_v1.find()

        d = dict()
        itera = 1
        for sub in subreddits:
            #print(sub['subreddit'], sub['title'])
            if sub['subreddit'] in d.keys():
                d[sub['subreddit']] = d[sub['subreddit']]+1
            else:
                d[sub['subreddit']] = 1

            #if sub['subreddit'] == 'funny':
            #    print(itera, sub['text'])
            #    itera+=1

        print(d)