# -*- coding: utf-8 -*-

import sys,os,cgi,sqlite3,datetime
import socket,fcntl
from wsgiref.simple_server import make_server
import android

droid=android.Android()

LIMIT=10  # 最大表示記事数.
DB_FILE='/sdcard/image_bbs.sqlite'
P=8080

con=sqlite3.connect(DB_FILE)
cur=con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS bbs (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, user TEXT, datetime TEXT, image TEXT, text TEXT)')
INSERT_DB='INSERT INTO bbs VALUES(NULL,?,?,?,?)'

def ipconfig():
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
  s.connect(('gmail.com',80))
  return s.getsockname()[0]

def post(user,image,text):
  if image=='' or text=='': return
  if user=='': user='匿名'
  dt=datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
  cur.execute(INSERT_DB,(cgi.escape(user.decode('utf-8')),dt,cgi.escape(image.decode('utf-8')).replace('\n','<br />'),cgi.escape(text.decode('utf-8')).replace('\n','<br />')))
  con.commit()
  droid.vibrate()
  #droid.notify(user,text)

def bbs(environ,start_response):
  global IP
  if environ['PATH_INFO']=='/':
    user=''
    if environ.has_key('HTTP_COOKIE'):
      cookie={}
      for d in environ['HTTP_COOKIE'].strip(';').split(';'):
        d=d.split('=')
        cookie[d[0]]=d[1]
      if cookie.has_key('BBSUSER'):
        user=cookie['BBSUSER']
    if environ['REQUEST_METHOD']=='POST':
      fs=cgi.FieldStorage(fp=environ['wsgi.input'],environ=environ,keep_blank_values=1)
      user=fs.getfirst('user','').strip()
      image=fs.getfirst('bbsImage','')
      text=fs.getfirst('text','').strip()
      post(user,image,text)
    data=u"""<!DOCTYPE html>
<html><head>
<meta http-equiv="Set-Cookie" content="BBSUSER=%s">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Image BBS by Android</title></head><body>
<p><a href="http://%s:%d">http://%s:%d</a></p>
<form action="/" method="post" id="form">
<span>名前:<input type="text" name="user" size="20" maxlength="30" value="%s" /></span>
<div><canvas id="bbsCanvas" width="400" height="200" style="border:1px solid;"></canvas></div>
<textarea name="text" cols="40" rows="5"></textarea><br />
<input type="hidden" name="bbsImage" id="bbsImage" />
<span><input type="button" onclick="clearCanvas();" value="画像消去" /></span>
<span><input type="button" value="更新" onclick="location.reload(true);" /></span>
<span><input type="button" value="送信" onclick="setImage();this.form.submit();" /></span>
</form>

<script type="text/javascript">
var mouseDownFlag = false;
window.onload = function() {
  draw();
  setImage();
};
function draw() {
  var canvas = document.getElementById('bbsCanvas');
  if (!canvas || !canvas.getContext) return false;
  var ctx = canvas.getContext('2d');
  canvas.onmousemove = function(e) {
    if (mouseDownFlag) {
      var rect = e.target.getBoundingClientRect();
      ctx.beginPath();
      ctx.arc(e.clientX - rect.left, e.clientY - rect.top, 3, 0, Math.PI * 2, false);
      ctx.fill();
    }
  }
  canvas.onmousedown = function(e) { mouseDownFlag = true; }
  canvas.onmouseup = function(e) { mouseDownFlag = false; }
  canvas.onmouseout = function(e) { mouseDownFlag = false; }
}
function setImage() {
  var canvas = document.getElementById('bbsCanvas');
  if (!canvas || !canvas.getContext) return false;
  document.getElementById("bbsImage").value = canvas.toDataURL();
}
function clearCanvas() {
  var canvas = document.getElementById('bbsCanvas');
  if (!canvas || !canvas.getContext) return false;
  var ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 400, 200);
  setImage();
}
</script>""" % (user,IP,P,IP,P,user)
    cur.execute('SELECT * FROM bbs ORDER BY id DESC')
    for i, row in enumerate(cur):
      if i>=LIMIT: break
      data+=('<div><p>%d <b>%s</b> %s</p><img src="%s" alt="Image" width="400" height="200" style="border:1px solid;" /><p>%s</p></div>' % row)
    data+='</body></html>'
    start_response('200 OK',[('Content-type','text/html;charset=utf-8')])
    return [data.encode('utf-8')]
