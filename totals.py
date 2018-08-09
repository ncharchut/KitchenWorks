from collections import defaultdict

class CreditTotals(object):
    """ docstring for CreditTotals """
    def __init__(self, spreadsheetId, service, contacts, tasks):
        self.spreadsheet_id = spreadsheetId
        self.contacts = contacts
        self.service = service
        self.tasks = tasks
        self.totals = self._init_totals(self.contacts)
    
    def _init_totals(self, contacts):
        return {contact.get_name(): PersonTotals(contact, self.tasks) for contact in contacts}

    def load_names_from_gsheets(self):
        pass

    def load_tasks_from_gsheets(self):
        pass

    def update(self, data):
        # 1. Identify what color it is ( *-1 if red, *1 if green, *0 if neither)
        # 2. Identify name
        # 3. Update that person accordingly. (task and credits)
        # name, multiplier, task object
        for job in data:
            name, multiplier, task = job
            self.totals[name].update(task, multiplier)

        return self

    def generate_request_values(self):
        values = []

        for person in self.totals:
            values.append(self.totals[person].generate_request_values())

        return values

    def full_request(self):
        values = self.generate_request_values()
        COLUMNS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        write_requests = [self.generate_task_header()]

        end_index = len(self.tasks) + 1
        end_col = COLUMNS[end_index]

        for i, person in enumerate(values):
            row = 2 + i
            write_range = "{0}!A{1}:{2}{1}".format("Totals", row, end_col)
            major_dimension = "COLUMNS"
            # person[1] = "=SUM(C{0}:{1}{0}) - {2}{0} + {3}{0}".format(row, end_col, COLUMNS[end_index + 1],
            #                                                         COLUMNS[end_index + 2])

            write_request = {
                            "range": write_range,
                            "majorDimension": major_dimension,
                            "values": [[item] for item in person]
                            }
            write_requests.append(write_request)

        return write_requests

    def generate_task_header(self):
        COLUMNS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        write_range = "{0}!A{1}:{2}{1}".format("Totals", 1, COLUMNS[len(self.tasks) + 3])
        major_dimension = "COLUMNS"
        values = [["Name"], ["Total"]]
        for task in self.tasks:
            values.append([task.name])
        values.append(["Fines"])
        values.append(["Special Forces"])

        write_request = {
                            "range": write_range,
                            "majorDimension": major_dimension,
                            "values": values
                            }

        return write_request


class PersonTotals(object):
    """docstring for PersonTotals"""
    def __init__(self, contact, tasks):
        super(PersonTotals, self).__init__()
        self.contact = contact
        self.task_ref = tasks
        self.tasks = defaultdict(int)
        for task in tasks:
            self.tasks[task] = 0

    def generate_request_values(self):
        values = [self.contact.get_name()]
        values.append(None)

        for task in self.task_ref:
            values.append(self.tasks[task])

        # values[1] = sum(values[2:])
        return values
        # generates the write request for a particular person and their completed tasks

    def update(self, task, multiplier):
        self.tasks[task] += task.credits * multiplier
        