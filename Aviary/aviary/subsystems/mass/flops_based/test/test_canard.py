import unittest

import openmdao.api as om
from openmdao.utils.assert_utils import assert_check_partials
from parameterized import parameterized

from aviary.subsystems.mass.flops_based.canard import CanardMass
from aviary.utils.aviary_values import AviaryValues
from aviary.utils.test_utils.variable_test import assert_match_varnames
from aviary.validation_cases.validation_tests import do_validation_test, print_case
from aviary.variable_info.variables import Aircraft, Mission

canard_test_data = {}
canard_test_data['1'] = AviaryValues(
    {
        Mission.Design.GROSS_MASS: (100000, 'lbm'),
        Aircraft.Canard.AREA: (250.00, 'ft**2'),
        Aircraft.Canard.TAPER_RATIO: (0.330, 'unitless'),
        Aircraft.Canard.MASS_SCALER: (1.0, 'unitless'),
        Aircraft.Canard.MASS: (1099.75, 'lbm'),
    }
)

canard_data_sets = [key for key in canard_test_data]


class CanardMassTest(unittest.TestCase):
    def setUp(self):
        self.prob = om.Problem()

    @parameterized.expand(canard_data_sets, name_func=print_case)
    def test_case1(self, case_name):
        # TODO: No test cases with canards. Use dummy vars.
        validation_data = canard_test_data[case_name]
        prob = self.prob

        prob.model.add_subsystem(
            'canard',
            CanardMass(),
            promotes_inputs=['*'],
            promotes_outputs=['*'],
        )

        prob.setup(check=False, force_alloc_complex=True)

        do_validation_test(
            prob,
            case_name,
            input_validation_data=validation_data,
            output_validation_data=validation_data,
            input_keys=[
                Mission.Design.GROSS_MASS,
                Aircraft.Canard.AREA,
                Aircraft.Canard.TAPER_RATIO,
                Aircraft.Canard.MASS_SCALER,
            ],
            output_keys=Aircraft.Canard.MASS,
            tol=1.0e-3,
            atol=1e-10,
            rtol=1e-10,
        )

    def test_IO(self):
        assert_match_varnames(self.prob.model)


class CanardMassTest2(unittest.TestCase):
    """Test mass-weight conversion."""

    def setUp(self):
        import aviary.subsystems.mass.flops_based.canard as canard

        canard.GRAV_ENGLISH_LBM = 1.1

    def tearDown(self):
        import aviary.subsystems.mass.flops_based.canard as canard

        canard.GRAV_ENGLISH_LBM = 1.0

    def test_case1(self):
        prob = om.Problem()
        prob.model.add_subsystem(
            'canard',
            CanardMass(),
            promotes_inputs=['*'],
            promotes_outputs=['*'],
        )
        prob.setup(check=False, force_alloc_complex=True)
        prob.set_val(Mission.Design.GROSS_MASS, 100000.0, 'lbm')
        prob.set_val(Aircraft.Canard.AREA, 250.00, 'ft**2')
        prob.set_val(Aircraft.Canard.TAPER_RATIO, 0.330, 'unitless')
        prob.set_val(Aircraft.Canard.MASS_SCALER, 1.0, 'unitless')
        prob.set_val(Aircraft.Canard.MASS, 1099.75, 'lbm')

        partial_data = prob.check_partials(out_stream=None, method='cs')
        assert_check_partials(partial_data, atol=1e-12, rtol=1e-12)


if __name__ == '__main__':
    unittest.main()
