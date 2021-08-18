import argparse
import logging
import signal

from . import __version__
from .application import Application

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help="show debug messages")
    parser.add_argument('--version', action='version', version=f"%(prog)s {__version__}")
    return parser.parse_args()

def main():
    args = parse_args()

    logger = logging.getLogger()
    formatter = logging.Formatter(
        "%(asctime)s::%(name)s::%(levelname)s::%(message)s",
        "%Y-%m-%dT%H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    app = Application()

    # Register interupt signal handler
    def signal_handler(signum, frame):
        if signum == signal.SIGINT:
            app.quit()
    signal.signal(signal.SIGINT, signal_handler)

    app.bootstrap()

if __name__ == '__main__':
    main()
