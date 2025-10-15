import numpy as np
from openmdao.api import ExplicitComponent

from aviary.examples.external_subsystems.battery.battery_variable_meta_data import ExtendedMetaData
from aviary.examples.external_subsystems.battery.battery_variables import Aircraft, Dynamic
from aviary.variable_info.functions import add_aviary_input, add_aviary_output


class CellComp(ExplicitComponent):
    """Compute behavior of a single battery cell then expand to the full pack."""

    def initialize(self):
        self.options.declare('num_nodes', types=int)

    def setup(self):
        n = self.options['num_nodes']

        # Inputs
        add_aviary_input(
            self,
            Dynamic.Battery.CURRENT,
            val=3.25 * np.ones(n),
            meta_data=ExtendedMetaData,
        )
        # Static Constants
        add_aviary_input(
            self, Aircraft.Battery.Cell.ENERGY_CAPACITY_MAX, meta_data=ExtendedMetaData
        )
        add_aviary_input(self, Aircraft.Battery.N_PARALLEL, val=40.0, meta_data=ExtendedMetaData)
        add_aviary_input(self, Aircraft.Battery.N_SERIES, val=128.0, meta_data=ExtendedMetaData)
        # Integrated State Variables
        add_aviary_input(
            self,
            Dynamic.Battery.STATE_OF_CHARGE,
            val=0.98 * np.ones(n),
            meta_data=ExtendedMetaData,
        )
        add_aviary_input(
            self,
            Dynamic.Battery.VOLTAGE_THEVENIN,
            val=np.ones(n),
            meta_data=ExtendedMetaData,
        )
        # Map Inputs From The Interpolation Component
        self.add_input('U_oc', val=4.16 * np.ones(n), units='V', desc='Open-circuit voltage')
        self.add_input(
            'C_Th',
            val=2000.0 * np.ones(n),
            units='F',
            desc='Thevenin RC parallel capacitance (polarization)',
        )
        self.add_input(
            'R_Th',
            val=0.01 * np.ones(n),
            units='ohm',
            desc='Thevenin RC parallel resistance (polarization)',
        )
        self.add_input(
            'R_0', val=0.01 * np.ones(n), units='ohm', desc='Internal resistance of the battery'
        )

        # Outputs
        add_aviary_output(
            self,
            Dynamic.Battery.STATE_OF_CHARGE_RATE,
            val=np.ones(n),
            meta_data=ExtendedMetaData,
        )
        add_aviary_output(
            self,
            Dynamic.Battery.VOLTAGE_THEVENIN_RATE,
            val=np.ones(n),
            meta_data=ExtendedMetaData,
        )
        add_aviary_output(
            self,
            Dynamic.Battery.VOLTAGE,
            val=416 * np.ones(n),
            meta_data=ExtendedMetaData,
        )
        add_aviary_output(
            self, Dynamic.Battery.HEAT_OUT, val=np.ones(n), meta_data=ExtendedMetaData
        )
        add_aviary_output(
            self, Dynamic.Battery.EFFICIENCY, val=np.ones(n), meta_data=ExtendedMetaData
        )

        # Partials
        self.declare_partials(of='*', wrt='*', dependent=False)
        ar = np.arange(n)

        self.declare_partials(
            of=Dynamic.Battery.STATE_OF_CHARGE_RATE,
            wrt=Dynamic.Battery.CURRENT,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(
            of=Dynamic.Battery.STATE_OF_CHARGE_RATE, wrt=Aircraft.Battery.N_PARALLEL
        )
        self.declare_partials(
            of=Dynamic.Battery.STATE_OF_CHARGE_RATE,
            wrt=Aircraft.Battery.Cell.ENERGY_CAPACITY_MAX,
        )

        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE_THEVENIN_RATE,
            wrt=Dynamic.Battery.VOLTAGE_THEVENIN,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE_THEVENIN_RATE, wrt='R_Th', rows=ar, cols=ar
        )
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE_THEVENIN_RATE, wrt='C_Th', rows=ar, cols=ar
        )
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE_THEVENIN_RATE,
            wrt=Dynamic.Battery.CURRENT,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE_THEVENIN_RATE, wrt=Aircraft.Battery.N_PARALLEL
        )

        self.declare_partials(of=Dynamic.Battery.VOLTAGE, wrt='U_oc', rows=ar, cols=ar)
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE,
            wrt=Dynamic.Battery.VOLTAGE_THEVENIN,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(
            of=Dynamic.Battery.VOLTAGE, wrt=Dynamic.Battery.CURRENT, rows=ar, cols=ar
        )
        self.declare_partials(of=Dynamic.Battery.VOLTAGE, wrt=Aircraft.Battery.N_PARALLEL)
        self.declare_partials(of=Dynamic.Battery.VOLTAGE, wrt='R_0', rows=ar, cols=ar)
        self.declare_partials(of=Dynamic.Battery.VOLTAGE, wrt=Aircraft.Battery.N_SERIES)

        self.declare_partials(
            of=Dynamic.Battery.HEAT_OUT, wrt=Dynamic.Battery.CURRENT, rows=ar, cols=ar
        )
        self.declare_partials(of=Dynamic.Battery.HEAT_OUT, wrt=Aircraft.Battery.N_PARALLEL)
        self.declare_partials(of=Dynamic.Battery.HEAT_OUT, wrt=Aircraft.Battery.N_SERIES)
        self.declare_partials(of=Dynamic.Battery.HEAT_OUT, wrt='R_0', rows=ar, cols=ar)
        self.declare_partials(
            of=Dynamic.Battery.HEAT_OUT,
            wrt=Dynamic.Battery.VOLTAGE_THEVENIN,
            rows=ar,
            cols=ar,
        )

        self.declare_partials(
            of=Dynamic.Battery.EFFICIENCY,
            wrt=Dynamic.Battery.CURRENT,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(of=Dynamic.Battery.EFFICIENCY, wrt=Aircraft.Battery.N_PARALLEL)
        # self.declare_partials(of=Dynamic.Battery.EFFICIENCY, wrt=Aircraft.Battery.N_SERIES, rows=ar, cols=ar) # known 0
        self.declare_partials(of=Dynamic.Battery.EFFICIENCY, wrt='R_0', rows=ar, cols=ar)
        self.declare_partials(
            of=Dynamic.Battery.EFFICIENCY,
            wrt=Dynamic.Battery.VOLTAGE_THEVENIN,
            rows=ar,
            cols=ar,
        )
        self.declare_partials(of=Dynamic.Battery.EFFICIENCY, wrt='U_oc', rows=ar, cols=ar)

    def compute(self, inputs, outputs):
        C_Th = inputs['C_Th']
        R_Th = inputs['R_Th']
        U_Th = inputs[Dynamic.Battery.VOLTAGE_THEVENIN]
        R_0 = inputs['R_0']
        Q_max = inputs[Aircraft.Battery.Cell.ENERGY_CAPACITY_MAX]
        U_oc = inputs['U_oc']
        n_p = inputs[Aircraft.Battery.N_PARALLEL]
        n_s = inputs[Aircraft.Battery.N_SERIES]
        I_pack = inputs[Dynamic.Battery.CURRENT]

        # cell
        I_Li = I_pack / n_p
        outputs[Dynamic.Battery.STATE_OF_CHARGE_RATE] = -I_Li / (
            3600.0 * Q_max
        )  # conversion from hours to seconds
        outputs[Dynamic.Battery.VOLTAGE_THEVENIN_RATE] = -U_Th / (R_Th * C_Th) + I_Li / C_Th
        U_L = U_oc - U_Th - (I_Li * R_0)

        # thermal
        Q_cell = I_Li**2 * (R_0 + U_Th / I_Li)

        # pack
        outputs[Dynamic.Battery.VOLTAGE] = U_L * n_s
        outputs[Dynamic.Battery.HEAT_OUT] = Q_cell * n_s * n_p
        P_tot = I_pack * outputs[Dynamic.Battery.VOLTAGE]
        outputs[Dynamic.Battery.EFFICIENCY] = 1.0 - outputs[Dynamic.Battery.HEAT_OUT] / (
            P_tot + outputs[Dynamic.Battery.HEAT_OUT]
        )

    def compute_partials(self, inputs, partials):
        C_Th = inputs['C_Th']
        R_Th = inputs['R_Th']
        U_Th = inputs[Dynamic.Battery.VOLTAGE_THEVENIN]
        R_0 = inputs['R_0']
        Q_max = inputs[Aircraft.Battery.Cell.ENERGY_CAPACITY_MAX]
        U_oc = inputs['U_oc']
        n_p = inputs[Aircraft.Battery.N_PARALLEL]
        n_s = inputs[Aircraft.Battery.N_SERIES]
        I_pack = inputs[Dynamic.Battery.CURRENT]

        I_Li = I_pack / n_p
        U_L = U_oc - U_Th - (I_Li * R_0)
        Q_cell = I_Li**2 * (R_0 + U_Th / I_Li)
        U_pack = U_L * n_s
        Q_pack = Q_cell * n_s * n_p
        P_tot = I_pack * U_pack

        dI_li__dnp = -I_pack / n_p**2
        dU_L__dnp = -R_0 * dI_li__dnp
        dU_pack__dnp = dU_L__dnp * n_s
        dQ_cell__dnp = 2 * I_Li * dI_li__dnp * (R_0 + U_Th / I_Li) - U_Th * dI_li__dnp
        dQ_pack__dnp = n_s * (dQ_cell__dnp * n_p + Q_cell)
        dPtot__dnp = I_pack * dU_pack__dnp
        dpack_eta__dnp = -dQ_pack__dnp / (P_tot + Q_pack) + Q_pack / (P_tot + Q_pack) ** 2 * (
            dPtot__dnp + dQ_pack__dnp
        )

        dI_li__dI_pack = 1 / n_p
        dQ_cell__dI_pack = 2 * I_Li * dI_li__dI_pack * (R_0 + U_Th / I_Li) - U_Th * dI_li__dI_pack
        dQ_pack__dI_pack = dQ_cell__dI_pack * n_s * n_p
        dU_pack__dI_pack = -R_0 * n_s / n_p
        dPtot__dI_pack = U_pack + dU_pack__dI_pack * I_pack
        dpack_eta__dI_pack = -dQ_pack__dI_pack / (P_tot + Q_pack) + Q_pack / (
            P_tot + Q_pack
        ) ** 2 * (dPtot__dI_pack + dQ_pack__dI_pack)

        dPtot__dU_th = -I_pack * n_s
        dQ_pack_dU_th = I_pack * n_s
        dpack_eta__dU_t = -dQ_pack_dU_th / (P_tot + Q_pack) + Q_pack / (P_tot + Q_pack) ** 2 * (
            dPtot__dU_th + dQ_pack_dU_th
        )

        dU_pack__dR_0 = -I_pack * n_s / n_p
        dPtot__dR_0 = I_pack * dU_pack__dR_0
        dQ_pack__dR_0 = (I_pack**2 * n_s) / n_p
        dpack_eta__dR_0 = -dQ_pack__dR_0 / (P_tot + Q_pack) + Q_pack / (P_tot + Q_pack) ** 2 * (
            dPtot__dR_0 + dQ_pack__dR_0
        )

        dPtot__dU_oc = I_pack * n_s
        dpack_eta__dU_oc = Q_pack / (P_tot + Q_pack) ** 2 * dPtot__dU_oc

        partials[Dynamic.Battery.STATE_OF_CHARGE_RATE, Dynamic.Battery.CURRENT] = -1.0 / (
            3600.0 * Q_max * n_p
        )
        partials[Dynamic.Battery.STATE_OF_CHARGE_RATE, Aircraft.Battery.N_PARALLEL] = I_pack / (
            3600.0 * Q_max * n_p**2
        )
        partials[
            Dynamic.Battery.STATE_OF_CHARGE_RATE,
            Aircraft.Battery.Cell.ENERGY_CAPACITY_MAX,
        ] = I_pack / (3600.0 * n_p * Q_max**2)

        partials[Dynamic.Battery.VOLTAGE_THEVENIN_RATE, Dynamic.Battery.VOLTAGE_THEVENIN] = -1.0 / (
            R_Th * C_Th
        )
        partials[Dynamic.Battery.VOLTAGE_THEVENIN_RATE, 'R_Th'] = U_Th / (C_Th * R_Th**2)
        partials[Dynamic.Battery.VOLTAGE_THEVENIN_RATE, 'C_Th'] = (n_p * U_Th - I_pack * R_Th) / (
            C_Th**2 * n_p * R_Th
        )
        partials[Dynamic.Battery.VOLTAGE_THEVENIN_RATE, Dynamic.Battery.CURRENT] = 1.0 / (
            C_Th * n_p
        )
        partials[Dynamic.Battery.VOLTAGE_THEVENIN_RATE, Aircraft.Battery.N_PARALLEL] = -I_pack / (
            C_Th * n_p**2
        )

        partials[Dynamic.Battery.VOLTAGE, 'U_oc'] = n_s
        partials[Dynamic.Battery.VOLTAGE, Dynamic.Battery.VOLTAGE_THEVENIN] = -n_s
        partials[Dynamic.Battery.VOLTAGE, 'R_0'] = dU_pack__dR_0
        partials[Dynamic.Battery.VOLTAGE, Aircraft.Battery.N_PARALLEL] = dU_pack__dnp
        partials[Dynamic.Battery.VOLTAGE, Dynamic.Battery.CURRENT] = dU_pack__dI_pack
        partials[Dynamic.Battery.VOLTAGE, Aircraft.Battery.N_SERIES] = (
            U_oc - U_Th - (I_pack / n_p * R_0)
        )

        partials[Dynamic.Battery.HEAT_OUT, Dynamic.Battery.CURRENT] = n_s * (
            (2 * I_pack * R_0) / n_p + U_Th
        )
        partials[Dynamic.Battery.HEAT_OUT, Aircraft.Battery.N_PARALLEL] = dQ_pack__dnp
        partials[Dynamic.Battery.HEAT_OUT, 'R_0'] = (I_pack**2 * n_s) / n_p
        partials[Dynamic.Battery.HEAT_OUT, Dynamic.Battery.VOLTAGE_THEVENIN] = dQ_pack_dU_th
        partials[Dynamic.Battery.HEAT_OUT, Aircraft.Battery.N_SERIES] = (
            I_pack**2 * ((n_p * U_Th) / I_pack + R_0)
        ) / n_p

        partials[Dynamic.Battery.EFFICIENCY, 'U_oc'] = dpack_eta__dU_oc
        partials[Dynamic.Battery.EFFICIENCY, Aircraft.Battery.N_PARALLEL] = dpack_eta__dnp
        partials[Dynamic.Battery.EFFICIENCY, Dynamic.Battery.CURRENT] = dpack_eta__dI_pack
        partials[Dynamic.Battery.EFFICIENCY, 'R_0'] = dpack_eta__dR_0
        partials[Dynamic.Battery.EFFICIENCY, Dynamic.Battery.VOLTAGE_THEVENIN] = dpack_eta__dU_t
        # partials[Dynamic.Battery.EFFICIENCY,Aircraft.Battery.N_SERIES] = 0.
