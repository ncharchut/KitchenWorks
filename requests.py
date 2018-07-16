import csv
from pprint import pprint

class DropdownMenu(object):
    """docstring for DropdownMenuRequest"""
    def __init__(self, names_file):
        super(DropdownMenu, self).__init__()
        self.names_file = names_file
        self.names = self.process_name_file(self.names_file)
        self.validation_rule = {
                                    "condition":
                                    {
                                        "type": "ONE_OF_LIST",
                                        "values": self.names
                                    },
                                    "strict": True,
                                    "showCustomUi": True,
                                    "inputMessage": "Type your full name or select it from the dropdown menu."
                                }

    def get_validation_rule(self):
        return self.validation_rule
        
    def generate_request(self, sheetId, startRowIndex, endRowIndex, startColumnIndex, endColumnIndex):
        """ Generates JSON request dropdown menus in a given range. """
        return {
                    "setDataValidation":
                    {
                        "range":
                        {
                            "sheetId": sheetId,
                            "startRowIndex": startRowIndex,
                            "endRowIndex": endRowIndex,
                            "startColumnIndex": startColumnIndex,
                            "endColumnIndex": endColumnIndex
                        },
                        "rule": self.rule
                    }
                }

    def process_name_file(self, file):
        names = []
        with open(file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                names.append({"userEnteredValue": row[0]})

        return names


class LockCells(object):
    """docstring for LockColumn"""
    def __init__(self, editors):
        super(LockCells, self).__init__()
        self.editors = editors

    def generate_request(self, sheetId, startRowIndex, endRowIndex, startColumnIndex, endColumnIndex):
        return {
                    "addProtectedRange":
                    {
                        "protectedRange":
                        {
                            "range":
                            {
                                "sheetId": sheetId,
                                "startRowIndex": startRowIndex,
                                "endRowIndex": endRowIndex,
                                "startColumnIndex": startColumnIndex,
                                "endColumnIndex": endColumnIndex
                            },
                            "warningOnly": False,
                            "editors":
                            {
                                "users": self.editors
                            }
                        }
                    }
                }

    def generate_lock_sheet_request(self, sheetId):
         return {
                    "addProtectedRange":
                    {
                        "protectedRange":
                        {
                            "range":
                            {
                                "sheetId": sheetId,
                            },
                            "warningOnly": False,
                            "editors":
                            {
                                "users": self.editors
                            }
                        }
                    }
                }
        


if __name__ == "__main__":
    names_file = "names.csv"
    editors = ["nicholas.charchut@gmail.com"]
    dropdown = DropdownMenu(names_file)
    lockcells = LockCells(editors)
    pprint(lockcells.generate_request("Name", 0, 1, 0, 1))