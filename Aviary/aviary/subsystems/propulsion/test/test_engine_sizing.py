import unittest

import numpy as np
import openmdao.api as om
from openmdao.utils.assert_utils import assert_check_partials, assert_near_equal

from aviary.subsystems.propulsion.engine_deck import EngineDeck
from aviary.subsystems.propulsion.engine_sizing import SizeEngine
from aviary.utils.aviary_values import AviaryValues
from aviary.utils.functions import get_path
from aviary.variable_info.variables import Aircraft


class EngineSizingTest1(unittest.TestCase):
    def setUp(self):
        self.prob = om.Problem()

    def test_case_multiengine(self):
        filename = 'models/engines/turbofan_28k.csv'
        filename = get_path(filename)

        options = AviaryValues()
        options.set_val(Aircraft.Engine.DATA_FILE, filename)
        options.set_val(Aircraft.Engine.SCALE_PERFORMANCE, True)
        options.set_val(Aircraft.Engine.GENERATE_FLIGHT_IDLE, True)
        options.set_val(Aircraft.Engine.IGNORE_NEGATIVE_THRUST, False)
        options.set_val(Aircraft.Engine.FLIGHT_IDLE_THRUST_FRACTION, 0.0)
        options.set_val(Aircraft.Engine.FLIGHT_IDLE_MAX_FRACTION, 1.0)
        options.set_val(Aircraft.Engine.FLIGHT_IDLE_MIN_FRACTION, 0.08)
        options.set_val(Aircraft.Engine.GEOPOTENTIAL_ALT, False)

        engine = EngineDeck(name='engine', options=options)
        # options.set_val(Aircraft.Engine.SCALE_PERFORMANCE, False)
        # engine2 = EngineDeck(name='engine2', options=options)
        # preprocess_propulsion(options, [engine, engine2])

        ref_thrust = engine.get_item(Aircraft.Engine.REFERENCE_SLS_THRUST)
        options = {
            Aircraft.Engine.SCALE_PERFORMANCE: True,
            Aircraft.Engine.REFERENCE_SLS_THRUST: ref_thrust,
        }

        self.prob.model.add_subsystem('engine', SizeEngine(**options), promotes=['*'])

        self.prob.setup(force_alloc_complex=True)

        self.prob.set_val(Aircraft.Engine.SCALE_FACTOR, np.array([0.52716908]))

        self.prob.run_model()

        sls_thrust = self.prob.get_val(Aircraft.Engine.SCALED_SLS_THRUST, units='lbf')

        expected_sls_thrust = np.array([15250])

        assert_near_equal(sls_thrust, expected_sls_thrust, tolerance=1e-8)

        partial_data = self.prob.check_partials(out_stream=None, method='cs')
        assert_check_partials(partial_data, atol=1e-12, rtol=1e-10)


if __name__ == '__main__':
    unittest.main()
