import csv

class Contacts(object):
    """docstring for Names"""
    def __init__(self, data):
        super(Contacts, self).__init__()
        self.raw_data = data
        self.contacts = self.load_contacts(self.raw_data)

    def load_contacts(self, data):
        contacts = []
        for person in data['values']:
            name, phone, email = person
            new_contact = Contact(name, phone, email)
            contacts.append(new_contact)

        contacts = sorted(contacts, key=lambda x: x.name.split(' ')[-1])

        return contacts

    def get_names(self):
        return [contact.get_name() for contact in self.contacts]

    def __iter__(self):
        for contact in self.contacts:
            yield contact

class Contact(object):
    """docstring for Name"""
    def __init__(self, name, phone, email):
        super(Contact, self).__init__()
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
        return "<{0}, {1}, {2}>".format(self.name, self.phone, self.email)

    def __repr__(self):
        return "Contact({0}, {1}, {2})".format(self.name, self.phone, self.email)
