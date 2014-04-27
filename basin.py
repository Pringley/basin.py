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
    title = pw.CharField(null=True, help_text='short description')
    body = pw.CharField(null=True, help_text='longer description')
    due = pw.DateTimeField(null=True, help_text='due date/time')
    project = pw.BooleanField(default=False, help_text='multi-step project?')

    created = pw.DateTimeField()
    updated = pw.DateTimeField()

    completed = pw.BooleanField(default=False)
    trashed = pw.BooleanField(default=False)

    assignee = pw.CharField(null=True)
    sleepforever = pw.BooleanField(default=False)
    sleepuntil = pw.DateTimeField(null=True)

    @classmethod
    def create(cls, **kwargs):
        now = datetime.datetime.now()
        kwargs.setdefault('created', now)
        kwargs.setdefault('updated', now)
        return super(Task, cls).create(**kwargs)

    def save(self, **kwargs):
        if 'updated' not in self.dirty_fields:
            self.updated = datetime.datetime.now()
        return super(Task, self).save(**kwargs)

    def complete(self):
        """Complete the task."""
        self.completed = True
        self.save()

    def uncomplete(self):
        """Revert task to incomplete."""
        self.completed = False
        self.save()

    def trash(self):
        """Trash the task."""
        self.trashed = True
        self.save()

    def untrash(self):
        """Remove task from the trash."""
        self.trashed = False
        self.save()

    def sleep(self, wakeup_time=None):
        """Defer this task until later."""
        if wakeup_time is None:
            self.sleepforever = True
        else:
            self.sleepuntil = wakeup_time
        self.save()

    def unsleep(self):
        """Un-defer the task."""
        self.sleepforever = False
        self.sleepuntil = None
        self.save()

    def block_on(self, blocking_task):
        """Block on another task."""
        Blocks.create(blocked=self, blocker=blocking_task)

    def unblock(self, blocking_task=None):
        """Mark a task as unblocked. Optionally only remove one blocker."""
        if blocking_task is None:
            query = Blocks.delete().where(Blocks.blocked == self)
        else:
            query = Blocks.delete().where(Blocks.blocked == self
                    and Blocks.blocker == blocking_task)
        query.execute()

    def delegate(self, assignee):
        self.assignee = assignee
        self.save()

    def undelegate(self):
        self.assignee = None
        self.save()

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
    trashed = pw.BooleanField(default=False)

class TaskToLabel(Model):
    """Match tasks to labels."""
    task = pw.ForeignKeyField(Task)
    label = pw.ForeignKeyField(Label)

def global_db_init(filename=':memory:'):
    """Globally initialize the database."""
    db_proxy.initialize(pw.SqliteDatabase(filename))
    if not Task.table_exists():
        Task.create_table()
        Blocks.create_table()
        Label.create_table()
        TaskToLabel.create_table()
