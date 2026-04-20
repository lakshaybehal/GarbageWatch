from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.secret_key = "garbagewatch_secret"

# ✅ EMAIL CONFIG
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'projectgarbagewatch@gmail.com'
app.config['MAIL_PASSWORD'] = 'jqwr hnzc pprq qmix'  # no spaces

mail = Mail(app)

# ✅ DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///garbage.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ UPLOAD FOLDER
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

# ✅ ADMIN USERS
admin_users = {
    "vabek": generate_password_hash("244466666"),
    "lakshay": generate_password_hash("244466666")
}

# ✅ MODEL
class Spot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    status = db.Column(db.String(20), default="not_cleaned")
    image = db.Column(db.String(200))
    approved = db.Column(db.Boolean, default=False)

# ✅ CREATE DB
with app.app_context():
    db.create_all()

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- REPORT ---------------- #

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        print("vabek")
        try:
            uploaded_file = request.files["image"]
            filename = None

            if uploaded_file and uploaded_file.filename != "":
                filename = uploaded_file.filename
                uploaded_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            place_name = request.form["place_name"]
            description = request.form["description"]
            email = request.form["email"]
            phone = request.form["phone"]
            latitude = float(request.form["latitude"])
            longitude = float(request.form["longitude"])
            status = request.form["status"]

            # ✅ VALIDATION
            if not phone.isdigit() or len(phone) != 10:
                return "⚠️ Invalid phone number!"

            if "@" not in email or "." not in email:
                return "⚠️ Invalid email!"

            # ✅ DUPLICATE CHECK
            existing = Spot.query.filter_by(latitude=latitude, longitude=longitude).first()
            if existing:
                return "⚠️ Location already reported!"

            # ✅ SAVE TO DB
            new_spot = Spot(
                place_name=place_name,
                description=description,
                latitude=latitude,
                longitude=longitude,
                phone=phone,
                email=email,
                status=status,
                image=filename,
                approved=False
            )

            db.session.add(new_spot)
            db.session.commit()

            # ✅ SEND EMAIL (THIS WAS MISSING ❗)
            msg = Message(
                subject="Garbage Report Submitted",
                sender='projectgarbagewatch@gmail.com',
                recipients=[email]
            )

            msg.body = f"""
Hello,

Your garbage report has been submitted successfully.

Location: {place_name}
Status: {status}

Thank you for helping keep the city clean 🌱

- GarbageWatch Team
"""

            mail.send(msg)

            print("✅ EMAIL SENT")

            return redirect("/success")

        except Exception as e:
            print("❌ ERROR:", e)
            return "Something went wrong (check terminal)"

    return render_template("report.html")

@app.route("/success")
def success():
    return render_template("success.html")

# ---------------- MAP ---------------- #

@app.route("/map")
def map_page():
    spots = Spot.query.filter_by(approved=True).all()
    return render_template("map.html", spots=spots)

@app.route("/spot/<int:spot_id>")
def spot_detail(spot_id):
    spot = Spot.query.get(spot_id)
    return render_template("spot_detail.html", spot=spot)

# ---------------- ADMIN ---------------- #

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in admin_users and check_password_hash(admin_users[username], password):
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")

        error = "Invalid Login ❌"

    return render_template("admin_login.html", error=error)

@app.route("/admin/approve/<int:spot_id>")
def approve_spot(spot_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spot = Spot.query.get(spot_id)
    if spot:
        spot.approved = True
        db.session.commit()

    return redirect("/admin/dashboard")


@app.route("/admin/reject/<int:spot_id>")
def reject_spot(spot_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spot = Spot.query.get(spot_id)
    if spot:
        db.session.delete(spot)
        db.session.commit()

    return redirect("/admin/dashboard")
@app.route("/admin/update_status/<int:spot_id>", methods=["POST"])
def update_status(spot_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spot = Spot.query.get(spot_id)

    if spot:
        spot.status = request.form["status"]
        db.session.commit()

    return redirect("/admin/approved")
@app.route("/admin/edit/<int:spot_id>", methods=["GET", "POST"])
def edit_spot(spot_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spot = Spot.query.get(spot_id)

    if request.method == "POST":
        spot.place_name = request.form["place_name"]
        spot.description = request.form["description"]
        spot.latitude = float(request.form["latitude"])
        spot.longitude = float(request.form["longitude"])
        spot.status = request.form["status"]

        image = request.files["image"]

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            spot.image = filename

        db.session.commit()

        return redirect("/admin/approved")

    return render_template("edit_spot.html", spot=spot)
@app.route("/admin/delete/<int:spot_id>")
def delete_spot(spot_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spot = Spot.query.get(spot_id)

    if spot:
        db.session.delete(spot)
        db.session.commit()

    return redirect("/admin/approved")
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    spots = Spot.query.filter_by(approved=False).all()
    return render_template("admin_dashboard.html", spots=spots)
@app.route("/admin/vabek")
def admin_vabek():
    return render_template("admin_vabek.html")

@app.route("/admin/approved")
def approved_spots_page():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    approved_spots = Spot.query.filter_by(approved=True).all()
    return render_template("admin_approved.html", spots=approved_spots)
@app.route("/admin/lakshay")
def admin_lakshay():
    return render_template("admin_lakshay.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)