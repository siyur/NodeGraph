# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from PySide2 import QtWidgets, QtCore

import sys
from Python.App import App
from PySide2.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)

    instance = App.instance(software="standalone")
    if instance is not None:
        app.setActiveWindow(instance)
        instance.show()

        try:
            sys.exit(app.exec_())
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()