import csv

class Names(object):
    """docstring for Names"""
    def __init__(self, names_file):
        super(Names, self).__init__()
        self.names_raw = names_file
        self.names = self.load_names(self.names_raw)

    def load_names(self, file):
        names = []

        with open(file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == "Timestamp": # ignore labels row (first row)
                    continue
                _, name, phone, email = row
                name = Name(name, phone, email)
                names.append(name)

        return names

class Name(object):
    """docstring for Name"""
    def __init__(self, name, phone, email):
        super(Name, self).__init__()
        self.name = name
        self.phone = phone
        self.email = email

    def get_name(self):
        return self.name

    def get_phone(self):
        return self.phone

    def get_email(self):
        return self.email

    def __str__(self):
        return self.name
