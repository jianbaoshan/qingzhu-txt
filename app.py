"""青竹txt书籍下载 - 书籍 TXT 批量下载器

运行：python app.py
"""
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.disclaimer import DisclaimerDialog
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("青竹txt书籍下载")
    app.setStyle("Fusion")

    # 启动免责弹窗
    disclaimer = DisclaimerDialog()
    if disclaimer.exec() != DisclaimerDialog.DialogCode.Accepted:
        return

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
