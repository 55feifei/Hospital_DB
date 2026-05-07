"""主窗口：根据登录角色加载对应面板。"""

from PyQt5.QtWidgets import QMainWindow, QStatusBar, QAction, QMessageBox
from PyQt5.QtCore import Qt

from ui.patient_panel import PatientPanel
from ui.doctor_panel import DoctorPanel
from ui.admin_panel  import AdminPanel
from config import APP_NAME, APP_VERSION


ROLE_LABEL = {"admin": "管理员", "doctor": "医生", "patient": "患者"}


class MainWindow(QMainWindow):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}  —  {ROLE_LABEL.get(user['role'], user['role'])}：{user['username']}")
        self.resize(1280, 760)
        self._build_panel()
        self._build_menu()
        self._build_status()

    def _build_panel(self):
        role = self.user["role"]
        if role == "patient":
            self.setCentralWidget(PatientPanel(self.user))
        elif role == "doctor":
            self.setCentralWidget(DoctorPanel(self.user))
        elif role == "admin":
            self.setCentralWidget(AdminPanel(self.user))

    def _build_menu(self):
        bar = self.menuBar()
        m = bar.addMenu("系统")
        a_logout = QAction("退出登录", self)
        a_logout.triggered.connect(self.close)
        m.addAction(a_logout)

        h = bar.addMenu("帮助")
        a_about = QAction("关于", self)
        a_about.triggered.connect(self._about)
        h.addAction(a_about)

    def _build_status(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage(f"已登录：{self.user['username']}（{ROLE_LABEL.get(self.user['role'], self.user['role'])}）")

    def _about(self):
        QMessageBox.about(
            self, "关于",
            f"{APP_NAME}\n版本 {APP_VERSION}"
        )
