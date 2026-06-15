# todo_manager - entry point.
#
# Build & run from this folder:
#     python build.spice.py --run

from models import Task, Priority, Status
from repository import Repository


def main() -> None {
    repo: Repository = Repository()
    repo.add(Task(1, "Write the docs", Priority.HIGH, Status.TODO))
    repo.add(Task(2, "Fix the parser bug", Priority.MEDIUM, Status.DOING))
    repo.add(Task(3, "Ship the release", Priority.HIGH, Status.DONE))

    print(f"{repo.count()} tasks:")

    open_count: int = 0
    for task in repo.all() {
        print(f"  {task.label()}")
        if not task.is_done() {
            open_count = open_count + 1
        }
    }

    print(f"{open_count} still open")
}


main()
