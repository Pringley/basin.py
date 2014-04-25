import unittest

from basin import Tasks

class TasksTestCase(unittest.TestCase):

    def test_create_task(self):
        tasks = Tasks()
        title = "My first task"
        tid = tasks.create_task(title=title)

        task = tasks.get_task(tid)
        self.assertEqual(task['title'], title)

    def test_update_task(self):
        tasks = Tasks()
        misspelled_title = "My frist task"
        correct_title = "My first task"
        tid = tasks.create_task(title=misspelled_title)
        tasks.update_task(tid, title=correct_title)

        task = tasks.get_task(tid)
        self.assertEqual(task['title'], correct_title)

if __name__ == '__main__':
    unittest.main()
