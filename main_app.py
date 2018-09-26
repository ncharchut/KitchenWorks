from googlesheetrequest import GSheetsRequest
from files import names, tasks
import sys
import glob
import os

def main(load=False, base_override=None):
        editors = ["nicholas.charchut@gmail.com", "sweeney.connorj@gmail.com"]
        spreadsheetId = "1vMFRfLKJV2hJv1KW2KgP52Ltv6-g8MzCL0sNyt9pApM"
        # gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId)
        if load:        
                list_of_files = glob.glob('./*.pickle') # * means all if need specific format then *.csv
                latest_file = max(list_of_files, key=os.path.getctime)
                gsheets = GSheetsRequest.load(latest_file)
        else:
                gsheets = GSheetsRequest(editors, names, tasks, spreadsheetId, new_page=True)        
                gsheets.new_week(base_date=base_override)

        gsheets.serve()

if __name__ == "__main__":
        if sys.argv[1] == "load":
                main(load=True)
        elif len(sys.argv) == 2:
                main(base_override=sys.argv[1])
        else:
                main()
