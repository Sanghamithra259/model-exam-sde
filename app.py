from flask import Flask, render_template, request
import mlflow

# Configure tracking URI to use local SQLite database
mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Optional: name the experiment
mlflow.set_experiment("Result Processing System")

app = Flask(__name__)

# simple in-memory storage
records = []

@app.route("/")
def home():
    return render_template("enter_marks.html")


@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"]
    subject = request.form["subject"]
    marks = float(request.form["marks"])
    credits = float(request.form["credits"])

    # grade logic
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

    record = {
        "name": name,
        "subject": subject,
        "marks": marks,
        "credits": credits,
        "grade": grade,
        "gpa": gpa
    }

    records.append(record)

    # MLflow logging
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


@app.route("/gradesheet")
def gradesheet():

    if len(records) == 0:
        return "No records yet."

    return render_template(
        "gradesheet.html",
        record=records[-1]
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)