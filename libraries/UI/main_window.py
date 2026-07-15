"""SwitchTools main window."""

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from libraries.UI.pipe_fill_tab import PipeFillTab
from libraries.UI.voltage_drop_tab import VoltageDropTab
from libraries.UI.transformer_tab import TransformerTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwitchTools - CEC Electrical Calculators")
        tabs = QTabWidget()
        tabs.addTab(PipeFillTab(), "Pipe Fill")
        tabs.addTab(VoltageDropTab(), "Voltage Drop")
        tabs.addTab(TransformerTab(), "Transformers")
        self.setCentralWidget(tabs)
        self.resize(880, 780)
