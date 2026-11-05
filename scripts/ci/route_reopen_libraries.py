"""Select one resolved timing corner for native master-swap callbacks."""
from fnmatch import fnmatchcase
from pathlib import Path


def select(settings):
    corner = settings['DEFAULT_CORNER']
    paths = list(settings['CELL_LIBS'][corner])
    for macro in settings.get('MACROS', {}).values():
        choices = [value for pattern, value in macro.get('lib', {}).items() if fnmatchcase(corner, pattern)]
        if len(choices) != 1:
            raise ValueError('Missing or ambiguous macro Liberty corner')
        paths.extend(choices[0])
    paths.extend(settings.get('EXTRA_LIBS') or [])
    if not paths or any(not isinstance(p, str) or not Path(p).is_absolute() for p in paths):
        raise ValueError('Expected resolved absolute Liberty paths')
    return list(dict.fromkeys(paths))
