from googlesheetrequest import GSheetsRequest
from files import names, tasks

editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId)

gsheets.new_week()

gsheets.serve()