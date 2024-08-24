import sys

from PyQt5.QtWidgets import QApplication
from gui import RedisMonitor

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = RedisMonitor()
    monitor.show()
    sys.exit(app.exec_())
