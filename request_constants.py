
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


def auto_resize_column_width(sheetId):
    return {
              "autoResizeDimensions": {
                "dimensions": {
                  "sheetId": sheetId,
                  "dimension": "COLUMNS"
                }
              }
            }

def update_spreadsheet_properties(sheetId, rows, cols, hidden=False):
    return {
            "updateSheetProperties": {
            "properties": {
                          "sheetId": sheetId,
                          "gridProperties": {
                                                "rowCount": rows,
                                                "columnCount": cols
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

def update_spreadsheet_name(sheetId, name):
    return {
            "updateSheetProperties": {
                                      "properties": {
                                                     "sheetId": sheetId,
                                                     "title": name
                                                    },
                                      "fields": "sheetId, title"
                                     }
            }
