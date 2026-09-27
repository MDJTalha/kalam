import sqlite3
p=r"C:\Users\Talha\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"
c=sqlite3.connect("file:"+p+"?mode=ro", uri=True)
q="select host_key,name,path,is_secure,is_httponly,expires_utc from cookies where name='corp_lms_session' and host_key in ('127.0.0.1','localhost')"
print(c.execute(q).fetchall())
