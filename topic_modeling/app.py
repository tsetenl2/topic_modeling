from flask import Flask, request, jsonify
from flask_cors import CORS
from os.path import dirname, realpath
from os import listdir
from analyze_documents import build_lda_model

app = Flask(__name__)
CORS(app)


def json_response(status_code, data):
    res = jsonify(data)
    res.status_code = status_code
    return res


@app.route('/get_CIKs', methods=['GET'])
def available_CIKs():
    path = dirname(realpath(__file__)) + "/data/14d9"
    CIKs = listdir(path)
    return json_response(200, CIKs)


@app.route('/get_topics', methods=['GET'])
def get_topics():
    CIKs = request.args.getlist('CIKs')
    num_topics = request.args.get('num_topics')
    ngram_num = request.args.get('ngram_num')
    topic_data = build_lda_model(CIKs, int(num_topics), int(ngram_num))
    return json_response(200, topic_data)


@app.route('/')
def index():
    return "<h1>Topic Modeling API</h1>"


if __name__ == '__main__':
    app.run(threaded=True)