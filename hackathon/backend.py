from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_BINDS'] = {
    'copied': 'mysql://root:anjanawatal%40240405@127.0.0.1:3306/copied'
}
db = SQLAlchemy(app)


# Define the models
class patient(db.Model):
    __bind_key__ = 'copied'
    id = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    phoneNumber = db.Column(db.String(15))
    emailid = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)


class beds(db.Model):
    __bind_key__ = 'copied'
    wardID = db.Column(db.String(50), primary_key=True)
    totalNumberOfBeds = db.Column(db.Integer, nullable=False)
    bedsAvailable = db.Column(db.Integer, nullable=False)


class bed_ids(db.Model):
    __bind_key__ = 'copied'
    bedID = db.Column(db.String(50), primary_key=True)
    wardID = db.Column(db.String(50), db.ForeignKey('beds.wardID'))
    patientID = db.Column(db.String(50), nullable=True)


class wards(db.Model):
    __bind_key__='copied'
    wardID = db.Column(db.String(10), primary_key=True)
    roomType = db.Column(db.String(50))
    numberOfRoomsAvailable = db.Column(db.Integer)

class waitlist(db.Model):
    __bind_key__ = 'copied'
    patientID = db.Column(db.String(50),primary_key=True, nullable=False)
    wardID = db.Column(db.String(50), db.ForeignKey('wards.wardID'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Index route
@app.route('/')
def index():
    if "user" in session:
        return render_template("index.html", visited=1)
    return render_template("index.html")


# Signup route
@app.route('/Signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        phoneNumber = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not phoneNumber or not email or not password:
            flash("All fields are required!")
            return render_template("Signup.html", visited=0)

        id = str(uuid.uuid4())
        user = patient.query.filter_by(emailid=email).first()
        if user:
            flash("Email already exists. Please use a different email.")
            return render_template("Signup.html", visited=0)
        else:
            new_user = patient(
                id=id,
                name=name,
                password=password,
                phoneNumber=phoneNumber,
                emailid=email,
            )
            db.session.add(new_user)
            db.session.commit()
            session['user'] = name
            return render_template('index.html', visited=1)
    return render_template("Signup.html", visited=0)


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form.get('userID')
        password = request.form.get('password')
        join_as = request.form.get('joinAs')
        ad = 1 if join_as == 'Admin' else 0

        if not userid or not password:
            flash("Both fields are required!")
            return render_template("login.html")

        user = patient.query.filter_by(id=userid).first()
        if user is None:
            flash("User ID not found. Please create an account first.")
            return render_template("login.html")
        elif user.password != password:
            flash("Wrong username or password.")
            return render_template("login.html")
        else:
            session['user'] = user.name
            if ad == 1:
                return render_template("discharge.html")
            return render_template('index.html', visited=1)
    return render_template("login.html")


# Logout route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('index.html', visited=0)


# Bed booking route
@app.route('/bed', methods=['GET', 'POST'])
def book_bed():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        ward_id = request.form.get('ward_id')  # Assuming you're getting this from the form

        if not patient_id or not ward_id:
            flash('Both Patient ID and Ward ID are required.')
            return render_template('bed.html')

        # Check if the patient exists in the bed_ids table and find a free bed in the given ward
        bed_entry = bed_ids.query.filter_by(wardID=ward_id,patientID=patient_id).first()

        if bed_entry:
            # Assign the bed to the patient
            response=bed_ids(wardID=ward_id,patientID=patient_id,bedID="B021_W009")
            db.session.add(response)
            db.session.commit()

            # Update the available beds count in the wards table
            ward = beds.query.filter_by(wardID=ward_id).first()
            waitlist1=ward.bedsAvailable
            if ward:
                ward.bedsAvailable -= 1
                db.session.commit()
                flash(f"Bed assigned to patient {patient_id} in ward {ward_id}.")
            else:
                flash(f"Ward {ward_id} not found.")

        # Fetch all available beds and pass to the template
        beds_data = beds.query.all()
        return render_template('bed.html', beds_data=beds_data)

    # Fetch all available beds and pass to the template for GET requests
    beds_data = beds.query.all()
    available=beds.query.all()
    return render_template('bed.html', beds_data=beds_data,waitlist=available)


# Discharge route
@app.route('/discharge', methods=['GET', 'POST'])
def discharge():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')

        if not patient_id:
            flash('Patient ID is missing')
            return render_template("discharge.html")

        # Find the bed assigned to the patient
        patient_bed = bed_ids.query.filter_by(patientID=patient_id).first()
        if patient_bed:
            ward_id = patient_bed.wardID
            bed_id = patient_bed.bedID

            # Delete patient bed assignment
            db.session.delete(patient_bed)

            # Update available beds count in the ward
            ward = beds.query.filter_by(wardID=ward_id).first()
            if ward:
                ward.bedsAvailable += 1

            # Check if anyone is on the waitlist for this ward
            waitlisted_patient = waitlist.query.filter_by(wardID=ward_id).order_by(waitlist.timestamp).first()
            if waitlisted_patient:
                # Assign the bed to the waitlisted patient
                new_bed_assignment = bed_ids(
                    bedID=bed_id,
                    wardID=ward_id,
                    patientID=waitlisted_patient.patientID
                )
                db.session.add(new_bed_assignment)

                # Decrease available bed count after assignment
                ward.bedsAvailable -= 1

                # Remove patient from the waitlist
                db.session.delete(waitlisted_patient)

                flash(f"Patient {waitlisted_patient.patientID} assigned from the waitlist")

            # Commit all changes at once
            db.session.commit()

            flash(f"Patient {patient_id} discharged")
        else:
            flash('No bed found for this patient ID.')

    return render_template('discharge.html')

@app.route('/handle',methods=['GET', 'POST'])
def handlewaitlist():
    if request.method=='POST':
        patient_id = request.form.get('patient_id')
        ward_id = request.form.get('ward_id')
        entry=waitlist(patientID=patient_id,wardID=ward_id)
        db.session.add(entry)
        db.session.commit()
        flash("you have beddn added to the waitlist")
        beds_data=beds.query.all()

        return render_template("bed.html",beds_data=beds_data)

# Other routes
@app.route('/opd')
def opd():
    return render_template("opd.html")

@app.route('/pharma')
def pharma():
    return render_template("pharmacy.html")


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
