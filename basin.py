import time
import collections

Task = collections.namedtuple('Task', [
    'tid', 'title', 'completed', 'project', 'owner', 'sleepuntil', 'blockers',
    'due', 'labels', 'body', 'trashed', 'created', 'updated',
])

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

    def all_tids(self):
        """Return a set of all task ids."""
        return set(self.tasks.keys())

    def active_tids(self):
        """Return a set of active task ids (not completed or trashed)."""
        return set(tid for tid in self.tasks if self.is_active(tid))

    def infocus_tids(self):
        """Return a set of task ids in the infocus set (not sleeping, blocked)."""
        return set(tid for tid in self.tasks if self.is_infocus(tid))

    def sleeping_tids(self):
        """Return a set of sleeping task ids (from active tasks)."""
        return set(tid for tid in self.active_tids() if self.is_sleeping(tid))

    def blocked_tids(self):
        """Return a set of blocked task ids (from active tasks)."""
        return set(tid for tid in self.active_tids() if self.is_blocked(tid))

    def delegated_tids(self):
        """Return a set of delegated task ids (from active tasks)."""
        return set(tid for tid in self.active_tids() if self.is_delegated(tid))

    def completed_tids(self):
        """Return a set of completed task ids (that aren't trashed)."""
        return set(tid for tid in self.tasks if self.is_completed(tid)
                and not self.is_trashed(tid))

    def trashed_tids(self):
        """Return a set of trashed task ids."""
        return set(tid for tid in self.tasks if self.is_trashed(tid))

    def is_active(self, tid):
        """Return True if given task id is active (not completed or trashed)."""
        return not (self.is_completed(tid) or self.is_trashed(tid))

    def is_infocus(self, tid):
        """Return True if given task id is infocus (not sleeping, blocked)."""
        return self.is_active(tid) and not (self.is_sleeping(tid) or self.is_blocked(tid))

    def is_sleeping(self, tid):
        """Return True if given task id is sleeping."""
        task = self.get_task(tid)
        return task.sleepuntil is not None and (task.sleepuntil == -1
                or time.time() < task.sleepuntil)

    def is_blocked(self, tid):
        """Return True if given task id is blocked."""
        task = self.get_task(tid)
        for blocking_tid in task.blockers:
            blocker = self.get_task(blocking_tid)
            if not blocker.completed:
                return True
        return False

    def is_delegated(self, tid):
        """Return True if given task id is delegated."""
        task = self.get_task(tid)
        return task.owner is not None

    def is_completed(self, tid):
        """Return True if given task id is completed."""
        task = self.get_task(tid)
        return task.completed

    def is_trashed(self, tid):
        """Return True if given task id is trashed."""
        task = self.get_task(tid)
        return task.trashed

    def is_project(self, tid):
        """Return True if given task id is a project."""
        task = self.get_task(tid)
        return task.project

    def get_task(self, tid):
        """Return the task corresponding to the given id."""
        return self.tasks[tid]

    def create(self, **params):
        """Create a new task."""
        now = time.time()
        set_defaults(params, {
            'tid': self.lowest_available_tid(),
            'title': '',
            'completed': False,
            'project': False,
            'owner': None,
            'sleepuntil': None,
            'blockers': set(),
            'due': None,
            'labels': set(),
            'body': '',
            'created': now,
            'updated': now,
            'trashed': False,
        })
        tid = params["tid"]
        if tid in self.tasks:
            raise BasinError("cannot recreate existing task %d" % tid)
        self.update(_create=True, **params)
        return tid

    def trash(self, tid):
        """Send a task to the trash."""
        self.update(tid=tid, trashed=True)

    def untrash(self, tid):
        """Remove a task from the trash."""
        self.update(tid=tid, trashed=False)

    def complete(self, tid):
        """Complete a task."""
        self.update(tid=tid, completed=True)

    def uncomplete(self, tid):
        """Mark a task as not complete."""
        self.update(tid=tid, completed=False)

    def sleep(self, tid, wakeup_time=-1):
        """Sleep a task until wakeup_time, or indefinitely if time not provided."""
        self.update(tid=tid, sleepuntil=wakeup_time)

    def unsleep(self, tid):
        """Remove sleep from a task."""
        self.update(tid=tid, sleepuntil=None)

    def delegate(self, tid, owner):
        """Delegate a task to a new owner."""
        self.update(tid=tid, owner=owner)

    def undelegate(self, tid):
        """Un-delegate a task."""
        self.update(tid=tid, owner=None)

    def block(self, blocked_tid, blocking_tid):
        """Mark a task as blocking another."""
        task = self.get_task(blocked_tid)
        self.update(tid=blocked_tid, blockers=(task.blockers |
            set([blocking_tid])))

    def unblock(self, blocked_tid, blocking_tid=None):
        """Mark a task as unblocked. Optionally only remove one blocker."""
        if blocking_tid is None:
            self.update(tid=blocked_tid, blockers=set())
            return
        task = self.get_task(blocked_tid)
        self.update(tid=blocked_tid, blockers=(task.blockers -
            set([blocking_tid])))

    def update(self, _create=False, **params):
        """Update a task."""
        if 'tid' not in params:
            raise TypeError("update() missing required argument: 'tid'")
        tid = params['tid']
        if _create:
            self.tasks[tid] = Task(**params)
            return
        if tid not in self.tasks:
            raise BasinError("tried to update non-existant task %d" % tid)
        set_defaults(params, {
            'updated': time.time(),
        })
        self.tasks[tid] = self.tasks[tid]._replace(**params)

    def lowest_available_tid(self):
        """Return the lowest task id that has not yet been used."""
        tid = 0
        while tid in self.tasks:
            tid += 1
        return tid
