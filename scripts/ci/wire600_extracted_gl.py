"""Expanded functional replay of the exact extracted-path clean preparation."""
from wire600_clean_gl import validate as replay_validate
from wire600_extracted_route import profile


def validate(root, run):
    selected = profile()
    return replay_validate(root, run, bound=selected['binding'],
                           screen_root=selected['screen_root'])
