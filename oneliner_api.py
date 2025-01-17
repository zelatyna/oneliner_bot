import requests
import logging
import json

API_DATE_FORMAT = '%Y-%m-%d'

class OneLiner_client:
    def __init__(self, host='https://cheesyapp.herokuapp.com/one_liner'):
        self.host = host
        self.headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

    def get_user(self, data):
        user_data ={}
        url = self.host + '/users/'
        params = {}
        if 'phone_number' in data.keys():
            params = ({'phone_number' : data['phone_number']})
        req = requests.get(url=url, params=params, headers=self.headers)
        if req.status_code != 200:
            logging.error(req.text)
        else:
            req_json = req.json()
            if req_json['count'] ==1:
                user_data = req_json['results'][0]
                self.username = user_data['username']
        return user_data


    def post_one_liner(self, data, token):
        files = {}
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml'}
        headers['Authorization'] = "Token {token}".format(token=token)
        post_data = {
            "one_liner_text": data['one_liner_txt'],
            "pub_date": data['date_pub']
        }
        if 'image_path' in data:
            files = {'update_image': open(data['image_path'], 'rb')}


        logging.info(json.dumps(post_data))
        r = requests.post(self.host + '/updates/', data=post_data, headers=headers, files = files)

        if r.status_code != 201:
            logging.error(r.text)
        return r
