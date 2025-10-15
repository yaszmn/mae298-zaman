import openmdao.api as om

from aviary.constants import GRAV_ENGLISH_LBM
from aviary.variable_info.functions import add_aviary_input, add_aviary_output
from aviary.variable_info.variables import Aircraft, Mission


class CanardMass(om.ExplicitComponent):
    """
    Calculates the mass of the canard. The methodology is based on the FLOPS weight
    equations, modified to output mass instead of weight.
    """

    def setup(self):
        add_aviary_input(self, Mission.Design.GROSS_MASS, units='lbm')
        add_aviary_input(self, Aircraft.Canard.AREA, units='ft**2')
        add_aviary_input(self, Aircraft.Canard.TAPER_RATIO, units='unitless')
        add_aviary_input(self, Aircraft.Canard.MASS_SCALER, units='unitless')

        add_aviary_output(self, Aircraft.Canard.MASS, units='lbm')

    def setup_partials(self):
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):
        togw = inputs[Mission.Design.GROSS_MASS] * GRAV_ENGLISH_LBM
        area = inputs[Aircraft.Canard.AREA]
        taper_ratio = inputs[Aircraft.Canard.TAPER_RATIO]

        canard_weight = 0.53 * area * togw**0.2 * (taper_ratio + 0.5)
        outputs[Aircraft.Canard.MASS] = (
            canard_weight * inputs[Aircraft.Canard.MASS_SCALER] / GRAV_ENGLISH_LBM
        )

    def compute_partials(self, inputs, J):
        area = inputs[Aircraft.Canard.AREA]
        taper_ratio = inputs[Aircraft.Canard.TAPER_RATIO]
        scaler = inputs[Aircraft.Canard.MASS_SCALER]
        gross_weight = inputs[Mission.Design.GROSS_MASS] * GRAV_ENGLISH_LBM

        gross_weight_exp = gross_weight**0.2

        J[Aircraft.Canard.MASS, Aircraft.Canard.AREA] = (
            0.53 * scaler * (taper_ratio + 0.5) * gross_weight_exp / GRAV_ENGLISH_LBM
        )

        J[Aircraft.Canard.MASS, Aircraft.Canard.TAPER_RATIO] = (
            0.53 * area * scaler * gross_weight_exp / GRAV_ENGLISH_LBM
        )

        J[Aircraft.Canard.MASS, Aircraft.Canard.MASS_SCALER] = (
            0.53 * area * (taper_ratio + 0.5) * gross_weight_exp / GRAV_ENGLISH_LBM
        )

        J[Aircraft.Canard.MASS, Mission.Design.GROSS_MASS] = (
            0.106 * area * scaler * (taper_ratio + 0.5)
        ) / gross_weight**0.8
