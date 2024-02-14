from flask import Blueprint, jsonify, request
from http import HTTPStatus
from src.extensions import db
from src.models import Doctor, Appointment
from datetime import datetime, timedelta

home = Blueprint('appointments', __name__)


# Utility functions for common responses
def response_not_found(message):
  return jsonify({'message': message}), HTTPStatus.NOT_FOUND


def response_bad_request(message):
  return jsonify({'message': message}), HTTPStatus.BAD_REQUEST


def response_created(data):
  return jsonify(data), HTTPStatus.CREATED


def response_ok(data):
  return jsonify(data), HTTPStatus.OK


def is_within_working_hours(start_time, end_time, doctor):
  return start_time.time() >= doctor.working_hours_start and end_time.time(
  ) <= doctor.working_hours_end


def has_appointment_conflict(doctor_id, start_time, end_time):
  conflict_count = Appointment.query.filter(
      Appointment.doctor_id == doctor_id, Appointment.end_time > start_time,
      Appointment.start_time < end_time).count()
  return conflict_count > 0


def convert_working_hours(start, end):
  return (datetime.strptime(start,
                            '%H:%M').time(), datetime.strptime(end,
                                                               '%H:%M').time())


@home.route('/appointments', methods=['POST'])
def create_appointment():
  data = request.json
  doctor_id = data.get('doctor_id')
  patient = data.get('patient')
  desc = data.get('desc')
  start_time = datetime.fromisoformat(data.get('start_time'))
  end_time = datetime.fromisoformat(data.get('end_time'))

  doctor = Doctor.query.get(doctor_id)
  if not doctor:
    return response_not_found('Doctor not found.')

  if not is_within_working_hours(start_time, end_time, doctor):
    return response_bad_request(
        'Appointment is outside doctor\'s working hours.')

  if has_appointment_conflict(doctor_id, start_time, end_time):
    return response_bad_request(
        'Appointment conflicts with existing appointment.')

  new_appointment = Appointment(doctor_id=doctor_id,
                                start_time=start_time,
                                end_time=end_time,
                                patient=patient,
                                desc=desc)
  db.session.add(new_appointment)
  db.session.commit()
  return response_created({'id': new_appointment.id})


@home.route('/appointments/<doctor_id>', methods=['GET'])
def get_appointments(doctor_id):
  start_time = request.args.get('start_time')
  end_time = request.args.get('end_time')

  if not start_time or not end_time:
    return response_bad_request(
        'Both start_time and end_time are required parameters.')

  start_time = datetime.fromisoformat(start_time)
  end_time = datetime.fromisoformat(end_time)

  doctor = Doctor.query.get(doctor_id)
  if not doctor:
    return response_not_found('Doctor not found.')

  if not is_within_working_hours(start_time, end_time, doctor):
    return response_bad_request(
        'Requested time window is outside doctor\'s working hours.')

  appointments = Appointment.query.filter(
      Appointment.doctor_id == doctor_id,
      Appointment.end_time >
      start_time,  # Appointment ends after the start of the range
      Appointment.start_time <
      end_time  # Appointment starts before the end of the range
  ).all()

  appointments_data = [{
      'start_time': appointment.start_time.isoformat(),
      'end_time': appointment.end_time.isoformat()
  } for appointment in appointments]
  return response_ok(appointments_data)


@home.route('/appointments/first-available/<doctor_id>', methods=['GET'])
def get_first_available_appointment(doctor_id):
  doctor = Doctor.query.get(doctor_id)
  if not doctor:
    return response_not_found('Doctor not found.')

  current_time = datetime.combine(datetime.today(), doctor.working_hours_start)
  while current_time.time() <= doctor.working_hours_end:
    end_time = current_time + timedelta(
        minutes=15)  # Assuming min appointment time is 15 min
    if not has_appointment_conflict(doctor_id, current_time, end_time):
      return response_ok({
          'start_time': current_time.isoformat(),
          'end_time': end_time.isoformat()
      })
    current_time += timedelta(
        minutes=15)  # Move to the next potential appointment

  return response_not_found('No available appointments found.')


### ENDPOINT FOR TESTS ###
@home.route('/doctors', methods=['POST'])
def add_doctor():
  data = request.json
  name = data.get('name')
  working_hours_start, working_hours_end = convert_working_hours(
      data.get('working_hours_start'), data.get('working_hours_end'))

  if not name or not working_hours_start or not working_hours_end:
    return response_bad_request('Missing required fields.')

  new_doctor = Doctor(name=name,
                      working_hours_start=working_hours_start,
                      working_hours_end=working_hours_end)
  db.session.add(new_doctor)
  db.session.commit()

  return response_created({'id': new_doctor.id})
