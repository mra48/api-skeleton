from src.extensions import db
from flask import jsonify


class Doctor(db.Model):
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String(50), nullable=False)
  working_hours_start = db.Column(db.Time, nullable=False)
  working_hours_end = db.Column(db.Time, nullable=False)

  def json(self):
    return jsonify({
        'id': self.id,
        'name': self.name,
        'working_hours_start': self.working_hours_start.isoformat(),
        'working_hours_end': self.working_hours_end.isoformat()
    })


class Appointment(db.Model):
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
  doctor = db.relationship('Doctor',
                           backref=db.backref('appointments', lazy=True))
  start_time = db.Column(db.DateTime, nullable=False)
  end_time = db.Column(db.DateTime, nullable=False)
  patient = db.Column(db.String(100))
  desc = db.Column(db.String(500))

  def json(self):
    return jsonify({
        'id': self.id,
        'doctor_id': self.doctor_id,
        'start_time': self.start_time.isoformat(),
        'end_time': self.end_time.isoformat(),
        'patient': self.patient,
        'desc': self.desc
    })
