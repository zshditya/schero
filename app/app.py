from flask import Flask, request, jsonify, Blueprint
from .model.prediction import predict, get_scholarship_details
from google.cloud import storage
import pandas as pd
import joblib

app = Flask(__name__)

# Load resources using a Blueprint
resources_bp = Blueprint('resources', __name__)

@resources_bp.record_once
def on_load(state):
    bucket_name = 'adityaschero'
    vectorizer_file_name = 'tfidf_vectorizer.pkl'
    model_file_name = 'tfidf_matrix.pkl'
    data_file_name = 'beasiswa.csv'

    download_file_from_gcs(bucket_name, f'model/{vectorizer_file_name}', f'app/model/{vectorizer_file_name}')
    download_file_from_gcs(bucket_name, f'model/{model_file_name}', f'app/model/{model_file_name}')
    download_file_from_gcs(bucket_name, f'data/{data_file_name}', f'app/data/{data_file_name}')

    state.data_content_based_filtering = pd.read_csv(f'app/data/{data_file_name}')
    state.model_file = f'app/model/{vectorizer_file_name}'
    state.tfidf_vectorizer = joblib.load(state.model_file)

def download_file_from_gcs(bucket_name, source_blob_name, destination_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

app.register_blueprint(resources_bp, url_prefix='/resources')

@app.route('/predict', methods=['POST'])
def predict_scholarships():
    try:
        input_data = request.json
        education = input_data.get('jenjang pendidikan', '')
        funding_type = input_data.get('pendanaan', '')
        continent = input_data.get('benua', '')

        recommendations = predict(education, funding_type, continent, app.data_content_based_filtering)

        result = {"recommendations": recommendations}
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/scholarship_details', methods=['GET'])
def get_details():
    try:
        scholarship_name = request.args.get('scholarship_name', '')
        details = get_scholarship_details(scholarship_name, app.data_content_based_filtering)
        return jsonify(details)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # to run on Google Cloud Platform
    # app.run(port=5000, debug=True)  # to run on local
