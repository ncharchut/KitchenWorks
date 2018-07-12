import csv


class Task(object):
    """docstring for Task"""
    def __init__(self, name, credits, schedule):
        super(Task, self).__init__()
        self.name = name
        self.credits = credits
        self.schedule = TaskSchedule(schedule)

    def get_schedule(self):
        return self.schedule

    def generate_template_request(self):
        pass

    def __str__(self):
        return "<Task: {0}, Credits: {1}>".format(self.name, self.credits)

    def __repr__(self):
        return "Task({0}, {1}, {2})".format(self.name, self.credits, self.schedule)


class TaskSchedule(object):
    """docstring for TaskSchedule"""
    def __init__(self, schedule_string):
        super(TaskSchedule, self).__init__()
        self._raw_schedule = schedule_string
        self.schedule = self.process_schedule_string(self._raw_schedule)

    def process_schedule_string(self, schedule_string):
        day_name_translator = {
                                "M": 0,
                                "T": 1,
                                "W": 2,
                                "R": 3,
                                "F": 4,
                                "S": 5,
                                "N": 6
                              }

        return [day_name_translator[day] for day in schedule_string]

    def generate_template(self):
        pass

    def __str__(self):
        return str([day for day in self.schedule])[1:-1] # ignore opening and closing brackets

    def __repr__(self):
        return "TaskSchedule({0})".format(self._raw_schedule)

    def __iter__(self):
        for day in self.schedule:
            yield day
        

class TaskManager(object):
    """docstring for TaskManager"""
    def __init__(self, tasks_file):
        super(TaskManager, self).__init__()
        self.file = tasks_file
        self.tasks = self.populate_tasks(self.file)

    def populate_tasks(self, file):
        tasks = []

        with open(file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0] == "Task": # ignore labels row (first row)
                    continue
                name, credits, schedule = row
                task = Task(name, credits, schedule)
                tasks.append(task)

        return tasks

    def generate_task_fields(self):
        """ Should return list of lists. """
        res = []

        for task in self.tasks:
            res.append((["{0} ({1} credits)".format(task.name, task.credits)], task.schedule))

        return self.clean_task_fields(res)

    def clean_task_fields(self, raw_fields):
        """ Cleans fields and forms JSON request for write values. """
        res = []
        schedule_dict = {}

        for task in raw_fields:
            name, schedule = task[0], task[1]
            res.append(name)
            schedule_dict[name[0]] = schedule

        return res, schedule_dict

    def __len__(self):
        return len(self.tasks)

    def __iter__(self):
        for task in self.tasks:
            yield task

if __name__ == "__main__":
    file = "tasks.csv"
    TaskManager(file)
        