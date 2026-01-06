# =============================================================================
# Generics in Spice
# =============================================================================
#
# Generics allow you to write type-safe, reusable code that works with
# different types. Spice supports:
#
# 1. Generic classes - class Box<T> { ... }
# 2. Bounded type parameters - class Sorted<T extends Comparable> { ... }
# 3. Multiple type parameters - class Pair<K, V> { ... }
#
# Syntax:
#   class ClassName<T> { ... }
#   class ClassName<T extends Bound> { ... }
#   class ClassName<T, U, V> { ... }
#
# Compiles to Python's typing.Generic with TypeVar.
# =============================================================================

# -----------------------------------------------------------------------------
# Simple Generic Class
# -----------------------------------------------------------------------------
# A container that can hold any type T.
# The type parameter T is used for type safety.

class Box<T> {
    def Box(self, value: T) -> None {
        self.value = value;
    }

    def get() -> T {
        return self.value;
    }

    def set(value: T) -> None {
        self.value = value;
    }
}

# Usage:
# int_box: Box[int] = Box(42)
# str_box: Box[str] = Box("hello")
# print(int_box.get())  # 42


# -----------------------------------------------------------------------------
# Generic with Bounded Type Parameter
# -----------------------------------------------------------------------------
# The type parameter T must extend (implement) Comparable.
# This allows the class to assume T has comparison methods.

interface Comparable {
    def compare_to(other: Comparable) -> int;
}

class SortedBox<T extends Comparable> {
    def SortedBox(self, value: T) -> None {
        self.value = value;
    }

    def is_greater_than(other: T) -> bool {
        return self.value.compare_to(other) > 0;
    }
}


# -----------------------------------------------------------------------------
# Multiple Type Parameters
# -----------------------------------------------------------------------------
# Classes can have multiple type parameters for complex data structures.

class Pair<K, V> {
    def Pair(self, key: K, value: V) -> None {
        self.key = key;
        self.value = value;
    }

    def get_key() -> K {
        return self.key;
    }

    def get_value() -> V {
        return self.value;
    }

    def swap() -> Pair {
        return Pair(self.value, self.key);
    }
}


# -----------------------------------------------------------------------------
# Generic Stack
# -----------------------------------------------------------------------------
# A classic data structure implemented with generics.

class Stack<T> {
    def Stack(self) -> None {
        self.items: list = [];
    }

    def push(item: T) -> None {
        self.items.append(item);
    }

    def pop() -> T {
        return self.items.pop();
    }

    def peek() -> T {
        return self.items[-1];
    }

    def is_empty() -> bool {
        return len(self.items) == 0;
    }

    def size() -> int {
        return len(self.items);
    }
}


# -----------------------------------------------------------------------------
# Generic Queue
# -----------------------------------------------------------------------------
# First-in-first-out data structure.

class Queue<T> {
    def Queue(self) -> None {
        self.items: list = [];
    }

    def enqueue(item: T) -> None {
        self.items.append(item);
    }

    def dequeue() -> T {
        return self.items.pop(0);
    }

    def front() -> T {
        return self.items[0];
    }

    def is_empty() -> bool {
        return len(self.items) == 0;
    }
}


# -----------------------------------------------------------------------------
# Generic Optional/Maybe
# -----------------------------------------------------------------------------
# Represents a value that may or may not be present.

class Optional<T> {
    def Optional(self, value: T, has_value: bool) -> None {
        self._value = value;
        self._has_value = has_value;
    }

    def is_present() -> bool {
        return self._has_value;
    }

    def get() -> T {
        if not self._has_value {
            raise Exception("No value present");
        }
        return self._value;
    }

    def or_else(default_val: T) -> T {
        if self._has_value {
            return self._value;
        }
        return default_val;
    }
}


# -----------------------------------------------------------------------------
# Generic Result/Either
# -----------------------------------------------------------------------------
# Represents either a success value or an error.

class Result<T, E> {
    def Result(self, value: T, error: E, is_ok: bool) -> None {
        self._value = value;
        self._error = error;
        self._is_ok = is_ok;
    }

    def is_ok() -> bool {
        return self._is_ok;
    }

    def is_err() -> bool {
        return not self._is_ok;
    }

    def unwrap() -> T {
        if not self._is_ok {
            raise Exception("Called unwrap on error");
        }
        return self._value;
    }

    def unwrap_err() -> E {
        if self._is_ok {
            raise Exception("Called unwrap_err on ok");
        }
        return self._error;
    }
}


# -----------------------------------------------------------------------------
# Generic Cache/Memoizer
# -----------------------------------------------------------------------------
# A simple key-value cache with generic types.

class Cache<K, V> {
    def Cache(self) -> None {
        self._data: dict = {};
    }

    def put(key: K, value: V) -> None {
        self._data[key] = value;
    }

    def get(key: K) -> V {
        return self._data[key];
    }

    def contains(key: K) -> bool {
        return key in self._data;
    }

    def remove(key: K) -> None {
        del self._data[key];
    }

    def clear() -> None {
        self._data = {};
    }
}


# -----------------------------------------------------------------------------
# Main - Demonstrate Usage
# -----------------------------------------------------------------------------

def main() -> None {
    # Simple generic box
    int_box: Box = Box(42);
    print(f"Box contains: {int_box.get()}");

    str_box: Box = Box("Hello, Generics!");
    print(f"String box: {str_box.get()}");

    # Pair with different types
    pair: Pair = Pair("name", 100);
    print(f"Pair: ({pair.get_key()}, {pair.get_value()})");

    # Generic stack
    stack: Stack = Stack();
    stack.push(1);
    stack.push(2);
    stack.push(3);
    print(f"Stack top: {stack.peek()}");
    print(f"Popped: {stack.pop()}");
    print(f"Stack size: {stack.size()}");

    # Generic queue
    queue: Queue = Queue();
    queue.enqueue("first");
    queue.enqueue("second");
    print(f"Queue front: {queue.front()}");
    print(f"Dequeued: {queue.dequeue()}");

    # Cache
    cache: Cache = Cache();
    cache.put("user:1", "Alice");
    cache.put("user:2", "Bob");
    print(f"Cached user:1 = {cache.get('user:1')}");
    print(f"Contains user:2: {cache.contains('user:2')}");
}

main();
