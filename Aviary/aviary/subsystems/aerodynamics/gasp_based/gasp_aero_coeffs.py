import numpy as np
import openmdao.api as om

from aviary.variable_info.functions import add_aviary_input, add_aviary_output
from aviary.variable_info.variables import Aircraft, Mission

SWETFCT = 1.02


class AeroFormfactors(om.ExplicitComponent):
    """Compute aero form factors."""

    def setup(self):
        add_aviary_input(self, Aircraft.Wing.THICKNESS_TO_CHORD_UNWEIGHTED, units='unitless')
        # add_aviary_input(self, Aircraft.Wing.THICKNESS_TO_CHORD_TIP)
        add_aviary_input(self, Aircraft.VerticalTail.THICKNESS_TO_CHORD, units='unitless')
        add_aviary_input(self, Aircraft.HorizontalTail.THICKNESS_TO_CHORD, units='unitless')
        add_aviary_input(self, Aircraft.Strut.THICKNESS_TO_CHORD, units='unitless')
        add_aviary_input(self, Aircraft.Wing.SWEEP, units='rad')
        add_aviary_input(self, Aircraft.VerticalTail.SWEEP, units='rad')
        add_aviary_input(self, Aircraft.HorizontalTail.SWEEP, units='rad')
        add_aviary_input(self, Aircraft.HorizontalTail.VERTICAL_TAIL_FRACTION, units='unitless')
        add_aviary_input(self, Mission.Design.MACH, units='unitless')
        add_aviary_input(self, Aircraft.Nacelle.AVG_DIAMETER, units='ft')
        add_aviary_input(self, Aircraft.Nacelle.AVG_LENGTH, units='ft')

        add_aviary_output(self, Aircraft.Wing.FORM_FACTOR, units='unitless')
        add_aviary_output(self, Aircraft.VerticalTail.FORM_FACTOR, units='unitless')
        add_aviary_output(self, Aircraft.HorizontalTail.FORM_FACTOR, units='unitless')
        add_aviary_output(self, Aircraft.Strut.FUSELAGE_INTERFERENCE_FACTOR, units='unitless')
        add_aviary_output(self, Aircraft.Nacelle.FORM_FACTOR, units='unitless')

    def setup_partials(self):
        self.declare_partials(
            Aircraft.Wing.FORM_FACTOR,
            [Aircraft.Wing.THICKNESS_TO_CHORD_UNWEIGHTED, Mission.Design.MACH, Aircraft.Wing.SWEEP],
        )
        self.declare_partials(
            Aircraft.VerticalTail.FORM_FACTOR,
            [
                Aircraft.VerticalTail.THICKNESS_TO_CHORD,
                Mission.Design.MACH,
                Aircraft.VerticalTail.SWEEP,
            ],
        )
        self.declare_partials(
            Aircraft.HorizontalTail.FORM_FACTOR,
            [
                Aircraft.HorizontalTail.THICKNESS_TO_CHORD,
                Mission.Design.MACH,
                Aircraft.HorizontalTail.SWEEP,
                Aircraft.HorizontalTail.VERTICAL_TAIL_FRACTION,
            ],
        )
        self.declare_partials(
            Aircraft.Strut.FUSELAGE_INTERFERENCE_FACTOR,
            [Aircraft.Strut.THICKNESS_TO_CHORD, Mission.Design.MACH],
        )
        self.declare_partials(
            Aircraft.Nacelle.FORM_FACTOR,
            [Aircraft.Nacelle.AVG_DIAMETER, Aircraft.Nacelle.AVG_LENGTH],
        )

    def compute(self, inputs, outputs):
        tc, tcvt, tcht, tcstrt, rlmc4, rswpvt, rswpht, sah, smn, dbarn, xln = inputs.values()

        ckw = (
            2.0
            * SWETFCT
            * (
                1.0
                + tc * (2.0 - smn**2) * np.cos(rlmc4) / np.sqrt(1.0 - smn**2 * (np.cos(rlmc4)) ** 2)
                + 100.0 * tc**4
            )
        )
        # ckwglt=2.*SWETFCT*(1. +tct*(2.-smn**2)*np.cos(rlmc4) /np.sqrt(1.-smn**2*(np.cos(rlmc4 ))**2) + 100.*tct**4)
        ckvt = (
            2.0
            * SWETFCT
            * (
                1.0
                + tcvt
                * (2.0 - smn**2)
                * np.cos(rswpvt)
                / np.sqrt(1.0 - smn**2 * (np.cos(rswpvt)) ** 2)
                + 100.0 * tcvt**4
            )
        )
        ckht = (
            2.0
            * SWETFCT
            * (
                1.0
                + tcht
                * (2.0 - smn**2)
                * np.cos(rswpht)
                / np.sqrt(1.0 - smn**2 * (np.cos(rswpht)) ** 2)
                + 100.0 * tcht**4
            )
            * (1.0 + 0.05 * (1.0 - sah))
        )
        ckstrt = (
            2.0
            * SWETFCT
            * (1.0 + tcstrt * (2.0 - smn**2) / np.sqrt(1.0 - smn**2) + 100.0 * tcstrt**4)
        )

        ckn = 1.5 * (1.0 + 0.35 / (xln / dbarn))

        outputs[Aircraft.Wing.FORM_FACTOR] = ckw
        # outputs[Aircraft.Winglet.FORM_FACTOR] = ckwglt
        outputs[Aircraft.VerticalTail.FORM_FACTOR] = ckvt
        outputs[Aircraft.HorizontalTail.FORM_FACTOR] = ckht
        outputs[Aircraft.Strut.FUSELAGE_INTERFERENCE_FACTOR] = ckstrt
        outputs[Aircraft.Nacelle.FORM_FACTOR] = ckn

    def compute_partials(self, inputs, J):
        tc, tcvt, tcht, tcstrt, rlmc4, rswpvt, rswpht, sah, smn, dbarn, xln = inputs.values()

        cos1 = np.cos(rlmc4)
        A1 = np.sqrt(1.0 - smn**2 * (cos1) ** 2)
        J[Aircraft.Wing.FORM_FACTOR, Aircraft.Wing.THICKNESS_TO_CHORD_UNWEIGHTED] = (
            2 * SWETFCT * ((2 - smn**2) * cos1 / A1 + 400 * tc**3)
        )
        J[Aircraft.Wing.FORM_FACTOR, Mission.Design.MACH] = (
            -2 * SWETFCT * (tc * smn * cos1) * ((A1**2 + 1 - 2 * cos1**2) / A1**3)
        )
        J[Aircraft.Wing.FORM_FACTOR, Aircraft.Wing.SWEEP] = (
            -2 * SWETFCT * (tc * (2 - smn**2) * np.sin(rlmc4)) * (1 / A1**3)
        )

        cos2 = np.cos(rswpvt)
        A2 = np.sqrt(1.0 - smn**2 * (cos2) ** 2)
        J[Aircraft.VerticalTail.FORM_FACTOR, Aircraft.VerticalTail.THICKNESS_TO_CHORD] = (
            2 * SWETFCT * ((2 - smn**2) * cos2 / A2 + 400 * tcvt**3)
        )
        J[Aircraft.VerticalTail.FORM_FACTOR, Mission.Design.MACH] = (
            -2 * SWETFCT * (tcvt * smn * cos2) * ((A2**2 + 1 - 2 * cos2**2) / A2**3)
        )
        J[Aircraft.VerticalTail.FORM_FACTOR, Aircraft.VerticalTail.SWEEP] = (
            -2 * SWETFCT * (tcvt * (2 - smn**2) * np.sin(rswpvt)) * (1 / A2**3)
        )

        cos3 = np.cos(rswpht)
        A3 = np.sqrt(1.0 - smn**2 * (cos3) ** 2)
        J[Aircraft.HorizontalTail.FORM_FACTOR, Aircraft.HorizontalTail.THICKNESS_TO_CHORD] = (
            2 * SWETFCT * ((2 - smn**2) * cos3 / A3 + 400 * tcht**3) * (1.0 + 0.05 * (1.0 - sah))
        )
        J[Aircraft.HorizontalTail.FORM_FACTOR, Mission.Design.MACH] = (
            -2
            * SWETFCT
            * (tcht * smn * cos3)
            * ((A3**2 + 1 - 2 * cos3**2) / A3**3)
            * (1.0 + 0.05 * (1.0 - sah))
        )
        J[Aircraft.HorizontalTail.FORM_FACTOR, Aircraft.HorizontalTail.SWEEP] = (
            -2
            * SWETFCT
            * (tcht * (2 - smn**2) * np.sin(rswpht))
            * (1 / A3**3)
            * (1.0 + 0.05 * (1.0 - sah))
        )
        J[Aircraft.HorizontalTail.FORM_FACTOR, Aircraft.HorizontalTail.VERTICAL_TAIL_FRACTION] = (
            2 * SWETFCT * (1 + tcht * (2 - smn**2) * cos3 / A3 + 100 * tcht**4) * -0.05
        )

        A4 = np.sqrt(1.0 - smn**2)
        J[Aircraft.Strut.FUSELAGE_INTERFERENCE_FACTOR, Aircraft.Strut.THICKNESS_TO_CHORD] = (
            2 * SWETFCT * ((2 - smn**2) / A4 + 400 * tcstrt**3)
        )
        J[Aircraft.Strut.FUSELAGE_INTERFERENCE_FACTOR, Mission.Design.MACH] = (
            -2 * SWETFCT * (tcstrt * smn) * ((A4**2 - 1) / A4**3)
        )

        J[Aircraft.Nacelle.FORM_FACTOR, Aircraft.Nacelle.AVG_DIAMETER] = 1.5 * 0.35 / xln
        J[Aircraft.Nacelle.FORM_FACTOR, Aircraft.Nacelle.AVG_LENGTH] = -1.5 * 0.35 * dbarn / xln**2
