"""行政考勤客户端（Windows）。

核心安全说明：
- 客户端不调用通达 OA 接口。
- 客户端不存储 OA 的 AppID/AppSecret/Token。
- 仅通过服务端授权 API 获取展示数据。
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from datetime import date
from pathlib import Path

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

CACHE_FILE = Path.home() / ".oa_attendance_client.json"


class ApiClient:
    def __init__(self) -> None:
        self.base_url = "https://127.0.0.1:8848"
        self.token = ""
        self.skip_tls_verify = False

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/api/health", timeout=8, verify=not self.skip_tls_verify)
        resp.raise_for_status()
        return resp.json()

    def login(self, username: str, password: str) -> None:
        device_fp = self._device_fingerprint()
        payload = {"username": username, "password": password, "device_fingerprint": device_fp}
        resp = requests.post(f"{self.base_url}/api/auth/login", json=payload, timeout=8, verify=not self.skip_tls_verify)
        resp.raise_for_status()
        self.token = resp.json()["access_token"]

    def query(self, group_id: str, start_date: str, end_date: str) -> dict:
        payload = {"group_id": group_id, "start_date": start_date, "end_date": end_date}
        resp = requests.post(f"{self.base_url}/api/query", json=payload, timeout=12, verify=not self.skip_tls_verify, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _device_fingerprint() -> str:
        raw = f"{platform.node()}|{platform.system()}|{platform.release()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.api = ApiClient()
        self.setWindowTitle("通达OA考勤助手（安全客户端）")
        self.resize(980, 620)
        self._build_ui()
        self._load_cache()

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)

        form = QFormLayout()
        self.server_input = QLineEdit("https://127.0.0.1:8848")
        self.user_input = QLineEdit("admin")
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.group_input = QLineEdit("default")
        self.start_input = QLineEdit(str(date.today().replace(day=1)))
        self.end_input = QLineEdit(str(date.today()))
        self.skip_tls_checkbox = QCheckBox("忽略TLS证书校验（仅测试环境）")
        form.addRow("服务端地址", self.server_input)
        form.addRow("账号", self.user_input)
        form.addRow("密码", self.pwd_input)
        form.addRow("打卡分组ID", self.group_input)
        form.addRow("开始日期", self.start_input)
        form.addRow("结束日期", self.end_input)
        form.addRow("TLS设置", self.skip_tls_checkbox)

        btn_row = QHBoxLayout()
        self.btn_test = QPushButton("测试连通")
        self.btn_login = QPushButton("登录")
        self.btn_query = QPushButton("查询统计")
        self.btn_export = QPushButton("导出CSV")
        btn_row.addWidget(self.btn_test)
        btn_row.addWidget(self.btn_login)
        btn_row.addWidget(self.btn_query)
        btn_row.addWidget(self.btn_export)

        self.status = QLabel("未连接")
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["用户ID", "打卡时间", "类型", "状态", "分组"])

        vbox.addLayout(form)
        vbox.addLayout(btn_row)
        vbox.addWidget(self.status)
        vbox.addWidget(self.table)
        self.setCentralWidget(root)

        self.btn_test.clicked.connect(self.on_test)
        self.btn_login.clicked.connect(self.on_login)
        self.btn_query.clicked.connect(self.on_query)
        self.btn_export.clicked.connect(self.on_export)

    def on_test(self) -> None:
        try:
            self.api.set_base_url(self.server_input.text().strip())
            self.api.skip_tls_verify = self.skip_tls_checkbox.isChecked()
            data = self.api.health()
            self.status.setText(f"服务端正常: {data['server_time']}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "连接失败", str(exc))

    def on_login(self) -> None:
        try:
            self.api.set_base_url(self.server_input.text().strip())
            self.api.skip_tls_verify = self.skip_tls_checkbox.isChecked()
            self.api.login(self.user_input.text().strip(), self.pwd_input.text())
            self.status.setText("登录成功（设备绑定已校验）")
            self._save_cache()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "登录失败", str(exc))

    def on_query(self) -> None:
        try:
            self.api.skip_tls_verify = self.skip_tls_checkbox.isChecked()
            data = self.api.query(self.group_input.text().strip(), self.start_input.text().strip(), self.end_input.text().strip())
            rows = data.get("records", [])
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row["oa_user_id"]))
                self.table.setItem(i, 1, QTableWidgetItem(row["punch_time"]))
                self.table.setItem(i, 2, QTableWidgetItem(row["punch_type"]))
                self.table.setItem(i, 3, QTableWidgetItem(row["status"]))
                self.table.setItem(i, 4, QTableWidgetItem(row["group_id"]))
            self.status.setText(f"查询完成，共 {len(rows)} 条记录")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "查询失败", str(exc))

    def on_export(self) -> None:
        file_path = Path.cwd() / "attendance_export.csv"
        with file_path.open("w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.writer(fp)
            writer.writerow(["用户ID", "打卡时间", "类型", "状态", "分组"])
            for i in range(self.table.rowCount()):
                writer.writerow([self.table.item(i, j).text() if self.table.item(i, j) else "" for j in range(5)])
        QMessageBox.information(self, "导出成功", f"已导出至: {file_path}")

    def _save_cache(self) -> None:
        data = {
            "server": self.server_input.text().strip(),
            "username": self.user_input.text().strip(),
        }
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _load_cache(self) -> None:
        if not CACHE_FILE.exists():
            return
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        self.server_input.setText(data.get("server", "https://127.0.0.1:8848"))
        self.user_input.setText(data.get("username", "admin"))


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    code = app.exec()
    # 客户端退出后清理临时缓存（仅保留连接配置可按需调整）
    if CACHE_FILE.exists():
        CACHE_FILE.unlink(missing_ok=True)
    sys.exit(code)


if __name__ == "__main__":
    main()
