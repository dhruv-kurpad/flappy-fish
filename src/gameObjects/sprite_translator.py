from typing import List

def generate_sprite(FilePath: str) -> List[List[str]]:
    with open(FilePath, 'r') as file:
        sprite = [list(line[:-1] if line.endswith('\n') else line) for line in file]
    return sprite