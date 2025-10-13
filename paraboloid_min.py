import openmdao.api as om
import numpy as np

# build the model
prob = om.Problem()

prob.model.add_subsystem('paraboloid', om.ExplicitComponent('f = (x-4)**2 + x*y + (y+3)**2 - 3')) 

# setup the optimization
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'

prob.model.add_design_var('paraboloid.x', lower=-50, upper=50)
prob.model.add_design_var('paraboloid.y', lower=-50, upper=50)
prob.model.add_objective('paraboloid.f')

prob.setup()

# Set initial values.
prob.set_val('paraboloid.x', -1.0)
prob.set_val('paraboloid.y', 7.0)

# run the optimization
prob.run_driver();