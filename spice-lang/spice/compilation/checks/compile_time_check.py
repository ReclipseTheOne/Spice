from abc import ABC, abstractmethod
from spice.compilation.spicefile import SpiceFile

class CompileTimeCheck(ABC):
    @abstractmethod
    def check(self, file: SpiceFile) -> bool:
        """Perform the compile-time check on the given SpiceFile.
        
        Args:
            file (SpiceFile): The Spice file to check.
        
        Returns:
            bool: True if the check passes, False otherwise.
        """
        pass
    