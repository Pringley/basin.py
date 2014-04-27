import unittest
import datetime

from basin import Task, global_db_init

class TaskTestCase(unittest.TestCase):

    @classmethod
    def setUp(cls):
        global_db_init(':memory:')

    def test_create_task(self):
        summary = "My first task"
        task = Task.create(summary=summary)
        self.assertEqual(task.summary, summary)

    def test_update_task(self):
        misspelled_summary = "My frist task"
        correct_summary = "My first task"
        task = Task.create(summary=misspelled_summary)
        task.summary = correct_summary
        task.save()
        self.assertEqual(task.summary, correct_summary)

    def test_complete(self):
        task = Task.create()
        self.assertTrue(not task.completed)
        task.complete()
        self.assertTrue(task.completed)

    def test_trash(self):
        task = Task.create()
        self.assertTrue(not task.trashed)
        task.trash()
        self.assertTrue(task.trashed)
        self.assertTrue(not task.is_active())
        task.sleep()
        # self.assertTrue(tid not in tasks.filter(sleeping=True))
        task.unsleep()
        task.delegate("Bob")
        # self.assertTrue(tid not in tasks.filter(delegated=True))
        task.undelegate()
        task2 = Task.create()
        task.block_on(task2)
        # self.assertTrue(tid not in tasks.filter(blocked=True))
        task.unblock()
        task.complete()
        # self.assertTrue(tid not in tasks.filter(completed=True))

    def test_sleep(self):
        now = datetime.datetime.now()
        future = now + datetime.timedelta(days=1)
        past = now - datetime.timedelta(days=1)
        task = Task.create()
        self.assertTrue(not task.is_sleeping())
        task.sleep(future)
        self.assertTrue(task.is_sleeping())
        task.unsleep()
        self.assertTrue(not task.is_sleeping())
        task.sleep()
        self.assertTrue(task.is_sleeping())
        task.unsleep()
        self.assertTrue(not task.is_sleeping())
        task.sleep(past)
        self.assertTrue(not task.is_sleeping())

    def test_block(self):
        task1 = Task.create()
        task2 = Task.create()
        self.assertTrue(not task1.is_blocked())
        self.assertTrue(not task2.is_blocked())
        task1.block_on(task2)
        self.assertTrue(task1.is_blocked())
        self.assertTrue(not task2.is_blocked())
        task1.unblock()
        self.assertTrue(not task1.is_blocked())
        self.assertTrue(not task2.is_blocked())
        task1.block_on(task2)
        task1.unblock(task2)
        self.assertTrue(not task1.is_blocked())
        self.assertTrue(not task2.is_blocked())

    def test_delegate(self):
        task = Task.create()
        self.assertTrue(not task.is_delegated())
        task.delegate('Bob')
        self.assertTrue(task.is_delegated())
        task.undelegate()
        self.assertTrue(not task.is_delegated())

    def test_active(self):
        task = Task.create()
        self.assertTrue(task.is_active())
        task.sleep()
        self.assertTrue(not task.is_active())
        task.unsleep()
        self.assertTrue(task.is_active())
        task2 = Task.create()
        task.block_on(task2)
        self.assertTrue(not task.is_active())
        task.unblock()
        self.assertTrue(task.is_active())
        task.complete()
        self.assertTrue(not task.is_active())
        task.uncomplete()
        self.assertTrue(task.is_active())
        task.trash()
        self.assertTrue(not task.is_active())
        task.untrash()
        self.assertTrue(task.is_active())

if __name__ == '__main__':
    unittest.main()
