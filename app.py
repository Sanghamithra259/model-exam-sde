from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import mlflow


# --------------------------------
# MLflow Configuration
# --------------------------------

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("Result Processing System")


# --------------------------------
# Flask App Setup
# --------------------------------

app = Flask(__name__, instance_relative_config=True)

app.config["SECRET_KEY"] = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --------------------------------
# Database Models
# --------------------------------

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(200))


class StudentRecord(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    subject = db.Column(db.String(100))

    marks = db.Column(db.Float)

    credits = db.Column(db.Float)

    grade = db.Column(db.String(5))

    gpa = db.Column(db.Float)


# Create tables if not exist
with app.app_context():
    db.create_all()


# --------------------------------
# Home Page (Login Page)
# --------------------------------

@app.route("/")
def home():
    return render_template("login.html")


# --------------------------------
# Signup Page
# --------------------------------

@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():

    username = request.form["username"]
    password = request.form["password"]

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return "User already exists"

    hashed_password = generate_password_hash(password)

    user = User(username=username, password=hashed_password)

    db.session.add(user)
    db.session.commit()

    return redirect("/")


# --------------------------------
# Login
# --------------------------------

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):

        session["user"] = username

        return redirect("/enter")

    return "Invalid login credentials"


# --------------------------------
# Logout
# --------------------------------

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


# --------------------------------
# Enter Marks Page
# --------------------------------

@app.route("/enter")
def enter_marks():

    if "user" not in session:
        return redirect("/")

    return render_template(
        "enter_marks.html",
        username=session["user"]
    )


# --------------------------------
# Submit Marks
# --------------------------------

@app.route("/submit", methods=["POST"])
def submit():

    if "user" not in session:
        return redirect("/")

    name = session["user"]

    subject = request.form["subject"]

    marks = float(request.form["marks"])

    credits = float(request.form["credits"])


    # -------------------------
    # Grade Calculation
    # -------------------------

    if marks >= 90:

        grade_point = 10
        grade = "A+"

    elif marks >= 80:

        grade_point = 9
        grade = "A"

    elif marks >= 70:

        grade_point = 8
        grade = "B"

    elif marks >= 60:

        grade_point = 7
        grade = "C"

    else:

        grade_point = 0
        grade = "F"


    gpa = grade_point


    # -------------------------
    # Save to Database
    # -------------------------

    record = StudentRecord(

        name=name,
        subject=subject,
        marks=marks,
        credits=credits,
        grade=grade,
        gpa=gpa
    )

    db.session.add(record)
    db.session.commit()


    # -------------------------
    # MLflow Logging
    # -------------------------

    with mlflow.start_run(run_name=name + "_" + subject) as run:

        mlflow.log_param("student", name)

        mlflow.log_param("subject", subject)

        mlflow.log_metric("marks", marks)

        mlflow.log_metric("credits", credits)

        mlflow.log_metric("gpa", gpa)

        run_id = run.info.run_id


    return render_template(

        "gradesheet.html",

        record=record,

        run_id=run_id
    )


# --------------------------------
# View Latest Gradesheet
# --------------------------------

@app.route("/gradesheet")
def gradesheet():

    if "user" not in session:
        return redirect("/")

    record = StudentRecord.query.order_by(StudentRecord.id.desc()).first()

    if not record:
        return "No records yet."

    return render_template("gradesheet.html", record=record)

@app.route("/results")
def results():

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    records = StudentRecord.query.filter_by(name=username).all()

    return render_template(
        "results.html",
        records=records,
        username=username
    )


# --------------------------------
# Run Flask Server
# --------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)