"""程序入口。"""

import sys
import os

# 让 src/ 内子模块可直接 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修复 conda 环境下 Qt 平台插件查找问题（Windows）
import PyQt5
_pyqt_dir = os.path.dirname(PyQt5.__file__)
_plugins  = os.path.join(_pyqt_dir, "Qt5", "plugins")
if os.path.isdir(_plugins):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(_plugins, "platforms")
    os.environ["QT_PLUGIN_PATH"] = _plugins

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.login_window import LoginWindow
from ui.main_window  import MainWindow
from ui.theme        import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    apply_theme(app)

    holder = {"win": None}

    def on_success(user):
        holder["win"] = MainWindow(user)
        holder["win"].show()

    login = LoginWindow(on_success)
    login.show()

    sys.exit(app.exec_())

# 程序入口
if __name__ == "__main__":
    main()
