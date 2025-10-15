import unittest

import numpy as np
import openmdao
import openmdao.api as om
from openmdao.utils.assert_utils import assert_check_partials, assert_near_equal
from packaging import version

from aviary.subsystems.aerodynamics.gasp_based.table_based import (
    GearDragIncrement,
    TabularCruiseAero,
    TabularLowSpeedAero,
)
from aviary.utils.functions import get_aviary_resource_path
from aviary.variable_info.variables import Aircraft, Dynamic, Mission


class TestCruiseAero(unittest.TestCase):
    def test_climb(self):
        prob = om.Problem()

        fp = 'models/large_single_aisle_1/large_single_aisle_1_aero_free.csv'
        prob.model = TabularCruiseAero(num_nodes=8, aero_data=fp)

        prob.setup(force_alloc_complex=True)

        prob.set_val(Dynamic.Atmosphere.MACH, [0.381, 0.384, 0.391, 0.399, 0.8, 0.8, 0.8, 0.8])
        prob.set_val(
            Dynamic.Vehicle.ANGLE_OF_ATTACK, [5.19, 5.19, 5.19, 5.18, 3.58, 3.81, 4.05, 4.18]
        )
        prob.set_val(
            Dynamic.Mission.ALTITUDE,
            [500, 1000, 2000, 3000, 35000, 36000, 37000, 37500],
        )
        prob.run_model()

        cl_exp = np.array([0.5968, 0.5975, 0.5974, 0.5974, 0.5566, 0.5833, 0.6113, 0.6257])
        cd_exp = np.array([0.0307, 0.0307, 0.0307, 0.0307, 0.0296, 0.0310, 0.0326, 0.0334])

        assert_near_equal(prob['CL'], cl_exp, tolerance=0.005)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.009)

        partial_data = prob.check_partials(method='cs', out_stream=None)
        assert_check_partials(partial_data, atol=4e-7, rtol=2e-7)

    def test_cruise(self):
        prob = om.Problem()
        ref = 'models/large_single_aisle_1/large_single_aisle_1_aero_free.csv'
        fp = get_aviary_resource_path(ref)
        prob.model = TabularCruiseAero(num_nodes=2, aero_data=fp)
        prob.setup(force_alloc_complex=True)

        prob.set_val(Dynamic.Atmosphere.MACH, [0.8, 0.8])
        prob.set_val(Dynamic.Vehicle.ANGLE_OF_ATTACK, [4.216, 3.146])
        prob.set_val(Dynamic.Mission.ALTITUDE, [37500, 37500])
        prob.run_model()

        cl_exp = np.array([0.6304, 0.5059])
        cd_exp = cl_exp / np.array([18.608, 18.425])

        assert_near_equal(prob['CL'], cl_exp, tolerance=0.005)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.005)

        partial_data = prob.check_partials(method='cs', out_stream=None)
        assert_check_partials(partial_data, atol=9e-8, rtol=2e-7)


class TestLowSpeedAero(unittest.TestCase):
    # gear retraction start time at takeoff
    t_init_gear_to = 37.3
    # flap retraction start time at takeoff
    t_init_flaps_to = 47.6
    # takeoff flap deflection (deg)
    flap_defl_to = 10

    free_data = get_aviary_resource_path(
        'models/large_single_aisle_1/large_single_aisle_1_aero_free.csv'
    )
    flaps_data = get_aviary_resource_path(
        'models/large_single_aisle_1/large_single_aisle_1_aero_flaps.csv'
    )
    ground_data = get_aviary_resource_path(
        'models/large_single_aisle_1/large_single_aisle_1_aero_ground.csv'
    )

    def test_groundroll(self):
        # takeoff with flaps applied, gear down, zero alt
        prob = om.Problem()
        prob.model = TabularLowSpeedAero(
            num_nodes=4,
            free_aero_data=self.free_data,
            flaps_aero_data=self.flaps_data,
            ground_aero_data=self.ground_data,
            extrapolate=True,
        )
        prob.model.set_input_defaults(Aircraft.Wing.AREA, val=1370.3)
        prob.setup()

        prob.set_val('t_curr', [0.0, 1.0, 2.0, 3.0])
        prob.set_val(Dynamic.Mission.ALTITUDE, 0)
        prob.set_val(Dynamic.Atmosphere.MACH, [0.0, 0.009, 0.018, 0.026])
        prob.set_val(Mission.Design.GROSS_MASS, 175400.0)
        prob.set_val(Dynamic.Vehicle.ANGLE_OF_ATTACK, 0)
        # TODO set q if we want to test lift/drag forces

        prob.set_val('flap_defl', self.flap_defl_to)
        prob.set_val('t_init_gear', self.t_init_gear_to)
        prob.set_val('t_init_flaps', self.t_init_flaps_to)
        prob.run_model()

        cl_exp = 0.5597 * np.ones(4)
        cd_exp = 0.0572 * np.ones(4)

        # TODO yikes @ tolerances
        assert_near_equal(prob['CL'], cl_exp, tolerance=0.1)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.3)

        partial_data = prob.check_partials(
            method='fd', out_stream=None
        )  # fd because there is a cs in the time ramp
        assert_check_partials(partial_data, atol=3e-7, rtol=6e-5)

    def test_takeoff(self):
        # takeoff crossing flap retraction and gear retraction points
        prob = om.Problem()
        prob.model = TabularLowSpeedAero(
            num_nodes=8,
            free_aero_data=self.free_data,
            flaps_aero_data=self.flaps_data,
            ground_aero_data=self.ground_data,
            extrapolate=True,
        )
        prob.model.set_input_defaults(Aircraft.Wing.AREA, val=1370.3)
        prob.setup()

        prob.set_val(
            't_curr',
            [37.0, 38.0, 39.0, 40.0, 47.0, 48.0, 49.0, 50.0],
        )

        alts = [44.2, 62.7, 84.6, 109.7, 373.0, 419.4, 465.3, 507.8]
        prob.set_val(Dynamic.Mission.ALTITUDE, alts)
        prob.set_val(
            Dynamic.Atmosphere.MACH,
            [0.257, 0.260, 0.263, 0.265, 0.276, 0.277, 0.279, 0.280],
        )
        prob.set_val(
            Dynamic.Vehicle.ANGLE_OF_ATTACK, [8.94, 8.74, 8.44, 8.24, 6.45, 6.34, 6.76, 7.59]
        )
        # TODO set q if we want to test lift/drag forces

        prob.set_val(Aircraft.Wing.SPAN, 117.8)

        prob.set_val('flap_defl', self.flap_defl_to)
        prob.set_val('t_init_gear', self.t_init_gear_to)
        prob.set_val('t_init_flaps', self.t_init_flaps_to)
        prob.set_val(Mission.Design.GROSS_MASS, 175400.0)
        prob.run_model()

        cl_exp = np.array([1.3734, 1.3489, 1.3179, 1.2979, 1.1356, 1.0645, 0.9573, 0.8876])
        cd_exp = np.array([0.1087, 0.1070, 0.1019, 0.0969, 0.0661, 0.0641, 0.0644, 0.0680])

        # TODO yikes @ tolerances
        assert_near_equal(prob['CL'], cl_exp, tolerance=0.02)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.09)

        partial_data = prob.check_partials(
            method='fd', out_stream=None
        )  # fd because there is a cs in the time ramp
        assert_check_partials(
            partial_data, atol=0.255, rtol=5e-7
        )  # fd does very poorly with the t_curr, t_init, and duration values in the time
        # ramp because its step is so much bigger that cs. By decreasing the fd step
        # size you can see that the derivatives are right wrt these values


class GearDragIncrementTest(unittest.TestCase):
    """Test Gear drag coefficient increment."""

    def test_case(self):
        prob = om.Problem()
        prob.model.add_subsystem(
            'drag_inc',
            GearDragIncrement(num_nodes=2),
            promotes_inputs=['*'],
            promotes_outputs=['*'],
        )
        prob.setup(check=False, force_alloc_complex=True)
        prob.set_val(Mission.Design.GROSS_MASS, 175000, 'lbm')
        prob.set_val(Aircraft.Wing.AREA, 1000, 'ft**2')
        prob.set_val('flap_defl', [0.0, 0.3], 'deg')
        prob.run_model()

        assert_near_equal(prob['dCD'], [0.04308, 0.04296], 1e-4)
        partial_data = prob.check_partials(out_stream=None, method='cs')
        assert_check_partials(partial_data, atol=1e-12, rtol=1e-12)


class GearDragIncrementTest2(unittest.TestCase):
    """Test mass-weight conversion."""

    def setUp(self):
        import aviary.subsystems.aerodynamics.gasp_based.table_based as table

        table.GRAV_ENGLISH_LBM = 1.1

    def tearDown(self):
        import aviary.subsystems.aerodynamics.gasp_based.table_based as table

        table.GRAV_ENGLISH_LBM = 1.0

    def test_case(self):
        prob = om.Problem()
        prob.model.add_subsystem(
            'drag_inc',
            GearDragIncrement(num_nodes=2),
            promotes_inputs=['*'],
            promotes_outputs=['*'],
        )
        prob.model.set_input_defaults(Aircraft.Wing.AREA, val=1370.3)
        prob.setup(check=False, force_alloc_complex=True)
        prob.set_val(Mission.Design.GROSS_MASS, 175400.0)

        partial_data = prob.check_partials(out_stream=None, method='cs')
        assert_check_partials(partial_data, atol=1e-12, rtol=1e-12)


class BWBCruiseAeroTest(unittest.TestCase):
    """
    Test of table based BWB cruise using a table generated by a CFD tool.
    The table is modified for demonstration purposes only. It does not represent any actual result.
    """

    def test_climb(self):
        prob = om.Problem()

        fp = 'models/aircraft/blended_wing_body/generic_BWB_GASP_aero.csv'
        prob.model = TabularCruiseAero(num_nodes=3, aero_data=fp)

        prob.setup(force_alloc_complex=True)

        prob.set_val(Dynamic.Atmosphere.MACH, [0.7, 0.8, 0.82])
        prob.set_val(Dynamic.Vehicle.ANGLE_OF_ATTACK, [5.0, 10.0, 2.0])
        prob.set_val(
            Dynamic.Mission.ALTITUDE,
            [10000.0, 30000.0, 35000],
        )
        prob.run_model()

        cl_exp = np.array([0.1509, 0.410764, -0.0384316])
        cd_exp = np.array([0.00610224, 0.0205816, 0.00460256])

        assert_near_equal(prob['CL'], cl_exp, tolerance=0.001)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.001)

        partial_data = prob.check_partials(method='cs', out_stream=None)
        assert_check_partials(partial_data, atol=4e-7, rtol=2e-7)

    def test_cruise(self):
        prob = om.Problem()
        ref = 'models/aircraft/blended_wing_body/generic_BWB_GASP_aero.csv'
        fp = get_aviary_resource_path(ref)
        prob.model = TabularCruiseAero(num_nodes=2, aero_data=fp)
        prob.setup(force_alloc_complex=True)

        prob.set_val(Dynamic.Atmosphere.MACH, [0.8, 0.82])
        prob.set_val(Dynamic.Vehicle.ANGLE_OF_ATTACK, [4.216, 3.146])
        prob.set_val(Dynamic.Mission.ALTITUDE, [37500, 41000])
        prob.run_model()

        cl_exp = np.array([0.1276112, 0.05515637])
        cd_exp = np.array([0.00599297, 0.00570541])

        assert_near_equal(prob['CL'], cl_exp, tolerance=0.001)
        assert_near_equal(prob['CD'], cd_exp, tolerance=0.001)

        partial_data = prob.check_partials(method='cs', out_stream=None)
        assert_check_partials(partial_data, atol=9e-8, rtol=2e-7)


if __name__ == '__main__':
    unittest.main()
