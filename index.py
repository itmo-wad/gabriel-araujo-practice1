from flask import Flask, request, render_template, url_for, redirect, flash, session, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os
from bson.objectid import ObjectId


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


client = MongoClient('localhost', 27017)
db = client.wad
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = './upload'
app.config['SECRET_KEY'] = 'super secret key'
auth = HTTPBasicAuth()


def checkPassword(username, password):
    user = db.users.find_one({"username": username})
    if user:
        if check_password_hash(user['password'], password):
            session['logged'] = f"{user['_id']}"
            return True
    return False

def allowedFile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getLoggedUsername():
    if 'logged' in session:
        user = db.users.find_one(ObjectId(session['logged']))
        if user:
            return user['username']
        session.pop('logged', None)
    return ''

@app.route('/')
def home():
    return render_template("home.html", username=getLoggedUsername())

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if username == '':
            flash('Invalid Username', 'danger')
            return redirect(request.url)
        if password == '':
            flash('Invalid Password', 'danger')
            return redirect(request.url)
        db.users.insert_one({"username": username, "password": generate_password_hash(password)})
        print(f"{username} - {password} SALVO")
        return redirect('/login')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if checkPassword(username, password):
            return redirect(url_for('myPage'))
        flash('Login Error', 'danger')
        return redirect(request.url)

@app.route('/myPage')
def myPage():
    username = getLoggedUsername()
    if username != '':
        return render_template("myPage.html", username=username)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'logged' in session:
        session.pop('logged', None)
    return redirect('/')

@app.route('/upload', methods=['GET', 'POST'])
def uploadFile():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if not allowedFile(file.filename):
            flash('Invalid file extension', 'danger')
            return redirect(request.url)
            
        if file and allowedFile(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Successfully saved', 'success')
            return redirect(url_for('uploadedFile', filename=filename))
  
    return render_template("upload.html")
    
       
@app.route('/uploads/<filename>')
def uploadedFile(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    db.users.drop()
    from faker import Faker

    faker = Faker()

    db.users.insert_one({"username": "user", "password": generate_password_hash('123')})

    app.run(host='localhost', port=5000, debug=True)