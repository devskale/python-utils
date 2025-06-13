from huey import SqliteHuey

huey = SqliteHuey(filename='robotni_tasks.db')


@huey.task()
def example_task(x, y):
    return x + y
