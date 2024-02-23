import json
import openai
from openai import OpenAI
import psycopg2
import boto3
import base64
from botocore.exceptions import ClientError


def get_secret(secret_name):
    secret_name = secret_name
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(e)
    else:
        if "SecretString" in secret_value_response:
            secret = json.loads(secret_value_response["SecretString"])
            return secret
        else:
            decoded_binary_secret = base64.b64decode(
                secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret


def generate_sql_query(natural_language_query, api_key=None):
    prompt = f"""### Task
Generate an SQL read-only query to answer [QUESTION]{natural_language_query}[/QUESTION]

### Instructions
- The query should only perform read operations (SELECT). It should not modify the database (no INSERT, UPDATE, DELETE, etc.).
- Remember that timestamps are in 24 hour format
- Remember that doctor_id is in the format "DM0097"
- Remember that when using a timestamps, don't forget to explicitly typecast with ::timestamp and perform actions

### Database Schema
This query will run on a database whose schema is represented in this string:
CREATE TABLE doctor (
  doctor_id INTEGER PRIMARY KEY, -- Unique ID for each doctor (Ex: d.doctor_id = "DM0097")
  department_name TEXT -- name of department whom this doctor belongs to
  doctor_name TEXT -- Name for each doctor (Starts with Dr. )
);


CREATE TABLE patient (
  umr_no INTEGER PRIMARY KEY, -- Unique ID for each patient
  patient_name VARCHAR(50), -- Name of the patient
  gender VARCHAR(10) -- Gender of patient (Male or Female)
  mobile_no VARCHAR(10) -- Mobile number of patient
  age INTEGER -- Age of patient
);

CREATE TABLE record (
  record_id INTEGER PRIMARY KEY, -- Unique ID for each record
  doctor_id INTEGER, -- ID of the doctor that checked the patient
  umr_no INTEGER,  -- ID of patient whom this record belongs to
  unit_id INTEGER, -- ID of unit the patient is admitted to
  consultation_no VARCHAR(50), -- unique id generated for each consultation
  appointment_date TEXT -- Date on which the patient is appointed to hospital
  visit_type VARCHAR(50) -- Type of visit by patient (NORMAL or REVISIT)
  schedule_start_time TEXT -- Timestamp at which the schedule is started
  created_at TEXT -- Timestamp at which the record is created
  updated_at TEXT -- Timestamp at which the record is updated
  checkin_time TEXT -- Timestamp at which the patient is entered to hospital
  inprogress_time TEXT -- Timestamp at which the patient is appointed to doctor
  checkout_time TEXT -- Timestamp at which the patient is leaved the hospital
  follow_up_date TEXT -- Date at which the patient is instructed to revisit
);

-- record.doctor_id can be joined with doctor.doctor_id
-- record.umr_no can be joined with patient.umr_no

Example:
QUESTION: How many patients did doctor DM0034 checked?
SQL: SELECT COUNT(DISTINCT r.umr_no) AS number_of_patients
FROM record r
JOIN doctor d ON r.doctor_id = d.doctor_id
WHERE d.doctor_id = 'DM0034';

QUESTION: How much time did each patient stayed in hospital?
SQL: SELECT p.patient_name,
       (r.checkout_time::timestamp - r.checkin_time::timestamp) AS total_stay
FROM patient p
JOIN record r ON p.umr_no = r.umr_no;

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{natural_language_query}[/QUESTION]
[SQL]"""

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    response = completion.choices[0].message.content
    return response


def lambda_handler(event, context):
    natural_language_query = event["queryStringParameters"]["query"]
    db_secrets = get_secret("rds!db-32b4142f-1543-4a41-b3f0-d8e4a4672cb0")
    api_secret = get_secret("AuroraChatGPTApiSecret")
    sql_query = generate_sql_query(
        natural_language_query, api_secret["AuroraChatGPTApiSecret"]
    )

    try:
        conn = psycopg2.connect(
            database="Hospital",
            user=db_secrets["username"],
            host="aurora-llm-db.c3li9wy40xse.us-east-1.rds.amazonaws.com",
            password=db_secrets["password"],
            port=5432,
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        result = {"column_names": column_names, "rows": rows}
        conn.close()
    except Exception as e:
        result = "Error: " + str(e)
        conn.close()

    return {"statusCode": 200, "body": json.dumps({"result": result})}