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
    QTabWidget,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
)

from mcp_fuzzer.client import run_fuzzer


class FuzzerWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        async def main():
            async for summary in run_fuzzer(self.settings):
                self.progress.emit(summary)
            self.finished.emit()

        asyncio.run(main())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCP Fuzzer")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # General Tab
        general_tab = QWidget()
        tabs.addTab(general_tab, "General")
        general_layout = QFormLayout(general_tab)

        self.url_input = QLineEdit()
        self.protocol_input = QComboBox()
        self.protocol_input.addItems(["http", "sse", "stdio", "streamablehttp"])
        self.mode_input = QComboBox()
        self.mode_input.addItems(["tools", "protocol", "both"])
        self.verbose_input = QCheckBox()
        self.log_level_input = QComboBox()
        self.log_level_input.addItems(
            ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
        )
        self.log_level_input.setCurrentText("INFO")

        general_layout.addRow(QLabel("Endpoint URL/Command:"), self.url_input)
        general_layout.addRow(QLabel("Protocol:"), self.protocol_input)
        general_layout.addRow(QLabel("Mode:"), self.mode_input)
        general_layout.addRow(QLabel("Verbose Logging:"), self.verbose_input)
        general_layout.addRow(QLabel("Log Level:"), self.log_level_input)

        # Fuzzing Tab
        fuzzing_tab = QWidget()
        tabs.addTab(fuzzing_tab, "Fuzzing")
        fuzzing_layout = QFormLayout(fuzzing_tab)

        self.phase_input = QComboBox()
        self.phase_input.addItems(["realistic", "aggressive", "both"])
        self.runs_input = QSpinBox()
        self.runs_input.setRange(1, 10000)
        self.runs_input.setValue(10)
        self.runs_per_type_input = QSpinBox()
        self.runs_per_type_input.setRange(1, 10000)
        self.runs_per_type_input.setValue(5)
        self.protocol_type_input = QLineEdit()
        self.tool_timeout_input = QSpinBox()
        self.tool_timeout_input.setRange(1, 300)
        self.tool_timeout_input.setValue(30)

        fuzzing_layout.addRow(QLabel("Phase:"), self.phase_input)
        fuzzing_layout.addRow(QLabel("Runs per tool:"), self.runs_input)
        fuzzing_layout.addRow(QLabel("Runs per type:"), self.runs_per_type_input)
        fuzzing_layout.addRow(QLabel("Protocol Type:"), self.protocol_type_input)
        fuzzing_layout.addRow(QLabel("Tool Timeout (s):"), self.tool_timeout_input)

        # Safety Tab
        safety_tab = QWidget()
        tabs.addTab(safety_tab, "Safety")
        safety_layout = QFormLayout(safety_tab)

        self.enable_safety_system_input = QCheckBox()
        self.fs_root_input = QLineEdit()
        self.fs_root_button = QPushButton("...")
        self.fs_root_button.clicked.connect(self.select_fs_root)
        self.safety_plugin_input = QLineEdit()
        self.no_safety_input = QCheckBox()
        self.retry_on_interrupt_input = QCheckBox()

        safety_layout.addRow(
            QLabel("Enable Safety System:"), self.enable_safety_system_input
        )
        fs_root_layout = QHBoxLayout()
        fs_root_layout.addWidget(self.fs_root_input)
        fs_root_layout.addWidget(self.fs_root_button)
        safety_layout.addRow(QLabel("Filesystem Root:"), fs_root_layout)
        safety_layout.addRow(QLabel("Safety Plugin:"), self.safety_plugin_input)
        safety_layout.addRow(QLabel("Disable Argument Filtering:"), self.no_safety_input)
        safety_layout.addRow(
            QLabel("Retry with Safety on Interrupt:"), self.retry_on_interrupt_input
        )

        # Reporting Tab
        reporting_tab = QWidget()
        tabs.addTab(reporting_tab, "Reporting")
        reporting_layout = QFormLayout(reporting_tab)

        self.output_dir_input = QLineEdit()
        self.output_dir_button = QPushButton("...")
        self.output_dir_button.clicked.connect(self.select_output_dir)
        self.safety_report_input = QCheckBox()
        self.export_safety_data_input = QLineEdit()

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(self.output_dir_button)
        reporting_layout.addRow(QLabel("Output Directory:"), output_dir_layout)
        reporting_layout.addRow(QLabel("Show Safety Report:"), self.safety_report_input)
        reporting_layout.addRow(
            QLabel("Export Safety Data:"), self.export_safety_data_input
        )

        # Run button
        self.run_button = QPushButton("Run Fuzzer")
        self.run_button.clicked.connect(self.start_fuzzer)
        layout.addWidget(self.run_button)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["Target", "Total Runs", "Exceptions", "Example Exception", "Error"]
        )
        layout.addWidget(self.results_table)

        # Status bar
        self.statusBar().showMessage("Ready")

    def select_fs_root(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Filesystem Root")
        if directory:
            self.fs_root_input.setText(directory)

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)

    def start_fuzzer(self):
        settings = {
            "url": self.url_input.text(),
            "protocol": self.protocol_input.currentText(),
            "mode": self.mode_input.currentText(),
            "verbose": self.verbose_input.isChecked(),
            "log_level": self.log_level_input.currentText(),
            "phase": self.phase_input.currentText(),
            "runs": self.runs_input.value(),
            "runs_per_type": self.runs_per_type_input.value(),
            "protocol_type": self.protocol_type_input.text(),
            "tool_timeout": self.tool_timeout_input.value(),
            "enable_safety_system": self.enable_safety_system_input.isChecked(),
            "fs_root": self.fs_root_input.text(),
            "safety_plugin": self.safety_plugin_input.text(),
            "no_safety": self.no_safety_input.isChecked(),
            "retry_on_interrupt": self.retry_on_interrupt_input.isChecked(),
            "output_dir": self.output_dir_input.text(),
            "safety_report": self.safety_report_input.isChecked(),
            "export_safety_data": self.export_safety_data_input.text(),
        }

        if not settings["url"]:
            self.statusBar().showMessage("URL/Endpoint cannot be empty.")
            return

        self.run_button.setEnabled(False)
        self.statusBar().showMessage("Fuzzing...")
        self.results_table.setRowCount(0)

        self.thread = QThread()
        self.worker = FuzzerWorker(settings)
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
        for target, result in summary.items():
            row_position = self.results_table.rowCount()
            self.results_table.insertRow(row_position)

            error = result.get("error", "")
            total_runs = str(result.get("total_runs", ""))
            exceptions = str(result.get("exceptions", ""))
            example_exception = ""
            if result.get("example_exception"):
                ex = result["example_exception"]
                example_exception = ex.get("exception", "")

            self.results_table.setItem(row_position, 0, QTableWidgetItem(target))
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
