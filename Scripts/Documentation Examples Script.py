#
# Runs examples in the PsyNeuLink Documentation
#

from PsyNeuLink.Globals.Keywords import *
from PsyNeuLink.Components.Process import process
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.TransferMechanism import TransferMechanism
from PsyNeuLink.Components.Mechanisms.ProcessingMechanisms.DDM import DDM
from PsyNeuLink.Components.Projections.MappingProjection import MappingProjection
from PsyNeuLink.Components.Projections.LearningProjection import LearningProjection
# from PsyNeuLink.Components.Functions.Function import Logistic, random_matrix
from PsyNeuLink.Components.Functions.Function import Logistic
from PsyNeuLink.Globals.Run import run

from PsyNeuLink.Components.Functions.Function import *

#region PROCESS EXAMPLES ********************************************************************

# Specification of mechanisms in a pathway
mechanism_1 = TransferMechanism()
mechanism_2 = DDM()
some_params = {PARAMETER_STATE_PARAMS:{FUNCTION_PARAMS:{THRESHOLD:2,NOISE:0.1}}}
my_process = process(pathway=[mechanism_1, TransferMechanism, (mechanism_2, some_params, 0)])
print(my_process.execute())

# Default projection specification
mechanism_1 = TransferMechanism()
mechanism_2 = TransferMechanism()
mechanism_3 = DDM()
my_process = process(pathway=[mechanism_1, mechanism_2, mechanism_3])
print(my_process.execute())

# Inline projection specification using an existing projection
mechanism_1 = TransferMechanism()
mechanism_2 = TransferMechanism()
mechanism_3 = DDM()
projection_A = MappingProjection()
my_process = process(pathway=[mechanism_1, projection_A, mechanism_2, mechanism_3])
print(my_process.execute())

mechanism_1 = TransferMechanism()
mechanism_2 = TransferMechanism()
mechanism_3 = DDM()
# Inline projection specification using a keyword
my_process = process(pathway=[mechanism_1, RANDOM_CONNECTIVITY_MATRIX, mechanism_2, mechanism_3])
print(my_process.execute())

# Stand-alone projection specification
mechanism_1 = TransferMechanism()
mechanism_2 = TransferMechanism()
mechanism_3 = DDM()
projection_A = MappingProjection(sender=mechanism_1, receiver=mechanism_2)
my_process = process(pathway=[mechanism_1, mechanism_2, mechanism_3])
print(my_process.execute())

# Process that implements learning
mechanism_1 = TransferMechanism(function=Logistic)
mechanism_2 = TransferMechanism(function=Logistic)
mechanism_3 = TransferMechanism(function=Logistic)
# my_process = process(pathway=[mechanism_1, mechanism_2, mechanism_3],
#                      learning=LEARNING_PROJECTION)
my_process = process(pathway=[mechanism_1, mechanism_2, mechanism_3],
                     learning=LEARNING_PROJECTION,
                     target=[0])
print(my_process.execute())

#endregion


#region SYSTEM EXAMPLES ********************************************************************
#
#endregion