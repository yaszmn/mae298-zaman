import unittest
from copy import deepcopy

from openmdao.core.problem import _clear_problem_names
from openmdao.utils.assert_utils import assert_near_equal
from openmdao.utils.testing_utils import require_pyoptsparse, use_tempdirs

from aviary.models.missions.two_dof_default import phase_info

from aviary.interface.methods_for_level1 import run_aviary
from aviary.variable_info.variables import Aircraft, Mission


@use_tempdirs
class ProblemPhaseTestCase(unittest.TestCase):
    """
    Test the setup and run of a BWB aircraft using GASP mass and aero method
    and TWO_DEGREES_OF_FREEDOM mission method. Expected outputs based on
    'models/aircraft/blended_wing_body/generic_BWB_GASP.csv' model.
    """

    def setUp(self):
        _clear_problem_names()  # need to reset these to simulate separate runs

    @require_pyoptsparse(optimizer='SNOPT')
    def test_bench_bwb_GwGm_SNOPT(self):
        local_phase_info = deepcopy(phase_info)
        prob = run_aviary(
            'models/aircraft/blended_wing_body/generic_BWB_GASP.csv',
            local_phase_info,
            optimizer='SNOPT',
            verbosity=1,
            max_iter=60,
        )

        # TODO: CI has some intermittent problems with hitting feasibility.
        # self.assertTrue(prob.result.success)

        rtol = 1e-3

        # There are no truth values for these.
        assert_near_equal(
            prob.get_val(Mission.Design.GROSS_MASS, units='lbm'),
            141345.01347269,
            tolerance=rtol,
        )

        assert_near_equal(
            prob.get_val(Aircraft.Design.OPERATING_MASS, units='lbm'),
            80199.17943303,
            tolerance=rtol,
        )

        assert_near_equal(
            prob.get_val(Mission.Summary.TOTAL_FUEL_MASS, units='lbm'),
            27395.83401138,
            tolerance=rtol,
        )

        assert_near_equal(
            prob.get_val(Mission.Landing.GROUND_DISTANCE, units='ft'),
            2203.95598924,
            tolerance=rtol,
        )

        assert_near_equal(prob.get_val(Mission.Summary.RANGE, units='NM'), 3500.0, tolerance=rtol)

        assert_near_equal(
            prob.get_val(Mission.Landing.TOUCHDOWN_MASS, units='lbm'),
            116439.9117977,
            tolerance=rtol,
        )


if __name__ == '__main__':
    unittest.main()
