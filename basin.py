import json
import datetime
import collections

import peewee as pw

db_proxy = pw.Proxy()

class Model(pw.Model):
    """Base class for Basin models."""
    class Meta:
        database = db_proxy

class Task(Model):
    """Represent a todo item."""
    title = pw.CharField(null=True)
    body = pw.CharField(null=True)
    due = pw.DateTimeField(null=True)
    project = pw.BooleanField(default=False)

    created = pw.DateTimeField()

    completed = pw.BooleanField(default=False)
    trashed = pw.BooleanField(default=False)

    assignee = pw.CharField(null=True)
    sleepforever = pw.BooleanField(default=False)
    sleepuntil = pw.DateTimeField(null=True)

    def is_active(self):
        """Check if the task is active (non-sleeping, etc)."""
        return not (self.completed or self.trashed or self.is_delegated()
                or self.is_sleeping() or self.is_blocked())

    def is_sleeping(self):
        """Check if the task is sleeping/deferred."""
        return self.sleepforever or (self.sleepuntil is not None and
                datetime.datetime.now() < self.sleepuntil)

    def is_blocked(self):
        """Check if the task is blocked/waiting."""
        return bool(list(self.blocks))

    def is_delegated(self):
        """Check if the task is assigned to someone else."""
        return self.assignee is not None

class Blocks(Model):
    """Represent the "blocking" relationship between tasks."""
    blocked = pw.ForeignKeyField(Task, related_name='blocks')
    blocker = pw.ForeignKeyField(Task, related_name='blocking')

class Label(Model):
    """Represent task labels."""
    name = pw.CharField()

class TaskToLabel(Model):
    """Match tasks to labels."""
    task = pw.ForeignKeyField(Task)
    label = pw.ForeignKeyField(Label)

class BasinError(RuntimeError):
    """Generic Basin-related error."""

def set_defaults(params, defaults):
    """Set default parameters.
    
    params -- original dict of parameters
    defaults -- dict of default values
    
    """
    if params is None:
        params = {}
    for key, default in defaults.items():
        if key not in params or params[key] is None:
            params[key] = default

class Tasks(object):

    def __init__(self):
        db_proxy.initialize(pw.SqliteDatabase(':memory:'))
        if not Task.table_exists():
            Task.create_table()
            Blocks.create_table()
            Label.create_table()
            TaskToLabel.create_table()

    def filter(self, **kwargs):
        # Ignore trashed and completed tasks by default.
        if not kwargs.pop('all', False):
            kwargs.setdefault('trashed', False)
            kwargs.setdefault('completed', False)
        fields = set(kwargs.keys()) & set(Task._meta.get_fields())
        pseudo_fields = set(kwargs.keys()) - set(Task._meta.get_fields())
        results = []
        for task in Task.select():
            if not all(getattr(task, field) == kwargs[field] for field in fields):
                continue
            pf = {
                'sleeping': task.is_sleeping(),
                'blocked': task.is_blocked(),
                'delegated': task.is_delegated(),
                'active': task.is_active(),
                'trashed': task.trashed,
                'completed': task.completed,
            }
            if not all(pf[field] == kwargs[field]
                    for field in pseudo_fields):
                continue
            results.append(task)
        return results

    def is_incomplete(self, task):
        """Return True if given task id is active (not completed or trashed)."""
        return not (task.completed or task.trashed)

    def is_active(self, task):
        """Return True if given task id is active (not sleeping, blocked, completed, ...)."""
        return task.is_active()

    def is_sleeping(self, task):
        """Return True if given task id is sleeping."""
        return task.is_sleeping()

    def is_blocked(self, task):
        """Return True if given task id is blocked."""
        return task.is_blocked()

    def is_delegated(self, task):
        """Return True if given task id is delegated."""
        return task.is_delegated()

    def is_completed(self, task):
        """Return True if given task id is completed."""
        return task.completed

    def is_trashed(self, task):
        """Return True if given task id is trashed."""
        return task.trashed

    def is_project(self, task):
        """Return True if given task id is a project."""
        return task.project

    def get(self, task):
        """Return the task corresponding to the given id."""
        return task

    def create(self, title=None, **params):
        """Create a new task."""
        params['title'] = title
        now = datetime.datetime.now()
        set_defaults(params, {
            'created': now,
        })
        return Task.create(**params)

    def trash(self, tid):
        """Send a task to the trash."""
        self.update(tid, trashed=True)

    def untrash(self, tid):
        """Remove a task from the trash."""
        self.update(tid, trashed=False)

    def complete(self, tid):
        """Complete a task."""
        self.update(tid, completed=True)

    def uncomplete(self, tid):
        """Mark a task as not complete."""
        self.update(tid, completed=False)

    def sleep(self, task, wakeup_time=None):
        """Sleep a task until wakeup_time, or indefinitely if time not provided."""
        if wakeup_time is None:
            self.update(task, sleepforever=True)
        else:
            self.update(task, sleepuntil=wakeup_time)

    def unsleep(self, task):
        """Remove sleep from a task."""
        self.update(task, sleepforever=False, sleepuntil=None)

    def delegate(self, task, assignee):
        """Delegate a task to a new owner."""
        self.update(task, assignee=assignee)

    def undelegate(self, task):
        """Un-delegate a task."""
        self.update(task, assignee=None)

    def block(self, blocked, blocker):
        """Mark a task as blocking another."""
        Blocks.create(blocked=blocked, blocker=blocker)

    def unblock(self, blocked, blocker=None):
        """Mark a task as unblocked. Optionally only remove one blocker."""
        if blocker is None:
            query = Blocks.delete().where(Blocks.blocked == blocked)
        else:
            query = Blocks.delete().where(Blocks.blocked == blocked
                    and Blocks.blocker == blocker)
        query.execute()

    def update(self, task, **params):
        """Update a task."""
        for param, value in params.items():
            setattr(task, param, value)
        task.save()
