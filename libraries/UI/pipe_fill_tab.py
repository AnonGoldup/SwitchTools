"""Pipe (conduit) fill calculator tab - CEC Rule 12-910, Tables 8/9/10,
with Table 5C ampacity derating for conductor count."""

import math

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QComboBox, QLineEdit, QLabel, QSpinBox, QScrollArea, QPushButton,
    QGroupBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QCheckBox,
)

from libraries import cec_data

FIND_SMALLEST = "Find the smallest size"

BADGES = {
    "ok": ("Within limit", "#1f7a1f"),
    "over": ("Over limit", "#b42318"),
    "unchecked": ("Not checked", "#6b7280"),
}
WARN_COLOR = BADGES["over"][1]
TIMES = chr(0xD7)


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def _positive_float(text: str):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None


def _resolve_limit(overridden: bool, typed: str, table8: int):
    """Return (limit, capped). A typed limit above Table 8 is capped at it;
    limit is None if the typed text is not a valid number."""
    if not overridden:
        return float(table8), False
    value = _positive_float(typed)
    if value is None:
        return None, False
    if table8 and value > table8:
        return float(table8), True
    return value, False


def _short_type(conduit_name: str) -> str:
    """'EMT (electrical metallic tubing)' -> 'EMT'"""
    return conduit_name.split(" (")[0]


def _size_text(conduit_name: str, metric: str) -> str:
    area = cec_data.CONDUIT_TYPES[conduit_name][metric]
    return (f"{cec_data.TRADE_SIZE_LABELS[metric]} {_short_type(conduit_name)}, "
            f"{area:,.0f} mm² inside")


def _smaller_size_note(conduit_name, metric, total_area, limit) -> str:
    """Why the next size down doesn't work ('' if already the smallest)."""
    areas = cec_data.CONDUIT_TYPES[conduit_name]
    sizes = list(areas)
    idx = sizes.index(metric)
    if idx == 0:
        return ""
    smaller = sizes[idx - 1]
    pct = cec_data.fill_percent(total_area, areas[smaller])
    return (f"One size smaller, {cec_data.TRADE_SIZE_LABELS[smaller]}, "
            f"would be {pct:.1f}% full, over the {limit:g}% limit.")


class CountSpinBox(QSpinBox):
    """Spin box that reads 0 when its text is cleared, instead of keeping the
    last value (which would still be counted in the results)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # QSpinBox.textChanged only fires when the value changes
        self.lineEdit().textChanged.connect(self._text_changed)

    def _text_changed(self, text: str):
        if not text.strip():
            self.setValue(0)
            self.lineEdit().selectAll()  # so the next digit replaces the 0


class PipeFillTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinboxes = {}  # wire size -> QSpinBox
        self._limit_overridden = False
        self._build_ui()
        self._rebuild_size_combo()
        self._rebuild_wire_grid()
        self._recalculate()

    def minimumSizeHint(self):
        # the word-wrapped result labels make the layout height-for-width,
        # which Qt leaves out of the minimum size; without this the window
        # can be shrunk until the sections overlap
        hint = super().minimumSizeHint()
        return hint.expandedTo(
            QSize(hint.width(), self.layout().heightForWidth(hint.width()))
        )

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

        self.size_combo = QComboBox()
        self.size_combo.currentIndexChanged.connect(self._recalculate)
        self.size_label = QLabel("Conduit size:")
        form.addRow(self.size_label, self.size_combo)

        self.wire_combo = QComboBox()
        self.wire_combo.addItems(list(cec_data.WIRE_TYPES.keys()))
        self.wire_combo.currentIndexChanged.connect(self._wire_type_changed)
        form.addRow("Wire type:", self.wire_combo)

        fill_row = QHBoxLayout()
        self.max_fill_edit = QLineEdit()
        self.max_fill_edit.setFixedWidth(70)
        self.max_fill_edit.setPlaceholderText("auto")
        # textEdited (not textChanged) so setting the Table 8 value in code
        # doesn't count as the user overriding it
        self.max_fill_edit.textEdited.connect(self._fill_edited)
        self.max_fill_edit.editingFinished.connect(self._fill_finished)
        fill_row.addWidget(self.max_fill_edit)
        fill_row.addWidget(QLabel("%"))
        self.limit_hint = QLabel("")
        fill_row.addWidget(self.limit_hint)
        self.use_table8_btn = QPushButton("Use Table 8")
        self.use_table8_btn.clicked.connect(self._use_table8)
        self.use_table8_btn.hide()
        fill_row.addWidget(self.use_table8_btn)
        fill_row.addStretch()
        form.addRow("Fill limit:", fill_row)

        amp_row = QHBoxLayout()
        self.material_combo = QComboBox()
        self.material_combo.addItems(list(cec_data.AMPACITY.keys()))
        self.material_combo.currentIndexChanged.connect(self._recalculate)
        amp_row.addWidget(self.material_combo)
        amp_row.addWidget(QLabel("at"))
        self.temp_combo = QComboBox()
        self.temp_combo.addItems(["60", "75", "90"])
        self.temp_combo.setCurrentText("75")  # most terminations are rated 75 °C
        self.temp_combo.currentIndexChanged.connect(self._recalculate)
        amp_row.addWidget(self.temp_combo)
        amp_row.addWidget(QLabel("°C termination/insulation"))
        amp_row.addStretch()
        form.addRow("Ampacity basis:", amp_row)

        bond_row = QHBoxLayout()
        self.add_bond_check = QCheckBox("Add Bond Conductor")
        self.add_bond_check.setChecked(True)
        self.bond_material_combo = QComboBox()
        self.bond_material_combo.addItems(["Copper", "Aluminum"])
        bond_tip = (
            "CEC Table 16: automatic sizing uses the largest selected conductor's "
            "base ampacity at the chosen ampacity basis (not the sum of quantities). "
            "The bond uses the selected wire insulation for fill and is excluded "
            "from Table 5C derating. Verify actual OCP, parallel circuits and "
            "local code requirements separately."
        )
        self.add_bond_check.setToolTip(bond_tip)
        self.bond_material_combo.setToolTip(bond_tip)
        self.add_bond_check.toggled.connect(self.bond_material_combo.setEnabled)
        self.add_bond_check.toggled.connect(self._recalculate)
        self.bond_material_combo.currentIndexChanged.connect(self._recalculate)
        bond_row.addWidget(self.add_bond_check)
        bond_row.addWidget(self.bond_material_combo)
        bond_row.addStretch()
        form.addRow(bond_row)

        layout.addWidget(settings_box)

        # --- wire counts ----------------------------------------------------
        counts_box = QGroupBox("Conductor counts (type a quantity beside each size)")
        counts_layout = QVBoxLayout(counts_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_scroll = scroll
        self.grid_host = QWidget()
        self.wire_grid = QGridLayout(self.grid_host)
        self.wire_grid.setContentsMargins(10, 8, 10, 8)
        self.wire_grid.setHorizontalSpacing(10)
        self.wire_grid.setVerticalSpacing(6)
        scroll.setWidget(self.grid_host)
        counts_layout.addWidget(scroll)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Clear all")
        clear_btn.clicked.connect(self._clear_counts)
        clear_row.addWidget(clear_btn)
        counts_layout.addLayout(clear_row)

        layout.addWidget(counts_box)

        # --- results --------------------------------------------------------
        results_box = QGroupBox("Results")
        rform = QFormLayout(results_box)

        self.total_label = QLabel("-")
        self.total_label.setWordWrap(True)
        rform.addRow("Conductors:", self.total_label)

        self.limit_result_label = QLabel("-")
        self.limit_result_label.setWordWrap(True)
        rform.addRow("Fill limit:", self.limit_result_label)

        big = self.total_label.font()
        big.setBold(True)
        big.setPointSize(big.pointSize() + 2)

        self.conduit_row_label = QLabel("Minimum conduit size:")
        self.required_label = QLabel("-")
        self.required_label.setFont(big)
        rform.addRow(self.conduit_row_label, self.required_label)

        fill_result_row = QHBoxLayout()
        self.fill_label = QLabel("-")
        self.fill_label.setFont(big)
        fill_result_row.addWidget(self.fill_label)
        self.badge = QLabel("")
        self.badge.hide()
        fill_result_row.addWidget(self.badge)
        fill_result_row.addStretch()
        rform.addRow("Fill:", fill_result_row)

        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_row_label = QLabel("")
        rform.addRow(self.detail_row_label, self.detail_label)

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
        layout.addStretch(1)

    def _rebuild_size_combo(self):
        """List the sizes for the current conduit type, keeping the selected
        size if the new type has it."""
        previous = self.size_combo.currentData()
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        self.size_combo.addItem(FIND_SMALLEST, None)
        name = self.conduit_combo.currentText()
        for metric in cec_data.CONDUIT_TYPES.get(name, {}):
            self.size_combo.addItem(cec_data.TRADE_SIZE_LABELS[metric], metric)
        idx = self.size_combo.findData(previous) if previous else 0
        self.size_combo.setCurrentIndex(max(idx, 0))
        self.size_combo.blockSignals(False)

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
            spin = CountSpinBox()
            spin.setRange(0, 999)
            spin.setValue(previous.get(size, 0))
            # sized for a 3-digit count rather than stretched across the column
            spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            spin.setMinimumWidth(80)
            spin.valueChanged.connect(self._recalculate)
            self._spinboxes[size] = spin
            self.wire_grid.addWidget(label, row, col * 3)
            self.wire_grid.addWidget(spin, row, col * 3 + 1)
            # added to a visible parent they'd stay hidden until the next event
            # loop pass, and be left out of the size hint below
            label.show()
            spin.show()
        # each label sits next to its box; spare width is split between the
        # gaps, so the first group lines up left and the last lines up right
        for col in range(columns - 1):
            self.wire_grid.setColumnMinimumWidth(col * 3 + 2, 28)
            self.wire_grid.setColumnStretch(col * 3 + 2, 1)
        self.wire_grid.setRowStretch(rows, 1)
        # never smaller than the grid, so no size is cut off and the window
        # can't be shrunk past it
        self.grid_scroll.setMinimumSize(self.grid_host.sizeHint())

    # ------------------------------------------------------------- handlers

    def _conduit_changed(self):
        is_custom = self.conduit_combo.currentText() == cec_data.CUSTOM_CONDUIT
        self.custom_id_label.setVisible(is_custom)
        self.custom_id_edit.setVisible(is_custom)
        self.size_label.setVisible(not is_custom)
        self.size_combo.setVisible(not is_custom)
        self._rebuild_size_combo()
        self._recalculate()

    def _wire_type_changed(self):
        default_temp = cec_data.WIRE_TYPE_TEMP_DEFAULT.get(
            self.wire_combo.currentText()
        )
        current_temp = int(self.temp_combo.currentText())
        if default_temp is not None and current_temp > default_temp:
            # the insulation rating caps the column (e.g. TW75 can't use 90 °C).
            # signals blocked so the old grid isn't recalculated against the
            # new wire table
            self.temp_combo.blockSignals(True)
            self.temp_combo.setCurrentText(str(default_temp))
            self.temp_combo.blockSignals(False)
        self._rebuild_wire_grid()
        self._recalculate()

    def _fill_edited(self, text: str):
        # an empty box goes back to the Table 8 value
        self._limit_overridden = bool(text.strip())
        self._recalculate()

    def _fill_finished(self):
        # cap a typed limit at the Table 8 maximum once the user is done typing
        table8 = cec_data.table8_max_fill_percent(self._read_fill()[1])
        if _resolve_limit(self._limit_overridden, self.max_fill_edit.text(),
                          table8)[1]:
            self._use_table8()

    def _use_table8(self):
        self._limit_overridden = False
        self._recalculate()

    def _clear_counts(self):
        for sb in self._spinboxes.values():
            sb.blockSignals(True)
            sb.setValue(0)
            sb.blockSignals(False)
        self._recalculate()

    # -------------------------------------------------------------- display

    def _set_badge(self, kind):
        if kind is None:
            self.badge.hide()
            return
        text, color = BADGES[kind]
        self.badge.setText(text)
        self.badge.setStyleSheet(
            f"background-color: {color}; color: white; font-weight: bold;"
            "border-radius: 9px; padding: 2px 10px;"
        )
        self.badge.show()

    def _show(self, conduit_text, fill_text, badge, detail):
        self.required_label.setText(conduit_text)
        self.fill_label.setText(fill_text)
        self._set_badge(badge)
        self.detail_label.setText(detail)
        self.detail_row_label.setText("Why:" if detail else "")

    def _set_hint(self, text, warn=False):
        self.limit_hint.setText(text)
        self.limit_hint.setStyleSheet(
            f"color: {WARN_COLOR}; font-weight: bold;" if warn else "color: gray;"
        )

    def _update_limit_controls(self, table8, total_count, capped):
        n_text = _plural(total_count, "conductor")
        if not self._limit_overridden:
            self.max_fill_edit.setText(str(table8) if total_count else "")
            self._set_hint(f"(CEC Table 8 maximum for {n_text})" if total_count
                           else "(set by CEC Table 8 once you add conductors)")
            self.use_table8_btn.hide()
            return

        self.use_table8_btn.setText(
            f"Use {table8}%" if total_count else "Use Table 8"
        )
        self.use_table8_btn.show()
        if capped:
            self._set_hint(
                f"The CEC Table 8 maximum is {table8}% for {n_text}.", warn=True
            )
        else:
            self._set_hint(f"(your limit; the CEC Table 8 maximum is {table8}%)"
                           if total_count else "(your limit)")

    # ---------------------------------------------------------- calculation

    def _read_counts(self):
        """Return (counts by size, total count, total area in mm²)."""
        table = cec_data.WIRE_TYPES[self.wire_combo.currentText()]
        counts = {s: sb.value() for s, sb in self._spinboxes.items() if sb.value()}
        total_area = sum(n * table[s] for s, n in counts.items())
        return counts, sum(counts.values()), total_area

    def _read_fill(self):
        """Include one automatic bond in fill only, never in current counts."""
        counts, total_count, total_area = self._read_counts()
        bond_text = ""
        error = ""
        if counts and self.add_bond_check.isChecked():
            try:
                material = self.bond_material_combo.currentText()
                size, amps = cec_data.automatic_bond(
                    counts, self.material_combo.currentText(),
                    int(self.temp_combo.currentText()), material
                )
                wire_type = self.wire_combo.currentText()
                area = cec_data.WIRE_TYPES[wire_type].get(size)
                if area is None:
                    raise ValueError("No fill-area data for the required bond size.")
                total_count += 1
                total_area += area
                bond_text = (
                    f"Bond: 1 {TIMES} {cec_data.wire_size_label(size)} {material}, "
                    f"{wire_type}\n"
                    f"CEC Table 16 basis: largest conductor {amps:g} A "
                    "(before derating; verify actual OCP)."
                )
            except ValueError as exc:
                error = f"Cannot size automatic bond: {exc}"
        return counts, total_count, total_area, bond_text, error

    def _recalculate(self):
        counts, total_count, total_area, bond_text, bond_error = self._read_fill()
        table8 = cec_data.table8_max_fill_percent(total_count)
        limit, capped = _resolve_limit(
            self._limit_overridden, self.max_fill_edit.text(), table8
        )
        if capped and not self.max_fill_edit.hasFocus():
            # conductor count changed and the maximum dropped below the
            # typed limit, so reset the box to the maximum
            self._limit_overridden = False
            capped = False
        self._update_limit_controls(table8, total_count, capped)
        self._update_derating(counts, sum(counts.values()))

        conduit_name = self.conduit_combo.currentText()
        is_custom = conduit_name == cec_data.CUSTOM_CONDUIT
        chosen = self.size_combo.currentData()  # None in find mode and for custom
        find_mode = not is_custom and chosen is None
        self.conduit_row_label.setText(
            "Minimum conduit size:" if find_mode else "Conduit size:"
        )

        if total_count == 0:
            self.total_label.setText("-")
            self.limit_result_label.setText("-")
            self._show("-", "-", None, "")
            return

        if bond_error:
            self.total_label.setText(bond_error)
            self.limit_result_label.setText("-")
            self._show("-", "-", "unchecked", "Choose a supported conductor/material "
                       "or disable automatic bonding to calculate fill without a bond.")
            return

        summary = f"{total_count}, total {total_area:.1f} mm²"
        self.total_label.setText(f"{summary}\n{bond_text}" if bond_text else summary)
        n_text = _plural(total_count, "conductor")

        if limit is None:
            self.limit_result_label.setText("Enter a fill limit as a number")
            self._show("-", "-", "unchecked", "")
            return

        own_limit = self._limit_overridden and not capped
        if capped:
            self.limit_result_label.setText(
                f"{table8}% (capped at the CEC Table 8 maximum for {n_text})"
            )
        elif own_limit:
            self.limit_result_label.setText(
                f"{limit:g}% (your limit; the CEC Table 8 maximum is {table8}% "
                f"for {n_text})"
            )
        else:
            self.limit_result_label.setText(
                f"{table8}% (CEC Table 8 maximum for {n_text})"
            )

        pipe = self._pipe_to_check(conduit_name, is_custom, chosen,
                                   total_area, limit)
        if pipe is None:
            self._show("Enter the custom internal diameter (mm)", "-", None, "")
            return
        label, area, metric = pipe
        fill = cec_data.fill_percent(total_area, area)
        if fill <= limit:
            badge = "ok"
            detail = (_smaller_size_note(conduit_name, metric, total_area, limit)
                      if find_mode else "")
        else:
            badge = "over"
            source = "your limit" if own_limit else "CEC Table 8"
            detail = self._over_limit_note(conduit_name, is_custom, find_mode,
                                           total_area, limit, n_text, source)
        self._show(label, f"{fill:.1f}%", badge, detail)

    def _pipe_to_check(self, conduit_name, is_custom, chosen, total_area, limit):
        """Return (label, internal area, trade size) for the pipe being checked,
        or None if the custom diameter is missing. In find mode this is the
        smallest size that fits, or the largest size if none do."""
        if is_custom:
            dia = _positive_float(self.custom_id_edit.text())
            if dia is None:
                return None
            area = math.pi / 4.0 * dia * dia
            return f"Custom Ø{dia:g} mm, {area:,.1f} mm² inside", area, None

        areas = cec_data.CONDUIT_TYPES[conduit_name]
        if chosen is None:
            fit = cec_data.min_conduit_size(conduit_name, total_area, limit)
            if fit is None:
                largest = list(areas)[-1]
                label = (f"Does not fit in the largest size, "
                         f"{cec_data.TRADE_SIZE_LABELS[largest]} "
                         f"{_short_type(conduit_name)}")
                return label, areas[largest], largest
            chosen = fit[0]
        return _size_text(conduit_name, chosen), areas[chosen], chosen

    def _over_limit_note(self, conduit_name, is_custom, find_mode, total_area,
                         limit, n_text, source):
        if find_mode:
            return "Split the run into more than one conduit."
        rule = f"{n_text.capitalize()} may fill {limit:g}% at most ({source})."
        if is_custom:
            return f"{rule} Use a larger pipe or split the run."
        fit = cec_data.min_conduit_size(conduit_name, total_area, limit)
        if fit is None:
            return (f"{rule} It does not fit in the largest size either. "
                    "Split the run.")
        size = cec_data.TRADE_SIZE_LABELS[fit[0]]
        return f"{rule} Use {size} or larger, or split the run."

    def _update_derating(self, counts: dict, total_count: int):
        """Per-size ampacity after the CEC Table 5C count correction."""
        self.derate_table.setRowCount(0)
        if total_count == 0:
            self.derate_label.setText("-")
            return

        factor = cec_data.table5c_derating_factor(total_count)
        self.derate_label.setText(
            f"{total_count} current-carrying conductors → {TIMES}{factor:.2f} "
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
