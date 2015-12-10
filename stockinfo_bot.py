#!/usr/bin/python

import urllib2, json, re, praw
from collections import deque
from time import sleep
from string import Template


username = "stockinfo_bot"
password = "Moder@tor"
user_agent = "Stock Quote Info Bot"

r = praw.Reddit(user_agent)
r.login(username, password)

subreddit = r.get_subreddit('wallstreetbets')
stock_regex = re.compile('\$[a-z]+')
baseurl = "https://query.yahooapis.com/v1/public/yql?q="
endurl = "&format=json&diagnostics=true&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback="
yql_query = "select * from yahoo.finance.quotes where symbol in ".replace(" ", "%20")
reply_row = Template("$sym|$ask|$pctch|$yrange|$mktcap|$peratio  \n")
reply_table = "Sym|Ask|%Change|YrRange|MktCap|PERatio\n:-----:|:-----:|:-----:|:-----:|:-----:|:-----:\n"
sub_cache = deque([])
comm_cache = deque([])


def format_query(lst):
    frmt = ""
    for item in lst:
        frmt = frmt + "\"" + item.replace("$", "").upper() + "\"%2C"
    frmt = yql_query + "(" + frmt[:-3] + ")"
    return frmt

def get_json(query):
    yql_url = baseurl + query + endurl
    result = urllib2.urlopen(yql_url).read()
    return json.loads(result)

def sub_reply_text(quotes, data):
    reply = ""
    def sub(stock):
        temp = ""
        try:
            temp = reply_row.substitute(sym=stock['symbol'],
                                            ask=stock['Ask'],
                                            pctch=stock['PercentChange'],
                                            yrange=stock['YearRange'],
                                            mktcap=stock['MarketCapitalization'],
                                            peratio=stock['PERatio'])
        except TypeError:
            print "TypeError in sub_reply_text(" + stock + ")"
        except:
            print "UnIdentified Error in sub_reply_text(" + stock + ")"
        return temp

    if(len(quotes) > 1):
        for stock in data['query']['results']['quote']:
            reply = reply + sub(stock);
    else:
        return sub(data['query']['results']['quote'])
    return reply

def proc_submissions():
    for submission in subreddit.get_new(limit=10):
        if submission.id not in sub_cache:
            op_text = submission.selftext.lower()
            quotes = set(re.findall(stock_regex, op_text))
            if quotes:
                data = get_json(format_query(quotes))
                reply_text = reply_table + sub_reply_text(quotes, data)
                if(len(reply_text) > 0):
                    submission.add_comment(reply_text)
                    sub_cache.append(submission.id)
                    #print submission.id
                    #print reply_text
                    sleep(120)
                else:
                    sub_cache.append(submission.id)
                    if len(sub_cache) > 10:
                        sub_cache.popleft()

def proc_comments():
    for comment in subreddit.get_comments(limit=35):
        if comment.id not in comm_cache:
            op_text = comment.body.lower()
            quotes = set(re.findall(stock_regex, op_text))
            if quotes:
                data = get_json(format_query(quotes))
                reply_text = reply_table + sub_reply_text(quotes, data)
                if(len(reply_text) > 0):
                    comment.reply(reply_text)
                    comm_cache.append(comment.id)
                    #print comment.id
                    #print reply_text
                    sleep(120)
                else:
                    comm_cache.append(submission.id)
                if len(comm_cache) > 20:
                    comm_cache.popleft()

running = True
while running:
    proc_submissions()
    proc_comments()
    sleep(300)
