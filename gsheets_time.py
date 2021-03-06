from request_constants import BACKGROUND_BLACK, dropdown_format, update_row_request
from pprint import pprint
import pickle
from task import TaskManager
from requests import DropdownMenu
from files import names, tasks
from datetime import datetime, timedelta

class Month(object):
    """
        Needs to have access to default request format for blackout, dropdown, lock.
    """
    def __init__(self, contacts, tasks, sheet_id, spreadsheetId, sheet_name, editors):
        super(Month, self).__init__()
        self.contacts = contacts
        self.names = self.contacts.get_names()
        self.tasks = tasks
        self.sheet_id = sheet_id
        self.spreadsheetId = spreadsheetId
        self.sheet_name = sheet_name
        self.last_location = Location(1, 1, self.sheet_id)
        self.editors = editors
        self.weeks = []

    def update_name(self, name):
        self.sheet_name = name
        for week in self.weeks:
            week.update_name(name)

    def update_contacts(self, contacts):
        self.contacts = contacts
        self.names = contacts.get_names()

    def update_credit_totals(self, total):
        locations = [week.data_location for week in self.weeks]
        update = self.get_data(total, locations)
        return update
        

    def get_data(self, total, locations):
        request = total.service.spreadsheets().get(spreadsheetId=self.spreadsheetId, ranges=locations, includeGridData=True)
        response = request.execute()
        processed_data = self.process_data(response)
        return total.update(processed_data)

    def process_data(self, data):
        this_sheet = data['sheets'][-1]
        GREEN = {'red': 0.8509804, 'green': 0.91764706, 'blue': 0.827451}
        RED = {'red': 0.95686275, 'green': 0.8, 'blue': 0.8}

        result = []

        for week in this_sheet['data']:
            for row, thing in enumerate(week['rowData']):
                task = thing['values']
                task_object = self.tasks[row]

                for day in task:
                    name = day.get('effectiveValue', {}).get('stringValue', None)
                    day_format = day.get('effectiveFormat', {}).get('backgroundColor', None)
                    if name is not None and day_format is not None:
                        if day_format == GREEN:
                            multiplier = 1
                        elif day_format == RED:
                            multiplier = -1
                        else:
                            multiplier = 0
                        result.append((name, multiplier, task_object))

        return result

    def lock_days_before(self):
        this_week = self.weeks[-1]
        # debug_date = datetime.today() + timedelta(days=5) # this will just be today in the future
        requests = this_week.lock_days_before(datetime.today())
        return requests

    def add_week(self, base_date=None):
        new_week = Week(self.tasks, self.last_location, self.editors, self.names, self.sheet_name, base_date)
        last_date = new_week.get_last_date()

        self.weeks.append(new_week)
        dates_writes, tasks_writes, tasks_fields = new_week.get_request()

        clean_tasks = self.format_cell_updates(tasks_fields)

        self.last_location = self.last_location.vertical_shift(len(self.tasks) + 3)
        self.save()

        properties_requests = self.get_properties_request()

        return dates_writes, tasks_writes, clean_tasks, properties_requests, last_date

    def get_properties_request(self, hidden=False):
        return {
                "updateSheetProperties": {
                "properties": {
                              "sheetId": self.sheet_id,
                              "gridProperties": {
                                                    "rowCount": (len(self.tasks) + 3) * len(self.weeks), # TODO Get rid of magic number
                                                    "columnCount": 10
                                                  },
                              "hidden": hidden,
                              "tabColor": {
                                        "red": 1.0,
                                        "green": 0.3,
                                        "blue": 0.4
                                      }
                  },
                  "fields": "sheetId, gridProperties, hidden, tabColor"
                  }
                }

    def format_cell_updates(self, cell_updates):
        requests = []
        first_loc = self.last_location
        last_loc = first_loc.horizontal_shift(len(self.tasks))

        for i, row in enumerate(cell_updates):
            new_first_loc = first_loc.vertical_shift(i + 1)
            new_last_loc = last_loc.vertical_shift(i + 1)
            grid_range = new_first_loc.convert_to_grid_range(new_last_loc)
            request = update_row_request(row, grid_range)
            requests.append(request)

        return requests

    def save(self):
        with open('test_load.pickle', 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return 

    def __getitem__(self, index):
        try:
            week = self.weeks[index]
            return week
        except IndexError:
            print("attempted to access a week that does not exist")
            return

    @staticmethod
    def load(file):
        with open(file, 'rb') as handle:
            month = pickle.load(handle)

        return month

class Week(object):
    """docstring for Week"""
    def __init__(self, tasks, location, editors, names, sheet_name, date_override=None):
        super(Week, self).__init__()
        self.tasks = tasks
        self.location = location
        self.editors = editors
        self.names = names
        self.sheet_name = sheet_name
        self.days = self._init_days(date_override)
        self.data_location = self.get_data_location(self.location)

        self._init_tasks(self.tasks)

    def _init_tasks(self, tasks):
        for i, task in enumerate(tasks):
            for j in range(7): # fix magic number
                day = self.days[j]
                day.add_day_task(task, i, self.names)

    def update_credit_totals(self, total, data):
        for task_number, values in enumerate(data):
            credits = self.tasks[task_number].credits
            task_name = self.tasks[task_number].name
            for value in values:
                total.update(task_name, value, credits)

    def get_data_location(self, location):
        COLUMNS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        DAYS_IN_WEEK = 7
        col_start = self.location.get_column()
        col_end = col_start + (DAYS_IN_WEEK - 1)

        row_start = self.location.get_row() + 2
        row_end = row_start + (len(self.tasks) - 1)

        return "{0}!{1}{2}:{3}{4}".format(self.sheet_name, COLUMNS[col_start], row_start,
                                          COLUMNS[col_end], row_end)

    def update_name(self, name):
        self.sheet_name = name
        self.data_location = self.get_data_location(self.location)

    def get_last_date(self):
        return self.days[-1].get_date()

    def get_request(self):
        dates_header = self.generate_dates_write_request(self.sheet_name, self.location)
        tasks_header = self.generate_task_writes_request(self.sheet_name, self.location, self.tasks)
        tasks_fields = self.generate_task_requests()
        return dates_header, tasks_header, tasks_fields

    def generate_task_requests(self):
        # either going to be black or have a dropdown menu
        res = [[] for _ in range(len(self.tasks))]
        DAYS_IN_WEEK = 7

        for i in range(DAYS_IN_WEEK):
            day = self.days[i]
            for j, task in enumerate(day.day_tasks):
                res[j].append(task.task_format)
        return res

    def generate_dates_write_request(self, sheet_name, location):
        """ Creates line of dates, assumed to be executed on a Sunday. """
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        values = []

        for day in self.days:
            date  = day.get_date()

            day_of_week = days_of_week[date.weekday()]
            date_string = date.strftime("%m/%d")
            values.append(["{0} ({1})".format(day_of_week, date_string)])

        return self.get_date_json(sheet_name, location, values)

    def generate_task_writes_request(self, sheet_name, location, tasks):
        TASK_OFFSET = 2
        root = location.get_row() + TASK_OFFSET
        values, _ = tasks.generate_task_fields()

        write_tasks_range = "{0}!A{1}:A{2}".format(sheet_name, root, root + len(tasks))
        major_tasks_dimension = "ROWS"
        write_tasks_request = {
                        "range": write_tasks_range,
                        "majorDimension": major_tasks_dimension,
                        "values": values
                        }

        return write_tasks_request

    def get_date_json(self, sheet_name, location, values):
        write_dates_range = "{0}!B{1}:H{1}".format(sheet_name, location.get_row() + 1)
        major_dates_dimension = "COLUMNS"

        write_dates_request = {
                                "range": write_dates_range,
                                "majorDimension": major_dates_dimension,
                                "values": values
                              }

        return write_dates_request

    def _init_days(self, date_override):
        DAYS_IN_WEEK = 7
        
        days = []
        if date_override is not None:
            date = datetime.strptime(date_override, "%m/%d/%y")
        else:
            date = self.get_next_monday()

        for i in range(DAYS_IN_WEEK):
            location = self.location.horizontal_shift(i)
            day = Day(date, location, self.editors)
            days.append(day)
            date = date + timedelta(days=1)
        
        return days

    def get_next_monday(self):
        today = datetime.today()
        date =  today + timedelta(days=(7 - today.weekday()))
        return date

    def lock_days_before(self, date_cutoff=None):
        """
            Locks the day specified, or today if not specified.
        """
        lock_requests = []

        if date_cutoff is not None:
            for day in self.days:
                if day.get_date() < date_cutoff and not day.locked:
                    lock_requests.append(day.lock())
        else:
            day = self.days[datetime.today().weekday]
            lock_requests.append(day.lock())

        return lock_requests

    def __repr__(self):
        return "Week({0}, {1}, {2})".format(repr(self.tasks), repr(self.location), self.editors)

    def __getitem__(self, index):
        try:
            day = self.days[index]
            return day
        except IndexError:
            print("attempted to access a day that does not exist")
            return


class Day(object):
    """
        
    """
    def __init__(self, date, location, editors):
        super(Day, self).__init__()
        self.date = date
        self.day_tasks = []
        self.editors = editors
        self.location = location # TODO
        self.locked = False

    def lock(self):
        """
            Prevents write access by anyone other than the specified editors.
        """
        # Generate range based on number of tasks, then create ONE lock request with that range.

        requests = [task.get_lock_request(self.editors) for task in self.day_tasks]
        self.locked = True
        return requests

    def generate_request(self):
        write_requests = []
        lock_requests = []

        for task in self.day_tasks:
            current_task = task.get_format()
            write_requests.append(current_task)
            if task.is_locked():
                lock_requests.append(task.get_lock_request(self.editors))

        return write_requests, lock_requests

    def get_location(self):
        return self.location

    def get_date(self):
        return self.date

    def add_day_task(self, task, task_number, names):
        day_task = DayTask(task_number, self.date.weekday() in task.get_schedule(), names, self, task)
        self.day_tasks.append(day_task)
        return True

    def __repr__(self):
        return "Day({0}, {1}, {2})".format(self.date, repr(self.location), self.editors)

    def __getitem__(self, index):
        try:
            day_task = self.day_tasks[index]
            return day_task
        except IndexError:
            print("attempted to access a day task that does not exist")
            return


class DayTask(object):
    """docstring for DayTask"""
    def __init__(self, task_number, task_on, names, day, task):
        super(DayTask, self).__init__()
        self.task_number = task_number
        self.available = task_on
        self.names = names
        self.task_format, self.locked = self.set_format(self.available)
        self.day = day
        self.task = task
        self.location = self.determine_location(self.task_number, self.day)

    def is_locked(self):
        return self.locked

    def set_format(self, available):
        task_format = None
        locked = False

        if available:
            task_format = dropdown_format([{"userEnteredValue": name} for name in self.names])
        else:
            task_format = BACKGROUND_BLACK
            locked = True

        return task_format, locked

    def get_format(self):
        return self.task_format

    def get_lock_request(self, editors):
        """
            Prevents write access by anyone other than the specified editors.
        """
        return {
                    "addProtectedRange":
                    {
                        "protectedRange":
                        {
                            "range": self.location,
                            "warningOnly": False,
                            "editors":
                            {
                                "users": editors
                            }
                        }
                    }
                }

    def __repr__(self):
        return "DayTask({0}, {1}, [NAMES], {2}, {3})".format(self.task_number, self.available, repr(self.day), repr(self.task))

    def determine_location(self, task_number, day):
        """
            Determine grid location on sheet given the day and task number, returns a GridArea JSON.
        """
        new_location = day.get_location().vertical_shift(task_number + 1)
        grid_area = new_location.convert_to_grid_area()
        return grid_area


class Location(object):
    """docstring for Location"""
    def __init__(self, row, column, sheet_id):
        super(Location, self).__init__()
        self.row = row
        self.column = column
        self.sheet_id = sheet_id

    def get_row(self):
        return self.row

    def get_column(self):
        return self.column

    def get_sheet_id(self):
        return self.sheet_id

    def __add__(self, other):
        new_row = self.row + other.get_row()
        new_column = self.column + other.get_column()
        return Location(new_row, new_column, self.sheet_id)

    def horizontal_shift(self, delta):
        return Location(self.row, self.column + delta, self.sheet_id)

    def vertical_shift(self, delta):
        return Location(self.row + delta, self.column, self.sheet_id)

    def convert_to_a1(self):
        pass

    def convert_to_grid_area(self):
         return {
                    "sheetId" : self.sheet_id,
                    "startRowIndex": self.row,
                    "endRowIndex": self.row + 1,
                    "startColumnIndex": self.column,
                    "endColumnIndex": self.column + 1
                }

    def convert_to_grid_range(self, other):
        return {
                    "sheetId" : self.sheet_id,
                    "startRowIndex": self.row,
                    "endRowIndex": other.get_row() + 1,
                    "startColumnIndex": self.column,
                    "endColumnIndex": other.get_column() + 1
                }

    def __repr__(self):
        return "Location({0}, {1}, {2})".format(self.row, self.column, self.sheet_id)


if __name__ == "__main__":
    editors = ['nick', 'cboy']
    sheet_id = 'abc123'
    sheet_name = 'TEST'
    test_week = Week(None, Location(0, 0, sheet_id), None)
    pprint(test_week.days)
        
