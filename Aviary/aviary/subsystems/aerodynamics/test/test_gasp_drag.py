"""Tests the aero builder with the 2dof (gasp-based) drag."""

import unittest
from copy import deepcopy

from openmdao.utils.assert_utils import assert_near_equal

from aviary.models.missions.two_dof_default import phase_info
from aviary.interface.methods_for_level2 import AviaryProblem
from aviary.variable_info.variables import Aircraft


class TestAeroBuilderGasp(unittest.TestCase):
    def test_parameters(self):
        # This test is to make sure that the aero builder creates a parameter
        # for wing height. It addresses a bug where this was absent.

        local_phase_info = deepcopy(phase_info)

        prob = AviaryProblem()

        prob.load_inputs(
            'models/aircraft/test_aircraft/aircraft_for_bench_GwGm.csv',
            local_phase_info,
        )

        # Change value just to be certain.
        prob.aviary_inputs.set_val(Aircraft.Wing.HEIGHT, 7.7777, units='ft')

        prob.check_and_preprocess_inputs()

        prob.build_model()

        prob.setup()

        prob.run_model()

        # verify that we are promoting the parameters.
        wing_height = prob.get_val(
            'traj.rotation.rhs_all.aircraft:wing:height',
            units='ft',
        )
        actual_wing_height = prob.aviary_inputs.get_val(Aircraft.Wing.HEIGHT, units='ft')
        assert_near_equal(wing_height, actual_wing_height)


if __name__ == '__main__':
    unittest.main()
