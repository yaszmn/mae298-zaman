import openmdao.api as om
import numpy as np

# Objective: Paraboloid component
class Paraboloid(om.ExplicitComponent):
    def setup(self):
        self.add_input('x', val=0.0)
        self.add_input('y', val=0.0)
        self.add_output('f', val=0.0)
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):
        x = inputs['x']
        y = inputs['y']
        outputs['f'] = (x - 4.0)**2 + x * y + (y + 3.0)**2 - 3.0

    def compute_partials(self, inputs, partials):
        x = inputs['x']
        y = inputs['y']
        partials['f', 'x'] = 2 * (x - 4.0) + y
        partials['f', 'y'] = x + 2 * (y + 3.0)

# Constraint: g(x, y) = x^2 + y
class ConstraintComp(om.ExplicitComponent):
    def setup(self):
        self.add_input('x', val=0.0)
        self.add_input('y', val=0.0)
        self.add_output('g', val=0.0)
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):
        x = inputs['x']
        y = inputs['y']
        outputs['g'] = x**2 + y

    def compute_partials(self, inputs, partials):
        x = inputs['x']
        partials['g', 'x'] = 2 * x
        partials['g', 'y'] = 1.0

# Set up the problem
prob = om.Problem()

# Add subsystems
prob.model.add_subsystem('paraboloid', Paraboloid(), promotes=['*'])
prob.model.add_subsystem('constraint', ConstraintComp(), promotes=['*'])

# Design vars, objective, constraint
prob.model.add_design_var('x', lower=-50, upper=50)
prob.model.add_design_var('y', lower=-50, upper=50)
prob.model.add_objective('f')
prob.model.add_constraint('g', lower=1.0, upper=8.0)  # 1 < x^2 + y < 8

# Optimization driver
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'

# Setup and initial guess
prob.setup()
prob.set_val('x', -1.0)
prob.set_val('y', 7.0)

# Run optimization
prob.run_driver()

# Output
print(f"x = {prob.get_val('x')[0]}")
print(f"y = {prob.get_val('y')[0]}")
print(f"f = {prob.get_val('f')[0]}")
print(f"g = {prob.get_val('g')[0]}  # Should be between 1 and 8")
