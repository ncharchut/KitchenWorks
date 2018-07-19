
BLACK = {
            "red": 0,
            "blue": 0,
            "green": 0
        }

BACKGROUND_BLACK = {
                        "userEnteredFormat":
                        {
                            "backgroundColor": BLACK
                        }
                    }


def dropdown_format(names):
    return {
                "dataValidation":
                {
                    "condition":
                    {
                        "type": "ONE_OF_LIST",
                        "values": names
                    },
                    "strict": True,
                    "showCustomUi": True,
                    "inputMessage": "Type your full name or select it from the dropdown menu."
                }
            }

def update_row_request(row, grid_range):
    return {
                "updateCells":
                {
                    "rows":
                    {
                        "values": row
                    },
                    "range": grid_range,
                    "fields": "userEnteredFormat.backgroundColor, dataValidation"
                }
            }


