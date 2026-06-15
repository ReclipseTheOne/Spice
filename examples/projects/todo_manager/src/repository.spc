# A generic in-memory store.
#
# `Repository<T>` works with any element type. Here the entry point uses it as a
# store of `Task`, but nothing in this file mentions Task - that is the point of
# the type parameter `T`.

class Repository<T> {
    def Repository() {
        self.items: list = []
    }

    def add(item: T) -> None {
        self.items.append(item)
    }

    def all() -> list {
        return self.items
    }

    def count() -> int {
        return len(self.items)
    }
}
