"""
Shows basic usage of the Sheets API. Prints values from a Google Spreadsheet.
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from pprint import pprint
from requests import DropdownMenu, LockCells
from task import TaskManager


# Setup the Sheets API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret_3.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

# Call the Sheets API
SPREADSHEET_ID = '1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM'
RANGE_NAME = 'TEST!A2:E2'
result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                             range=RANGE_NAME).execute()


tasks_file = "tasks.csv"
task_manager = TaskManager(tasks_file)
tasks = task_manager.generate_task_fields()
print(tasks)


# dropdown_menu = DropdownMenu("names.csv")
# dropdown_request = dropdown_menu.generate_request(0, 3, 4, 1, 5)

# editors = ["nicholas.charchut@gmail.com"]
# lock_cells = LockCells(editors)
# lock_cells_request = lock_cells.generate_request(0, 5, 6, 0, 5)

# body = {
#         "requests": [dropdown_request, lock_cells_request]
# }
# response = service.spreadsheets() \
#     .batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
# print('{0} cells updated.'.format(len(response.get('replies'))))

# values = result.get('values', [])
