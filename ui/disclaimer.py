"""启动免责声明弹窗。"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                             QTextBrowser, QVBoxLayout)

DISCLAIMER_TEXT = """<h3>⚠️ 法律声明</h3>
<p>本软件仅用于抓取<b>公有领域</b>、<b>作者授权开放</b>的书籍文本，仅供个人学习研究。</p>
<ul>
<li>禁止未经版权方许可抓取受版权保护作品；</li>
<li>禁止将侵权抓取的文本用于二次创作、抖音等平台发布；</li>
<li>请遵守目标网站 robots 协议，控制抓取频率。</li>
</ul>
<p>用户使用本工具产生的一切法律责任由使用者自行承担。</p>
<p style="color:#888;">点击【确认】继续使用。</p>"""


class DisclaimerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("青竹txt书籍下载 - 免责声明")
        self.setModal(True)
        self.resize(480, 360)

        browser = QTextBrowser()
        browser.setHtml(DISCLAIMER_TEXT)
        browser.setOpenExternalLinks(True)

        confirm = QPushButton("确认")
        confirm.setMinimumWidth(140)
        confirm.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(browser)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(confirm)
        row.addStretch()
        layout.addLayout(row)
