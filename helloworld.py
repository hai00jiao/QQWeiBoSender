# -*- coding:utf8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import datetime
from google.appengine.ext import db
from google.appengine.api import users
import urllib2,urllib
import string
import time
import sched
import urlparse  
import cgi
import time
import datetime

#global variable
_url = "zhuchao0801.appspot.com"
#_url = "localhost:8080"
_appKey = "801259056"
_secret = "65de84d2611318f71a6667cf8b467fbe"

class AuthData(db.Model):
    theKey = db.StringProperty(required=False)
    value = db.StringProperty(required=False)

class MainPage(webapp.RequestHandler):
    def showAuthPage(self):
        html = '''
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <meta http-equiv="refresh" content="1; url=https://open.t.qq.com/cgi-bin/oauth2/authorize?client_id=%s&response_type=code&redirect_uri=http://%s"/>
        </head>
        <body>
        <h1>加载认证页面...</h1>
        <a href="https://open.t.qq.com/cgi-bin/oauth2/authorize?client_id=%s&response_type=code&redirect_uri=http://%s">点击认证</a>
        </body></html>
        '''%(_appKey,_url,_appKey,_url)
        print html;
    def showMessage(self,message):
        html ='''
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        </head>
        <body>
        <h1>%s</h1>
        </body></html>
        '''%message
        print html

    def parseToken(self,tokenStr):
        params = cgi.parse_qs(tokenStr,True)
        self.showMessage(params)
        if params.get('access_token')[0]:
            self.showReAuth()
            self.updateValue('access_token',params['access_token'][0])
            if params['expires_in'][0]:
				self.updateValue('expires_in',(datetime.datetime.now()+datetime.timedelta(seconds = int(params['expires_in'][0]))).strftime('%Y-%m-%d %H:%M'))
            if params['refresh_token'][0]:
				self.updateValue('refresh_token',params['refresh_token'][0])
            if params['name'][0]:
				self.updateValue('name',params['name'][0])
            if params['nick'][0]:
				self.updateValue('nick',params['nick'][0].decode('utf-8'))


    def getToken(self,code):
        url = '''https://open.t.qq.com/cgi-bin/oauth2/access_token?client_id=%s&client_secret=%s&redirect_uri=http://%s&grant_type=authorization_code&code=%s'''%(_appKey,_secret,_url,code)
        result = urllib2.urlopen(url).read()
        self.parseToken(result)

	



    def showReAuth(self):
        html = '''
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        </head>
        <body>
        <h1>已经认证</h1>
        <a href="https://open.t.qq.com/cgi-bin/oauth2/authorize?client_id=%s&response_type=code&redirect_uri=http://%s">重新认证</a>
        </body></html>
        '''%(_appKey,_url)
        print html;



    def updateValue(self,key,avalue):
        tokenQuery = AuthData.all()
        tokenQuery.filter("theKey =",key)
        if tokenQuery.fetch(100) :
            for obj in tokenQuery:
                obj.delete()
        data = AuthData(theKey = key,value = avalue)
        data.put()

    def get(self):	
        acode = self.request.get('code')
        if acode :
            aopenid = self.request.get('openid')
            aopenkey = self.request.get('openkey')
            self.response.out.write("<html><body><p>code:%s openid:%s openkey:%s </p></body></html>" %(acode,aopenid,aopenkey))	
            self.updateValue('code',acode)
            self.updateValue('openid',aopenid)
            self.updateValue('openkey',aopenkey)
            self.getToken(acode)
            return

        tokenQuery = AuthData.all()
        tokenQuery.filter("theKey =","access_token")
        if tokenQuery.fetch(100):
            token = ''
            for obj in tokenQuery:
                token = token + '\n' + obj.value
            self.showReAuth()
            return


        self.showAuthPage()


#""""""""""""""""""""""""""""""""""""""""""""""""
def getValue(key):
    tokenQuery = AuthData.all()
    tokenQuery.filter("theKey =",key)
    return tokenQuery.fetch(1)[0].value


class MessagePost(webapp.RequestHandler):
    def sendAnMessage(self):
        expireDate =datetime.datetime.strptime(getValue("expires_in"),'%Y-%m-%d %H:%M')
        if datetime.datetime.now() >= expireDate:
            f = RefreshToken()
            f.get()

        requiredData = {'oauth_consumer_key':_appKey,
            'access_token':getValue('access_token'),
            'clientip':'218.247.198.99',
            'openid':getValue('openid'),
            'oauth_version':'2.a',
            'scope':'all',
            'format':'json',
            'content':'%s时间过得真快啊，又一天过去了。 !'%time.strftime('%Y-%m-%d %A',time.localtime(time.time()))
            #'signtype':'1'
            }
        f = urllib2.urlopen(
            url = 'https://open.t.qq.com/api/t/add',
            data = urllib.urlencode(requiredData)
            )
        m = MainPage()
        m.showMessage(f.read())

    def get(self):
        self.sendAnMessage()

    
class RefreshToken(webapp.RequestHandler):
    def get(self):
        url = '''https://open.t.qq.com/cgi-bin/oauth2/access_token?client_id=%s&grant_type=refresh_token&refresh_token=%s'''%(_appKey,getValue('refresh_token'))
        result = urllib2.urlopen(url).read();
        m = MainPage()
        m.parseToken(result)	








#________________________________________


application = webapp.WSGIApplication([('/', MainPage),
    ('/tasks/send',MessagePost),
    ('/tasks/refreshToken',RefreshToken)
    ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

