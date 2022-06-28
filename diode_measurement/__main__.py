import argparse
import logging
import signal

from PyQt5 import QtWidgets

from . import __version__
from .application import Application

QT_STYLES = QtWidgets.QStyleFactory().keys()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help="show debug messages")
    parser.add_argument('--style', metavar='<name>', choices=QT_STYLES, help="select Qt style")
    parser.add_argument('--version', action='version', version=f"%(prog)s {__version__}")
    return parser.parse_args()


def configure_logger(debug=False):
    logger = logging.getLogger()
    formatter = logging.Formatter(
        "%(asctime)s::%(name)s::%(levelname)s::%(message)s",
        "%Y-%m-%dT%H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)


def main():
    args = parse_args()

    configure_logger(args.debug)

    app = Application()

    # Register interupt signal handler
    def signal_handler(signum, frame):
        if signum == signal.SIGINT:
            app.quit()
    signal.signal(signal.SIGINT, signal_handler)

    if args.style:
        app.setStyle(args.style)

    app.bootstrap()


if __name__ == '__main__':
    main()
