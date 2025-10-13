import openmdao.api as om
import numpy as np


#DISCIPLINE 1
class SellarDis1(om.ExplicitComponent): 

    #discipline 1 for sellar example
    #y1 = z1**2 + z2 + x1 -0.2*y2
    def setup(self):

        #design variables
        self.add_input('z', val=np.zeros(2))
        self.add_input('x', val=0.0)
        #coupling parameter
        self.add_input('y2', val=1.0)

        #output
        self.add_output('y1', val=1.0)

        #equivalent to below 
        # self.declare_partials('y1', ['z', 'x', 'y2'])

    #partials
    def setup_partials(self):
        self.declare_partials('*', '*', method='fd') 

    def compute(self, inputs, outputs):
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        x1 = inputs['x']
        y2 = inputs['y2']

        outputs['y1'] = z1**2 + z2 + x1 - 0.2*y2


#DISCIPLINE 2
class SellarDis2(om.ExplicitComponent):
    
    #discipline 2 for sellar example
    #y2 = sqrt(y1) + z1 + z2

    def setup(self):
        #design variables
        self.add_input('z', val=np.zeros(2))
        #coupling parameter
        self.add_input('y1', val=1.0)

        #output
        self.add_output('y2', val=1.0)

        #equivalent to below 
        # self.declare_partials('y2', ['z', 'y1'])

    #partials
    def setup_partials(self):
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        y1 = inputs['y1']

        if y1.real < 0.0:
            y1 *= -1

        outputs['y2'] = y1**0.5 + z1 + z2

class SellarMDAConnect(om.Group):
    def setup(self): #coupling EVERYTHING together 
        indvar = self.add_subsystem('indvar', om.IndepVarComp()) 
        indvar.add_output('x', val=1.0)
        indvar.add_output('z', val=np.array([5.0, 2.0]))

        #couple the cycle with a non-linear solver 
        cycle = self.add_subsystem('cycle', om.Group())
        cycle.add_subsystem('d1', SellarDis1())
        cycle.add_subsystem('d2', SellarDis2())

        cycle.connect('d1.y1', 'd2.y1')
        cycle.connect('d2.y2', 'd1.y2') #the above

        cycle.nonlinear_solver = om.NonlinearBlockGS() #non-linear block gauss-seidel solver - kind of gradient free solver 

        #objective function definition
        self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)', 
                                                  z=np.zeros(2), x=0.0))
        self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'))
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'))

        #wire this group together 
        self.connect('indvar.x', ['cycle.d1.x', 'obj_cmp.x'])
        self.connect('indvar.z', ['cycle.d1.z', 'cycle.d2.z', 'obj_cmp.z'])
        self.connect('cycle.d1.y1', ['obj_cmp.y1', 'con_cmp1.y1']) #could have included cycle coupling in the inputs but cleaner to do the above
        self.connect('cycle.d2.y2', ['obj_cmp.y2', 'con_cmp2.y2']) #linking an output to an input | output: cycle, input: obj_cmp, con_cmp2

    #new group
    class SellarMDA_simplepromote(om.Group):

        def setup(self): 
            cycle = self.add_subsystem('cycle', om.Group(), promotes=['*']) #promotes everything in the cycle group to the parent group
            cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x','z','y2'], 
                                    promotes_outputs=['y1']) #promotes the inputs and outputs to the parent group
            cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['z','y1'], 
                                    promotes_outputs=['y2'])
                
            cycle.set_input_defaults('x', 1.0)
            cycle.set_input_defaults('z',np.array([5.0, 2.0]))

            cycle.nonlinear_solver = om.NonlinearBlockGS()

                #build in objective and constraints 
            self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)', 
                                                        z=np.array([0.0,0.0]), x=0.0), promotes=['x', 'z', 'y1', 'y2', 'obj'])
            self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'), promotes=['y1', 'con1'])
            self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'), promotes=['y2', 'con2'])