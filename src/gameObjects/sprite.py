from typing import List

class Sprite:
    display = List[List[str]]

    def __init__(self, file_path: str):
        self.display = self._generate_display(file_path)

    def _generate_display(self, file_path: str) -> List[List[str]]:
        with open(file_path, 'r') as file:
            display = [list(line[:-1] if line.endswith('\n') else line) for line in file]
        return display