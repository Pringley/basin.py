import time
import json
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

    def __init__(self, _from_history=None):
        self.tasks = {}
        self.history = []

        if _from_history:
            for update_params in _from_history:
                self._update(**update_params)

    def _archive(self, include_history=True):
        """Create an archive (for dump to file)."""
        archive = {
            'timestamp': time.time(),
            'snapshot': dict((tid, task._asdict()) for tid, task in
                self.tasks.items())
        }
        if include_history:
            archive['history'] = self.history
        return archive

    def dumps(self):
        """Return a string representation of full current state."""
        return json.dumps(self._archive())

    def dump(self, tofile):
        """Write representation of full current state to file."""
        return json.dump(self._archive(), tofile)

    @classmethod
    def loads(cls, fromstr):
        """Read dump'd state from string."""
        archive = json.loads(fromstr)
        return cls(_from_history=archive['history'])

    @classmethod
    def load(cls, fromfile):
        """Read dump'd state from file."""
        archive = json.load(fromfile)
        return cls(_from_history=archive['history'])

    def all_tids(self):
        """Return a set of all task ids."""
        return set(self.tasks.keys())

    def filter(self, **kwargs):
        # Ignore trashed and completed tasks by default.
        if not kwargs.pop('all', False):
            kwargs.setdefault('trashed', False)
            kwargs.setdefault('completed', False)
        fields = set(kwargs.keys()) & set(Task._fields)
        pseudo_fields = set(kwargs.keys()) - set(Task._fields)
        results = []
        for tid, task in self.tasks.items():
            if not all(getattr(task, field) == kwargs[field]
                    for field in fields):
                continue
            pf = {
                'sleeping': self.is_sleeping(tid),
                'blocked': self.is_blocked(tid),
                'delegated': self.is_delegated(tid),
                'active': self.is_infocus(tid),
            }
            if not all(pf[field] == kwargs[field]
                    for field in pseudo_fields):
                continue
            results.append(tid)
        return set(results)

    def active_tids(self):
        """Return a set of active task ids (not completed or trashed)."""
        return set(tid for tid in self.tasks if self.is_active(tid))

    def infocus_tids(self):
        """Return a set of task ids in the infocus set (not sleeping, blocked)."""
        return self.filter(active=True)

    def sleeping_tids(self):
        """Return a set of sleeping task ids (from active tasks)."""
        return self.filter(sleeping=True)

    def blocked_tids(self):
        """Return a set of blocked task ids (from active tasks)."""
        return self.filter(blocked=True)

    def delegated_tids(self):
        """Return a set of delegated task ids (from active tasks)."""
        return self.filter(delegated=True)

    def completed_tids(self):
        """Return a set of completed task ids (that aren't trashed)."""
        return self.filter(completed=True)

    def trashed_tids(self):
        """Return a set of trashed task ids."""
        return self.filter(all=True, trashed=True)

    def is_active(self, tid):
        """Return True if given task id is active (not completed or trashed)."""
        return not (self.is_completed(tid) or self.is_trashed(tid))

    def is_infocus(self, tid):
        """Return True if given task id is infocus (not sleeping, blocked)."""
        return self.is_active(tid) and not (self.is_sleeping(tid) or self.is_blocked(tid))

    def is_sleeping(self, tid):
        """Return True if given task id is sleeping."""
        task = self.get(tid)
        return task.sleepuntil is not None and (task.sleepuntil == -1
                or time.time() < task.sleepuntil)

    def is_blocked(self, tid):
        """Return True if given task id is blocked."""
        task = self.get(tid)
        return any(not self.get(blk_tid).completed
                   for blk_tid in task.blockers)

    def is_delegated(self, tid):
        """Return True if given task id is delegated."""
        task = self.get(tid)
        return task.owner is not None

    def is_completed(self, tid):
        """Return True if given task id is completed."""
        task = self.get(tid)
        return task.completed

    def is_trashed(self, tid):
        """Return True if given task id is trashed."""
        task = self.get(tid)
        return task.trashed

    def is_project(self, tid):
        """Return True if given task id is a project."""
        task = self.get(tid)
        return task.project

    def get(self, tid):
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
            'blockers': [],
            'due': None,
            'labels': [],
            'body': '',
            'created': now,
            'updated': now,
            'trashed': False,
        })
        tid = params["tid"]
        if tid in self.tasks:
            raise BasinError("cannot recreate existing task %d" % tid)
        self._update(**params)
        return tid

    def trash(self, tid):
        """Send a task to the trash."""
        self._update(tid=tid, trashed=True)

    def untrash(self, tid):
        """Remove a task from the trash."""
        self._update(tid=tid, trashed=False)

    def complete(self, tid):
        """Complete a task."""
        self._update(tid=tid, completed=True)

    def uncomplete(self, tid):
        """Mark a task as not complete."""
        self._update(tid=tid, completed=False)

    def sleep(self, tid, wakeup_time=-1):
        """Sleep a task until wakeup_time, or indefinitely if time not provided."""
        self._update(tid=tid, sleepuntil=wakeup_time)

    def unsleep(self, tid):
        """Remove sleep from a task."""
        self._update(tid=tid, sleepuntil=None)

    def delegate(self, tid, owner):
        """Delegate a task to a new owner."""
        self._update(tid=tid, owner=owner)

    def undelegate(self, tid):
        """Un-delegate a task."""
        self._update(tid=tid, owner=None)

    def block(self, blocked_tid, blocking_tid):
        """Mark a task as blocking another."""
        task = self.get(blocked_tid)
        self._update(tid=blocked_tid, blockers=list((set(task.blockers) |
            set([blocking_tid]))))

    def unblock(self, blocked_tid, blocking_tid=None):
        """Mark a task as unblocked. Optionally only remove one blocker."""
        if blocking_tid is None:
            self._update(tid=blocked_tid, blockers=[])
            return
        task = self.get(blocked_tid)
        self._update(tid=blocked_tid, blockers=list((set(task.blockers) -
            set([blocking_tid]))))

    def update(self, tid, **params):
        """Update a task."""
        if tid not in self.tasks:
            raise BasinError("cannot update non-existing tid %d" % tid)
        self._update(tid=tid, **params)

    def _update(self, **params):
        """(Internal) update a task."""
        if 'tid' not in params:
            raise TypeError("update() missing required argument: 'tid'")
        tid = params['tid']
        if tid not in self.tasks:
            self.tasks[tid] = Task(**params)
        else:
            set_defaults(params, {
                'updated': time.time(),
            })
            self.tasks[tid] = self.tasks[tid]._replace(**params)
        self.history.append(params)

    def lowest_available_tid(self):
        """Return the lowest task id that has not yet been used."""
        tid = 0
        while tid in self.tasks:
            tid += 1
        return tid
