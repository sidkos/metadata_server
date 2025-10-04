"""Django management entrypoint.

Provides the main() function to execute administrative tasks.
"""

import os
import sys


def main() -> None:
    """Run administrative tasks.

    Reads Django settings module from environment and delegates to Django's
    command-line utility.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
