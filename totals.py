


class CreditTotals(object):
    """ docstring for CreditTotals """
    def __init__(self, spreadsheetId, service):
	self.spreadsheet_id = spreadsheetId
	self.service = service
	self.names = self.load_names_from_gsheets()
	self.tasks = self.load_tasks_from_gsheets()
	
    def load_names_from_gsheets(self):
	pass

    def load_tasks_from_gheets(self):
	pass

    def update(self):
	# For sheet in sheets:
	# 	For week in sheet:
	# 		For day in week:
	# 			
			
	pass
