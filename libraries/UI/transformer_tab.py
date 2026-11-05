"""Transformer sizing tab - CEC Rules 26-250s.

- Primary/secondary full-load current from kVA and voltages
- Conductors at 125% of rated current (Rule 26-256), and never smaller than
  the breaker that protects them (Rule 14-104, including the 14-104(2)
  small-conductor limits)
- Primary OCP: max 125%, next standard size permitted (Rule 26-254(1)/(3));
  up to 300% when the secondary has its own OCP at <= 125%, which rounds
  down (Rule 26-254(2))
- Without secondary OCP, the secondary conductors are protected by the
  primary breaker through the voltage ratio (Rule 26-256(4))
"""

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QLabel, QGroupBox, QCheckBox,
)

from libraries import cec_data

SQRT3 = math.sqrt(3.0)


class TransformerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._recalculate()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)

        inputs_box = QGroupBox("Transformer")
        form = QFormLayout(inputs_box)

        self.kva_edit = QLineEdit()
        self.kva_edit.setPlaceholderText("e.g. 75")
        form.addRow("Rating (kVA):", self.kva_edit)

        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["Three-phase", "Single-phase"])
        form.addRow("Phase:", self.phase_combo)

        self.primary_v_edit = QLineEdit("600")
        form.addRow("Primary voltage (V):", self.primary_v_edit)

        self.secondary_v_edit = QLineEdit("208")
        form.addRow("Secondary voltage (V):", self.secondary_v_edit)

        amp_row = QHBoxLayout()
        self.material_combo = QComboBox()
        self.material_combo.addItems(list(cec_data.AMPACITY.keys()))
        amp_row.addWidget(self.material_combo)
        amp_row.addWidget(QLabel("at"))
        self.temp_combo = QComboBox()
        self.temp_combo.addItems(["60", "75", "90"])
        self.temp_combo.setCurrentText("75")
        amp_row.addWidget(self.temp_combo)
        amp_row.addWidget(QLabel("°C termination"))
        amp_row.addStretch()
        form.addRow("Conductors:", amp_row)

        self.secondary_ocp_check = QCheckBox(
            "Secondary overcurrent protection provided (≤ 125%, Rule 26-254)"
        )
        form.addRow(self.secondary_ocp_check)

        layout.addWidget(inputs_box)

        # --- primary results ------------------------------------------------
        bold = self.font()
        bold.setBold(True)
        bold.setPointSize(bold.pointSize() + 1)

        primary_box = QGroupBox("Primary")
        pform = QFormLayout(primary_box)
        self.pri_fla_label = QLabel("-")
        self.pri_fla_label.setFont(bold)
        pform.addRow("Full-load current:", self.pri_fla_label)
        self.pri_wire_label = QLabel("-")
        self.pri_wire_label.setFont(bold)
        pform.addRow("Conductor (125%, Rule 26-256):", self.pri_wire_label)
        self.pri_brk_min_label = QLabel("-")
        pform.addRow("Breaker - recommended:", self.pri_brk_min_label)
        self.pri_brk_max_label = QLabel("-")
        pform.addRow("Breaker - maximum permitted:", self.pri_brk_max_label)
        layout.addWidget(primary_box)

        # --- secondary results ----------------------------------------------
        secondary_box = QGroupBox("Secondary")
        sform = QFormLayout(secondary_box)
        self.sec_fla_label = QLabel("-")
        self.sec_fla_label.setFont(bold)
        sform.addRow("Full-load current:", self.sec_fla_label)
        self.sec_wire_label = QLabel("-")
        self.sec_wire_label.setFont(bold)
        self.sec_wire_label.setWordWrap(True)
        sform.addRow("Conductor (Rule 26-256):", self.sec_wire_label)
        self.sec_brk_label = QLabel("-")
        sform.addRow("Breaker (≤ 125%):", self.sec_brk_label)
        layout.addWidget(secondary_box)

        note = QLabel(
            "Dry-type transformer rules, 750 V or less. Conductors are sized "
            "for the recommended breaker; a larger breaker needs larger "
            "conductors (Rule 14-104). Check Table 5C derating if more than "
            "3 conductors share a raceway."
        )
        note.setStyleSheet("color: gray;")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

        for w in (self.kva_edit, self.primary_v_edit, self.secondary_v_edit):
            w.textChanged.connect(self._recalculate)
        for w in (self.phase_combo, self.material_combo, self.temp_combo):
            w.currentIndexChanged.connect(self._recalculate)
        self.secondary_ocp_check.toggled.connect(self._recalculate)

    # ---------------------------------------------------------- calculation

    @staticmethod
    def _parse(edit: QLineEdit):
        try:
            v = float(edit.text())
            return v if v > 0 else None
        except ValueError:
            return None

    def _clear_results(self):
        for lbl in (self.pri_fla_label, self.pri_wire_label,
                    self.pri_brk_min_label, self.pri_brk_max_label,
                    self.sec_fla_label, self.sec_wire_label,
                    self.sec_brk_label):
            lbl.setText("-")

    def _wire_text(self, required_amps: float, ocp) -> str:
        """Smallest conductor carrying required_amps that may also sit on an
        ocp-amp breaker (Rule 14-104(2))."""
        material = self.material_combo.currentText()
        temp = int(self.temp_combo.currentText())
        result = cec_data.min_conductor_size(required_amps, material, temp, ocp)
        if result is None:
            return (f"needs {required_amps:.1f} A - parallel runs required")
        size, amp = result
        return (f"{cec_data.wire_size_label(size)} {material.lower()} "
                f"({amp} A @ {temp} °C ≥ {required_amps:.1f} A)")

    def _recalculate(self):
        kva = self._parse(self.kva_edit)
        vp = self._parse(self.primary_v_edit)
        vs = self._parse(self.secondary_v_edit)
        if None in (kva, vp, vs):
            self._clear_results()
            return

        three_phase = self.phase_combo.currentIndex() == 0
        divisor_p = vp * SQRT3 if three_phase else vp
        divisor_s = vs * SQRT3 if three_phase else vs
        ip = kva * 1000.0 / divisor_p
        i_sec = kva * 1000.0 / divisor_s

        self.pri_fla_label.setText(f"{ip:.1f} A")
        self.sec_fla_label.setText(f"{i_sec:.1f} A")

        pri_125 = 1.25 * ip
        sec_125 = 1.25 * i_sec
        secondary_ocp = self.secondary_ocp_check.isChecked()

        # primary OCP: the most Rule 26-254 permits
        if secondary_ocp:
            max_brk = cec_data.largest_standard_ocp_at_or_below(3.0 * ip)
            max_text = (f"300% of {ip:.1f} A = {3.0 * ip:.1f} A, "
                        "Rule 26-254(2) with secondary OCP")
        elif ip >= 9:
            max_brk = cec_data.next_standard_ocp(pri_125)
            max_text = "next standard size above 125% permitted, Rule 26-254(3)"
        else:
            # kept at or below 125% for small primary currents
            max_brk = cec_data.largest_standard_ocp_at_or_below(pri_125)
            max_text = "kept at or below 125% (rated current under 9 A)"
        self.pri_brk_max_label.setText(
            f"{max_brk} A  ({max_text})" if max_brk
            else f"125% = {pri_125:.1f} A - below 15 A, use a suitably rated fuse"
        )

        # recommended: the smallest standard size at or above 125%, within
        # the maximum
        next_up = cec_data.next_standard_ocp(pri_125)
        brk = min(next_up, max_brk) if next_up and max_brk else max_brk
        self.pri_brk_min_label.setText(
            f"{brk} A  (125% of {ip:.1f} A = {pri_125:.1f} A)" if brk
            else "below 15 A - use a suitably rated fuse"
        )

        # primary conductors are protected by the recommended breaker
        self.pri_wire_label.setText(self._wire_text(max(pri_125, brk or 0), brk))

        if secondary_ocp:
            # the secondary device must not exceed 125%, so it rounds down
            sec_brk = cec_data.largest_standard_ocp_at_or_below(sec_125)
            self.sec_brk_label.setText(
                f"{sec_brk} A  (largest standard size at or below 125% of "
                f"{i_sec:.1f} A = {sec_125:.1f} A, Rule 26-254(2))" if sec_brk
                else f"125% = {sec_125:.1f} A - below 15 A, use a fuse"
            )
            self.sec_wire_label.setText(self._wire_text(sec_125, sec_brk))
        else:
            # no secondary device: the primary breaker protects the secondary
            # conductors through the voltage ratio (Rule 26-256(4))
            self.sec_brk_label.setText("not selected")
            reflected = brk * vp / vs if brk else 0.0
            text = self._wire_text(max(sec_125, reflected), reflected or None)
            if reflected > sec_125:
                text += (f", for the {brk} A primary breaker seen through "
                         f"the {vp:g}/{vs:g} V ratio")
            self.sec_wire_label.setText(text)
