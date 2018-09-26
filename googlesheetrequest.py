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
from task import TaskManager
import schedule, time


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
            self.new_page()
            self.full_send(request_only=True)

        contact_info, task_info = self.get_contact_task_information(self.spreadsheetId)
        self.contacts = Contacts(contact_info)
        self.tasks = TaskManager(task_info)
        self.current_sheet_name, self.current_sheet_id, self.totals_sheet_id = self.get_sheet_name_and_id(self.spreadsheetId)
        self.months = [Month(self.contacts, self.tasks, self.current_sheet_id, self.spreadsheetId, self.current_sheet_name,
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

    def serve(self):
        # 1. Every 3 seconds, update totals.
        # 2. Every Wednesday at 6 PM, generate a new week
        # 2b. When it's a new month, generate a new month.

        # Update service credentials  every hour.
        schedule.every().hour.do(self.reload_credentials)

        # Updates total sheet.
        schedule.every(5).seconds.do(self.update_total)
        schedule.every().hour.do(self.update_total, True)

        # Updates contact information.
        schedule.every().day.do(self.update_contact_info)

        # Creates new week and sends email notifications.
        schedule.every().wednesday.at("18:00").do(self.create_next_kitchenworks)

        # Send email notifications each day. 
        schedule.every().day.at("9:00").do(self.email_alerts)

        # Lock the previous day everyday.
        schedule.every().day.at("11:59").do(self.lock_past_days)

        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except:
                print("Error occurred.")
                return

    def reload_credentials(self):
        self.service = self.start()

    def create_next_kitchenworks(self):
        """ Creates new kitchenwork, whether month or week. """
        new_month = self.determine_if_new_month()

        if new_month:
            self.new_month()

        else:
            self.new_week()


        self.save()

    def determine_if_new_month(self):
        """ Determines if a new month sheet should be created. """
        if self.sheet_name_date_start is None or self.sheet_name_date_end is None:
            return True
        return self.sheet_name_date_start.month != self.sheet_name_date_end.month

    def email_alerts(self):
        
        pass

    def update_contact_info(self):
        """ Updates contact information in the database. """
        contact_info, task_info = self.get_contact_task_information(self.spreadsheetId)
        self.contacts = Contacts(contact_info)
        for month in self.months:
            month.update_contacts(self.contacts)

    def update_total(self, full_update=False):
        """ Updates the credit totals, defaults to updating according only to the most recent month. """
        new_total = CreditTotals(self.spreadsheetId, self.service, self.contacts, self.tasks)

        if full_update:
            for month in self.months:
                month.update_credit_totals(new_total)
        else:
             self.recent_month.update_credit_totals(new_total)

        new_totals_requests = new_total.full_request()
        for request in new_totals_requests:
            self.push_write(request)


        width_request = auto_resize_column_width(self.totals_sheet_id)
        
        self.push(width_request)
        self.full_send()
        return new_totals_requests

    def new_page(self):
        """ Creates a new page. """
        request = {"addSheet": {
                        "properties": {
                          "title": "New Week"
                        },
                    }
                  }
        self.push(request)

    def lock_past_days(self):
        """ Locks previous days so only the previously specified editors can edit. """
        lock_request = self.recent_month.lock_days_before()
        self.push(lock_request)

    def get_sheet_name_and_id(self, spreadsheetId):
        """ Identifies most recent sheet name and ID, as well as the ID
                of the credit total sheet. """
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheetId).execute()
        sheets = sheet_metadata.get('sheets', '')
        current_sheet = sheets[-1]
        current_sheet_name = current_sheet.get("properties", {}).get("title", -1)
        current_sheet_id = current_sheet.get("properties", {}).get("sheetId", -1)
        totals_sheet_id = sheets[0].get("properties", {}).get("sheetId", -1)

        return current_sheet_name, current_sheet_id, totals_sheet_id

    def get_contact_task_information(self, spreadsheetId):
        """ Extracts contact and task information from spreadsheet. """
        data = self.service.spreadsheets().values().batchGet(spreadsheetId=spreadsheetId, ranges=["Contacts", "Tasks"]).execute()
        contact_data, task_data = data['valueRanges']

        return contact_data, task_data

    def new_week(self, base_date=None):
        # 1. Read in current month sheet
        date_writes, task_writes, cell_updates, properties_request, last_date = self.recent_month.add_week(base_date)
        
        width_request = None
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
            
        name_update = self.update_sheet_name(last_date)
        self.push_write(date_writes)
        self.push_write(task_writes)
        self.push(properties_request)
        self.push(cell_updates)

        self.full_send()

        self.push(name_update)
        if width_request is not None:
            self.push(width_request)
        self.full_send(request_only=True)

        self.save()
        return "New week successfully added."

    def new_month(self):
        # 1. Create new page.
        self.new_page()
        self.full_send(request_only=True)

        # 2. Update sheet information.
        self.sheet_name_date_start = None
        self.sheet_name_date_end = None

        # 3. Create new month.
        self.current_sheet_name, self.current_sheet_id, self.totals_sheet_id = self.get_sheet_name_and_id(self.spreadsheetId)
        new_month = Month(self.contacts, self.tasks, self.current_sheet_id, self.spreadsheetId, self.current_sheet_name,
                           self.editors)
        
        self.months.append(new_month)
        self.recent_month = self.months[-1]
        self.save()
        self.new_week()

    def update_sheet_name(self, date):
        # 1. Determine start date for name of sheet.
        if self.sheet_name_date_start is None:
            inferred_start = date - timedelta(days=6)
            self.sheet_name_date_start = inferred_start

        # 2. Adjust end date name of sheet.
        self.sheet_name_date_end = date
        new_name = self.generate_sheet_name()
        self.recent_month.update_name(new_name)
        self.current_sheet_name = new_name

        return update_spreadsheet_name(self.current_sheet_id, new_name)

    def generate_sheet_name(self):
        """ Generates sheet name based on the weeks the month contains. """
        start = self.sheet_name_date_start.strftime("%m/%d")
        end = self.sheet_name_date_end.strftime("%m/%d")

        return "{0} - {1}".format(start, end)

    def change_font_request(self, font):
        pass

    def push_write(self, request):
        """ Pushes cell write requests. """
        if "valueInputOption" not in self.write_body:
            self.write_body["valueInputOption"] = "USER_ENTERED"
            self.write_body["data"] = [request]
        else:
            self.write_body["data"].append(request)

        return

    def push(self, request):
        """ Pushes cell format request. """
        if "requests" not in self.request_body:
            self.request_body["requests"] = [request]

        else:
            self.request_body["requests"].append(request)

        return

    def full_send(self, request_only=False):
        """ Executes requests, defaults to both cell format and write requests. """

        response = self.service.spreadsheets() \
            .batchUpdate(spreadsheetId=self.spreadsheetId, body=self.request_body).execute()

        if not request_only:
            response_w = self.service.spreadsheets() \
                .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()
    
        self.request_body = {}
        self.write_body = {}
        return

    def full_send_writes(self):
        """ Executes cell write requests. """
        response = self.service.spreadsheets() \
            .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()

        self.write_body = {}
        return

    def view_last_task(self):
        """ View most recent cell format request added to the queue. """
        if 'requests' not in self.body:
            return {}
        return self.body['requests'][-1]

    def view_last_write(self):
        """ View most recent cell write request added to the queue. """
        if 'data' not in self.write_body:
            return {}
        return self.write_body

    def save(self, file=None):
        """ Saves the current object. """
        if file is None:
            time = datetime.now()
            file = time.strftime("%m_%d@%H_%M_%S.pickle")

        with open(file, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return

    @staticmethod
    def load(file):
        """ Loads object given filename. """
        with open(file, 'rb') as handle:
            gsheets = pickle.load(handle)

        gsheets.service = gsheets.start()
        return gsheets 



if __name__ == "__main__":
    editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
    spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
    gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId, new_page=True)
    gsheets.new_week()
    gsheets.update_total()
