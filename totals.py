


class CreditTotals(object):
    """ docstring for CreditTotals """
    def __init__(self, spreadsheetId, service, contacts):
        self.spreadsheet_id = spreadsheetId
        self.contacts = contacts
        self.service = service
        self.totals = 
        self.tasks = self.load_tasks_from_gsheets()
    
    def load_names_from_gsheets(self):
        pass

    def load_tasks_from_gsheets(self):
        pass

    def update(self, data):
        # 1. Identify what color it is ( *-1 if red, *1 if green, *0 if neither)
        # 2. Identify name
        # 3. Update that person accordingly. (task and credits)
        # name, multiplier, task object

        pass



class PersonTotals(object):
    """docstring for PersonTotals"""
    def __init__(self, arg):
        super(PersonTotals, self).__init__()
        self.arg = arg

    def generate_request(self):
        pass
        # generates the write request for a particular person and their completed tasks
        
