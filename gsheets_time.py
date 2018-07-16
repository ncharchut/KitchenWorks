from request_constants import BACKGROUND_BLACK, dropdown_format

class Month(object):
    """
        Needs to have access to default request format for blackout, dropdown, lock.
    """
    def __init__(self, arg, names):
        super(Month, self).__init__()
        self.arg = arg
        self.names = names
        self.dropdown = dropdown_format(names) # needs to fix

    def add_week(self):
        pass


class Week(object):
    """docstring for Week"""
    def __init__(self, arg):
        super(Week, self).__init__()
        self.arg = arg
        self.days = []

    def add_task(self, task):
        """
            Adds a task to the week schedule.
        """
        pass

    def lock_day(self, day=None):
        """
            Locks the day specified, or yesterday if not specified.
        """
        pass


class Day(object):
    """
        
    """
    def __init__(self, arg, editors):
        super(Day, self).__init__()
        self.arg = arg
        self.day_tasks = []
        self.editors = editors

    def lock(self):
        """
            Prevents write access by anyone other than the specified editors.
        """
        # Generate range based on number of tasks, then create ONE lock request with that range.
        pass

    def generate_request(self):
        write_requests = []
        lock_requests = []

        for task in self.day_tasks:
            current_task = task.get_format()
            write_requests.append(current_task)
            if task.is_locked():
                lock_requests.append(task.get_lock_request(self.editors))

        return write_requests, lock_requests


class DayTask(object):
    """docstring for DayTask"""
    def __init__(self, task_number, task_on, names, day):
        super(DayTask, self).__init__()
        self.task_number = task_number
        self.available = task_on
        self.task_format, self.locked = self.set_format(self.available)
        self.names = names
        self.locked = False
        self.day = day
        self.location = self.determine_location(self.task_number, self.day)

    def is_locked(self):
        return self.locked

    def set_format(self, available):
        task_format = None
        locked = False

        if available:
            task_format = dropdown_format(self.names)
        else:
            task_format = BACKGROUND_BLACK
            locked = True

        return task_format, locked

    def get_format(self):
        return self.task_format

    def get_lock_request(self, editors):
        """
            Prevents write access by anyone other than the specified editors.
        """
        return {
                    "addProtectedRange":
                    {
                        "protectedRange":
                        {
                            "range": self.location,
                            "warningOnly": False,
                            "editors":
                            {
                                "users": editors
                            }
                        }
                    }
                }

    def determine_location(self, task_number, day):
        """
            Determine grid location on sheet given the day and task number, returns a GridArea JSON.
        """
        pass


class Location(object):
    """docstring for Location"""
    def __init__(self, arg):
        super(Location, self).__init__()
        self.arg = arg



if __name__ == "__main__":
    pass
        