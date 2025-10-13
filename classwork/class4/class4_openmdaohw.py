import numpy as np
import openmdao.api as om

prob = om.Problem()

prob.model.add_subsystem('paraboloid', om.ExecComp('f = (x-4)**2 + x*y + (y+3)**2 - 3'))

# setup the optimization
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'

prob.model.add_design_var('paraboloid.x', lower=-50, upper=50)
prob.model.add_design_var('paraboloid.y', lower=-50, upper=50)
prob.model.add_objective('paraboloid.f')

prob.setup()

# Set initial values.
prob.set_val('paraboloid.x', 3.0)
prob.set_val('paraboloid.y', -4.0)

# run the optimization
prob.run_driver();

print('Optimal x value: ', prob.get_val('paraboloid.x'))
print('Optimal y value: ', prob.get_val('paraboloid.y'))
print('Objective value: ', prob.get_val('paraboloid.f'))