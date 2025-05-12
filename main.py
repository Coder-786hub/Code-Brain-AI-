from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json, os
from werkzeug.utils import secure_filename
import math



with open("config.json", "r") as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = "super-secrect-key"
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]
)
mail = Mail(app)

if (local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80),  nullable = False)
    email = db.Column(db.String(80), nullable = False)
    phone_num = db.Column(db.String(12),  nullable = False)
    message = db.Column(db.String(140),  nullable = False)
    date = db.Column(db.Integer, nullable = True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(80),  nullable = False)
    sub_title = db.Column(db.String(200),  nullable = False)
    slug = db.Column(db.String(21), nullable = False)
    content = db.Column(db.String(10000),  nullable = False)
    img_file = db.Column(db.String(15), nullable = True)
    date = db.Column(db.Integer, nullable = True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params["no_of_post"]))
    # [0:params["no_of_post"]]
    page = request.args.get("page")
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)    
    posts = posts[(page-1)*int(params["no_of_post"]):(page-1)*int(params["no_of_post"])+int(params["no_of_post"])]
    if (page == 1):
        prev = "#"
        next = "/?page="+ str(page + 1)
    elif (page == last):
       
        prev = "/?page="+ str(page - 1)
        next = "#"
    else:
        prev = "/?page="+ str(page - 1)
        next = "/?page="+ str(page + 1)  

    
    return render_template("index.html", posts = posts, prev = prev, next = next)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():

    if ("user" in session and session["user"] == params["admin_user"]):
        posts = Posts.query.all()
        return render_template("dashboard.html", posts = posts)


    if request.method== "POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if (username== params["admin_user"] and userpass==params["admin_pass"]):
            # set the session variable
            session["user"] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", posts = posts)
        

    # REDIRECT TO ADMIN PANEL
    
    return render_template("login.html")


@app.route("/edit/<string:sno>", methods = ["GET", "POST"])
def edit(sno):
    if ("user" in session and session["user"] == params["admin_user"]):
        if request.method == "POST":
            req_title = request.form.get("title")
            sub_title = request.form.get("stitle")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")
            date = datetime.now()

            if sno =="0":
                post = Posts(title = req_title, sub_title = sub_title, slug = slug, content = content, img_file = img_file, date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first() 
                post.title = req_title
                post.sub_tile = sub_title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect("/edit"+sno)
        post = Posts.query.filter_by(sno = sno).first()                
        return render_template("edit.html", post = post)
    

@app.route("/uploader", methods = ["GET", "POST"])
def uploader():
    if ("user" in session and session["user"] == params["admin_user"]):
        if (request.method=="POST"):
            f = request.files["file1"]
            f.save(os.path.join(params["upload_location"], secure_filename(f.filename)))
            return "Uploaded successffully"

@app.route("/delete/<string:sno>", methods = ["GET", "POST"])
def delete(sno):
    if ("user" in session and session["user"] == params["admin_user"]):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")    


@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")



@app.route("/contact", methods = ["GET", "POST"])
def contact():
    if (request.method=="POST"):
        "ADD ENTRY to the Database"
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
        # name = request.form.get("name")
        # name = request.form.get("name")

        entry = Contacts(name = name, email = email, phone_num = phone, message = message, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(f"New Message from {name}", 
                        sender = email,
                        recipients = [params["gmail_user"]],
                        body=f"{message}\nContact Number: {phone}"
                        )

    return render_template("contact.html")

@app.route("/post/<string:post_slug>", methods = ["GET"])
def post(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()

    return render_template("post.html", post = post)

app.run(debug = True)




