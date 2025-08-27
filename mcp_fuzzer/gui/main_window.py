import sys
import asyncio

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
)

from mcp_fuzzer.client import run_fuzzer


class FuzzerWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(dict)

    def __init__(self, url, runs):
        super().__init__()
        self.url = url
        self.runs = runs

    def run(self):
        async def main():
            async for summary in run_fuzzer(self.url, self.runs):
                self.progress.emit(summary)
            self.finished.emit()

        asyncio.run(main())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCP Fuzzer")

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Form layout for inputs
        form_layout = QFormLayout()
        self.url_input = QLineEdit()
        self.runs_input = QSpinBox()
        self.runs_input.setRange(1, 1000)
        self.runs_input.setValue(10)
        form_layout.addRow(QLabel("Server URL:"), self.url_input)
        form_layout.addRow(QLabel("Runs per tool:"), self.runs_input)
        layout.addLayout(form_layout)

        # Run button
        self.run_button = QPushButton("Run Fuzzer")
        self.run_button.clicked.connect(self.start_fuzzer)
        layout.addWidget(self.run_button)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["Tool", "Total Runs", "Exceptions", "Example Exception", "Error"]
        )
        layout.addWidget(self.results_table)

        # Status bar
        self.statusBar().showMessage("Ready")

    def start_fuzzer(self):
        url = self.url_input.text()
        runs = self.runs_input.value()

        if not url:
            self.statusBar().showMessage("URL cannot be empty.")
            return

        self.run_button.setEnabled(False)
        self.statusBar().showMessage("Fuzzing...")
        self.results_table.setRowCount(0)

        self.thread = QThread()
        self.worker = FuzzerWorker(url, runs)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_table)

        self.thread.start()

        self.thread.finished.connect(
            lambda: self.statusBar().showMessage("Fuzzing finished.")
        )
        self.thread.finished.connect(lambda: self.run_button.setEnabled(True))

    def update_table(self, summary):
        for tool, result in summary.items():
            row_position = self.results_table.rowCount()
            self.results_table.insertRow(row_position)

            error = result.get("error", "")
            total_runs = str(result.get("total_runs", ""))
            exceptions = str(result.get("exceptions", ""))
            example_exception = ""
            if result.get("example_exception"):
                ex = result["example_exception"]
                example_exception = ex.get("exception", "")

            self.results_table.setItem(row_position, 0, QTableWidgetItem(tool))
            self.results_table.setItem(row_position, 1, QTableWidgetItem(total_runs))
            self.results_table.setItem(row_position, 2, QTableWidgetItem(exceptions))
            self.results_table.setItem(
                row_position, 3, QTableWidgetItem(example_exception)
            )
            self.results_table.setItem(row_position, 4, QTableWidgetItem(error))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
