import json
from flask import Flask, request, abort, url_for, redirect, session, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    message_list = db.relationship("Message", backref="chat", lazy="dynamic")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, name):
        self.name = name

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300))
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"))

    def __init__(self, content):
        self.content = content

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    owned_chats = db.relationship("Chat", backref="user", lazy="dynamic")

    def __init__(self, name, password):
        self.name = name
        self.password = password


@app.cli.command("initdb")
def initdb_command():
    db.drop_all()
    db.create_all()

    db.session.commit()


@app.route("/")
def default():
    
    if (logged_in()):
        return redirect(url_for("home"))
    else: 
        return redirect(url_for("login"))


@app.route("/logout/")
def logout():
    if "user" in session:
        session.clear()
    return redirect(url_for("login"))


@app.route("/login/", methods = ["GET", "POST"])
def login():
    message = ""

    if (logged_in()):
        return redirect(url_for("home"))
    
    if request.method == "POST":
        user = User.query.filter_by(name=request.form["user"]).first()
        if user:
            if request.form["pass"] == user.password:
                session["user"] = request.form["user"]
                return redirect(url_for("home"))
            else:
                message = "Invalid credentials"
        else:
            message = "Invalid credentials"

    return render_template("login.html", message=message)


@app.route("/signup/", methods = ["GET", "POST"])
def signup():
    message = ""

    if (logged_in()):
        return redirect(url_for("home"))

    if request.method == "POST":
        if not User.query.filter_by(name=request.form["user"]).all():
            db.session.add(User(request.form["user"], request.form["pass"]))
            db.session.commit()
            message = "New user added"
        else:
            message = "Username already in use"

    return render_template("signup.html", message=message)



@app.route("/chat/", methods = ["GET", "POST"])
def home():
    message = ""

    if (not logged_in()):
        return redirect(url_for("login"))

    user = User.query.filter_by(name=session["user"]).first()

    if request.method == "POST":
        user_input = next(iter(request.form.values()))
        if request.form.get("chat_name"):
            if not Chat.query.filter_by(name=request.form["chat_name"]).all():
                user.owned_chats.append(Chat(request.form["chat_name"]))
                db.session.commit()
            else:
                message = "Chat name already in use"
        else:
            chat = Chat.query.filter_by(name=user_input).first()
            user.owned_chats.remove(chat)
            db.session.delete(chat)
            db.session.commit()

    chat_list = Chat.query.all()
    return render_template("home.html", chat_list=chat_list, user=user, message=message)


@app.route("/chat/<chat_name>")
def chat(chat_name):

    if (not logged_in()):
        return redirect(url_for("login"))

    chat = Chat.query.filter_by(name = chat_name).first()

    session["chat_name"] = chat_name
    session["last_message"] = chat.message_list.count() - 1

    return render_template("chat.html", chat=chat)


@app.route("/chat/<chat_name>/new_message", methods=["POST"])
def add(chat_name):

    if (not logged_in()):
        return

    chat = Chat.query.filter_by(name=chat_name).first()
    text = next(iter(request.form.values()))
    chat.message_list.append(Message(text))
    db.session.commit()
    return "OK!"


@app.route("/chat/<chat_name>/messages")
def get_messages(chat_name):

    if (not logged_in()):
        return

    if "chat_name" in session:
        if session["chat_name"] != chat_name:
            session["chat_name"] = chat_name
            session["last_message"] = len(chat.message_list)
    else:
        session["chat_name"] = chat_name
        session["last_message"] = len(chat.message_list)
        
    chat = Chat.query.filter_by(name=chat_name).first()
    if chat:
        messages = chat.message_list
        messages = [m.content for m in messages]
        message_list = []
        for i in range(session["last_message"] + 1, len(messages)):
            message_list.append(messages[i])
        # print("User:                ", session["user"])
        # print("Last message index:  ", session["last_message"])
        session["last_message"] = len(messages) - 1
        # print("New message index:   ", session["last_message"])
        # print("Messages to display: ", len(message_list))
        return json.dumps(message_list)
    else:
        return "It's gone!" 


def logged_in():
    if "user" in session:
        if not User.query.filter_by(name=session["user"]).first():
            session.clear()
            return False 
        else:
            return True
    else:
        return False


app.secret_key = "git git git brrrrrwrwrwaaaahh"
