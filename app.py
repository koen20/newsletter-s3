import os
import time
import boto3
import flask
from botocore.config import Config
from flask import Flask, render_template, request, redirect
from werkzeug.utils import secure_filename
import json

if not os.path.exists('upload'):
    os.makedirs('upload')


def get_s3_resource(endpoint, key_id, application_key):
    s3 = boto3.resource(service_name='s3',
                        endpoint_url=endpoint,
                        aws_access_key_id=key_id,
                        aws_secret_access_key=application_key,
                        config=Config(
                            signature_version='s3v4',
                        ))
    return s3


def get_s3_client(endpoint, key_id, application_key):
    s3 = boto3.client(service_name='s3',
                      endpoint_url=endpoint,
                      aws_access_key_id=key_id,
                      aws_secret_access_key=application_key)
    return s3


bucket = os.environ['bucket']
s3_client = get_s3_client(os.environ['endpoint'], os.environ['access_key'], os.environ['secret_access_key'])
s3_resource = get_s3_resource(os.environ['endpoint'], os.environ['access_key'], os.environ['secret_access_key'])

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main_page():
    latest_json = []
    result = s3_client.list_objects_v2(Bucket=bucket, Prefix="newsletters.json")

    if 'Contents' in result:
        print("Key exists in the bucket.")
        newsletters = s3_client.get_object(Bucket=bucket, Key='newsletters.json')
        files_json = json.loads(newsletters['Body'].read().decode("utf-8"))
    else:
        print("Key doesn't exist in the bucket.")
        files_json = []

    error = ''
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)

        files = flask.request.files.getlist("file")
        for file in files:
            if len(file.filename) > 0:
                filename = secure_filename(file.filename)
                filename_stripped = file.filename.rsplit('.', 1)[0]
                file.save(os.path.join("upload/", filename))
                files_json.append({"name": filename_stripped, "file_name": filename, "timestamp": time.time()})
                latest_json.append({"name": filename_stripped, "file_name": filename, "timestamp": time.time()})
                s3_client.upload_file(
                    os.path.join("upload/", filename),
                    bucket,
                    "newsletters/" + filename,
                    ExtraArgs={'ContentType': 'application.pdf'}
                )
            else:
                error = 'Ongeldig bestand.'

        upload_result = s3_resource.Object(bucket, 'newsletters.json').put(Body=json.dumps(files_json))
        upload_result2 = s3_resource.Object(bucket, 'newsletters_latest.json').put(Body=json.dumps(latest_json))
        assert upload_result["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert upload_result2["ResponseMetadata"]["HTTPStatusCode"] == 200

    return render_template("index.html", error=error)
