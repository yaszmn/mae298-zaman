import unittest

import numpy as np
import openmdao.api as om
from openmdao.utils.assert_utils import assert_check_partials, assert_near_equal
from parameterized import parameterized

from aviary.subsystems.mass.flops_based.thrust_reverser import ThrustReverserMass
from aviary.subsystems.propulsion.engine_deck import EngineDeck
from aviary.utils.aviary_values import AviaryValues
from aviary.utils.preprocessors import preprocess_propulsion
from aviary.utils.test_utils.variable_test import assert_match_varnames
from aviary.validation_cases.validation_tests import (
    flops_validation_test,
    get_flops_case_names,
    get_flops_inputs,
    print_case,
)
from aviary.variable_info.variables import Aircraft, Settings


class ThrustReverserMassTest(unittest.TestCase):
    def setUp(self):
        self.prob = om.Problem()

    @parameterized.expand(
        get_flops_case_names(omit=['LargeSingleAisle1FLOPS', 'AdvancedSingleAisle']),
        name_func=print_case,
    )
    def test_case(self, case_name):
        prob = self.prob

        inputs = get_flops_inputs(case_name, preprocess=True)

        options = {
            Aircraft.Engine.NUM_ENGINES: inputs.get_val(Aircraft.Engine.NUM_ENGINES),
        }

        prob.model.add_subsystem('thrust_rev', ThrustReverserMass(**options), promotes=['*'])

        prob.setup(check=False, force_alloc_complex=True)

        flops_validation_test(
            prob,
            case_name,
            input_keys=[
                Aircraft.Engine.THRUST_REVERSERS_MASS_SCALER,
                Aircraft.Engine.SCALED_SLS_THRUST,
            ],
            output_keys=[
                Aircraft.Engine.THRUST_REVERSERS_MASS,
                Aircraft.Propulsion.TOTAL_THRUST_REVERSERS_MASS,
            ],
        )

    def test_case_multiengine(self):
        prob = om.Problem()

        aviary_options = get_flops_inputs('LargeSingleAisle1FLOPS')

        engine_options = AviaryValues()
        engine_options.set_val(Settings.VERBOSITY, 0)
        engine_options.set_val(Aircraft.Engine.NUM_ENGINES, 2)
        engine_options.set_val(Aircraft.Engine.DATA_FILE, 'models/engines/turbofan_28k.csv')
        engineModel1 = EngineDeck(options=engine_options)
        engine_options.set_val(Aircraft.Engine.NUM_ENGINES, 2)
        engineModel2 = EngineDeck(options=engine_options)
        engine_options.set_val(Aircraft.Engine.NUM_ENGINES, 4)
        engineModel3 = EngineDeck(options=engine_options)

        preprocess_propulsion(
            aviary_options, [engineModel1, engineModel2, engineModel3], verbosity=0
        )

        options = {
            Aircraft.Engine.NUM_ENGINES: aviary_options.get_val(Aircraft.Engine.NUM_ENGINES),
        }

        prob.model.add_subsystem(
            'thrust_reverser_mass', ThrustReverserMass(**options), promotes=['*']
        )

        prob.setup(force_alloc_complex=True)

        prob.set_val(
            Aircraft.Engine.THRUST_REVERSERS_MASS_SCALER,
            np.array([1.0, 1.22, 0.0]),
            units='unitless',
        )

        prob.set_val(Aircraft.Engine.SCALED_SLS_THRUST, np.array([1000, 20000, 150]), 'lbf')

        prob.run_model()

        thrust_rev_mass = prob.get_val(Aircraft.Engine.THRUST_REVERSERS_MASS, 'lbm')
        total_thrust_rev_mass = prob.get_val(Aircraft.Propulsion.TOTAL_THRUST_REVERSERS_MASS, 'lbm')

        # manual computation of expected thrust reverser mass
        thrust_rev_mass_expected = [68.0, 1659.2, 0.0]
        total_thrust_rev_mass_expected = sum(thrust_rev_mass_expected)
        assert_near_equal(thrust_rev_mass, thrust_rev_mass_expected, tolerance=1e-10)
        assert_near_equal(total_thrust_rev_mass, total_thrust_rev_mass_expected, tolerance=1e-10)

        partial_data = prob.check_partials(
            out_stream=None,
            compact_print=True,
            show_only_incorrect=True,
            form='central',
            method='fd',
        )
        assert_check_partials(partial_data, atol=1e-5, rtol=1e-5)

    def test_IO(self):
        assert_match_varnames(self.prob.model)


class ThrustReverserMassTest2(unittest.TestCase):
    """Test mass-weight conversion."""

    def setUp(self):
        import aviary.subsystems.mass.flops_based.thrust_reverser as reverser

        reverser.GRAV_ENGLISH_LBM = 1.1

    def tearDown(self):
        import aviary.subsystems.mass.flops_based.thrust_reverser as reverser

        reverser.GRAV_ENGLISH_LBM = 1.0

    def test_case(self):
        prob = om.Problem()

        inputs = get_flops_inputs('AdvancedSingleAisle', preprocess=True)

        options = {
            Aircraft.Engine.NUM_ENGINES: inputs.get_val(Aircraft.Engine.NUM_ENGINES),
        }

        prob.model.add_subsystem('thrust_rev', ThrustReverserMass(**options), promotes=['*'])
        prob.setup(check=False, force_alloc_complex=True)
        prob.set_val(Aircraft.Engine.SCALED_SLS_THRUST, 10000.0, 'lbf')

        partial_data = prob.check_partials(out_stream=None, method='cs')
        assert_check_partials(partial_data, atol=1e-12, rtol=1e-12)


if __name__ == '__main__':
    unittest.main()
