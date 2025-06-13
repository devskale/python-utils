from huey import FileHuey

# Use file-based Huey (tasks and results stored in ./huey-data/)
huey = FileHuey('my-app', path='./huey-data')

@huey.task()
def add(x, y):
    return x + y
