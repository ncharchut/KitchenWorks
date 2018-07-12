"""
BEFORE RUNNING:
---------------
1. If not already done, enable the Google Sheets API
   and check the quota for your project at
   https://console.developers.google.com/apis/api/sheets
2. Install the Python client library for Google APIs by running
   `pip install --upgrade google-api-python-client`
"""
from pprint import pprint
from googleapiclient import discovery
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# TODO: Change placeholder below to generate authentication credentials. See
# https://developers.google.com/sheets/quickstart/python#step_3_set_up_the_sample
#
# Authorize using one of the following scopes:
#     'https://www.googleapis.com/auth/drive'
#     'https://www.googleapis.com/auth/drive.file'
#     'https://www.googleapis.com/auth/spreadsheets'
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
store = file.Storage('credentials.json')
credentials = store.get()
if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    credentials = tools.run_flow(flow, store)

service = discovery.build('sheets', 'v4', credentials=credentials)

spreadsheet_body = {
    # TODO: Add desired entries to the request body.
    "range": "A1:A5",
    "majorDimension": "ROWS",
    "values": [
    	["hello", "my", "name", "is", "god"]
    ]
}

request = service.spreadsheets().create(body=spreadsheet_body)
response = request.execute()

# TODO: Change code below to process the `response` dict:
pprint(response)