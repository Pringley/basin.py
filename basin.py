import time

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
        self.tasks = {}

    def active_tids(self, tid):
        """Return a list of active task ids."""
        return [tid for tid in self.tasks if self.is_active(tid)]

    def sleeping_tids(self, tid):
        """Return a list of sleeping task ids."""
        return [tid for tid in self.tasks if self.is_sleeping(tid)]

    def blocked_tids(self, tid):
        """Return a list of blocked task ids."""
        return [tid for tid in self.tasks if self.is_blocked(tid)]

    def waiting_tids(self, tid):
        """Return a list of waiting task ids."""
        return [tid for tid in self.tasks if self.is_waiting(tid)]

    def is_active(self, tid):
        """Return True if given task id is active."""
        return not (is_sleeping(tid) or is_blocked(tid) or is_waiting(tid))

    def is_sleeping(self, tid):
        """Return True if given task id is sleeping."""
        task = self.get_task(tid)
        sleepuntil = task.params['sleepuntil']
        return sleepuntil is not None and time.time() < sleepuntil

    def is_blocked(self, tid):
        """Return True if given task id is blocked."""
        task = self.get_task(tid)
        blockers = task.params['blockers']
        for blocking_tid in blockers:
            blocker = self.get_task(blocking_tid)
            if not blocker['done']:
                return True
        return False

    def is_waiting(self, tid):
        """Return True if given task id is waiting."""
        task = self.get_task(tid)
        owner = task.params['owner']
        return owner is not None

    def create_task(self, **params):
        """Create a new task."""
        set_defaults(params, {
            'tid': self.lowest_available_tid(),
            'title': '',
            'done': False,
            'isproject': False,
            'forproject': None,
            'owner': None,
            'sleepuntil': None,
            'blockedby': [],
            'due': None,
            'labels': [],
            'body': '',
        })
        tid = params["tid"]
        if tid in self.tasks:
            raise BasinError("cannot recreate existing task %d" % tid)
        self.tasks[tid] = params
        return tid

    def get_task(self, tid):
        """Return the parameters of the given task id."""
        return self.tasks[tid]

    def update_task(self, tid, **params):
        """Update a task."""
        if tid not in self.tasks:
            raise BasinError("tried to update non-existant task %d" % tid)
        self.tasks[tid].update(params)

    def lowest_available_tid(self):
        """Return the lowest task id that has not yet been used."""
        tid = 0
        while tid in self.tasks:
            tid += 1
        return tid
