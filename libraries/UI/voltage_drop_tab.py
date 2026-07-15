"""Voltage drop calculator tab - CEC Rule 8-102 (3% branch / 5% total)."""

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QLabel, QSpinBox, QGroupBox,
)

from libraries import cec_data

SQRT3 = math.sqrt(3.0)
FT_PER_M = 3.28084


class VoltageDropTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._material_changed()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        inputs_box = QGroupBox("Circuit")
        form = QFormLayout(inputs_box)

        self.voltage_edit = QLineEdit("120")
        form.addRow("System voltage (V):", self.voltage_edit)

        self.phase_combo = QComboBox()
        self.phase_combo.addItems([
            "Single-phase (2-wire)",
            "Three-phase (3-wire / 4-wire)",
        ])
        form.addRow("Phase:", self.phase_combo)

        self.current_edit = QLineEdit()
        self.current_edit.setPlaceholderText("Load current, A")
        form.addRow("Load current (A):", self.current_edit)

        length_row = QHBoxLayout()
        self.length_edit = QLineEdit()
        self.length_edit.setPlaceholderText("One-way run length")
        self.length_unit = QComboBox()
        self.length_unit.addItems(["m", "ft"])
        length_row.addWidget(self.length_edit, stretch=1)
        length_row.addWidget(self.length_unit)
        form.addRow("Run length (one-way):", length_row)

        self.material_combo = QComboBox()
        self.material_combo.addItems(list(cec_data.RESISTANCE_OHM_PER_KM.keys()))
        self.material_combo.currentIndexChanged.connect(self._material_changed)
        form.addRow("Conductor material:", self.material_combo)

        self.size_combo = QComboBox()
        form.addRow("Conductor size:", self.size_combo)

        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 20)
        form.addRow("Parallel sets:", self.parallel_spin)

        self.limit_edit = QLineEdit("3")
        form.addRow("Max voltage drop (%):", self.limit_edit)

        hint = QLabel("CEC 8-102: max 3% for a branch circuit, 5% feeder + branch combined.")
        hint.setStyleSheet("color: gray;")
        form.addRow(hint)

        layout.addWidget(inputs_box)

        results_box = QGroupBox("Results")
        rform = QFormLayout(results_box)

        self.drop_label = QLabel("-")
        f = self.drop_label.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)
        self.drop_label.setFont(f)
        rform.addRow("Voltage drop:", self.drop_label)

        self.load_v_label = QLabel("-")
        rform.addRow("Voltage at load:", self.load_v_label)

        self.status_label = QLabel("-")
        self.status_label.setFont(f)
        rform.addRow("Status:", self.status_label)

        self.min_size_label = QLabel("-")
        rform.addRow("Minimum size for limit:", self.min_size_label)

        self.max_len_label = QLabel("-")
        rform.addRow("Max length at limit (this size):", self.max_len_label)

        layout.addWidget(results_box)
        layout.addStretch()

        for w in (self.voltage_edit, self.current_edit, self.length_edit,
                  self.limit_edit):
            w.textChanged.connect(self._recalculate)
        for w in (self.phase_combo, self.size_combo, self.length_unit):
            w.currentIndexChanged.connect(self._recalculate)
        self.parallel_spin.valueChanged.connect(self._recalculate)

    def _material_changed(self):
        table = cec_data.RESISTANCE_OHM_PER_KM[self.material_combo.currentText()]
        current = self.size_combo.currentText()
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        for size in cec_data.WIRE_SIZE_ORDER:
            if size in table:
                self.size_combo.addItem(cec_data.wire_size_label(size), size)
        idx = self.size_combo.findText(current)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)
        self.size_combo.blockSignals(False)
        self._recalculate()

    # ---------------------------------------------------------- calculation

    @staticmethod
    def _parse(edit: QLineEdit):
        try:
            v = float(edit.text())
            return v if v > 0 else None
        except ValueError:
            return None

    def _clear_results(self, msg="-"):
        for lbl in (self.drop_label, self.load_v_label, self.status_label,
                    self.min_size_label, self.max_len_label):
            lbl.setText(msg)
        self.status_label.setStyleSheet("")

    def _recalculate(self):
        voltage = self._parse(self.voltage_edit)
        current = self._parse(self.current_edit)
        length = self._parse(self.length_edit)
        limit = self._parse(self.limit_edit)
        if None in (voltage, current, length) or self.size_combo.count() == 0:
            self._clear_results()
            return

        unit = self.length_unit.currentText()
        length_m = length / FT_PER_M if unit == "ft" else length
        multiplier = 2.0 if self.phase_combo.currentIndex() == 0 else SQRT3
        sets = self.parallel_spin.value()

        table = cec_data.RESISTANCE_OHM_PER_KM[self.material_combo.currentText()]
        size = self.size_combo.currentData()
        r_per_km = table[size] / sets

        drop = multiplier * current * length_m * r_per_km / 1000.0
        pct = drop / voltage * 100.0

        self.drop_label.setText(f"{drop:.2f} V  ({pct:.2f}%)")
        self.load_v_label.setText(f"{voltage - drop:.2f} V")

        if limit is None:
            self.status_label.setText("Enter a valid max VD %")
            self.min_size_label.setText("-")
            self.max_len_label.setText("-")
            return

        ok = pct <= limit
        self.status_label.setText(
            f"OK - within {limit:g}% limit" if ok else f"EXCEEDS {limit:g}% limit"
        )
        self.status_label.setStyleSheet(
            "color: #2e8b2e;" if ok else "color: #cc3333;"
        )

        # smallest size meeting the limit under the same conditions
        min_size = None
        for s in cec_data.WIRE_SIZE_ORDER:
            if s not in table:
                continue
            d = multiplier * current * length_m * (table[s] / sets) / 1000.0
            if d / voltage * 100.0 <= limit:
                min_size = s
                break
        self.min_size_label.setText(
            cec_data.wire_size_label(min_size) if min_size
            else "None - increase parallel sets or voltage"
        )

        # max one-way length for the selected size at the limit
        max_len_m = limit / 100.0 * voltage * 1000.0 / (multiplier * current * r_per_km)
        if unit == "ft":
            self.max_len_label.setText(f"{max_len_m * FT_PER_M:.1f} ft "
                                       f"({max_len_m:.1f} m)")
        else:
            self.max_len_label.setText(f"{max_len_m:.1f} m "
                                       f"({max_len_m * FT_PER_M:.1f} ft)")
