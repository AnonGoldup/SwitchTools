"""Pipe (conduit) fill calculator tab - CEC Rule 12-910, Tables 8/9/10,
with Table 5C ampacity derating for conductor count."""

import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QComboBox, QLineEdit, QLabel, QSpinBox, QScrollArea, QPushButton,
    QGroupBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)

from libraries import cec_data


class PipeFillTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinboxes = {}  # wire size -> QSpinBox
        self._build_ui()
        self._rebuild_wire_grid()
        self._recalculate()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- settings -----------------------------------------------------
        settings_box = QGroupBox("Settings")
        form = QFormLayout(settings_box)

        self.conduit_combo = QComboBox()
        self.conduit_combo.addItems(list(cec_data.CONDUIT_TYPES.keys()))
        self.conduit_combo.addItem(cec_data.CUSTOM_CONDUIT)
        self.conduit_combo.currentIndexChanged.connect(self._conduit_changed)
        form.addRow("Conduit type:", self.conduit_combo)

        self.custom_id_edit = QLineEdit()
        self.custom_id_edit.setPlaceholderText("Internal diameter, mm")
        self.custom_id_edit.textChanged.connect(self._recalculate)
        self.custom_id_label = QLabel("Custom internal diameter (mm):")
        form.addRow(self.custom_id_label, self.custom_id_edit)
        self.custom_id_label.hide()
        self.custom_id_edit.hide()

        self.wire_combo = QComboBox()
        self.wire_combo.addItems(list(cec_data.WIRE_TYPES.keys()))
        self.wire_combo.currentIndexChanged.connect(self._wire_type_changed)
        form.addRow("Wire type:", self.wire_combo)

        fill_row = QHBoxLayout()
        self.max_fill_edit = QLineEdit("40")
        self.max_fill_edit.setFixedWidth(70)
        self.max_fill_edit.textChanged.connect(self._recalculate)
        fill_row.addWidget(self.max_fill_edit)
        fill_row.addWidget(QLabel("%"))
        self.table8_hint = QLabel("")
        self.table8_hint.setStyleSheet("color: gray;")
        fill_row.addWidget(self.table8_hint)
        fill_row.addStretch()
        form.addRow("Maximum fill:", fill_row)

        amp_row = QHBoxLayout()
        self.material_combo = QComboBox()
        self.material_combo.addItems(list(cec_data.AMPACITY.keys()))
        self.material_combo.currentIndexChanged.connect(self._recalculate)
        amp_row.addWidget(self.material_combo)
        amp_row.addWidget(QLabel("at"))
        self.temp_combo = QComboBox()
        self.temp_combo.addItems(["60", "75", "90"])
        self.temp_combo.setCurrentText("90")
        self.temp_combo.currentIndexChanged.connect(self._recalculate)
        amp_row.addWidget(self.temp_combo)
        amp_row.addWidget(QLabel("°C termination/insulation"))
        amp_row.addStretch()
        form.addRow("Ampacity basis:", amp_row)

        layout.addWidget(settings_box)

        # --- wire counts ----------------------------------------------------
        counts_box = QGroupBox("Conductor counts (type a quantity beside each size)")
        counts_layout = QVBoxLayout(counts_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_host = QWidget()
        self.wire_grid = QGridLayout(self.grid_host)
        self.wire_grid.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(self.grid_host)
        counts_layout.addWidget(scroll)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Clear all")
        clear_btn.clicked.connect(self._clear_counts)
        clear_row.addWidget(clear_btn)
        counts_layout.addLayout(clear_row)

        layout.addWidget(counts_box, stretch=1)

        # --- results --------------------------------------------------------
        results_box = QGroupBox("Results")
        rform = QFormLayout(results_box)

        self.total_label = QLabel("-")
        rform.addRow("Total conductors / area:", self.total_label)

        self.required_label = QLabel("-")
        f = self.required_label.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)
        self.required_label.setFont(f)
        rform.addRow("Required conduit:", self.required_label)

        self.fill_label = QLabel("-")
        self.fill_label.setFont(f)
        rform.addRow("Fill:", self.fill_label)

        self.derate_label = QLabel("-")
        rform.addRow("Derating (CEC Table 5C):", self.derate_label)

        self.derate_table = QTableWidget(0, 4)
        self.derate_table.setHorizontalHeaderLabels(
            ["Size", "Qty", "Base ampacity (A)", "Derated ampacity (A)"]
        )
        self.derate_table.verticalHeader().setVisible(False)
        self.derate_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.derate_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.derate_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.derate_table.setMaximumHeight(160)
        rform.addRow(self.derate_table)

        layout.addWidget(results_box)

    def _rebuild_wire_grid(self):
        """Rebuild the size/quantity grid for the selected wire type,
        preserving any counts already entered for matching sizes."""
        previous = {size: sb.value() for size, sb in self._spinboxes.items()}
        while self.wire_grid.count():
            item = self.wire_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._spinboxes = {}

        table = cec_data.WIRE_TYPES[self.wire_combo.currentText()]
        sizes = [s for s in cec_data.WIRE_SIZE_ORDER if s in table]

        columns = 3
        rows = math.ceil(len(sizes) / columns)
        for i, size in enumerate(sizes):
            col, row = divmod(i, rows)
            label = QLabel(cec_data.wire_size_label(size))
            spin = QSpinBox()
            spin.setRange(0, 999)
            spin.setValue(previous.get(size, 0))
            spin.valueChanged.connect(self._recalculate)
            self._spinboxes[size] = spin
            self.wire_grid.addWidget(label, row, col * 3)
            self.wire_grid.addWidget(spin, row, col * 3 + 1)
        for col in range(columns):
            self.wire_grid.setColumnMinimumWidth(col * 3 + 2, 30)
        self.wire_grid.setRowStretch(rows, 1)

    # ------------------------------------------------------------- handlers

    def _conduit_changed(self):
        is_custom = self.conduit_combo.currentText() == cec_data.CUSTOM_CONDUIT
        self.custom_id_label.setVisible(is_custom)
        self.custom_id_edit.setVisible(is_custom)
        self._recalculate()

    def _wire_type_changed(self):
        default_temp = cec_data.WIRE_TYPE_TEMP_DEFAULT.get(
            self.wire_combo.currentText()
        )
        if default_temp is not None:
            self.temp_combo.setCurrentText(str(default_temp))
        self._rebuild_wire_grid()
        self._recalculate()

    def _clear_counts(self):
        for sb in self._spinboxes.values():
            sb.blockSignals(True)
            sb.setValue(0)
            sb.blockSignals(False)
        self._recalculate()

    # ---------------------------------------------------------- calculation

    def _recalculate(self):
        table = cec_data.WIRE_TYPES[self.wire_combo.currentText()]
        counts = {}
        total_area = 0.0
        total_count = 0
        for size, sb in self._spinboxes.items():
            n = sb.value()
            if n:
                counts[size] = n
                total_count += n
                total_area += n * table[size]

        hint = cec_data.table8_max_fill_percent(total_count)
        self.table8_hint.setText(
            f"(CEC Table 8 allows {hint}% for {total_count} conductor"
            f"{'s' if total_count != 1 else ''})" if total_count else ""
        )

        self._update_derating(counts, total_count)

        if total_count == 0:
            self.total_label.setText("-")
            self.required_label.setText("-")
            self.fill_label.setText("-")
            return

        self.total_label.setText(f"{total_count} conductors, {total_area:.1f} mm²")

        try:
            max_fill = float(self.max_fill_edit.text())
            if not 0 < max_fill <= 100:
                raise ValueError
        except ValueError:
            self.required_label.setText("Enter a valid max fill % (0-100)")
            self.fill_label.setText("-")
            return

        conduit_name = self.conduit_combo.currentText()
        if conduit_name == cec_data.CUSTOM_CONDUIT:
            self._recalculate_custom(total_area, max_fill)
            return

        areas = cec_data.CONDUIT_TYPES[conduit_name]
        for metric, area in areas.items():
            if total_area <= area * max_fill / 100.0:
                fill_pct = total_area / area * 100.0
                self.required_label.setText(
                    f"{cec_data.TRADE_SIZE_LABELS[metric]}  -  {area:.0f} mm² internal"
                )
                self.fill_label.setText(
                    f"{fill_pct:.1f}%  (limit {max_fill:.0f}% = "
                    f"{area * max_fill / 100.0:.1f} mm²)"
                )
                self.fill_label.setStyleSheet("color: #2e8b2e;")
                return

        largest = list(areas)[-1]
        area = areas[largest]
        self.required_label.setText(
            f"Does not fit in largest size ({cec_data.TRADE_SIZE_LABELS[largest]}) - "
            "split into multiple runs"
        )
        self.fill_label.setText(
            f"{total_area / area * 100.0:.1f}% in {cec_data.TRADE_SIZE_LABELS[largest]}"
        )
        self.fill_label.setStyleSheet("color: #cc3333;")

    def _recalculate_custom(self, total_area: float, max_fill: float):
        try:
            dia = float(self.custom_id_edit.text())
            if dia <= 0:
                raise ValueError
        except ValueError:
            self.required_label.setText("Enter the custom internal diameter (mm)")
            self.fill_label.setText("-")
            return

        area = math.pi / 4.0 * dia * dia
        fill_pct = total_area / area * 100.0
        ok = fill_pct <= max_fill
        self.required_label.setText(
            f"Custom conduit Ø{dia:g} mm  -  {area:.1f} mm² internal"
        )
        self.fill_label.setText(
            f"{fill_pct:.1f}% - {'OK' if ok else 'OVERFILLED'} "
            f"(limit {max_fill:.0f}%)"
        )
        self.fill_label.setStyleSheet(
            "color: #2e8b2e;" if ok else "color: #cc3333;"
        )

    def _update_derating(self, counts: dict, total_count: int):
        """Per-size ampacity after the CEC Table 5C count correction."""
        self.derate_table.setRowCount(0)
        if total_count == 0:
            self.derate_label.setText("-")
            return

        factor = cec_data.table5c_derating_factor(total_count)
        self.derate_label.setText(
            f"{total_count} current-carrying conductors → ×{factor:.2f} "
            f"({factor * 100:.0f}%)"
        )

        material = self.material_combo.currentText()
        temp = int(self.temp_combo.currentText())
        amp_table = cec_data.AMPACITY[material][temp]

        for size in cec_data.WIRE_SIZE_ORDER:
            if size not in counts:
                continue
            base = amp_table.get(size)
            row = self.derate_table.rowCount()
            self.derate_table.insertRow(row)
            values = [
                cec_data.wire_size_label(size),
                str(counts[size]),
                f"{base:g}" if base is not None else "n/a",
                f"{base * factor:.1f}" if base is not None else "n/a",
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.derate_table.setItem(row, col, item)
