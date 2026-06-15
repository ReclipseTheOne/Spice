# Domain model for the todo manager.
#
# Two enums describe a task's priority and lifecycle, and a data class ties them
# together with an id and title. The data class auto-generates its constructor,
# repr and equality; the methods are extra behaviour layered on top.

enum Priority {
    LOW,
    MEDIUM,
    HIGH
}


enum Status {
    TODO,
    DOING,
    DONE
}


data class Task(id: int, title: str, priority: Priority, status: Status) {
    def is_done() -> bool {
        return self.status == Status.DONE
    }

    def label() -> str {
        return f"#{self.id} [{self.status.name}/{self.priority.name}] {self.title}"
    }
}
