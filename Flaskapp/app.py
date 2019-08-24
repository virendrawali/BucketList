from flask import Flask, render_template, request, json, redirect,session
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

pageLimit = 2

app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Virendra@14'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


@app.route("/")
def main():
    return render_template('index.html')

@app.route("/showSignUp")
def showSignUp():
    return render_template('signup.html')

@app.route("/signin")
def signin():
    return render_template('signin.html')


@app.route('/signUp', methods=['POST'])
def signUp():
    # read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']

    conn = mysql.connect()
    cursor = conn.cursor()

    _hashed_password = generate_password_hash(_password)

    cursor.callproc('sp_createUser1', (_name, _email, _password))
    data = cursor.fetchall()

    if len(data) is 0:
        conn.commit()
        return json.dumps({'message': 'User created successfully !'})
    else:
        return json.dumps({'error': str(data[0])})

    return jsonify(result={"status": 200})


@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        # connect to mysql

        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin2', (_username,))
        data = cursor.fetchall()

        if len(data) > 0:
            if str(data[0][3]) ==  _password:
                session['user'] = data[0][0]
                return redirect('/userhome')
            else:
                return render_template('error.html', error='Wrong Email address or Password.')
        else:
            return render_template('error.html', error='Wrong Email address or Password.')


    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        cursor.close()
        con.close()

@app.route('/userhome')
def userhome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

@app.route('/showAddWish')
def showAddWish():
    return render_template('addWish.html')

@app.route('/addWish', methods = ['POST'])
def addWish():
    try:
        if session.get('user'):
            _title =request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_wishadd',(_title,_description,_user))
            data =cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return redirect('/userhome')
            else:
                return render_template('error.html',error = "An error occured")
        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))
    finally:
        cursor.close()
        conn.close()


@app.route('/getWish', methods=['POST'])
def getWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _limit = pageLimit
            _offset = request.form['offset']
            _total_records = 0

            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetWishByUser1', (_user, _limit, _offset, _total_records))

            wishes = cursor.fetchall()
            cursor.close()

            cursor = con.cursor()

            cursor.execute('SELECT @_sp_GetWishByUser1_3');

            outParam = cursor.fetchall()

            response = []
            wishes_dict = []
            for wish in wishes:
                wish_dict = {
                    'Id': wish[0],
                    'Title': wish[1],
                    'Description': wish[2],
                    'Date': wish[4]}
                wishes_dict.append(wish_dict)
            response.append(wishes_dict)
            response.append({'total': outParam[0][0]})

            return json.dumps(response)
        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/getWishById', methods=['POST'])
def getWishById():
    try:
        if session.get('user'):

            _id = request.form['id']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetWishById1', (_id, _user))
            result = cursor.fetchall()

            wish = []
            wish.append({'Id': result[0][0], 'Title': result[0][1], 'Description': result[0][2]})

            return json.dumps(wish)
        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/updateWish', methods=['POST'])
def updateWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = request.form['id']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_updateWish', (_title, _description, _wish_id, _user))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'status': 'OK'})
            else:
                return json.dumps({'status': 'ERROR'})
    except Exception as e:
        return json.dumps({'status': 'Unauthorized access'})
    finally:
        cursor.close()
        conn.close()

@app.route('/deleteWish',methods=['POST'])
def deleteWish():
    try:
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_deleteWish1',(_id,_user))
            result = cursor.fetchall()

            if len(result) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'An Error occured'})
        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return json.dumps({'status':str(e)})
    finally:
        cursor.close()
        conn.close()


@app.route('/upload',methods = ['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        extention = os.path.splitext(file.filename)[1]
        f_name = str(uuid.uuid4()) + extention
        app.config['UPLOAD_FOLDER'] = 'static/Uploads'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
        return json.dumps({'filename': f_name})


if __name__ == "__main__":
    app.debug = True
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run()



