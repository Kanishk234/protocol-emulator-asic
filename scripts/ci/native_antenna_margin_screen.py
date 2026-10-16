"""Reserve native antenna headroom before final timing repair and rerouting."""
from native_shortwire_screen import configure as shortwire_configure
from native_margin_screen import main as margin_screen


def configure(config):
    result = shortwire_configure(config)
    if result.get('GRT_ANTENNA_REPAIR_MARGIN', 10) != 10:
        raise ValueError('Unexpected source antenna repair margin')
    result['GRT_ANTENNA_REPAIR_MARGIN'] = 50
    return result


if __name__ == '__main__':
    margin_screen(config_transform=configure)
