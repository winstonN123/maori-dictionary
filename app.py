from flask import Flask,render_template,request,redirect,session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

app=Flask(__name__)
app.secret_key="valorant"
DATABASE="dictionary.db"
bcrypt=Bcrypt(app)


def create_connection(db_file):
    """create a connection to the sqlite db"""
    try:
        connection=sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as error:
        print(error)

    return None


def is_logged_in():
    if session.get('email') is None:
        print("not logged in ")
        return False
    else:
        print("logged in")
        return True


@app.route('/')
def main():
    con = create_connection(DATABASE)
    query = "SELECT category FROM category"
   # querry = "SELECT maori,english ,categories,definition,level,image FROM wordbank "
    cur = con.cursor()
    cur.execute(query)
    #cur.execute(querry)
    category_list = cur.fetchall()
    #wordlist_list = cur.fetchall(querry)
    con.close()
    print(category_list)
    return render_template("home.html",categories=category_list,logged_in=is_logged_in())


@app.route("/login",methods=['POST','GET'])
def login():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        email=request.form['email'].lower().strip()
        password=request.form['password'].strip()
        query="""SElECT id,firstname,password from login WHERE email = ?"""
        con=create_connection(DATABASE)
        cur=con.cursor()
        cur.execute(query,(email,))
        user_data=cur.fetchall()
        con.close()

        try:
            id=user_data[0][0]
            firstname=user_data[0][1]
            db_password=user_data[0][2]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password,password):
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')

        session['email']=email
        session['id']=id
        session['firstname']=firstname
        print(session)
        return redirect('/')
    return render_template('login.html',logged_in=is_logged_in())

@app.route("/signup",methods=['POST','GET'])
def signin():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        print(request.form)
        firstname=request.form.get('firstname')
        lastname=request.form.get('lastname')
        email=request.form.get('email')
        password=request.form.get('password')
        Password_check=request.form.get('confirm_password')

        if Password_check != password:
            return redirect('/signup?error=Password+dont+match')

        hashed_password=bcrypt.generate_password_hash(password)

        con=create_connection(DATABASE)

        try:
            query="INSERT INTO login (firstname,lastname,email,password) VALUES (?,?,?,?)"
        except sqlite3.IntegrityError:
            redirect('/signup?error=Passwords+dont+match')

        cur = con.cursor()
        cur.execute(query,(firstname,lastname,email,hashed_password))
        con.commit()
        con.close()
        return redirect('/login')
    error=request.args.get('error')

    if error == None:
        error=""
    return render_template("signup.html",error=error,logged_in=is_logged_in())

@app.route('/logout',methods=['POST','GET'])
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')



if __name__ == '__main__':
    app.run()
