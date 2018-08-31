from googlesheetrequest import GSheetsRequest
from files import names, tasks
import sys

def main(load=False):
        editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
        spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
        # gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId)
        if load:        
                gsheets = GSheetsRequest.load('gsheets_obj.pickle')
        else:
                gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId)        
                gsheets.new_week()

        gsheets.serve()

if __name__ == "__main__":
        if sys.argv[1] == "load":
                main(load=True)
        else:
                main()
