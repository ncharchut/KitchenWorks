from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from pprint import pprint
from requests import DropdownMenu, LockCells
from task import TaskManager
from files import names, tasks
import datetime

class GSheetsRequest(object):
    """docstring for GSheetsRequest"""
    def __init__(self, editors, root_location, spreadsheetId):
        super(GSheetsRequest, self).__init__()
        self.editors = editors
        self.root_location = root_location
        self.service = None
        self.tasks = TaskManager(tasks)
        self.dropdown = DropdownMenu(names)
        self.lockcells = LockCells(self.editors)
        self.spreadsheetId = spreadsheetId
        self.write_body = {}
        self.request_body = {}

    def start(self):
        """ Initializes credentials with Google Sheets API. """
        SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
        store = file.Storage('credentials.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret_3.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('sheets', 'v4', http=creds.authorize(Http()))
        self.service = service

        return 1

    def new_week_template(self, week_number):
        # 1. Read in current month sheet
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheetId).execute()
        sheets = sheet_metadata.get('sheets', '')
        current_sheet = sheets[-1]
        current_sheet_name = current_sheet.get("properties", {}).get("title", -1)
        current_sheet_id = current_sheet.get("properties", {}).get("sheetId", -1)

        # 2. Find location for next write using week_number
        TASK_OFFSET = 4
        new_location = (week_number - 1) * (len(self.tasks) + TASK_OFFSET)

        if week_number == 1:
            # A. Clear the sheet.
            clear_request = {
                                "updateCells": 
                                {
                                    "range": 
                                    {
                                        "sheetId": current_sheet_id
                                    },
                                    "fields": "userEnteredValue"
                                }
                            }
            self.push(clear_request)

            # B. Lock the sheet.
            # lock_sheet_request = self.lockcells.generate_lock_sheet_request(current_sheet_id)
            # self.push(lock_sheet_request)

        # 3. Generate new week body and write it there
        values, schedule_dict = self.tasks.generate_task_fields()
        write_request, lockdown_request = self.generate_write_request(values, current_sheet_name, current_sheet_id, new_location, schedule_dict)
        self.push_write(write_request)
        self.push(lockdown_request)

    def generate_write_request(self, values, sheet_name, sheet_id, location, schedule_dict):
        """ Generates write request and blacks out the correct cells according
                to the schedule dictionary. """

        # 1. Generate requests for tasks and dates
        write_tasks_request = self.generate_task_write_request(values, sheet_name, location)
        write_dates_request = self.generate_dates_write_request(sheet_name, location, schedule_dict)
        blackout_request, lockdown_request = self.generate_blackout_request(sheet_id, location)


        request = [write_tasks_request,
                   write_dates_request]

        return request, blackout_request

    def generate_task_write_request(self, values, sheet_name, location):
        # 1. Generate write request for tasks
        root = location + 2
        write_tasks_range = "{0}!A{2}:A{1}".format(sheet_name, len(values) + root, root)
        major_tasks_dimension = "ROWS"
        write_tasks_request = {
                        "range": write_tasks_range,
                        "majorDimension": major_tasks_dimension,
                        "values": values
                        }

        return write_tasks_request

    def generate_dates_write_request(self, sheet_name, location, schedule_dict):
        """ Creates line of dates, assumed to be executed on a Sunday. """
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        values = []
        today = datetime.datetime.today()

        for i, day in enumerate(days_of_week):
            new_date = today + datetime.timedelta(days=i + 1)
            new_date = new_date.strftime("%m/%d")
            values.append(["{0} ({1})".format(day, new_date)])

        write_dates_range = "{0}!B{1}:H{1}".format(sheet_name, location + 1)
        major_dates_dimension = "COLUMNS"

        write_dates_request = {
                                "range": write_dates_range,
                                "majorDimension": major_dates_dimension,
                                "values": values
                              }

        return write_dates_request

    def generate_blackout_request(self, sheet_id, location):
        background_black = {
                                "userEnteredFormat":
                                {
                                    "backgroundColor":
                                    {
                                        "red": 0,
                                        "green": 0,
                                        "blue": 0
                                    }
                                }
                            }



        dropdown_menu = {
                            "dataValidation": self.dropdown.get_validation_rule()
                        }

        DAYS_IN_WEEK = 7
        data = []
        ALPHABET = "abcdefghijklmnopqrstuvwxyz"
        translate = {i: char for i, char in enumerate(ALPHABET)}
        lockdown_requests = []

        for j, task in enumerate(self.tasks):
            schedule = task.schedule
            task_data = []
            for i in range(DAYS_IN_WEEK):
                if i not in schedule:
                    # Make black and lock.
                    task_data.append(background_black)
                    a1_input_lock = "{0}{1}:{0}{1}".format(translate[i + 2], location + 1 + j)
                    grid_range_lock = self.convert_A1_to_GridRange(sheet_id, a1_input_lock)
                    lockdown_request = {
                                            "addProtectedRange":
                                            {
                                                "protectedRange":
                                                {
                                                    "range": grid_range_lock,
                                                    "warningOnly": False,
                                                    "editors":
                                                    {
                                                        "users": self.editors
                                                    }
                                                }
                                            }
                                        }
                    lockdown_requests.append(lockdown_request)
                else:
                    # Add dropdown menu.
                    task_data.append(dropdown_menu)



            data.append(task_data)

        requests = []
        for i, row in enumerate(data):
            a1_input_color = "B{0}:H{0}".format(location + 1 + i)
            grid_range_color = self.convert_A1_to_GridRange(sheet_id, a1_input_color)

            request = {
                        "updateCells":
                        {
                            "rows":
                            {
                                "values": row
                            },
                            "range": grid_range_color,
                            "fields": "userEnteredFormat.backgroundColor, dataValidation"
                        }
                      }
            requests.append(request)

            for lockdown_request in lockdown_requests:
                requests.append(lockdown_request)

        return requests, None

    def convert_A1_to_GridRange(self, sheet_id, a1_input):
        start, end = a1_input.lower().split(":")
        ALPHABET = "abcdefghijklmnopqrstuvwxyz"
        translate = {char: i for i, char in enumerate(ALPHABET)}

        start_col = translate[start[0]]
        start_row = int(start[1:])

        end_col = translate[end[0]] + 1
        end_row = int(end[1:]) + 1

        GridRange = {
                        "sheetId" : sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    }

        return GridRange

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

    def test_dropdown_menu_debug(self):
        sample_request = self.dropdown.generate_request(0, 3, 4, 1, 5)
        # TODO: create Constants file with directed filenames for easy import of task names and contact information
        self.push(sample_request)


    def test_lock_debug(self):
        sample_request = self.lockcells.generate_request(0, 0, 1, 0, 1)
        self.push(sample_request)


    def full_send(self):
        response = self.service.spreadsheets() \
            .batchUpdate(spreadsheetId=self.spreadsheetId, body=self.request_body).execute()
        response_w = self.service.spreadsheets() \
            .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()
        print('{0} cells updated.'.format(len(response.get('replies')))) 
        # print('{0} cells updated.'.format(len(response.get('replies'))))
        pprint(response_w) 
        self.request_body = {}
        self.write_body = {}
        return

    def full_send_writes(self):
        response = self.service.spreadsheets() \
            .values().batchUpdate(spreadsheetId=self.spreadsheetId, body=self.write_body).execute()
        print('{0} cells updated.'.format(len(response.get('replies')))) 
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



if __name__ == "__main__":
    # TODO
    # 1. Lock cells
    # 2. Dropdown menu

    editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
    spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
    gsheets = GSheetsRequest(editors, (0, 0), spreadsheetId)
    gsheets.start()
    gsheets.new_week_template(1)
    gsheets.new_week_template(2)
    gsheets.new_week_template(3)
    gsheets.new_week_template(4)
    # gsheets.new_week_template(2)
    # pprint(gsheets.request_body)
    gsheets.full_send()
    # # pprint(gsheets.view_last_write())

    # # gsheets.test_lock_debug()
    # # gsheets.test_dropdown_menu_debug()
    # gsheets.full_send_writes()

    # pprint(gsheets.generate_blackout_request(0, 0, 1))




