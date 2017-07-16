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
    user_id = db.Column(db.Integer)
    time = db.Column(db.DateTime)

    def __init__(self, content, user_id):
        self.content = content
        self.user_id = user_id
        self.time = datetime.now()

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

    c = Chat("Dan's chatting extrvaganza!!!")
    u = User("Dan", "ayyo")
    db.session.add(u)
    u.owned_chats.append(c)


    """
    c1 = Chat("First")
    c2 = Chat("Second")
    db.session.add(c1)
    db.session.add(c2)

    m1 = Message("git", 2)
    print(m1.time)

    c1.message_list.append(Message("ayyo", 0))
    c1.message_list.append(Message("yaao", 1))

    c2.message_list.append(Message("ayyo", 2))
    """

    db.session.commit()


@app.cli.command("check")
def check():

    chats = Chat.query.all()
    for c in chats:
        print("")
        print(c.name)
        for m in c.message_list:
            print(m.content)
            print(m.time)
            print("")


@app.route("/")
def default():
    if "user" in session:
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

    if "user" in session:
        return redirect(url_for("home"))
    
    elif request.method == "POST":
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

    if "user" in session:
        return redirect(url_for("home"))

    elif request.method == "POST":
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

    if "user" not in session:
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
            Chat.query.filter_by(name=user_input).delete()
            db.session.commit()

    chat_list = Chat.query.all()
    return render_template("home.html", chat_list=chat_list, user=user, message=message)


@app.route("/chat/<chat_name>", methods = ["GET", "POST"])
def chat(chat_name):
    if "user" not in session:
        return redirect(url_for("login"))

    chat = Chat.query.filter_by(name = chat_name).first()

    if request.method == "POST":
        chat.message_list.append(Message(request.form["text"], 0))
        db.session.commit()

    return render_template("chat.html", chat=chat)


app.secret_key = "git git git brrrrrwrwrwaaaahh"
