"""Boot entry point. MicroPython automatically runs the file named
main.py on every power-up/reset - this just starts the real monitoring
loop in plant_status.py, so the device runs standalone with no laptop
or mpremote connection needed."""

import plant_status  # noqa: F401  pylint: disable=unused-import
