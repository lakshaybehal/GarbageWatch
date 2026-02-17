from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "garbagewatch_secret"

# ✅ Database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///garbage.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Upload folder
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

# ✅ Admin Users (Secure Hash)
admin_users = {
    "vabek": generate_password_hash("244466666"),
    "lakshay": generate_password_hash("244466666")
}


# ✅ Spot Table
class Spot(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    place_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    phone = db.Column(db.String(15), nullable=False)

    status = db.Column(db.String(20), default="not_cleaned")
    image = db.Column(db.String(200), nullable=True)

    approved = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()


# ✅ Home
@app.route("/")
def home():
    return render_template("index.html")


# ✅ Report Form
@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":

        uploaded_file = request.files["image"]
        filename = None

        if uploaded_file and uploaded_file.filename != "":
            filename = uploaded_file.filename
            uploaded_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        new_spot = Spot(
            place_name=request.form["place_name"],
            description=request.form["description"],
            latitude=float(request.form["latitude"]),
            longitude=float(request.form["longitude"]),
            phone=request.form["phone"],
            status=request.form["status"],
            image=filename,
            approved=False
        )

        db.session.add(new_spot)
        db.session.commit()

        return redirect("/success")

    return render_template("report.html")


# ✅ Popup Page
@app.route("/success")
def success():
    return render_template("success.html")


# ✅ Map Page (Approved Only)
@app.route("/map")
def map_page():
    approved_spots = Spot.query.filter_by(approved=True).all()
    return render_template("map.html", spots=approved_spots)


# ✅ Spot Detail
@app.route("/spot/<int:spot_id>")
def spot_detail(spot_id):
    spot = Spot.query.get(spot_id)
    return render_template("spot_detail.html", spot=spot)


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in admin_users and check_password_hash(admin_users[username], password):
            session["admin_logged_in"] = True
            session["admin_user"] = username
            return redirect("/admin/dashboard")

        error = "Invalid Login ❌"

    return render_template("admin_login.html", error=error)


# ✅ Pending Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    pending_spots = Spot.query.filter_by(approved=False).all()
    return render_template("admin_dashboard.html", spots=pending_spots)


# ✅ Approve Spot
@app.route("/admin/approve/<int:spot_id>")
def approve_spot(spot_id):

    spot = Spot.query.get(spot_id)

    if spot:
        spot.approved = True
        db.session.commit()

    return redirect("/admin/dashboard")


# ✅ Reject Spot
@app.route("/admin/reject/<int:spot_id>")
def reject_spot(spot_id):

    spot = Spot.query.get(spot_id)

    if spot:
        db.session.delete(spot)
        db.session.commit()

    return redirect("/admin/dashboard")


# ✅ NEW: Approved Spots List Page
@app.route("/admin/approved")
def approved_spots_page():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    approved_spots = Spot.query.filter_by(approved=True).all()
    return render_template("admin_approved.html", spots=approved_spots)


# ✅ NEW: Update Spot Status
@app.route("/admin/update_status/<int:spot_id>", methods=["POST"])
def update_status(spot_id):

    spot = Spot.query.get(spot_id)

    if spot:
        spot.status = request.form["status"]
        db.session.commit()

    return redirect("/admin/approved")


# ✅ Logout
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
