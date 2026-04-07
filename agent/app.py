from flask import  Flask, request, jsonify, render_template
from models.models import Job,Appointment,User,db 
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "..", "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DB_PATH = os.path.join(INSTANCE_DIR, "revy.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

@app.route("/")
def index():
    return render_template("index.html")


# جيب كل الوظايف
@app.route("/jobs", methods=["GET"])
def get_jobs():
    jobs = Job.query.all()
    return jsonify([{
        "id":           j.id,
        "job_name":     j.job_name,
        "description":  j.description,
        "is_available": j.is_available
    } for j in jobs])


# عدّل وظيفة
@app.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    job  = Job.query.get_or_404(job_id)
    data = request.json

    if "job_name"     in data: job.job_name     = data["job_name"]
    if "description"  in data: job.description  = data["description"]
    if "is_available" in data: job.is_available = data["is_available"]

    db.session.commit()
    return jsonify({"message": "updated ✅"})


# اضف وظيفة جديدة
@app.route("/jobs", methods=["POST"])
def add_job():
    data = request.json
    job  = Job(
        job_name     = data["job_name"],
        description  = data["description"],
        is_available = data.get("is_available", True)
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "added ✅", "id": job.id})


# احذف وظيفة
@app.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "deleted ✅"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)