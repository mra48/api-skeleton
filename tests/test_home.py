from datetime import datetime, timedelta
from http import HTTPStatus


def add_doctor(client):
  new_doctor_data = {
      'name': 'Strange',
      'working_hours_start': '09:00',
      'working_hours_end': '17:00',
  }

  client.post('/doctors', json=new_doctor_data)


def create_appointment(client):
  start_time = datetime.now().replace(hour=10,
                                      minute=00,
                                      second=0,
                                      microsecond=0)
  end_time = start_time + timedelta(hours=1)
  appointment_data = {
      'doctor_id': 1,
      'start_time': start_time.isoformat(),
      'end_time': end_time.isoformat(),
      'patient': 'patient',
      'desc': 'desc'
  }
  client.post('/appointments', json=appointment_data)


def test_create_appointment_within_working_hours(client):
  add_doctor(client)  # Will create doctor with id 1
  doctor_id = 1
  start_time = datetime.now().replace(
      hour=9, minute=0, second=0,
      microsecond=0)  # 9 AM is within working hours
  end_time = start_time + timedelta(
      hours=1)  # 10 AM, still within working hours
  response = client.post('/appointments',
                         json={
                             'doctor_id': doctor_id,
                             'start_time': start_time.isoformat(),
                             'end_time': end_time.isoformat(),
                             'patient': 'patient',
                             'desc': ''
                         })
  assert response.status_code == HTTPStatus.CREATED


def test_create_appointment_outside_working_hours(client):
  add_doctor(client)  # Will create doctor with id 1
  doctor_id = 1
  start_time = datetime.now().replace(
      hour=6, minute=0, second=0,
      microsecond=0)  # 6 AM is outside working hours
  end_time = start_time + timedelta(
      hours=1)  # 7 AM, still outside working hours
  response = client.post('/appointments',
                         json={
                             'doctor_id': doctor_id,
                             'start_time': start_time.isoformat(),
                             'end_time': end_time.isoformat(),
                             'patient': 'patient',
                             'desc': ''
                         })
  assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_conflicting_appointment(client):
  add_doctor(client)  # Will create doctor with id 1
  create_appointment(client)  # Setup appointment between 10 AM and 11 AM
  doctor_id = 1  # Use the same doctor_id
  start_time = datetime.now().replace(
      hour=10, minute=30, second=0,
      microsecond=0)  # This time overlaps with the existing appointment
  end_time = start_time + timedelta(hours=1)  # 11:30 AM
  response = client.post('/appointments',
                         json={
                             'doctor_id': doctor_id,
                             'start_time': start_time.isoformat(),
                             'end_time': end_time.isoformat(),
                             'patient': 'patient',
                             'desc': ''
                         })
  assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_appointments_within_requested_time_window(client):
  add_doctor(client)  # Will create doctor with id 1
  create_appointment(client)  # Setup appointment between 10 AM and 11 AM
  start_time = datetime.now().replace(
      hour=10, minute=00, second=0,
      microsecond=0)  # This time overlaps with the existing appointment
  end_time = start_time + timedelta(hours=1)  # 11:00 AM
  response = client.get(
      f'/appointments/1?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}'
  )
  assert response.status_code == HTTPStatus.OK


def test_get_first_available_appointment(client):
  add_doctor(client)  # Will create doctor with id 1
  create_appointment(client)  # Setup appointment between 10 AM and 11 AM
  response = client.get('/appointments/first-available/1')
  assert response.status_code == HTTPStatus.OK, "Expected HTTPStatus.OK but got {}".format(
      response.status_code)


def test_no_available_appointments_outside_working_hours(client):
  add_doctor(client)  # Will create doctor with id 1
  doctor_id = 1
  response = client.get(f'/appointments/first-available/{doctor_id}')
  data = response.get_json()
  start_time = datetime.fromisoformat(data['start_time'])
  assert start_time.time() >= datetime.now().time()
  assert response.status_code == HTTPStatus.OK


def test_appointment_starts_at_end_of_working_hours(client):
  add_doctor(client)  # Will create doctor with id 1
  start_time = datetime.now().replace(hour=16, minute=00)
  end_time = start_time + timedelta(hours=1)  # 17:00 to 18:00
  response = client.post('/appointments',
                         json={
                             'doctor_id': 1,
                             'start_time': start_time.isoformat(),
                             'end_time': end_time.isoformat(),
                             'patient': 'patient',
                             'desc': ''
                         })
  assert response.status_code == HTTPStatus.BAD_REQUEST


def test_appointment_ends_at_start_of_working_hours(client):
  add_doctor(client)  # Will create doctor with id 1
  start_time = datetime.now().replace(hour=8, minute=00)  # 08:00 to 09:00
  end_time = start_time + timedelta(hours=1)
  response = client.post('/appointments',
                         json={
                             'doctor_id': 1,
                             'start_time': start_time.isoformat(),
                             'end_time': end_time.isoformat(),
                             'patient': 'patient',
                             'desc': ''
                         })
  assert response.status_code == HTTPStatus.BAD_REQUEST


def test_multiple_appointments_within_time_window(client):
  add_doctor(client)  # Will create doctor with id 1
  create_appointment(client)  # First appointment from 10:00 to 11:00
  # Add a second appointment from 11:00 to 12:00
  start_time = datetime.now().replace(hour=11, minute=00)
  end_time = start_time + timedelta(hours=1)
  client.post('/appointments',
              json={
                  'doctor_id': 1,
                  'start_time': start_time.isoformat(),
                  'end_time': end_time.isoformat(),
                  'patient': 'patient2',
                  'desc': ''
              })
  # Fetch appointments from 10:00 to 12:00
  response = client.get(
      f'/appointments/1?start_time={datetime.now().replace(hour=10, minute=00).isoformat()}&end_time={datetime.now().replace(hour=12, minute=00).isoformat()}'
  )
  assert response.status_code == HTTPStatus.OK
  appointments = response.get_json()
  assert len(appointments) == 2  # Expecting 2 appointments in the response
