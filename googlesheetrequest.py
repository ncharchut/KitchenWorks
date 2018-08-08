from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from pprint import pprint
from files import names, tasks
from gsheets_time import Month
from request_constants import update_row_request, auto_resize_column_width,\
                              update_spreadsheet_properties, update_spreadsheet_name
from datetime import datetime, timedelta
from totals import CreditTotals
import pickle
from contacts import Contacts


class GSheetsRequest(object):
    """docstring for GSheetsRequest"""
    def __init__(self, editors, names, tasks, spreadsheetId, month_file=None, new_page=False):
        super(GSheetsRequest, self).__init__()
        self.editors = editors
        self.service = None
        self.spreadsheetId = spreadsheetId
        self.write_body = {}
        self.request_body = {}
        self.service = self.start()

        if new_page:
            self.new_page_test()
            self.full_send(request_only=True)

        self.contacts = Contacts(self.get_contact_information(self.spreadsheetId))
        self.totals = CreditTotals(spreadsheetId, self.service, self.contacts)
        self.current_sheet_name, self.current_sheet_id = self.get_sheet_name_and_id(self.spreadsheetId)
        self.months = [Month(self.contacts, tasks, self.current_sheet_id, self.spreadsheetId, self.current_sheet_name,
                           self.editors) if month_file is None else Month.load(month_file)]
        self.recent_month = self.months[0]
        self.sheet_name_date_start = None
        self.sheet_name_date_end = None
        
        self.save()

    def start(self):
        """ Initializes credentials with Google Sheets API. """
        SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
        store = file.Storage('credentials.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('sheets', 'v4', http=creds.authorize(Http()))
        return service

    def update_total(self, full_update=False):
        new_total = CreditTotals(self.spreadsheetId, self.service)

        if full_update:
            for month in self.months:
                month.update_credit_totals(new_total)
        else:
            return self.recent_month.update_credit_totals(new_total)

        # new_totals_request = self.new_total.full_request()
        # self.push_write(new_totals_request)
        # self.full_send_writes()

    def new_page_test(self):
        request = {"addSheet": {
                        "properties": {
                          "title": "New Week"
                        },
                        }}
        self.push(request)

    def lock_past_days(self):
        lock_request = self.recent_month.lock_days_before()
        self.push(lock_request)

    def get_sheet_name_and_id(self, spreadsheetId):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
        sheets = sheet_metadata.get('sheets', '')
        current_sheet = sheets[-1]
        current_sheet_name = current_sheet.get("properties", {}).get("title", -1)
        current_sheet_id = current_sheet.get("properties", {}).get("sheetId", -1)

        return current_sheet_name, current_sheet_id

    def get_contact_information(self, spreadsheetId):
        contact_data = self.service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range="Contacts").execute()

        return contact_data

    def new_week(self):
        # 1. Read in current month sheet
        date_writes, task_writes, cell_updates, properties_request, last_date = self.recent_month.add_week()
        

        if len(self.recent_month.weeks) == 1: # first week added, need to reformat

            clear_request = {
                                "updateCells": 
                                {
                                    "range": 
                                    {
                                        "sheetId": self.recent_month.sheet_id
                                    },
                                    "fields": "userEnteredValue"
                                }
                            }
            self.push(clear_request)
            width_request = auto_resize_column_width(self.recent_month.sheet_id)
            self.push(width_request)
        # new_cells = self.format_cell_updates(cell_updates)

        name_update = self.update_sheet_name(last_date)

        self.push_write(date_writes)
        self.push_write(task_writes)
        self.push(properties_request)
        self.push(cell_updates)
    
        self.full_send()

        self.push(name_update)
        self.full_send(request_only=True)

        # return date_writes, task_writes, cell_updates
        self.save()
        return "New week successfully added."

    def new_month(self):
        # creates a new spreadsheet and shit for a new month
        pass

    def update_sheet_name(self, date):
        if self.sheet_name_date_start is None:
            inferred_start = date - timedelta(days=7)
            self.sheet_name_date_start = inferred_start

        self.sheet_name_date_end = date
        new_name = self.generate_sheet_name()
        self.recent_month.update_name(new_name)
        self.current_sheet_name = new_name

        return update_spreadsheet_name(self.current_sheet_id, new_name)



    def generate_sheet_name(self):
        start = self.sheet_name_date_start.strftime("%m/%d")
        end = self.sheet_name_date_end.strftime("%m/%d")

        return "{0} - {1}".format(start, end)

    def change_font_request(self, font):
        pass

    def push_write(self, request):
        if "valueInputOption" not in self.write_body:
            self.write_body["valueInputOption"] = "USER_ENTERED"
            self.write_body["data"] = [request]
        else:
            self.write_body["data"].append(request)

        return

    def push(self, request):
        if "requests" not in self.request_body:
            self.request_body["requests"] = [request]

        else:
            self.request_body["requests"].append(request)

        return

    def full_send(self, request_only=False):


        response = self.service.spreadsheets() \
            .batchUpdate(spreadsheetId=self.spreadsheetId, body=self.request_body).execute()

        if not request_only:
            response_w = self.service.spreadsheets() \
                .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()

            # print(response_w)

        self.request_body = {}
        self.write_body = {}
        # print(self.request_body) 
        return

    def full_send_writes(self):
        response = self.service.spreadsheets() \
            .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()
        # print('{0} cells updated.'.format(len(response.get('replies')))) 
        self.write_body = {}
        return

    def view_last_task(self):
        if 'requests' not in self.body:
            return {}
        return self.body['requests'][-1]

    def view_last_write(self):
        if 'data' not in self.write_body:
            return {}
        return self.write_body

    def save(self, file="gsheets_obj.pickle"):
        with open(file, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return

    @staticmethod
    def load(file):
        with open(file, 'rb') as handle:
            gsheets = pickle.load(handle)

        gsheets.service = gsheets.start()
        return gsheets 



if __name__ == "__main__":
    # editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
    # spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
    # names = "names.csv"
    # tasks = "tasks.csv"
    # gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId)
    # gsheets.new_week()
    # gsheets.update_total()


    editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
    spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
    gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId, new_page=True)
    gsheets.new_week()
    gsheets.update_total()
