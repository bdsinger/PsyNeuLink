# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.


# *************************************************  LVOCControlMechanism ******************************************************

"""

Overview
--------

An LVOCControlMechanism is a `ControlMechanism <ControlMechanism>` that learns to regulate its `ControlSignals
<ControlSignal>` in order to optimize the performance of the `Composition` to which it belongs.  It implements a form
of the Learned Value of Control model described in `Leider et al.
<https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006043&rev=2>`_, which learns to select the
value for its `control_signals <LVOCControlMechanism.control_signals>` (i.e., its `allocation_policy
<LVOCControlMechanism.allocation_policy>`) that maximzes its `EVC <LVOCControlMechanism_EVC>` based on a set of
`predictors <LVOCControlMechanism_Feature_Predictors>`.

.. _LVOCControlMechanism_EVC:

*Expected Value of Control (EVC)*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **expected value of control (EVC)** is the outcome of executing the `composition`
to which the LVOCControlMechanism belongs under a given `allocation_policy <LVOCControlMechanism.allocation_policy>`,
as determined by its `objective_mechanism <LVOCControlMechanism.objective_mechanism>`, discounted by the `cost
<ControlSignal.cost> of the `control_signals <LVOCControlMechanism.control_signals>` under that `allocation_policy
<LVOCControlMechanism.allocation_policy>`.

The LVOCControlMechanism's `function <LVOCControlMechanism.function>` learns to predict the outcome of its
`objective_mechanism <LVOCControlMechanism.objective_mechanism>` from a weighted sum of its `feature_predictors
<LVOCControlMechanism.feature_preditors>`, `control_signals <LVOCControlMechanism.control_signals>`, interactions 
among these, and the costs of the `control_signals <LVOCControlMechanism.control_signals>`.  This is referred to as 
the "learned value of control," or LVOC.

.. _LVOCControlMechanism_Creation:

Creating an LVOCControlMechanism
------------------------

 An LVOCControlMechanism can be created in the same was as any `ControlMechanism`, with the exception that it cannot
 be assigned as the `controller <Composition.controller>` of a Composition.  The following arguments of its
 constructor are specific to the LVOCControlMechanism:

  * **feature_predictors** -- this takes the place of the standard **input_states** argument in the constructor for a
    Mechanism`, and specifies the inputs that it learns to use to determine its `allocation_policy
    <LVOCControlMechanism.allocation_policy>` in each `trial` of execution.
    It can be specified using any of the following, singly or combined in a list:

        * {*SHADOW_EXTERNAL_INPUTS*: <`ORIGIN` Mechanism, InputState for one, or list with either or both>} --
          InputStates of the same shapes as those listed are created on the LVOC, and are connected to the
          corresponding input_CIM OutputStates by projections. The external input values that are passed through the
          input_CIM are used as the `feature_predictors <LVOCControlMechanism_Feature>`. If a Mechanism is included
          in the list, it refers to all of its InputStates.
        |
        * *InputState specification* -- this can be any form of `InputState specification <InputState_Specification>`
          that resolves to an OutputState from which the InputState receives a Projection;  the `value
          <OutputState.value>` of that OutputState is used as the `feature <LVOCControlMechanism.feature>`. Each of
          these InputStates is marked as internal_only.

    Feature_predictors can also be added to an existing LVOCControlMechanism using its `add_features` method.

  * **feature_function** specifies `function <InputState>` of the InputState created for each item listed in
    **feature_predictors**.

.. _LVOCControlMechanism_Structure:

Structure
---------

.. _LVOCControlMechanism_Input:

*Input*
~~~~~~~

An LVOCControlMechanism has one `InputState` that receives a `Projection` from its `objective_mechanism
<LVOCControlMechanism.objective_mechanism>` (its primary InputState <InputState_Primary>`), and additional ones for
each of its feature_predictors, as described below.

.. _LVOCControlMechanism_Feature_Predictors:

Feature_Predictors
^^^^^^^^^^^^^^^^^^

Features_Predictors, together with the LVOCControlMechanism's `control_signals <LVOCControlMechanism.control_signals>`,
are used by its `function <LVOCControlMechanism.function>` to learn to predict the outcome of its
`objective_mechanism <LVOCControlMechanism.objective_mechanism>` and to determine its `allocation_policy
<LVOCControlMechanism.allocation_policy>`.

Feature_Preditors can be of two types:

* *Input Feature* -- this is a value received as input by an `ORIGIN` Mechanism in the Composition.
    These are specified in the **feature_predictors** argument of the LVOCControlMechanism's constructor (see
    `LVOCControlMechanism_Creation`), in a dictionary containing a *SHADOW_EXTERNAL_INPUTS* entry, the value of
    which is one or more `ORIGIN` Mechanisms and/or their InputStates to be shadowed.  For each, a Projection is
    automatically created that parallels ("shadows") the Projection from the Composition's `InputCIM` to the `ORIGIN`
    Mechanism, projecting from the same `OutputState` of the InputCIM to the the InputState of the
    LVOCControlMechanism assigned to that feature.

* *Output Feature* -- this is the `value <OutputState.value>` of an OutputState of some other Mechanism in the
    Composition.  These too are specified in the **feature_predictors** argument of the LVOCControlMechanism's
    constructor (see `LVOCControlMechanism_Creation`), and each is assigned a Projection to the InputState of
    the LVOCControlMechanism for that feature.

The current `values <InputState.value>` of the InputStates for the feature_predictors are listed in the `feature_values
<LVOCControlMechanism.feature_values>` attribute.

.. _LVOCControlMechanism_ObjectiveMechanism:

ObjectiveMechanism
^^^^^^^^^^^^^^^^^^

Like any ControlMechanism, an LVOCControlMechanism receives its input from the *OUTCOME* `OutputState
<ObjectiveMechanism_Output>` of its `objective_mechanism <LVOCControlMechanism.objective_mechanism>`,
via a MappingProjection to its `primary InputState <InputState_Primary>`. By default, the ObjectiveMechanism's
function is a `LinearCombination` function with its `operation <LinearCombination.operation>` attribute assigned as
*PRODUCT*; this takes the product of the `value <OutputState.value>`\\s of the OutputStates that it monitors (listed
in its `monitored_output_states <ObjectiveMechanism.monitored_output_states>` attribute.  However, this can be
customized in a variety of ways:

    * by specifying a different `function <ObjectiveMechanism.function>` for the ObjectiveMechanism
      (see `Objective Mechanism Examples <ObjectiveMechanism_Weights_and_Exponents_Example>` for an example);
    ..
    * using a list to specify the OutputStates to be monitored  (and the `tuples format
      <InputState_Tuple_Specification>` to specify weights and/or exponents for them) in either the
      **monitor_for_control** or **objective_mechanism** arguments of the LVOCControlMechanism's constructor;
    ..
    * using the  **monitored_output_states** argument for an ObjectiveMechanism specified in the `objective_mechanism
      <LVOCControlMechanism.objective_mechanism>` argument of the LVOCControlMechanism's constructor;
    ..
    * specifying a different `ObjectiveMechanism` in the **objective_mechanism** argument of the LVOCControlMechanism's
      constructor.

    .. _LVOCControlMechanism_Objective_Mechanism_Function_Note:

    .. note::
       If a constructor for an `ObjectiveMechanism` is used for the **objective_mechanism** argument of the
       LVOCControlMechanism's constructor, then the default values of its attributes override any used by the
       LVOCControlMechanism for its `objective_mechanism <LVOCControlMechanism.objective_mechanism>`.  In particular,
       whereas an LVOCControlMechanism uses the same default `function <ObjectiveMechanism.function>` as an
       `ObjectiveMechanism` (`LinearCombination`), it uses *PRODUCT* rather than *SUM* as the default value of the
       `operation <LinearCombination.operation>` attribute of the function.  As a consequence, if the constructor for
       an ObjectiveMechanism is used to specify the LVOCControlMechanism's **objective_mechanism** argument,
       and the **operation** argument is not specified, *SUM* rather than *PRODUCT* will be used for the
       ObjectiveMechanism's `function <ObjectiveMechanism.function>`.  To ensure that *PRODUCT* is used, it must be
       specified explicitly in the **operation** argument of the constructor for the ObjectiveMechanism (see 1st
       example under `System_Control_Examples`).

The LVOCControlMechanism's `function <LVOCControlMechanism.function>` learns to predict the `value <OutputState.value>`
of the *OUTCOME* `OutputState` of the LVOCControlMechanism's `objective_mechanism
<LVOCControlMechanism.objective_mechanism>`, as described below.

.. _LVOCControlMechanism_Function:

*Function*
~~~~~~~~~~

The `function <LVOCControlMechanism.function>` of an LVOCControlMechanism learns how to weight its `feature_predictors
<LVOCControlMechanism_Feature_Predictors>`, the `values <ControlSignal.value>` of its  `control_signals
<LVOCControlMechanism.control_signals>`, the interactions between these, and the `costs <ControlSignal.costs>` of the
`control_signals <LVOCControlMechanism.control_signals>`, to best predict the outcome of its `objective_mechanism
<LVOCControlMechanism.objective_mechanism>`.  Using those weights, and the current set of feature_predictors, it then
searches for and returns the `allocation_policy <LVOCControlMechanism.allocation_policy>` that maximizes the `EVC
<LVOCControlMechanism_EVC>`.  By default, `function <LVOCControlMechanism.function>` is `BayesGLM`. However,
any function can be used that accepts a 2d array, the first item of which is an array of scalar values (the prediction
terms) and the second that is a scalar value (the outcome to be predicted), and returns an array with the same shape as
the LVOCControlMechanism's `allocation_policy <LVOCControlMechanism.allocation_policy>`.

.. note::
  The LVOCControlMechanism's `function <LVOCControlMechanism.function>` is provided the values of the
  `feature_predictors <LVOCControlMechanism_Feature_Predictors>` and outcome of its `objective_mechanism
  <LVOCControlMechanism.objective_mechanism>` from the *previous* trial to update the `prediction_weights
  `prediction_weights <LVOCControlMechanism.prediction_weights>`.  Those are then used to determine (and implement)
  the `allocation_policy <LVOCControlMechanism.allocation_policy>` that is predicted to generate the greatest `EVC
  <LVOCControlMechanism_EVC>` based on the `feature_values <LVOCControlMechanism.feature_values>` for the current
  trial.

.. _LVOCControlMechanism_ControlSignals:

*ControlSignals*
~~~~~~~~~~~~~~~~

The OutputStates of an LVOCControlMechanism (like any `ControlMechanism`) are a set of `ControlSignals
<ControlSignal>`, that are listed in its `control_signals <LVOCControlMechanism.control_signals>` attribute (as well as
its `output_states <ControlMechanism.output_states>` attribute).  Each ControlSignal is assigned a `ControlProjection`
that projects to the `ParameterState` for a parameter controlled by the LVOCControlMechanism.  Each ControlSignal is
assigned an item of the LVOCControlMechanism's `allocation_policy`, that determines its `allocation
<ControlSignal.allocation>` for a given `TRIAL` of execution.  The `allocation <ControlSignal.allocation>` is used by
a ControlSignal to determine its `intensity <ControlSignal.intensity>`, which is then assigned as the `value
<ControlProjection.value>` of the ControlSignal's ControlProjection.   The `value <ControlProjection>` of the
ControlProjection is used by the `ParameterState` to which it projects to modify the value of the parameter (see
`ControlSignal_Modulation` for description of how a ControlSignal modulates the value of a parameter it controls).
A ControlSignal also calculates a `cost <ControlSignal.cost>`, based on its `intensity <ControlSignal.intensity>`
and/or its time course. The `cost <ControlSignal.cost>` may be included in the evaluation carried out by the
LVOCControlMechanism's `function <LVOCControlMechanism.function>` for a given `allocation_policy`,
and that it uses to adapt the ControlSignal's `allocation <ControlSignal.allocation>` in the future.

.. _LVOCControlMechanism_Execution:

Execution
---------

When an LVOCControlMechanism is executed, it uses the values of its `feature_predictors
<LVOCControlMechanism_Feature_Predictors>` (listed in its `feature_values <LVOCControlMechanism.feature_values>`
attribute), together with the `values <ControlSignals.value>` of its `control_signals
<LVOCControlMechanism.control_signals>` and their `costs <ControlSignal.cost>` to update its prediction of the
outcome measure provided by its `objective_mechanism <LVOCControlMechanism.objective_mechanism>`, and then determines
the `allocation_policy` that maximizes `EVC <LVOCControlMechanism_EVC>` for the current `trial` of execution.
Specifically it executes the following steps:

  * Updates `prediction_vector <LVOCControlMechanism.prediction_vector>` with the current `features_values
    <LVOCControlMechanism.feature_values>`, `values <ControlSignal.value>` of its  `control_signals
    <LVOCControlMechanism.control_signals>`, and their `costs <ControlSignal.cost>`.

  * Calls its `function <LVOCControlMechanism.function>` with the `prediction_vector
    <LVOCControlMechanism.prediction_vector>` and the outcome received from the
    LVOCControlMechanism's `objective_mechanism <LVOCControlMechanism.objective_mechanism>`, discounted by the
    `costs <ControlSignal.cost>` associated with each of its `control_signals <LVOCControlMechanism.control_signals>`,
    to update its `prediction_weights <LVOCControlMechanism.prediction_weights>`.

  * Calls its `gradient_ascent <LVOCControlMechanism.gradient_ascent>` function with `prediction_vector
    <LVOCControlMechanism.prediction_vector>` and `prediction_weights <LVOCControlMechanism.prediction_weights>`
    to determine the `allocation_policy <LVOCControlMechanism.alocation_policy>` that yields the greatest `EVC
    <LVOCControlMechanism_EVC>`, and returns that `allocation_policy <LVOCControlMechanism.allocation_policy>`.

The values specified by the `allocation_policy <LVOCControlMechanism.allocation_policy>` returned by the
LVOCControlMechanism's `function <LVOCControlMechanism.function>` are assigned as the `values <ControlSignal.values>`
of its `control_signals <LVOCControlMechanism.control_signals>`.

COMMENT:
.. _LVOCControlMechanism_Examples:

Example
-------
COMMENT

.. _LVOCControlMechanism_Class_Reference:

Class Reference
---------------

"""
import warnings
from collections import Iterable, deque
from itertools import product
import typecheck as tc
from aenum import Enum

import autograd.numpy as np
from autograd import grad

from psyneulink.core.components.functions.function import \
    ModulationParam, _is_modulation_param, Buffer, Linear, BayesGLM, EPSILON, is_function_type
from psyneulink.core.components.mechanisms.mechanism import Mechanism
from psyneulink.core.components.mechanisms.adaptive.control.controlmechanism import ControlMechanism
from psyneulink.core.components.mechanisms.processing.objectivemechanism import OUTCOME, ObjectiveMechanism, \
    MONITORED_OUTPUT_STATES
from psyneulink.core.components.states.state import _parse_state_spec
from psyneulink.core.components.states.inputstate import InputState
from psyneulink.core.components.states.outputstate import OutputState
from psyneulink.core.components.states.parameterstate import ParameterState
from psyneulink.core.components.states.modulatorysignals.controlsignal import ControlSignalCosts
from psyneulink.core.components.shellclasses import Composition_Base, Function
from psyneulink.core.globals.context import ContextFlags
from psyneulink.core.globals.keywords import INTERNAL_ONLY, PARAMS, LVOCCONTROLMECHANISM, NAME, PARAMETER_STATES, \
    VARIABLE, OBJECTIVE_MECHANISM, FUNCTION, ALL, INIT_FULL_EXECUTE_METHOD, CONTROL_SIGNALS
from psyneulink.core.globals.preferences.componentpreferenceset import is_pref_set
from psyneulink.core.globals.preferences.preferenceset import PreferenceLevel
from psyneulink.core.globals.defaults import defaultControlAllocation
from psyneulink.core.globals.utilities import ContentAddressableList, is_iterable, is_numeric, powerset, tensor_power

__all__ = [
    'LVOC', 'LVOCControlMechanism', 'LVOCError', 'SHADOW_EXTERNAL_INPUTS', 'PREDICTION_TERMS', 'PV'
]

LVOC = 'LVOC'
FEATURE_PREDICTORS = 'feature_predictors'
SHADOW_EXTERNAL_INPUTS = 'SHADOW_EXTERNAL_INPUTS'
PREDICTION_WEIGHTS = 'PREDICTION_WEIGHTS'
PREDICTION_TERMS = 'prediction_terms'
PREDICTION_WEIGHT_PRIORS = 'prediction_weight_priors'


class PV(Enum):
    '''PV()
    Specifies terms used to compute `prediction_vector <LVOCControlMechanism.prediction_vector>`.

    Attributes
    ----------

    F
        Main effect of `feature_predictors <LVOCControlMechanism_Feature_Predictors>`.
    C
        Main effect of `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    FF
        Interaction among `feature_predictors <LVOCControlMechanism_Feature_Predictors>`.
    CC
        Interaction among `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    FC
        Interaction between `feature_predictors <LVOCControlMechanism_Feature_Predictors>` and
        `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    FFC
        Interaction between interactions of `feature_predictors <LVOCControlMechanism_Feature_Predictors>` and
        `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    FCC
        Interaction between `feature_predictors <LVOCControlMechanism_Feature_Predictors>` and interactions among
        `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    FFCC
        Interaction between interactions of `feature_predictors <LVOCControlMechanism_Feature_Predictors>` and
        interactions among `values <ControlSignal.value>` of `control_signals <LVOCControlMechanism.control_signals>`.
    COST
        Main effect of `costs <ControlSignal.cost>` of `control_signals <LVOCControlMechanism.control_signals>`.
    '''
    F = 'f'
    C = 'c'
    FF = 'ff'
    CC = 'cc'
    FC = 'fc'
    FFC = 'ffc'
    FCC = 'fcc'
    FFCC = 'ffcc'
    COST = 'cst'


class LVOCError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)


class LVOCControlMechanism(ControlMechanism):
    """LVOCControlMechanism(                             \
    feature_predictors,                                  \
    feature_function=None,                               \
    objective_mechanism=None,                            \
    origin_objective_mechanism=False,                    \
    terminal_objective_mechanism=False,                  \
    function=BayesGLM,                                   \
    prediction_terms=[PV.F, PV.C, PV.FC, PV.COST]        \
    update_rate=0.01,                                    \
    convergence_criterion=LVOC                           \
    convergence_threshold=.001,                          \
    max_iterations=1000,                                 \
    control_signals=None,                                \
    modulation=ModulationParam.MULTIPLICATIVE,           \
    params=None,                                         \
    name=None,                                           \
    prefs=None)

    Subclass of `ControlMechanism <ControlMechanism>` that learns to optimize its `ControlSignals <ControlSignal>`.

    Arguments
    ---------

    feature_predictors : Mechanism, OutputState, Projection, dict, or list containing any of these
        specifies the values that the LVOCControlMechanism learns to use for determining its `allocation_policy
        <LVOCControlMechanism.allocation_policy>`.  Any `InputState specification <InputState_Specification>`
        can be used that resolves to an `OutputState` that projects to the InputState.  In addition, a dictionary
        with a *SHADOW_EXTERNAL_INPUTS* entry can be used to shadow inputs to the Composition's `ORIGIN` Mechanism(s)
        (see `LVOCControlMechanism_Creation` for details).

    feature_function : Function or function : default None
        specifies the `function <InputState.function>` for the `InputState` assigned to each `feature_predictor
        <LVOCControlMechanism_Feature_Predictors>`.

    objective_mechanism : ObjectiveMechanism or List[OutputState specification] : default None
        specifies either an `ObjectiveMechanism` to use for the LVOCControlMechanism, or a list of the `OutputState
        <OutputState>`\\s it should monitor; if a list of `OutputState specifications
        <ObjectiveMechanism_Monitored_Output_States>` is used, a default ObjectiveMechanism is created and the list
        is passed to its **monitored_output_states** argument.

    function : LearningFunction or callable : BayesGLM
        specifies the function used to learn to predict the outcome of `objective_mechanism
        <LVOCControlMechanism.objective_mechanism>` minus the `costs <ControlSignal.cost>` of the
        `control_signals <LVOCControlMechanism.control_signals>` from the `prediction_vector
        <LVOCControlMechanism.prediction_vector>` (see `LVOCControlMechanism_Function` for details).

    prediction_terms : List[PV] : default [PV.F, PV.C, PV.FC, PV.COST]
        specifies terms to be included in `prediction_vector <LVOCControlMechanism.prediction_vector>`.
        items must be members of the `PV` Enum.  If the keyword *ALL* is specified, then all of the terms are used;
        if `None` is specified, the default values will automatically be assigned.

    update_rate : int or float : default 0.01
        specifies the amount by which the `value <ControlSignal.value>` of each `ControlSignal` in the
        `allocation_policy <LVOCControlMechanism.allocation_policy>` is modified in each iteration of the
        `gradient_ascent <LVOCControlMechanism.gradient_ascent>` method.

    convergence_criterion : LVOC or CONTROL_SIGNALS : default LVOC
        specifies the measure used to determine when to terminate execution of the `gradient_ascent
        <LVOCControlMechanism.gradient_ascent>` method.

    convergence_threshold : int or float : default 0.001
        specifies the change in value of the `convergence_criterion` below which the `gradient_ascent
        <LVOCControlMechanism.gradient_ascent>` method is terminated and returns an `allocation_policy
        <LVOCControlMechanism.allocation_policy>`.

    max_iterations : int : default 1000
        specifies the maximum number of iterations `gradient_ascent <LVOCControlMechanism.gradient_ascent>`
        method is allowed to execute; if exceeded, a warning is issued, and the method returns the
        last `allocation_policy <LVOCControlMechanism.allocation_policy>` evaluated.

    control_signals : ControlSignal specification or List[ControlSignal specification, ...]
        specifies the parameters to be controlled by the LVOCControlMechanism
        (see `ControlSignal_Specification` for details of specification).

    params : Dict[param keyword: param value] : default None
        a `parameter dictionary <ParameterState_Specification>` that can be used to specify the parameters for the
        Mechanism, its `function <LVOCControlMechanism.function>`, and/or a custom function and its parameters.  Values
        specified for parameters in the dictionary override any assigned to those parameters in arguments of the
        constructor.

    name : str : default see `name <LVOCControlMechanism.name>`
        specifies the name of the LVOCControlMechanism.

    prefs : PreferenceSet or specification dict : default Mechanism.classPreferences
        specifies the `PreferenceSet` for the LVOCControlMechanism; see `prefs <LVOCControlMechanism.prefs>` for details.

    Attributes
    ----------

    feature_values : 1d ndarray
        the current `values <InputState.value>` of the InputStates used by `function <LVOCControlMechanism.function>`
        to determine `allocation_policy <LVOCControlMechanism.allocation_policy>` (see
        `LVOCControlMechanism_Feature_Predictors` for details about feature_predictors).

    objective_mechanism : ObjectiveMechanism
        the 'ObjectiveMechanism' used by the LVOCControlMechanism to evaluate the performance of its `system
        <LVOCControlMechanism.system>`.  If a list of OutputStates is specified in the **objective_mechanism** argument
        of the LVOCControlMechanism's constructor, they are assigned as the `monitored_output_states
        <ObjectiveMechanism.monitored_output_states>` attribute for the `objective_mechanism
        <LVOCControlMechanism.objective_mechanism>` (see LVOCControlMechanism_ObjectiveMechanism for additional
        details).

    monitored_output_states : List[OutputState]
        list of the OutputStates monitored by `objective_mechanism <LVOCControlMechanism.objective_mechanism>`
        (and listed in its `monitored_output_states <ObjectiveMechanism.monitored_output_states>` attribute),
        and used to evaluate the performance of the LVOCControlMechanism's `system <LVOCControlMechanism.system>`.

    monitored_output_states_weights_and_exponents: List[Tuple[scalar, scalar]]
        a list of tuples, each of which contains the weight and exponent (in that order) for an OutputState in
        `monitored_outputStates`, listed in the same order as the outputStates are listed in `monitored_outputStates`.

    prediction_terms : List[PV]
        identifies terms included in `prediction_vector <LVOCControlMechanism.prediction_vector>`.
        Items are members of the `PV` enum; the default is [`F <PV.F>`, `C <PV.C>` `FC <PV.FC>`, `COST <PV.COST>`].

    prediction_vector : 1d ndarray
        current values, respectively, of `feature_predictors <LVOCControlMechanism_Feature_Predictors>`,
        interaction terms for feature_predictors x control_signals, `control_signals
        <LVOCControlMechanism.control_signals>`, and `costs <ControlSignal.cost>` of control_signals.

    prediction_weights : 1d ndarray
        weights assigned to each term of `prediction_vector <LVOCControlMechanism.prediction_vectdor>`
        last returned by `function <LVOCControlMechanism.function>`.

    function : LearningFunction or callable
        takes `prediction_vector <LVOCControlMechanism.prediction_vector>` and outcome and returns an updated set of
        `prediction_weights <LVOCControlMechanism.prediction_weights>` (see `LVOCControlMechanism_Function`
        for additional details).

    update_rate : int or float
        determines the amount by which the `value <ControlSignal.value>` of each `ControlSignal` in the
        `allocation_policy <LVOCControlMechanism.allocation_policy>` is modified in each iteration of the
        `gradient_ascent <LVOCControlMechanism.gradient_ascent>` method.

    convergence_criterion : LVOC or CONTROL_SIGNALS
        determines the measure used to terminate execution of the `gradient_ascent
        <LVOCControlMechanism.gradient_ascent>` method;  when the change in its value from one iteration of the
        method to the next falls below `convergence_threshold <LVOCControlMechanism.convergence_threshold>`,
        the method is terminated and an `allocation_policy <LVOCControlMechanism.allocation_policy>` is returned.

    convergence_threshold : int or float : default 0.001
        determines the threhsold of change in the value of the `convergence_criterion` across iterations of
        `gradient_ascent <LVOCControlMechanism.gradient_ascent>`, below which the method is terminated and an
        `allocation_policy <LVOCControlMechanism.allocation_policy>` is returned.

    max_iterations : int
        determines the maximum number of iterations `gradient_ascent <LVOCControlMechanism.gradient_ascent>`
        method is allowed to execute; if exceeded, a warning is issued, and the method returns the
        last `allocation_policy <LVOCControlMechanism.allocation_policy>` evaluated.

    allocation_policy : 2d np.array : defaultControlAllocation
        determines the value assigned as the `variable <ControlSignal.variable>` for each `ControlSignal` and its
        associated `ControlProjection`.  Each item of the array must be a 1d array (usually containing a scalar)
        that specifies an `allocation` for the corresponding ControlSignal, and the number of items must equal the
        number of ControlSignals in the LVOCControlMechanism's `control_signals` attribute.

    control_signals : ContentAddressableList[ControlSignal]
        list of the LVOCControlMechanism's `ControlSignals <LVOCControlMechanism_ControlSignals>`, including any that it inherited
        from its `system <LVOCControlMechanism.system>` (same as the LVOCControlMechanism's `output_states
        <Mechanism_Base.output_states>` attribute); each sends a `ControlProjection` to the `ParameterState` for the
        parameter it controls

    name : str
        the name of the LVOCControlMechanism; if it is not specified in the **name** argument of the constructor, a
        default is assigned by MechanismRegistry (see `Naming` for conventions used for default and duplicate names).

    prefs : PreferenceSet or specification dict
        the `PreferenceSet` for the LVOCControlMechanism; if it is not specified in the **prefs** argument of the
        constructor, a default is assigned using `classPreferences` defined in __init__.py (see :doc:`PreferenceSet
        <LINK>` for details).
    """

    componentType = LVOCCONTROLMECHANISM

    classPreferenceLevel = PreferenceLevel.SUBTYPE
    # classPreferenceLevel = PreferenceLevel.TYPE
    # Any preferences specified below will override those specified in TypeDefaultPreferences
    # Note: only need to specify setting;  level will be assigned to Type automatically
    # classPreferences = {
    #     kwPreferenceSetName: 'DefaultControlMechanismCustomClassPreferences',
    #     kp<pref>: <setting>...}

    class Params(ControlMechanism.Params):
        function = BayesGLM

    paramClassDefaults = ControlMechanism.paramClassDefaults.copy()
    paramClassDefaults.update({PARAMETER_STATES: NotImplemented}) # This suppresses parameterStates

    @tc.typecheck
    def __init__(self,
                 feature_predictors:tc.optional(tc.any(Iterable, Mechanism, OutputState, InputState))=None,
                 feature_function:tc.optional(tc.any(is_function_type))=None,
                 objective_mechanism:tc.optional(tc.any(ObjectiveMechanism, list))=None,
                 origin_objective_mechanism=False,
                 terminal_objective_mechanism=False,
                 function=BayesGLM,
                 prediction_terms:tc.optional(list)=None,
                 prediction_weight_priors:tc.optional(tc.any(list, np.ndarray, dict))=None,
                 update_rate=0.01,
                 convergence_criterion:tc.enum(LVOC, CONTROL_SIGNALS)=LVOC,
                 convergence_threshold=0.01,
                 max_iterations=1000,
                 control_signals:tc.optional(tc.any(is_iterable, ParameterState))=None,
                 modulation:tc.optional(_is_modulation_param)=ModulationParam.MULTIPLICATIVE,
                 params=None,
                 name=None,
                 prefs:is_pref_set=None,
                 **kwargs):

        prediction_terms = prediction_terms or [PV.F,PV.C,PV.FC, PV.COST]
        if ALL in prediction_terms:
            prediction_terms = list(PV.__members__.values())

        if feature_predictors is None:
            # Included for backward compatibility
            if 'predictors' in kwargs:
                feature_predictors = kwargs['predictors']
                del(kwargs['predictors'])
            else:
                raise LVOCError("{} arg for {} must be specified".format(repr(FEATURE_PREDICTORS),
                                                                         self.__class__.__name__))
        if kwargs:
                for i in kwargs.keys():
                    raise LVOCError("Unrecognized arg in constructor for {}: {}".format(self.__class__.__name__,
                                                                                        repr(i)))


        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(input_states=feature_predictors,
                                                  feature_function=feature_function,
                                                  prediction_terms=prediction_terms,
                                                  prediction_weight_priors=prediction_weight_priors,
                                                  convergence_criterion=convergence_criterion,
                                                  convergence_threshold=convergence_threshold,
                                                  max_iterations=max_iterations,
                                                  update_rate=update_rate,
                                                  origin_objective_mechanism=origin_objective_mechanism,
                                                  terminal_objective_mechanism=terminal_objective_mechanism,
                                                  params=params)

        super().__init__(system=None,
                         objective_mechanism=objective_mechanism,
                         function=function,
                         control_signals=control_signals,
                         modulation=modulation,
                         params=params,
                         name=name,
                         prefs=prefs)

    def _validate_params(self, request_set, target_set=None, context=None):
        '''Insure that specification of ObjectiveMechanism has projections to it'''

        super()._validate_params(request_set=request_set, target_set=target_set, context=context)

        if (OBJECTIVE_MECHANISM in request_set and
                isinstance(request_set[OBJECTIVE_MECHANISM], ObjectiveMechanism)
                and not request_set[OBJECTIVE_MECHANISM].path_afferents):
            raise LVOCError("{} specified for {} ({}) must be assigned one or more {}".
                            format(ObjectiveMechanism.__name__, self.name,
                                   request_set[OBJECTIVE_MECHANISM], repr(MONITORED_OUTPUT_STATES)))

        if PREDICTION_TERMS in request_set:
            if not all(term in PV for term in request_set[PREDICTION_TERMS]):
                raise LVOCError("One or more items in list specified for {} arg of {} is not a member of the {} enum".
                                format(repr(PREDICTION_TERMS), self.name, PV.__class__.__name__))

        if PREDICTION_WEIGHT_PRIORS in request_set and request_set[PREDICTION_WEIGHT_PRIORS]:
            priors = request_set[PREDICTION_WEIGHT_PRIORS]
            if isinstance(priors, dict):
                if not all(key in PV for key in request_set[PREDICTION_WEIGHT_PRIORS.keys()]):
                    raise LVOCError("One or more keys in dict specifed for {} arg of {} is not a member of the {} enum".
                                    format(repr(PREDICTION_WEIGHT_PRIORS), self.name, PV.__class__.__name__))
                if not all(key in self.prediction_terms for key in request_set[PREDICTION_WEIGHT_PRIORS.keys()]):
                    raise LVOCError("One or more keys in dict specifed for {} arg of {} "
                                    "is for a prediction term not specified in {} arg".
                                    format(repr(PREDICTION_WEIGHT_PRIORS), self.name,
                                           PV.__class__.__name__, repr(PREDICTION_TERMS)))


    def _instantiate_input_states(self, context=None):
        """Instantiate input_states for Projections from features and objective_mechanism.

        Inserts InputState specification for Projection from ObjectiveMechanism as first item in list of
        InputState specifications generated in _parse_feature_specs from the **feature_predictors** and
        **feature_function** arguments of the LVOCControlMechanism constructor.
        """

        self.input_states = self._parse_feature_specs(self.input_states, self.feature_function)

        # Insert primary InputState for outcome from ObjectiveMechanism; assumes this will be a single scalar value
        self.input_states.insert(0, {NAME:OUTCOME, PARAMS:{INTERNAL_ONLY:True}}),

        # Configure default_variable to comport with full set of input_states
        self.instance_defaults.variable, ignore = self._handle_arg_input_states(self.input_states)

        super()._instantiate_input_states(context=context)

    def _instantiate_attributes_before_function(self, function=None, context=None):
        super()._instantiate_attributes_before_function(function=function, context=context)

    tc.typecheck
    def add_features(self, feature_predictors):
        '''Add InputStates and Projections to LVOCControlMechanism for feature_predictors used to predict outcome

        **feature_predictors** argument can use any of the forms of specification allowed for InputState(s),
            as well as a dictionary containing an entry with *SHADOW_EXTERNAL_INPUTS* as its key and a
            list of `ORIGIN` Mechanisms and/or their InputStates as its value.
        '''

        feature_predictors = self._parse_feature_specs(feature_predictors=feature_predictors,
                                                 context=ContextFlags.COMMAND_LINE)
        self.add_states(InputState, feature_predictors)

    @tc.typecheck
    def _parse_feature_specs(self, feature_predictors, feature_function, context=None):
        """Parse entries of feature_predictors into InputState spec dictionaries

        For InputState specs in SHADOW_EXTERNAL_INPUTS ("shadowing" an Origin InputState):
            - Call _parse_shadow_input_spec

        For standard InputState specs:
            - Call _parse_state_spec
            - Set INTERNAL_ONLY entry of params dict of InputState spec dictionary to True

        Assign functions specified in **feature_function** to InputStates for all feature_predictors

        Returns list of InputState specification dictionaries
        """

        parsed_features = []

        if not isinstance(feature_predictors, list):
            feature_predictors = [feature_predictors]

        for spec in feature_predictors:

            # e.g. {SHADOW_EXTERNAL_INPUTS: [A]}
            if isinstance(spec, dict):
                if SHADOW_EXTERNAL_INPUTS in spec:
                    #  composition looks for node.shadow_external_inputs and uses it to set external_origin_sources
                    self.shadow_external_inputs = spec[SHADOW_EXTERNAL_INPUTS]
                    spec = self._parse_shadow_inputs_spec(spec, feature_function)
                else:
                    raise LVOCError("Incorrect specification ({}) in feature_predictors argument of {}."
                                    .format(spec, self.name))
            # e.g. Mechanism, OutputState
            else:
                spec = _parse_state_spec(state_type=InputState, state_spec=spec)    # returns InputState dict
                spec[PARAMS][INTERNAL_ONLY] = True
                if feature_function:
                    spec[PARAMS][FUNCTION] = feature_function
                spec = [spec]   # so that extend works below

            parsed_features.extend(spec)

        return parsed_features

    @tc.typecheck
    def _parse_shadow_inputs_spec(self, spec:dict, fct:tc.optional(Function)):
        ''' Return a list of InputState specifications for the inputs specified in value of dict

        For any other specification, specify an InputState with a Projection from the sender of any Projections
            that project to the specified item
        If FUNCTION entry, assign as Function for all InputStates specified in SHADOW_EXTERNAL_INPUTS
        '''

        input_state_specs = []

        shadow_spec = spec[SHADOW_EXTERNAL_INPUTS]

        if not isinstance(shadow_spec, list):
            shadow_spec = [shadow_spec]
        for item in shadow_spec:
            if isinstance(item, Mechanism):
                # Shadow all of the InputStates for the Mechanism
                input_states = item.input_states
            if isinstance(item, InputState):
                # Place in a list for consistency of handling below
                input_states = [item]
            # Shadow all of the Projections to each specified InputState
            input_state_specs.extend([
                {
                    #NAME:i.name + ' of ' + i.owner.name,
                    VARIABLE: i.variable}
                for i in input_states
            ])
        if fct:
            for i in input_state_specs:
                i.update({FUNCTION:fct})

        return input_state_specs

    def _instantiate_control_signal(self, control_signal, context=None):
        '''Implement ControlSignalCosts.DEFAULTS as default for cost_option of ControlSignals
        LVOCControlMechanism requires use of at least one of the cost options
        '''
        control_signal = super()._instantiate_control_signal(control_signal, context)

        if control_signal.cost_options is None:
            control_signal.cost_options = ControlSignalCosts.DEFAULTS
            control_signal._instantiate_cost_attributes()
        return control_signal

    # FIX: ??MOVE THIS TO _instantiate_attributes_before_function AND USE IN CONSTRUCTION OF FUNCTION??
    def _instantiate_attributes_after_function(self, context=None):
        super()._instantiate_attributes_after_function(context=context)
        # FIX: ??SHOULD THIS ASSIGNMENT BE TO self.parameters_states['mu_0'] INSTEAD:
        if self.prediction_weight_priors and 'mu_0' in self.function_object.params:
            mu_0 = self.function_object.params['mu_0']
            if isinstance(self.prediction_weights_priors, (int, float)):
                mu_0 = np.full((len(mu_0),1), mu_0)
            elif isinstance(self.prediction_weights_priors, (list, np.ndarray)):
                if len(mu_0) != len(self.prediction_weights_priors):
                    raise LVOCError("Length of array specified for {} arg of {} ({}) does not match one expected ({})".
                                    format(repr('mu_0'), repr(PREDICTION_WEIGHT_PRIORS), self.name,
                                           len(self.prediction_weight_priors), len(mu_0)))
            elif isinstance(self.prediction_weight_priors, dict):
                for k, v in self.prediction_weight_priors:
                    mu_0[getattr(self.prediction_vector.idx, k.value)] = v
            else:
                raise LVOCError("Unrecognized specification ({}) for {} arg of {}.".
                                format(repr(self.prediction_weight_priors), repr(PREDICTION_WEIGHT_PRIORS), self.name))
        self.cost_functions = [c.intensity_cost_function for c in self.control_signals]


    def _execute(self, variable=None, runtime_params=None, context=None):
        """Determine `allocation_policy <LVOCControlMechanism.allocation_policy>` for current run of Composition

        Items of variable should be:
          - variable[0]: `value <OutputState.value>` of the *OUTCOME* OutputState of `objective_mechanism
            <LVOCControlMechanism.objective_mechanism>`.
          - variable[n]: current value of `feature_predictor <LVOCControlMechanism_Feature_Predictors>`\\[n]

        Call to super._execute updates the prediction_vector, and calculates outcome from last trial, by subtracting
        the `costs <ControlSignal.costs>` for the `control_signal <LVOCControlMechanism.control_signals>` values used
        in the previous trial from the value received from the `objective_mechanism
        <LVOCControlMechanism.objective_mechanism>` (in variable[0]) reflecting performance on the previous trial.
        It then calls the LVOCControlMechanism's `function <LVOCControlMechanism.function>` to update the
        `prediction_weights <LVOCControlMechanism.prediction_weights>` so as to better predict the outcome.

        Call to `gradient_ascent` determines `allocation_policy <LVOCControlMechanism>` that yields greatest `EVC
        <LVCOControlMechanism_EVC>` given the new `prediction_weights <LVOCControlMechanism.prediction_weights>`.
        """

        if (self.context.initialization_status == ContextFlags.INITIALIZING):
            return defaultControlAllocation

        # Get sample of weights
        # IMPLEMENTATION NOTE: skip ControlMechanism._execute since it is a stub method that returns input_values
        self.prediction_weights = super(ControlMechanism, self)._execute(variable=variable,
                                                                         runtime_params=runtime_params,
                                                                         context=context
                                                                         )

        # Compute allocation_policy using gradient_ascent
        allocation_policy = self.autograd_ascent(self.control_signals,
                                                 self.prediction_vector,
                                                 self.prediction_weights)

        # allocation_policy = self.gradient_ascent(self.control_signals,
        #                                          self.prediction_vector,
        #                                          self.prediction_weights)


        # return allocation_policy.reshape((len(allocation_policy),1))
        return allocation_policy

    def _parse_function_variable(self, variable, context=None):
        '''Update current prediction_vector, and return prediction vector and outcome from previous trial

        Updates prediction_vector for current trial, and buffers this in prediction_buffer;
        also buffers costs of control_signals used in previous trial ]in previous_costs.

        Computes outcome for previous trial by subtracting costs of control_signals from outcome received
        from objective_mechanism, both of which reflect values assigned in previous trial
        (since Projection from objective_mechanism is a feedback Projection, the value received from it corresponds
        to the one computed on the previous trial).
        # FIX: SHOULD REFERENCE RELEVANT DOCUMENTATION ON COMPOSITION REGARDING FEEDBACK CONNECTIONS)

        Returns prediction_vector and outcome from previous trial,
        used by function to update prediction_weights that will be used to predict the EVC for the current trial.
        '''

        # This is the value received from the objective_mechanism's OUTCOME OutputState:
        obj_mech_outcome = variable[0]

        # This is the current values of the feature_predictors
        self.feature_values = np.array(np.array(variable[1:]).tolist())

        # Instantiate PredictionVector and related attributes
        if context is ContextFlags.INSTANTIATE:
            self.prediction_vector = self.PredictionVector(self.feature_values,
                                                           self.control_signals,
                                                           self.prediction_terms)
            self.prediction_buffer = deque([self.prediction_vector.vector], maxlen=2)
            self.previous_cost = np.zeros_like(obj_mech_outcome)

        # Update values
        else:
            control_signal_values = [c.value for c in self.control_signals]
            control_signal_costs = [0 if c.cost is None else c.cost for c in self.control_signals]
            self.prediction_vector._update(self.feature_values,
                                           control_signal_values,
                                           control_signal_costs,
                                           self.prediction_terms)

            self.prediction_buffer.append(self.prediction_vector.vector)
            self.previous_cost = np.sum(self.prediction_vector.vector[self.prediction_vector.idx.cst])

        outcome = obj_mech_outcome + self.previous_cost # costs are assigned as negative above, so add them here

        return [self.prediction_buffer.popleft(), outcome]


    class PredictionVector():
        '''Full generalization:  allow main effect and interactio jterms to be specified for inclusion
        STILL UNDER DEVELOPMENT
        '''

        class idx():
            '''Indices into PredictionVector.vector -- assigned in __init__'''
            f = None
            c = None
            fc = None
            ff = None
            cc = None
            ffc = None
            fcc = None
            ffcc = None
            cst = None


        class labels():
            '''labels indivual items in each set of terms of PredictionVector.vector -- assigned in __init__'''
            f = None
            c = None
            fc = None
            ff = None
            cc = None
            ffc = None
            fcc = None
            ffcc = None
            cst = None


        def __init__(self, feature_values, control_signals, terms):

            # ASSIGN TERMS

            # Used for computing partial derivatives
            labels = self.labels
            def get_intrxn_labels(x):
                # return list([s for s in powerset([str(i) for i in range(0,n)]) if len(s)>1])
                return list([s for s in powerset(x) if len(s)>1])

            def error_for_too_few_terms(term):
                spec_type = {'FF':'feature_predictors', 'CC':'control_signals'}
                raise LVOCError("Specification of {} for {} arg of {} requires at least two {} be specified".
                                format('PV.'+terms, repr(PREDICTION_TERMS), self.name, spec_type(term)))

            # MAIN EFFECT TERMS (unflattened)

            # Feature_predictors
            self.f = feature_values
            self.num_f = len(self.f)  # feature_predictors are arrays; num_f is the number of arrays
            self.num_f_elems = len(self.f.reshape(-1)) # number of total elements assigned to prediction_vector.vector
            labels.f = ['f'+str(i) for i in range(0,self.num_f)]

            # ControlSignals - place value of each in a 1d array (for computing tensor products)
            self.c = np.array([[0]] * len(control_signals)) # Placemarker until control_signals are instantiated
            self.num_c = len(self.c)
            self.num_c_elems = len(self.c.reshape(-1))
            labels.c = ['c'+str(i) for i in range(0,len(control_signals))]

            # Costs
            self.num_cst = self.num_c
            labels.cst = ['cst'+str(i) for i in range(0,self.num_cst)]

            # INTERACTION TERMS (unflattened)

            # Interactions among feature_predictor vectors
            if any(term in terms for term in [PV.FF, PV.FFC, PV.FFCC]):
                if self.num_f < 2:
                    self.error_for_too_few_terms('FF')
                self.ff = np.array(tensor_power(self.f, levels=range(2,self.num_f+1)))
                self.num_ff = len(self.ff)
                self.num_ff_elems = len(self.ff.reshape(-1))
                labels.ff= get_intrxn_labels(labels.f)

            # Interactions among values of control_signals
            if any(term in terms for term in [PV.CC, PV.FCC, PV.FFCC]):
                if self.num_c < 2:
                    self.error_for_too_few_terms('CC')
                self.cc = np.array(tensor_power(self.c, levels=range(2,self.num_c+1)))
                self.num_cc=len(self.cc)
                self.num_cc_elems = len(self.cc.reshape(-1))
                labels.cc = get_intrxn_labels(labels.c)

            # Feature-Control interactions
            if any(term in terms for term in [PV.FC, PV.FCC, PV.FFCC]):
                self.fc = np.tensordot(feature_values, self.c, axes=0)
                self.num_fc = len(self.fc.reshape(-1))
                self.num_fc_elems = len(self.fc.reshape(-1))
                labels.fc = list(product(labels.f, labels.c))

            # Feature-Feature-Control interactions
            if any(term in terms for term in [PV.FFC, PV.FFCC]):
                if self.num_f < 2:
                    self.error_for_too_few_terms('FF')
                self.ffc = np.tensordot(self.ff, self.c, axes=0)
                self.num_ffc = len(self.ffc.reshape(-1))
                self.num_ffc_elems = len(self.ffc.reshape(-1))
                labels.ffc = list(product(labels.ff, labels.c))

            # Feature-Control-Control interactions
            if any(term in terms for term in [PV.FCC, PV.FFCC]):
                if self.num_c < 2:
                    self.error_for_too_few_terms('CC')
                self.fcc = np.tensordot(self.f, self.cc, axes=0)
                self.num_fcc = len(self.fcc.reshape(-1))
                self.num_fcc_elems = len(self.fcc.reshape(-1))
                labels.fcc = list(product(labels.f, labels.cc))

            # Feature-Feature-Control-Control interactions
            if PV.FFCC in terms:
                if self.num_f < 2:
                    self.error_for_too_few_terms('FF')
                if self.num_c < 2:
                    self.error_for_too_few_terms('CC')
                self.ffcc = np.tensordot(self.ff, self.cc, axes=0)
                self.num_ffcc = len(self.ffcc.reshape(-1))
                self.num_ffcc_elems = len(self.ffcc.reshape(-1))
                labels.ffcc = list(product(labels.ff, labels.cc))

            # Construct "flattened" prediction_vector based on specified terms and assign indices (as slices)
            idx = self.idx
            # FIX: ??refactor as iterate through enum
            i = 0
            if PV.F in terms:
                idx.f = slice(i, i+self.num_f_elems)
                i += self.num_f
            if PV.C in terms:
                idx.c = slice(i, i+self.num_c_elems)
                i += self.num_c
            if PV.FF in terms:
                idx.ff = slice(i, i+self.num_ff_elems)
                i += self.num_ff
            if PV.CC in terms:
                idx.cc = slice(i, i+self.num_cc_elems)
                i += self.num_cc
            if PV.FC in terms:
                idx.fc = slice(i, i+self.num_fc_elems)
                i += self.num_fc
            if PV.FFC in terms:
                idx.ffc = slice(i, i+self.num_ffc_elems)
                i += self.num_ffc
            if PV.FCC in terms:
                idx.fcc = slice(i, i+self.num_fcc_elems)
                i += self.num_fcc
            if PV.FFCC in terms:
                idx.ffcc = slice(i, i+self.num_ffcc_elems)
                i += self.num_ffcc
            if PV.COST in terms:
                idx.cst = slice(i, i+self.num_cst)
                i+= self.num_cst

            self.vector = np.zeros(i)

        def _update(self, feature_values, control_signal_values, control_signal_costs, terms):

            # Populate fields (subvectors) of prediction_vector

            idx = self.idx
            self.f = np.array(feature_values)
            self.c = np.array(control_signal_values)

            # Compute terms that are used (preserving their structure):
            if any(term in terms for term in [PV.FF, PV.FFC, PV.FFCC]):
                self.ff = np.array(tensor_power(self.f, range(2,self.num_f+1)))
            if any(term in terms for term in [PV.CC, PV.FCC, PV.FFCC]):
                self.cc = np.array(tensor_power(self.c, range(2,self.num_c+1)))
            if any(term in terms for term in [PV.FC, PV.FCC, PV.FFCC]):
                self.fc= np.tensordot(self.f, self.c,axes=0)
            if any(term in terms for term in [PV.FFC, PV.FFCC]):
                self.ffc = np.tensordot(self.ff,self.c,axes=0)
            if any(term in terms for term in [PV.FCC, PV.FFCC]):
                self.fcc = np.tensordot(self.f,self.cc,axes=0)
            if PV.FFCC in terms:
                self.ffcc = np.tensordot(self.ff,self.cc,axes=0)

            # Assign specified terms to flattened vector
            if PV.F in terms:
                self.vector[idx.f] = self.f.reshape(-1)
            if PV.C in terms:
                self.vector[idx.c] = self.c.reshape(-1)
            if PV.FF in terms:
                self.vector[idx.ff] = self.ff.reshape(-1)
            if PV.CC in terms:
                self.vector[idx.cc] = self.cc.reshape(-1)
            if PV.FC in terms:
                self.vector[idx.fc] = self.fc.reshape(-1)
            if PV.FFC in terms:
                self.vector[idx.ffc] = self.ffc.reshape(-1)
            if PV.FCC in terms:
                self.vector[idx.fcc] = self.fcc.reshape(-1)
            if PV.FFCC in terms:
                self.vector[idx.ffcc] = self.ffcc.reshape(-1)
            if PV.COST in terms:
                self.vector[idx.cst] = np.array(control_signal_costs).reshape(-1) * -1

        def _partial_derivative(self, term_label, pw, ctl_idx, ctl_val):
            '''Compute derivative of interaction (term) for prediction vector (pv) and prediction_weights (pw)
            with respect to control_signal i'''


            # Get label and value of control signal with respect to which the derivative is being taken
            ctl_label = self.labels.c[ctl_idx]

            # Get labels and values of terms, and weights
            t_labels = getattr(self.labels, term_label.value)
            terms = getattr(self, term_label.value)
            wts_idx = getattr(self.idx, term_label.value)
            # Reshape weights to match termss
            weights = pw[wts_idx].reshape(np.array(terms).shape)

            gradient = 0

            # Compute derivative for terms that contain control signal
            for t_label, term, wts in zip(t_labels,terms,weights):
                if ctl_label in t_label:
                    gradient += np.sum((term/ctl_val)*wts)

            return gradient

    def gradient_ascent(self, control_signals, prediction_vector, prediction_weights):
        '''Determine the `allocation_policy <LVOCControlMechanism.allocation_policy>` that maximizes the `EVC
        <LVOCControlMechanism_EVC>`.

        Iterate over prediction_vector; for each iteration: \n
        - compute gradients based on current control_signal values and their costs (in prediction_vector);
        - compute new control_signal values based on gradients;
        - update prediction_vector with new control_signal values and the interaction terms and costs based on those;
        - use prediction_weights and updated prediction_vector to compute new `EVC <LVOCControlMechanism_EVC>`.

        Continue to iterate until difference between new and old EVC is less than `convergence_threshold
        <LearnAllocationPolicy.convergence_threshold>` or number of iterations exceeds `max_iterations
        <LearnAllocationPolicy.max_iterations>`.

        Return control_signals field of prediction_vector (used by LVOCControlMechanism as its `allocation_vector
        <LVOCControlMechanism.allocation_policy>`).
        '''

        pv = prediction_vector.vector
        idx = prediction_vector.idx
        # labels = prediction_vector.labels
        num_c = prediction_vector.num_c
        num_cst = prediction_vector.num_cst
        # num_intrxn = prediction_vector.num_interactions

        convergence_metric = self.convergence_threshold + EPSILON
        previous_lvoc = np.finfo(np.longdouble).max
        prev_control_signal_values = np.full(num_c, np.finfo(np.longdouble).max)

        feature_predictors = self.feature_values.reshape(-1)

        control_signal_values = [np.array(c.value) for c in self.control_signals]

        costs = [np.array(c.cost) for c in self.control_signals]
        if PV.COST in self.prediction_terms:
            cost_weights = prediction_weights[idx.cst]

        # COMPUTE DERIVATIVES THAT ARE CONSTANTS
        #    Do it here so don't have to do it in each iteration of the while loop

        gradient_constants = np.zeros(num_c)

        # Derivative for control_signals
        if PV.C in self.prediction_terms:
            # d(c*wt)/(dc) = wt
            gradient_constants += np.array(prediction_weights[idx.c])

        # FIX: CHECK THAT THESE COMPUTE SAME VALUES AS _partial_derivative
        # Derivatives for fc interactions:
        if PV.FC in self.prediction_terms:
            # Get weights for fc interaction term and reshape so that there is one row per control_signal
            #    containing the terms for the interaction of that control_signal with each of the feature_predictors
            fc_weights = prediction_weights[idx.fc].reshape(num_c, prediction_vector.num_f_elems)
            fc_weights_x_features = fc_weights * feature_predictors
            for i in range(num_c):
                gradient_constants[i] += np.sum(fc_weights_x_features[i])

        # Derivatives for ffc interactions:
        if PV.FFC in self.prediction_terms:
            # Get weights for ffc interaction term and reshape so that there is one row per control_signal
            #    containing the terms for the interaction of that control_signal with each of the feature interactions
            ffc_weights = prediction_weights[idx.ffc].reshape(num_c, prediction_vector.num_ff_elems)
            ffc_weights_x_ff = ffc_weights * prediction_vector.ff.reshape(-1)
            for i in range(num_c):
                gradient_constants[i] += np.sum(ffc_weights_x_ff[i])

        # TEST PRINT:
        print(
                '\nprediction_weights: ', prediction_weights,
              )
        self.test_print(prediction_vector)
        # TEST PRINT END:

        # Perform gradient ascent on d(control_signals)/dEVC until convergence criterion is reached
        j=0
        while convergence_metric > self.convergence_threshold:
            # initialize gradient arrray (one gradient for each control signal)
            gradient = np.copy(gradient_constants)

            for i, control_signal_value in enumerate(control_signal_values):

                # Derivative of cc interaction term with respect to current control_signal_value
                if PV.CC in self.prediction_terms:
                    gradient[i] += prediction_vector._partial_derivative(PV.CC, prediction_weights, i,
                                                                         control_signal_value)

                # Derivative of ffcc interaction term with respect to current control_signal_value
                if PV.FFCC in self.prediction_terms:
                    gradient[i] += prediction_vector._partial_derivative(PV.FFCC, prediction_weights, i,
                                                                         control_signal_value)

                # Derivative for costs (since costs depend on control_signals)
                if PV.COST in self.prediction_terms:
                    cost_function_derivative = control_signals[i].intensity_cost_function.__self__.derivative
                    gradient[i] += np.sum(cost_function_derivative(control_signal_value) * cost_weights[i])

                # Update control_signal_value with gradient
                control_signal_values[i] = control_signal_value + self.update_rate * gradient[i]

                # Update cost based on new control_signal_value
                costs[i] = control_signals[i].intensity_cost_function(control_signal_value)

            # Only updatre terms with control_signal in them
            terms = [term for term in self.prediction_terms if 'c' in term.value]
            prediction_vector._update(self.feature_values, control_signal_values, costs, terms)

            # Compute current LVOC using current feature_predictors, weights and new control signals
            current_lvoc = self.compute_lvoc(pv, prediction_weights)

            if self.convergence_criterion == LVOC:
                # Compute convergence metric with updated control signals
                convergence_metric = np.abs(current_lvoc - previous_lvoc)
            else:
                convergence_metric = np.max(np.abs(np.array(control_signal_values) -
                                                   np.array(prev_control_signal_values)))

            # TEST PRINT:
            print(
                    '\niteration {}-{}'.format(self.current_execution_count-1, j),
                    '\nprevious_lvoc: ', previous_lvoc,
                    '\ncurrent_lvoc: ',current_lvoc ,
                    '\nconvergence_metric: ',convergence_metric,
            )
            self.test_print(prediction_vector)
            # TEST PRINT END

            j+=1
            if j > self.max_iterations:
                warnings.warn("{} failed to converge after {} iterations".format(self.name, self.max_iterations))
                break

            previous_lvoc = current_lvoc
            prev_control_signal_values = control_signal_values

        return control_signal_values

    def compute_lvoc(self, v, w):
        return np.sum(v * w)

    def autograd_ascent(self, control_signals, prediction_vector, prediction_weights):

        convergence_metric = self.convergence_threshold + EPSILON
        previous_lvoc = np.finfo(np.longdouble).max
        num_c = len(self.control_signals)
        prev_control_signal_values = np.full(num_c, np.finfo(np.longdouble).max)
        control_signal_values = np.array([c.value for c in control_signals])
        # FIX: MOVE TO PredictionVector
        grad_of_lvoc_wrt_control_signals = grad(self.compute_lvoc_from_control_signals)

        iteration=0
        while convergence_metric > self.convergence_threshold:

            # FIX: put in _instantiate_attributes_after_function
            current_lvoc = self.compute_lvoc_from_control_signals(control_signal_values)
            # grad_of_lvoc_wrt_control_signals = grad(self.compute_lvoc_from_control_signals)

            gradients = grad_of_lvoc_wrt_control_signals(control_signal_values)
            # control_signal_values = control_signal_values + self.update_rate * gradients
            control_signal_values = (np.array(control_signal_values) + self.update_rate * np.array(gradients)).tolist()

            if self.convergence_criterion == LVOC:
                # Compute convergence metric with updated control signals
                convergence_metric = np.abs(current_lvoc - previous_lvoc)
            else:
                convergence_metric = np.max(np.abs(np.array(control_signal_values) -
                                                   np.array(prev_control_signal_values)))

            # TEST PRINT:
            print(
                    '\niteration {}-{}'.format(self.current_execution_count-1, iteration),
                    '\nprevious_lvoc: ', previous_lvoc,
                    '\ncurrent_lvoc: ',current_lvoc ,
                    '\nconvergence_metric: ',convergence_metric,
            )
            self.test_print(prediction_vector)
            # TEST PRINT END

            iteration+=1
            if iteration > self.max_iterations:
                warnings.warn("{} failed to converge after {} iterations".format(self.name, self.max_iterations))
                break

            self.lvoc = current_lvoc
            previous_lvoc = current_lvoc
            prev_control_signal_values = control_signal_values

        return control_signal_values


    def compute_lvoc_from_control_signals(self, control_signal_values):

        idx = self.prediction_vector.idx
        terms = self.prediction_terms
        v = self._compute_terms(control_signal_values)
        w = self.prediction_weights

        lvoc = 0
        i = 0
        if PV.F in terms:
            lvoc += np.sum(np.array(v[i]).reshape(-1) * self.prediction_weights[idx.f])
            i+=1
        if PV.C in terms:
            lvoc += np.sum(np.array(control_signal_values).reshape(-1) * self.prediction_weights[idx.c])
            i+=1
        if PV.FF in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.ff])
            i+=1
        if PV.CC in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.cc])
            i+=1
        if PV.FC in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.fc])
            i+=1
        if PV.FFC in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.ffc])
            i+=1
        if PV.FCC in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.fcc])
            i+=1
        if PV.FFCC in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.ffcc])
            i+=1
        if PV.COST in terms:
            lvoc += np.sum(v[i].reshape(-1) * self.prediction_weights[idx.cst])

        return lvoc

        # return np.sum(v*w)

    def _compute_terms(self, control_signal_values):

        terms = self.prediction_terms
        num_f = len(self.feature_values)
        num_c = len(self.control_signals)
        idx = self.prediction_vector.idx

        # Compute terms that are used
        f = np.array(self.feature_values)
        c = control_signal_values
        if any(term in terms for term in [PV.FF, PV.FFC, PV.FFCC]):
            ff = np.array(tensor_power(f, range(2, num_f+1)))
        if any(term in terms for term in [PV.CC, PV.FCC, PV.FFCC]):
            cc = np.array(tensor_power(c, range(2, num_c+1)))
        if any(term in terms for term in [PV.FC, PV.FCC, PV.FFCC]):
            fc = np.tensordot(f, c, axes=0)
        if any(term in terms for term in [PV.FFC, PV.FFCC]):
            ffc = np.tensordot(ff, c, axes=0)
        if any(term in terms for term in [PV.FCC, PV.FFCC]):
            fcc = np.tensordot(f,cc,axes=0)
        if PV.FFCC in terms:
            ffcc = np.tensordot(ff,cc,axes=0)
        if PV.COST in terms:
            cst = -np.exp(c)

        opv = self.prediction_vector.vector
        # Construct list with computed terms (for use by autograd) and update prediction_vector
        computed_terms = []
        if PV.F in terms:
            computed_terms += [f]
        if PV.C in terms:
            computed_terms += [c]
        if PV.FF in terms:
            computed_terms += [ff]
        if PV.CC in terms:
            computed_terms += [cc]
        if PV.FC in terms:
            computed_terms += [fc]
        if PV.FFC in terms:
            computed_terms += [ffc]
        if PV.FCC in terms:
            computed_terms += [fcc]
        if PV.FFCC in terms:
            computed_terms += [ffcc]
        if PV.COST in terms:
            computed_terms += [cst]
            if isinstance(cst, (np.ndarray, list)):
                self.prediction_vector.vector[idx.cst] = np.array(cst).reshape(-1)
            else:
                self.prediction_vector.vector[idx.cst] = np.array(cst._value).reshape(-1)

        # Update actual prediction_vector
        return computed_terms



    # TEST PRINT:
    def test_print(self, pv):
        terms = self.prediction_terms
        vector = pv.vector
        idx = pv.idx

        if PV.F in terms:
            print('feature_values: ', vector[idx.f])
        if PV.FF in terms:
            print('ff: ', vector[idx.ff])
        if PV.CC in terms:
            print('cc: ', vector[idx.cc])
        if PV.FC in terms:
            print('fc: ', vector[idx.fc])
        if PV.FFC in terms:
            print('ffc: ', vector[idx.ffc])
        if PV.FCC in terms:
            print('fcc: ', vector[idx.fcc])
        if PV.FFCC in terms:
            print('ffcc: ', vector[idx.ffcc])
        if PV.COST in terms:
            print('cst: ', vector[idx.cst])
        print('control_signal_values: ', vector[idx.c])