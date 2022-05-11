from flask import Flask,render_template,request,redirect,session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

app=Flask(__name__)
app.secret_key="valorant"
DATABASE="dictionary.db"
bcrypt=Bcrypt(app)

def create_connection(db_file):
    """create a connection to the sqlite db"""
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as error:
        print(error)

    return None


def is_logged_in():
    if session.get('email') == None:
        print("not logged in ")
        return False
    else:
        print("logged in")
        return True

def is_admin():
    if session.get('admin') != 1:
        print("not admin ")
        return False
    else:
        print("is admin")
        return True


def categories():
    con = create_connection(DATABASE)
    query = "SELECT category,id FROM category"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    return category_list

def username():
    con = create_connection(DATABASE)
    query = "SELECT id,firstname,lastname FROM login"
    cur = con.cursor()
    cur.execute(query)
    username = cur.fetchall()
    print(username)
    con.close()

    return username


def wordbank_list():
    con = create_connection(DATABASE)
    query = "SELECT id,maori,english,categories,definition,level,image,date,user FROM wordbank"
    cur = con.cursor()
    cur.execute(query,)
    wordbank_list = cur.fetchall()
    con.close()
    return wordbank_list


@app.route('/')
def main():
    return render_template("home.html",categories=categories(),logged_in=is_logged_in(),wordbank_list=wordbank_list(),is_admin=is_admin())


@app.route("/add_category",methods=['POST','GET'])
def admin():
    if request.method == "POST":
        print(request.form)
        category = request.form.get('add_category').strip().title()
        con = create_connection(DATABASE)
        query = "INSERT INTO category (category) VALUES (?)"
        cur = con.cursor()
        try:
            cur.execute(query,(category,))
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM INSERTING INTO DATABASE- FOREIGN KEY ###")
            return redirect('/home?error=Something+went+very+very+wrong')

        con.commit()
        con.close()
    return render_template('add_category.html', logged_in=is_logged_in(), categories=categories(),is_admin=is_admin())


@app.route("/login",methods=['POST','GET'])
def login():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        email = request.form['email'].lower().strip()
        password=request.form['password'].strip()
        query = """SElECT id,firstname,password,admin FROM login WHERE email = ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query,(email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
            admin = user_data[0][3]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password,password):
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')
        session['admin'] = admin
        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template('login.html',logged_in=is_logged_in(),categories=categories(),is_admin=is_admin())


@app.route("/signup",methods=['POST','GET'])
def signup():
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

        cur=con.cursor()
        cur.execute(query,(firstname,lastname,email,hashed_password))
        con.commit()
        con.close()
        return redirect('/login')
    error=request.args.get('error')

    if error == None:
        error=""
    return render_template("signup.html",error=error,logged_in=is_logged_in(),categories=categories(),is_admin=is_admin())


@app.route('/logout',methods=['POST','GET'])
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')


@app.route('/category/<category_id>/<confirmation>')
def category_pages(category_id,confirmation):
    if confirmation == "yes":
        query="DELETE FROM category WHERE id = ?"
        con=create_connection(DATABASE)
        cur=con.cursor()
        cur.execute(query,(category_id,))
        con.commit()
        con.close()
        return redirect("/")
    if confirmation == "no":
        return redirect("/category/{}/0".format(category_id))

    try:
        category_id = int(category_id)
    except ValueError:
        print("{} is not an integer".format(category_id))
        return redirect("/menu?error=Invalid+product+id")
    return render_template("category.html",wordlist=wordbank_list(),categories=categories(),category_id=category_id,logged_in=is_logged_in(),is_admin=is_admin(),confirmation=confirmation)


@app.route('/word/<word_id>/<confirmation>/<category_id>',methods=['POST','GET'])
def word_page(word_id,confirmation,category_id):
    word_id = int(word_id)
    if confirmation == "yes":
        query="DELETE FROM wordbank WHERE id = ?"
        con=create_connection(DATABASE)
        cur=con.cursor()
        cur.execute(query,(word_id,))
        con.commit()
        con.close()
        return redirect("/category/{}".format(category_id))
    if confirmation == "no":
        return redirect("/category/{}".format(category_id))

    if request.method == 'POST':
        print(request.form)
        Modify_maori = request.form.get('Modify_maori').strip().title()
        Modify_english = request.form.get('Modify_english').strip().title()
        Modify_level = request.form.get('Modify_level')
        Modify_definition = request.form.get('Modify_definition')
        Date = datetime.now()
        user_id = session.get('user_id')
        print(user_id)
        con=create_connection(DATABASE)
        try:
            query = "UPDATE wordbank SET maori = ? ,english = ?  ,definition = ?  ,level = ? ,last_modify_by = ?  ,editted_date = ?   WHERE id = ?"
        except sqlite3.IntegrityError:
            redirect('/signup?error=Passwords+dont+match')
        cur = con.cursor()
        cur.execute(query,(Modify_maori,Modify_english,Modify_definition,Modify_level,user_id,Date,word_id))
        con.commit()
        con.close()

    return render_template("word.html",wordlist=wordbank_list(),categories=categories(),word_id=word_id,logged_in=is_logged_in(),username=username(),confirmation=confirmation,category_id=category_id,is_admin=is_admin())


@app.route("/add_words",methods=['POST','GET'])
def add_words():
    if request.method == 'POST':
        print(request.form)
        Maori_word = request.form.get('Maori').strip().title()
        English_word = request.form.get('English').strip().title()
        Level = request.form.get('Level')
        Definition = request.form.get('Definition')
        Date = datetime.now()
        Category_id = request.form.get('Categories')
        user_id = session.get('user_id')

        print(user_id)
        con=create_connection(DATABASE)
        try:
            query = "INSERT INTO wordbank (maori,english,categories,definition,level,date,user) VALUES (?,?,?,?,?,?,?)"
        except sqlite3.IntegrityError:
            redirect('/signup?error=Passwords+dont+match')

        cur = con.cursor()
        cur.execute(query,(Maori_word,English_word,Category_id,Definition,Level,Date,user_id))
        con.commit()
        con.close()
    error = request.args.get('error')

    if error == None:
        error = ""
    return render_template("add_words.html",error=error,logged_in=is_logged_in(),categories=categories(),is_admin=is_admin())


if __name__ == '__main__':
    app.run()
