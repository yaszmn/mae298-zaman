import unittest

from openmdao.utils.testing_utils import use_tempdirs

import aviary.api as av
from aviary.subsystems.geometry.geometry_builder import CoreGeometryBuilder
from aviary.variable_info.enums import LegacyCode
from aviary.variable_info.variable_meta_data import _MetaData as BaseMetaData
from aviary.variable_info.variables import Aircraft

FLOPS = LegacyCode.FLOPS
GASP = LegacyCode.GASP


@use_tempdirs
class TestFLOPSGeomBuilder(av.TestSubsystemBuilderBase):
    """
    That class inherits from TestSubsystemBuilder. So all the test functions are
    within that inherited class. The setUp() method prepares the class and is run
    before the test methods; then the test methods are run.
    """

    def setUp(self):
        self.subsystem_builder = CoreGeometryBuilder(
            'core_geometry',
            BaseMetaData,
            code_origin=FLOPS,
            code_origin_to_prioritize=FLOPS,
        )
        self.aviary_values = av.AviaryValues()
        self.aviary_values.set_val(Aircraft.Engine.NUM_ENGINES, [1], units='unitless')
        self.aviary_values.set_val(Aircraft.Electrical.HAS_HYBRID_SYSTEM, False, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.HAS_FOLD, True, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.HAS_STRUT, True, units='unitless')
        self.aviary_values.set_val(
            Aircraft.Design.COMPUTE_HTAIL_VOLUME_COEFF, True, units='unitless'
        )
        self.aviary_values.set_val(
            Aircraft.Design.COMPUTE_VTAIL_VOLUME_COEFF, True, units='unitless'
        )
        self.aviary_values.set_val(Aircraft.Wing.SPAN_EFFICIENCY_REDUCTION, True, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.CHOOSE_FOLD_LOCATION, True, units='unitless')
        self.aviary_values.set_val(
            Aircraft.Wing.FOLD_DIMENSIONAL_LOCATION_SPECIFIED, True, units='unitless'
        )
        self.aviary_values.set_val(
            Aircraft.Strut.DIMENSIONAL_LOCATION_SPECIFIED, True, units='unitless'
        )


class TestFLOPSGeomBuilderHybrid(av.TestSubsystemBuilderBase):
    """
    That class inherits from TestSubsystemBuilder. So all the test functions are
    within that inherited class. The setUp() method prepares the class and is run
    before the test methods; then the test methods are run.
    """

    def setUp(self):
        self.subsystem_builder = CoreGeometryBuilder(
            'core_geometry',
            BaseMetaData,
            code_origin=(FLOPS, GASP),
            code_origin_to_prioritize=FLOPS,
        )
        self.aviary_values = av.AviaryValues()
        self.aviary_values.set_val(Aircraft.Engine.NUM_ENGINES, [1], units='unitless')
        self.aviary_values.set_val(Aircraft.Electrical.HAS_HYBRID_SYSTEM, True, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.HAS_FOLD, True, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.HAS_STRUT, True, units='unitless')
        self.aviary_values.set_val(
            Aircraft.Design.COMPUTE_HTAIL_VOLUME_COEFF, True, units='unitless'
        )
        self.aviary_values.set_val(
            Aircraft.Design.COMPUTE_VTAIL_VOLUME_COEFF, True, units='unitless'
        )
        self.aviary_values.set_val(Aircraft.Wing.SPAN_EFFICIENCY_REDUCTION, True, units='unitless')
        self.aviary_values.set_val(Aircraft.Wing.CHOOSE_FOLD_LOCATION, True, units='unitless')
        self.aviary_values.set_val(
            Aircraft.Wing.FOLD_DIMENSIONAL_LOCATION_SPECIFIED, True, units='unitless'
        )
        self.aviary_values.set_val(
            Aircraft.Strut.DIMENSIONAL_LOCATION_SPECIFIED, True, units='unitless'
        )
        self.aviary_values.set_val(Aircraft.Propulsion.TOTAL_NUM_WING_ENGINES, 2, units='unitless')


if __name__ == '__main__':
    unittest.main()
