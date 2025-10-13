import openmdao.api as om
import class5.c5demo as dsc 


#set up the problem
prob = om.Problem()
prob.model = dsc.SellarMDA_simplepromote()

#prob.setup()

#prob.set_val('indvar.x', 2.0)
#prob.set_val('indvar.z', [-1.0, -1.0])

#prob.run_model()

#om.n2(prob)

#print(f"y1 = {prob.get_val('cycle.d1.y1')}, y2 = {prob.get_val('cycle.d2.y2')}")

#optimisation

prob.driver = om.ScipyOptimizeDriver
prob.driver.options['optimizer'] = 'SLSQP'
prob.driver.options['maxiter'] = 100
prob.driver.options['tol'] = 1e-8

#add design variables - bounds 
prob.model.add_design_var('x', lower=0.0, upper=10.0)
prob.model.add_design_var('z', lower=-10.0, upper=10.0)

#add objective
prob.model.add_objective('obj')

#add constraints 
prob.model.add_constraint('con1', upper=0.0)
prob.model.add_constraint('con2', upper=0.0)

prob.model.approx_totals(method='fd') #everything should work without this line but just in case

prob.set_solver_print(level=1)

prob.setup()

prob.run_driver()

print('minimum found at')
print(prob.get_val('x'))
print(prob.get_val('z'))