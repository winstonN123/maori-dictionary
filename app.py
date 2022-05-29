from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime
#imports all functions requried

app = Flask(__name__)
app.secret_key = "valorant"  # scramble key
DATABASE = "dictionary.db"  # the database
bcrypt = Bcrypt(app)


def create_connection(db_file):  # creates the general function to connect to the database
    """create a connection to the sqlite db"""
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as error:
        print(error)
    return None


def is_logged_in():  # creates the function to show if someone is logged in
    if session.get('email') is None:
        print("not logged in ")
        return False
    else:
        print("logged in")
        return True


def is_admin():  # creates the function to show if someone has admin rights
    if session.get('admin') != 1:
        print("denied")
        return False
    else:
        return True


def valid_characters(text):  # creates a general function to check if it contains a number or not
    return any(map(str.isdigit, text))


def categories():  # queries category and id columns into a list
    con = create_connection(DATABASE)
    query = "SELECT category,id FROM category ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    return category_list


def username():  # queries id,firstname and lastname columns into a list
    con = create_connection(DATABASE)
    query = "SELECT id,firstname,lastname FROM login"
    cur = con.cursor()
    cur.execute(query)
    username = cur.fetchall()
    print(username)
    con.close()
    return username


def wordbank_list():  # queries all the columns into a list
    con = create_connection(DATABASE)
    query = "SELECT * FROM wordbank ORDER BY maori ASC"
    cur = con.cursor()
    cur.execute(query, )
    wordbank_list = cur.fetchall()
    con.close()
    return wordbank_list


def real_page(list, id, id_postsition):  # checks if the page is a real page
    for i in list:
        if i[id_postsition] == id:
            break
    else:
        return True


@app.route('/', methods=['POST', 'GET'])
def main():  # renders the homepage witch contains a search bar

    if request.method == "GET":
        search = str("{}{}".format(request.args.get('Search'), "%"))  # pulls data from the url
        con = create_connection(DATABASE)
        query = "SELECT * FROM wordbank WHERE english LIKE ? OR maori LIKE ?"  # selects data form maori and english
        cur = con.cursor()
        cur.execute(query, (search, search))  # column that is similar to a variable
        search_results = cur.fetchall()  # and puts it into a list
        con.close()

        if len(search_results) == 0 and search == "None%":  # checks if the query actually finds
            # something and the search button has been used
            search_results = "Empty"
        elif len(search_results) == 0:   # checks if the query actually finds
            # anything and if the search button been used
            search_results = "None"
    print(search_results)
    return render_template("home.html", categories=categories(), logged_in=is_logged_in(),
                           Search_results=search_results, is_admin=is_admin())


@app.route("/login", methods=['POST', 'GET'])
def login():  # renders the login page
    error = request.args.get('error')  # get error data from the url

    if is_logged_in():  # if they are logged in, it will redirect them to home
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        email = request.form['email'].lower().strip()  # getting data from the form
        password = request.form['password'].strip()
        query = """SElECT id,password,admin FROM login WHERE email = ?"""  # selects data from
        con = create_connection(DATABASE)  # the login database
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()  # and puts them into a list
        con.commit()
        con.close()

        try:
            user_id = user_data[0][0]  # sets up variables for sessions
            db_password = user_data[0][1]
            admin = user_data[0][2]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')

        session['admin'] = admin  # sets up sessions
        session['email'] = email
        session['user_id'] = user_id
        print(session)
        return redirect('/')

    if error is None:
        error = ""

    return render_template('login.html', logged_in=is_logged_in(), categories=categories(), is_admin=is_admin(),
                           error=error)


@app.route("/signup", methods=['POST', 'GET'])
def signup():  # renders the signup page
    error = request.args.get('error')  # gets error data from url
    if is_logged_in():  # if they are logged in, redirects them to home
        return redirect('/')
    if request.method == 'POST':
        print(request.form)
        firstname = request.form.get('firstname')  # getting data from the form
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        password_check = request.form.get('confirm_password')
        admin = request.form.get('Admin')

        if len(password) < 8:  # checks if password is too short
            return redirect('/signup?error=password+must+be+greater+than+eight+characters')

        if password != password_check:  # checks if they can type their password twice correctly
            return redirect('/signup?error=Passwords+dont+match')

        if valid_characters(firstname) or valid_characters(lastname):  # checks if there is any numbers
            return redirect('/signup?error=input+cannot+contain+characters')  # in their first or last names

        if len(firstname) < 2 or len(lastname) < 2:  # checks if their last and first name
            # has to be longer than two characters
            return redirect('/signup?error=firstname+or+lastname+must+both+contain+more+than+two+characters')

        hashed_password = bcrypt.generate_password_hash(password)  # encrypts the password with hash
        con = create_connection(DATABASE)
        query = "INSERT INTO login (firstname,lastname,email,password,admin) VALUES (?,?,?,?,?)"  # adds the data
        # into the database
        cur = con.cursor()

        try:
            cur.execute(query, (firstname, lastname, email, hashed_password, admin))
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM INSERTING INTO DATABASE- FOREIGN KEY ###")
            return redirect('/signup?error=email+used+already')

        con.commit()
        con.close()
        return redirect('/login')  # redirects them to login so that they can login

    if error is None:
        error = ""

    return render_template("signup.html", error=error, logged_in=is_logged_in(), categories=categories(),
                           is_admin=is_admin())


@app.route('/logout', methods=['POST', 'GET'])
def logout():  # the function for the user to sign out
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')


@app.route('/category/<category_id>', methods=['POST', 'GET'])
def category_pages(category_id):  # rendering the category pages
    error = request.args.get('error')  # gets the error data from url
    confirmation = str(request.args.get('confirmation'))  # gets the confirmation data from url
    try:
        category_id = int(category_id)  # checks if there is this category page
    except ValueError:  # if not, redirects them to home
        print("{} is not an integer".format(category_id))
        return redirect("/")

    if real_page(categories(), category_id, 1):  # checks if it is real page
        return redirect('/')

    if confirmation == "yes":
        if is_admin():  # checks if they have access to this action
            return redirect('/')
        query = "DELETE FROM category WHERE id = ?"  # deletes the category
        con = create_connection(DATABASE)
        cur = con.cursor()

        try:
            cur.execute(query, (category_id,))
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM DELETING FROM DATABASE- FOREIGN KEY ###")
            return redirect('/category/{}?error=Something+went+very+very+wrong'.format(category_id))

        con.commit()
        con.close()
        return redirect("/")
    elif confirmation == "no":  # if they cancel, it just redirects them back
        return redirect("/category/{}".format(category_id))

    if request.method == 'POST':
        method = request.form.get('submit_type')
        if method == 'add word':
            print(request.form)
            new_maori_word = request.form.get('Maori').strip().title()  # gets data from forms
            new_english_word = request.form.get('English').strip().title()
            new_level = request.form.get('Level')
            new_definition = request.form.get('Definition')
            date = datetime.now()
            user_id = session.get('user_id')

            if valid_characters(new_maori_word) or valid_characters(new_english_word) or valid_characters(
                    new_definition):  # checks if they contain inputs
                return redirect('/category/{}?error=input+cannot+contain+numbers'.format(category_id))

            con = create_connection(DATABASE)
            query = "INSERT INTO wordbank (maori,english,categories,definition,level,date,user,image) " \
                    "VALUES (?,?,?,?,?,?,?,?)"
            cur = con.cursor()

            try:
                cur.execute(query, (new_maori_word, new_english_word, category_id, new_definition,
                                    new_level, date, user_id, "noimage.png"))  # inserts it into database
            except sqlite3.IntegrityError as e:
                print(e)
                print("### PROBLEM INSERTING INTO DATABASE- FOREIGN KEY ###")
                return redirect('/category/{}?error=Something+went+very+very+wrong'.format(category_id))

            con.commit()
            con.close()
        elif method == 'modify category':
            modify_category = request.form.get('modify_category').strip().title()

            if valid_characters(modify_category):
                return redirect('/category/{}?error=input+cannot+contain+characters'.format(category_id))

            con = create_connection(DATABASE)
            query = "UPDATE category SET category = ? WHERE id = ? "  # modifies that specific word with new data
            cur = con.cursor()

            try:
                cur.execute(query, (modify_category, category_id))
            except sqlite3.IntegrityError as e:
                print(e)
                print("### PROBLEM UPDATING DATABASE- FOREIGN KEY ###")
                return redirect('/category/{}?error=Something+went+very+very+wrong'.format(category_id))

            con.commit()
            con.close()

    if error is None:
        error = ""

    return render_template("category.html", wordlist=wordbank_list(), categories=categories(), category_id=category_id,
                           logged_in=is_logged_in(), is_admin=is_admin(), confirmation=confirmation, error=error)


@app.route('/word/<word_id>', methods=['POST', 'GET'])
def word_page(word_id):  # rendering the word pages
    error = request.args.get('error')  # gets error data from url
    confirmation = str(request.args.get('confirmation'))  # gets confirmation data from url
    wordbank = wordbank_list()

    try:   # checks if there is a word page
        word_id = int(word_id)
    except ValueError:  # returns them to home if there isn't
        print("{} is not an integer".format(word_id))
        return redirect("/")

    if real_page(wordbank_list(), word_id, 0):  # checks if it is a real page
        return redirect('/')

    for word in wordbank:  # finds the word's category id
        if word[0] == word_id:
            category_id = word[3]

    if confirmation == "yes":
        if is_admin():  # checks if they have access to this action
            return redirect('/')
        query = "DELETE FROM wordbank WHERE id = ?"  # deletes word form database
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (word_id,))
        con.commit()
        con.close()
        return redirect("/category/{}".format(category_id))
    elif confirmation == "no":  # if they cancel, it redirects them back
        return redirect("/word/{}".format(word_id))

    if request.method == 'POST':
        if is_admin():  # checks if they have access to this action
            return redirect('/')
        print(request.form)
        modify_maori = request.form.get('Modify_maori').strip().title()  # getting all the data from the forms
        modify_english = request.form.get('Modify_english').strip().title()
        modify_level = request.form.get('Modify_level')
        modify_definition = request.form.get('Modify_definition')
        date = datetime.now()
        user_id = session.get('user_id')

        if valid_characters(modify_maori) or valid_characters(modify_english) or valid_characters(modify_definition):
            return redirect('/word/{}?error=input+cannot+contain+characters'.format(word_id))

        con = create_connection(DATABASE)
        query = "UPDATE wordbank SET maori = ? ,english = ? ,definition = ? ,level = ? " \
                ",last_modify_by = ? ,editted_date = ?  WHERE id = ?"  # modifies that specific word with new data
        cur = con.cursor()

        try:
            cur.execute(query, (modify_maori, modify_english, modify_definition, modify_level, user_id, date, word_id))
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM UPDATING DATABASE- FOREIGN KEY ###")
            return redirect('/word/{}?error=Something+went+very+very+wrong'.format(word_id))

        con.commit()
        con.close()

    if error is None:
        error = ""

    return render_template("word.html", wordlist=wordbank_list(), categories=categories(), word_id=word_id,
                           logged_in=is_logged_in(), username=username(), confirmation=confirmation,
                           is_admin=is_admin(), error=error, category_id=category_id)


@app.route("/add_words", methods=['POST', 'GET'])
def add_words_page():  # renders the add words page
    error = request.args.get('error')

    if request.method == 'POST':
        print(request.form)
        new_maori_word = request.form.get('Maori').strip().title()  # gets data from forms
        new_english_word = request.form.get('English').strip().title()
        new_level = request.form.get('Level')
        new_definition = request.form.get('Definition')
        date = datetime.now()
        category_id = request.form.get('Categories')
        user_id = session.get('user_id')

        if valid_characters(new_maori_word) or valid_characters(new_english_word) or valid_characters(
                new_definition):  # checks if they contain inputs
            return redirect('/add_words?error=input+cannot+contain+numbers')

        con = create_connection(DATABASE)
        query = "INSERT INTO wordbank (maori,english,categories,definition,level,date,user,image) " \
                "VALUES (?,?,?,?,?,?,?,?)"
        cur = con.cursor()

        try:
            cur.execute(query, (new_maori_word, new_english_word, category_id, new_definition, new_level, date, user_id,
                                "noimage.png"))  # inserts it into database
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM INSERTING INTO DATABASE- FOREIGN KEY ###")
            return redirect('/add_words?error=Something+went+very+very+wrong')

        con.commit()
        con.close()

    if error is None:
        error = ""

    return render_template("add_words.html", error=error, logged_in=is_logged_in(), categories=categories(),
                           is_admin=is_admin())


@app.route("/add_category", methods=['POST', 'GET'])
def add_category():  # renders the add category page
    error = request.args.get('error')

    if request.method == "POST":
        if is_admin():  # checks if they have access to this action
            return redirect('/')
        category = request.form.get('add_category').strip().title()

        if valid_characters(category):  # checks if it has numbers in the input
            return redirect('/add_category?error=input+cannot+contain+characters')
        category = request.form.get('add_category').strip().title()
        con = create_connection(DATABASE)
        query = "INSERT INTO category (category) VALUES (?)"  # adds new category into database
        cur = con.cursor()

        try:
            cur.execute(query, (category,))
        except sqlite3.IntegrityError as e:
            print(e)
            print("### PROBLEM INSERTING INTO DATABASE- FOREIGN KEY ###")
            return redirect('/add_category?error=Something+went+very+very+wrong')

        con.commit()
        con.close()

    if error is None:
        error = ""

    return render_template('add_category.html', logged_in=is_logged_in(), categories=categories(), is_admin=is_admin(),
                           error=error)


if __name__ == '__main__':
    app.run()
