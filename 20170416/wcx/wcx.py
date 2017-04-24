from flask import Flask
from flask import request
import pymysql.cursors

f = open('C://Users/wcx/Desktop/sql.txt')
a = f.read()

connection = pymysql.connect(host='112.74.215.22',
                             port=3306,
                             user='wcx',
                             password=a,
                             db='wcx'
                             )

cursor = connection.cursor()


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def signin_form():
    return '''<form action="/signin" method="post">
                 <p><code>用户名</code><input name="username"></p>
                 <p><code>密  码</code><input name="password" type="password"></p>
                 <button type="submit">登录</button>
                 </form>
                 <form action="/login" method="get">
                 <button type="submit">注册</button>
                 </form>'''


@app.route('/success')
def success():
    sql = 'select * from wcx where username =  \'%s\' ' % request.form['username']
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        word1 = row[1]
        str = word1

    return'''<h1>Hello %s.</h1>
             <form action="/change" method="get">
                            <p><button type="submit">change</button></p>
                            </form>''' % str


@app.route('/change',methods=['GET'])
def change():
    return '''
                  <form action="/change" method="post">
                  <p><code>id</code><input name="id" </p>
                  <p><code>new-password</code><input name="newpassword" </p>
                  <p><button type="submit">修改密码</button></p>
                  </form>'''


@app.route('/change', methods=['post'])
def mima():
    id = request.form['id']
    password = request.form['newpassword']
    flag = updata(id, password)
    if flag:
        return '''
                  <form action="/" method="get">
                  <h3>successed</h3>
                  <p><button type="submit">back</button></p>
                  </form>'''
    else:
        return '''
                          <form action="/" method="get">
                          <h3>失败</h3>
                          <p><button type="submit">back</button></p>
                          </form>'''


@app.route('/login', methods=['GET'])
def login_form():
    return'''<form action="/login" method="post">
             <p>username:<input name="username"></p>
             <p>password:<input name="password"></p>
             <p>nickname:<input name="nickname"></p>
             <p>id:<input name="id"></p>
             <p><button type="submit">   Save  </button></p>
             </form>'''


@app.route('/login', methods=['POST'])
def login():
        username = request.form['username']
        nickname = request.form['nickname']
        password = request.form['password']
        flag = insert(username, nickname, password)
        if flag:
            return '''<form action="/" method="get">
                             <h3>成功</h3>
                             <p><button type="submit">back</button></p>
                             </form>'''
        else:
            return '''<form action="/" method="get">
                                <h3>失败</h3>
                                <p><button type="submit">back</button></p>
                                </form>
                                </form>
                                <form action="/login" method="get">
                                <button type="submit">Login</button>
                                </form>'''


@app.route('/signin', methods=['POST'])
def signin():
    sql = 'select * from wcx where username =  \'%s\' ' % request.form['username']
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        word = row[3]
        if request.form['password'] == word:
            return success()
        return '<p>Bad username or password.</p>'






def insert(username, nickname, password):
    try:
        sql = "insert into wcx (username, password, nickname)values('"+username+"','" + password + "','"+nickname+"')"
        cursor.execute(sql)
        connection.commit()
        return True
    except:
        return False
    finally:
        connection.close()

def updata(id, newpassword):
    try:
        sql = "Update wcx set password = '"+newpassword+"'where id = '"+id+"'"
        cursor.execute(sql)
        connection.commit()
        return True
    except:
        return False
    finally:
        connection.close()


f.close()

if __name__ == '__main__':
    app.run(debug=True)