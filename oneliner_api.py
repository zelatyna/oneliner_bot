import requests
import logging
import json

API_DATE_FORMAT = '%Y-%m-%d'

class OneLiner_client:
    def __init__(self, host='http://localhost:8000/one_liner'):
        self.host = host
        self.token = None

    def is_auth(self):
        return self.token is not None

    def fetch_token(self, data):
        url = self.host + '/api-token-auth/'
        r = requests.post(url, json=data)
        if r.status_code != 200:
            logging.error(r.text)
        else:
            r_json = r.json()
            self.token = r_json['token']

        return self.token


    def post_one_liner(self, data):
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        headers['Authorization'] = "Token {token}".format(token=self.token)
        post_data = {
            "one_liner_text": data['one_liner_txt'],
            "pub_date": data['date_pub'],
            "user_id": 2
        }


        logging.info(json.dumps(post_data))
        r = requests.post(self.host + '/updates/', json=post_data, headers=headers)

        if r.status_code != 201:
            logging.error(r.text)
        return r
