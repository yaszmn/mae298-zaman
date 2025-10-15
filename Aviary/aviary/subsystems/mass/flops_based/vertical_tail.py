import openmdao.api as om

from aviary.constants import GRAV_ENGLISH_LBM
from aviary.variable_info.functions import add_aviary_input, add_aviary_option, add_aviary_output
from aviary.variable_info.variables import Aircraft, Mission


class VerticalTailMass(om.ExplicitComponent):
    """
    Calculates the mass of the vertical tail(s). The methodology is based on the FLOPS weight
    equations, modified to output mass instead of weight.
    """

    def initialize(self):
        add_aviary_option(self, Aircraft.VerticalTail.NUM_TAILS)

    def setup(self):
        add_aviary_input(self, Aircraft.VerticalTail.AREA, units='ft**2')
        add_aviary_input(self, Aircraft.VerticalTail.TAPER_RATIO, units='unitless')
        add_aviary_input(self, Aircraft.VerticalTail.MASS_SCALER, units='unitless')
        add_aviary_input(self, Mission.Design.GROSS_MASS, units='lbm')

        add_aviary_output(self, Aircraft.VerticalTail.MASS, units='lbm')

    def setup_partials(self):
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):
        num_tails = self.options[Aircraft.VerticalTail.NUM_TAILS]

        area = inputs[Aircraft.VerticalTail.AREA]
        taper_ratio = inputs[Aircraft.VerticalTail.TAPER_RATIO]
        scaler = inputs[Aircraft.VerticalTail.MASS_SCALER]
        gross_weight = inputs[Mission.Design.GROSS_MASS] * GRAV_ENGLISH_LBM

        outputs[Aircraft.VerticalTail.MASS] = (
            scaler
            * 0.32
            * gross_weight**0.30
            * (taper_ratio + 0.50)
            * area**0.85
            * num_tails**0.7
            / GRAV_ENGLISH_LBM
        )

    def compute_partials(self, inputs, J):
        num_tails = self.options[Aircraft.VerticalTail.NUM_TAILS]

        area = inputs[Aircraft.VerticalTail.AREA]
        gross_weight = inputs[Mission.Design.GROSS_MASS] * GRAV_ENGLISH_LBM
        taper_ratio = inputs[Aircraft.VerticalTail.TAPER_RATIO]
        scaler = inputs[Aircraft.VerticalTail.MASS_SCALER]

        gross_weight_exp = gross_weight**0.30
        area_exp = area**0.85
        num_tails_exp = num_tails**0.7

        J[Aircraft.VerticalTail.MASS, Aircraft.VerticalTail.AREA] = (
            scaler
            * 0.272
            * gross_weight_exp
            * (taper_ratio + 0.50)
            * area**-0.15
            * num_tails_exp
            / GRAV_ENGLISH_LBM
        )

        J[Aircraft.VerticalTail.MASS, Mission.Design.GROSS_MASS] = (
            scaler * 0.096 * gross_weight**-0.70 * (taper_ratio + 0.50) * area_exp * num_tails_exp
        )

        J[Aircraft.VerticalTail.MASS, Aircraft.VerticalTail.TAPER_RATIO] = (
            scaler * 0.32 * gross_weight_exp * area_exp * num_tails_exp / GRAV_ENGLISH_LBM
        )

        J[Aircraft.VerticalTail.MASS, Aircraft.VerticalTail.MASS_SCALER] = (
            0.32
            * gross_weight_exp
            * (taper_ratio + 0.50)
            * area_exp
            * num_tails_exp
            / GRAV_ENGLISH_LBM
        )


class AltVerticalTailMass(om.ExplicitComponent):
    """
    Calculates the mass of the vertical tail(s) using the alternate method.
    The methodology is based on the FLOPS weight- equations, modified to
    output mass instead of weight.
    """

    def setup(self):
        add_aviary_input(self, Aircraft.VerticalTail.AREA, units='ft**2')

        add_aviary_input(self, Aircraft.VerticalTail.MASS_SCALER, units='unitless')

        add_aviary_output(self, Aircraft.VerticalTail.MASS, units='lbm')

    def setup_partials(self):
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):
        area = inputs[Aircraft.VerticalTail.AREA]
        scaler = inputs[Aircraft.VerticalTail.MASS_SCALER]

        outputs[Aircraft.VerticalTail.MASS] = scaler * 6.0 * area

    def compute_partials(self, inputs, J):
        area = inputs[Aircraft.VerticalTail.AREA]
        scaler = inputs[Aircraft.VerticalTail.MASS_SCALER]

        J[Aircraft.VerticalTail.MASS, Aircraft.VerticalTail.AREA] = 6.0 * scaler

        J[Aircraft.VerticalTail.MASS, Aircraft.VerticalTail.MASS_SCALER] = 6.0 * area
