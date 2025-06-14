from huey import SqliteHuey

huey = SqliteHuey(filename='robotni.db')

# Import tasks to ensure they are registered with this Huey instance
# when the huey consumer (worker) loads this module.
import tasks
