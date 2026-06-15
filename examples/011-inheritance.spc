# =============================================================================
# Inheritance
# =============================================================================
#
# Python spells inheritance with parentheses: `class Dog(Animal)`. Spice uses an
# `extends` keyword instead:
#
#   class Dog extends Animal { ... }
#
# Everything else is familiar: subclasses inherit attributes and methods, can
# override them, and reach the parent with `super`.
#
# Spice gives `super` a small shortcut: inside a constructor, `super(args)` is
# shorthand for `super().__init__(args)`.


class Animal {
    def Animal(name: str) {
        self.name = name
    }

    def make_sound() -> str {
        return "..."
    }

    def describe() -> str {
        return f"{self.name} says {self.make_sound()}"
    }
}


class Dog extends Animal {
    def Dog(name: str, breed: str) {
        # Shorthand for super().__init__(name)
        super(name)
        self.breed = breed
    }

    # Override a method from the parent.
    def make_sound() -> str {
        return "Woof"
    }

    # Add behaviour specific to Dog.
    def fetch() -> str {
        return f"{self.name} the {self.breed} fetches the ball"
    }
}


class Puppy extends Dog {
    def Puppy(name: str) {
        super(name, "unknown")
    }

    def make_sound() -> str {
        # You can still call up the chain explicitly.
        return f"{super().make_sound()} (but tiny)"
    }
}


def main() -> None {
    animal: Animal = Animal("Generic")
    dog: Dog = Dog("Rex", "Labrador")
    puppy: Puppy = Puppy("Bingo")

    print(animal.describe())
    print(dog.describe())
    print(dog.fetch())
    print(puppy.describe())
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 011-inheritance.spc -o build
#     python build/011-inheritance.py
# -----------------------------------------------------------------------------
