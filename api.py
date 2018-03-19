import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import pymongo
from pymongo import MongoClient
import os
from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from flask import send_from_directory
from bson.regex import Regex
from bson import BSON
from bson import json_util
import subprocess
app = Flask(__name__)
import json
from datetime import datetime

consumer_key = 'dKUQo0IIf1ZYo3EtMNdbPT374'
consumer_secret = 'lnRA8izXCEG6mRMePUV88k6XL3SzUs5fe3iOtKbArMFlaw3jio'
access_token = '3565074266-3Zb3chDQv8FZTeVc5JFNCqqbSFU65f8oF8bNXRl'
access_token_secret = 'SmcYCHvaTOZobS3ecK2sPiZQOAFlr1wgGIexVECl2Mlk3'
MONGO_HOST= 'mongodb://localhost:27017/twitterdb'
WORDS=[]
wordDict={}
class StreamListener(tweepy.StreamListener):
    def __init__(self,num):
        # super.__init__()
        self.counter=0
        self.num=num
        super(StreamListener, self).__init__()
    def on_connect(self):
        print("connected")
    def on_error(self,status_code):
        print('an error has occured' +repr(status_code))
        return False
    def on_data(self,data):
        try:
            # client = MongoClient(MONGO_HOST)
            # db = client.twitterdb
            self.counter += 1
            if(self.counter > self.num):
                return False
            print("collected tweet " + WORDS[0])
            dataJson = json.loads(data)
            created_time = dataJson['created_at']
            dataJson['created_at'] = datetime.strptime(created_time, '%a %b %d %H:%M:%S +0000 %Y').isoformat()
            db.word_search.insert({ WORDS[0] : dataJson['id']}) 
            db.twitter_search.insert(dataJson) # our collection
        except Exception as e:
            print(e)

@app.route("/track")
def track():
    word = request.args.get('word')
    num =  int(request.args.get('num'))
    hashTag = request.args.get('hashTag',None)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    listener = StreamListener(num=num)
    streamer = tweepy.Stream(auth=auth, listener=listener)
    if(hashTag is not None):
        word= '#'+str(word)
    del(WORDS[:])
    WORDS.append(str(word))
    print("Tracking: " + str(WORDS[0]))
    streamer.filter(track=WORDS,async=True)
    return 'tracking '+ word

@app.route("/tweets")
def getTweets():
    sortDateAsc=request.args.get('sortDateAsc',None)
    sortDateDesc=request.args.get('sortDateDesc',None)
    sortText=request.args.get('sortText',None)
    sortId=request.args.get('sortId',None)
    if(sortDateAsc is not None):
        cursor = db['twitter_search'].find({}).sort('created_at',pymongo.ASCENDING)
    elif(sortDateDesc is not None):
        cursor = db['twitter_search'].find({}).sort('created_at',pymongo.DESCENDING)
    elif(sortText is not None):
        cursor = db['twitter_search'].find({}).sort('text',pymongo.ASCENDING)
    elif(sortId is not None):
        cursor = db['twitter_search'].find({}).sort('id',pymongo.ASCENDING)
    else:
        cursor = db['twitter_search'].find({})
    l=list(cursor)
    res = json.dumps(l,indent=4,default=json_util.default)
    return Response(res,status=200,mimetype='application/json')

@app.route("/tweets/<int:pagenum>/<int:pagesize>")
def getPage(pagenum,pagesize):
    if(pagesize > 50):
        data= { 'error' : 'pagesize should be less than 51' }
        d=json.dumps(data)
        return Response(d,status=400,mimetype='application/json')
    sortDateAsc=request.args.get('sortDateAsc',None)
    sortDateDesc=request.args.get('sortDateDesc',None)
    sortText=request.args.get('sortText',None)
    sortId=request.args.get('sortId',None)

    skips = pagesize * (pagenum - 1)

    if(sortDateAsc is not None):
        cursor = db['twitter_search'].find({}).skip(skips).limit(pagesize).sort('created_at',pymongo.ASCENDING)
    elif(sortDateDesc is not None):
        cursor = db['twitter_search'].find({}).skip(skips).limit(pagesize).sort('created_at',pymongo.DESCENDING)
    elif(sortText is not None):
        cursor = db['twitter_search'].find({}).skip(skips).limit(pagesize).sort('text',pymongo.ASCENDING)
    elif(sortId is not None):
        cursor = db['twitter_search'].find({}).skip(skips).limit(pagesize).sort('id',pymongo.ASCENDING)
    else:
        cursor=db['twitter_search'].find().skip(skips).limit(pagesize)
    l=list(cursor)
    res = json.dumps(l,indent=4,default=json_util.default)
    return Response(res,status=200,mimetype='application/json')

@app.route("/search")
def search():
    q=str(request.args.get('query'))
    hashTag = request.args.get('hashTag')
    if(hashTag is not None):
        q = str('#' + str(q))
    print("searching for " + q)
    collection=db['twitter_search']
    collection.create_index([('text','text'),('user.name','text')])
    cursor = collection.find({"$text": {"$search" : q }})
    l=list(cursor)
    print(cursor.count())
    res=json.dumps(l,indent=4,default=json_util.default)
    return Response(res,status=200,mimetype='application/json')

@app.route("/filter")
def filter():
    print(request.data)
    nameContains = request.args.get('nameContains',None)
    textContains = request.args.get('textContains',None)
    textStarts = request.args.get('textStarts',None)
    nameBegins = request.args.get('nameBegins',None)
    favouriteCount = request.args.get('favouriteCount',None)
    language = request.args.get('language',None)
    followers = request.args.get('followers',None)
    retweetCountLt = request.args.get('retweetCountLt',None)
    retweetCountGt = request.args.get('retweetCountLt',None)
    retweetCountEq = request.args.get('retweetCountEq',None)
    dateGt = request.args.get('dateGt',None)
    dateLt = request.args.get('dateLt',None)
    dateEq = request.args.get('dateEq',None)
    screenName = request.args.get('screenName',None)


    collection=db['twitter_search']
    q = []
    if(nameContains is not None):
        q.append({'user.name':Regex(".*"+nameContains+".*", "i")})
    elif(nameBegins is not None):
        q.append({'user.name' : Regex("^"+nameBegins+".*", "i")})
    if(textContains is not None):
        q.append({'text':Regex(".*"+textContains+".*", "i")})
    if(screenName is not None):
        q.append({'user.screen_name':Regex(".*"+screenName+".*", "i")})
        
    if(textStarts is not None):
        q.append({'text' : Regex("^"+textStarts+".*", "i")})
    if(favouriteCount is not None):
        q.append({'user.favourites_count': int(favouriteCount)})
    if(language is not None):
        q.append({'user.lang':language})
    if(followers is not None):
        q.append({'user.followers_count': int(followers)})
    if(retweetCountEq is not None):
        q.append({'retweet_count' : int(retweetCountEq)})
    elif (retweetCountGt is not None):
        q.append({'retweet_count' :  {"$gt" : int(retweetCountGt)}})
    if(retweetCountLt is not None):
        q.append({'retweet_count': {"$lt" : int(retweetCountGt)}})
    if(dateEq is not None):
        d=datetime.strptime(dateEq,'%b %d %Y').isoformat()
        q.append({'created_at':d})
    elif (dateLt is not None):
        d=datetime.strptime(dateLt,'%b %d %Y').isoformat() 
        q.append({'created_at':{'$lte':d}})
    if(dateGt is not None):
        d=datetime.strptime(dateGt,'%b %d %Y').isoformat()
        q.append({'created_at':{'$gte':d}})
    cursor = collection.find({"$and":q})
    res= json.dumps(list(cursor),indent=4,default=json_util.default)
    return Response(res,status=200,mimetype='application/json')

@app.route("/getcsv")
def getCsv():
    subprocess.run('mongoexport --host=localhost:27017 --db=twitterdb --collection=twitter_search  --type csv --fields id,user.name,text,retweet_count,created_at --out=twitter.csv',shell=True)
    dir=os.getcwd()
    return send_from_directory(dir,filename='twitter.csv',as_attachment=True)
    
if __name__ == '__main__':
    print("running...")
    try:
        client = MongoClient(MONGO_HOST)
        db = client.twitterdb
        db.twitter_search.create_index('id',unique=True)
    except pymongo.errors.ConnectionFailure:
        print("Failed to connect ")
    num=50
    counter=0
    app.run(debug=True)
