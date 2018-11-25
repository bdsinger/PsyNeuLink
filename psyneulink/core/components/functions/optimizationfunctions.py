#
# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
#
# ******************************************   OPTIMIZATION FUNCTIONS **************************************************
'''

* `OptimizationFunction`
* `GradientOptimization`
* `GridSearch`

Overview
--------

Functions that return the sample of a variable yielding the optimized value of an objective_function.

'''

import warnings

import numpy as np
import typecheck as tc

from psyneulink.core.components.functions.function import Function_Base, is_function_type
from psyneulink.core.globals.keywords import DEFAULT_VARIABLE, OPTIMIZATION_FUNCTION_TYPE, OWNER, \
    GRADIENT_OPTIMIZATION_FUNCTION, VALUE, VARIABLE, GRID_SEARCH_FUNCTION
from psyneulink.core.globals.parameters import Param
from psyneulink.core.globals.context import ContextFlags
from psyneulink.core.globals.defaults import MPI_IMPLEMENTATION
from psyneulink.core.globals.utilities import call_with_pruned_args

__all__ = ['OptimizationFunction', 'GradientOptimization', 'GridSearch',
           'OBJECTIVE_FUNCTION', 'SEARCH_FUNCTION', 'SEARCH_SPACE', 'SEARCH_TERMINATION_FUNCTION',
           'DIRECTION', 'ASCENT', 'DESCENT', 'MAXIMIZE', 'MINIMIZE']

OBJECTIVE_FUNCTION = 'objective_function'
SEARCH_FUNCTION = 'search_function'
SEARCH_SPACE = 'search_space'
SEARCH_TERMINATION_FUNCTION = 'search_termination_function'
DIRECTION = 'direction'


class OptimizationFunction(Function_Base):
    """
    OptimizationFunction(                            \
    default_variable=None,                           \
    objective_function=lambda x:0,                   \
    search_function=lambda x:x,                      \
    search_space=[0],                                \
    search_termination_function=lambda x,y,z:True,   \
    save_samples=False,                              \
    save_values=False,                               \
    max_iterations=None,                             \
    params=Nonse,                                    \
    owner=Nonse,                                     \
    prefs=None)

    Provides an interface to subclasses and external optimization functions. The default `function
    <OptimizationFunction.function>` executes iteratively, evaluating samples from `search_space
    <OptimizationFunction.search_space>` using `objective_function <OptimizationFunction.objective_function>`
    until terminated by `search_termination_function <OptimizationFunction.search_termination_function>`.
    Subclasses can override this to implement their own optimization function or call an external one.

    .. _OptimizationFunction_Process:

    **Default Optimization Process**

    When `function <OptimizationFunction.function>` is executed, it iterates over the following steps:

        - get sample from `search_space <OptimizationFunction.search_space>` using `search_function
          <OptimizationFunction.search_function>`.
        ..
        - compute value of `objective_function <OptimizationFunction.objective_function>` using the sample;
        ..
        - evaluate `search_termination_function <OptimizationFunction.search_termination_function>`.

    The current iteration is contained in `iteration <OptimizationFunction.iteration>`. Iteration continues until all
    values of `search_space <OptimizationFunction.search_space>` have been evaluated (i.e., `search_termination_function
    <OptimizationFunction.search_termination_function>` returns `True`).  The `function <OptimizationFunction.function>`
    returns:

    - the last sample evaluated (which may or may not be the optimal value, depending on the `objective_function
      <OptimizationFunction.objective_function>`);

    - the value of `objective_function <OptimzationFunction.objective_function>` associated with the last sample;

    - two lists, that may contain all of the samples evaluated and their values, depending on whether `save_samples
      <OptimizationFunction.save_samples>` and/or `save_vales <OptimizationFunction.save_values>` are `True`,
      respectively.

    .. _OptimizationFunction_Defaults:

    .. note::

        An OptimizationFunction or any of its subclasses can be created by calling its constructor.  This provides
        runnable defaults for all of its arguments (see below). However these do not yield useful results, and are
        meant simply to allow the  constructor of the OptimziationFunction to be used to specify some but not all of
        its parameters when specifying the OptimizationFunction in the constructor for another Component. For
        example, an OptimizationFunction may use for its `objective_function <OptimizationFunction.objective_function>`
        or `search_function <OptimizationFunction.search_function>` a method of the Component to which it is being
        assigned;  however, those methods will not yet be available, as the Component itself has not yet been
        constructed. This can be handled by calling the OptimizationFunction's `reinitialization
        <OptimizationFunction.reinitialization>` method after the Component has been instantiated, with a parameter
        specification dictionary with a key for each entry that is the name of a parameter and its value the value to
        be assigned to the parameter.  This is done automatically for Mechanisms that take an ObjectiveFunction as
        their `function <Mechanism.function>` (such as the `EVCControlMechanism`, `LVOCControlMechanism` and
        `ParamterEstimationControlMechanism`), but will require it be done explicitly for Components for which that
        is not the case. A warning is issued if defaults are used for the arguments of an OptimizationFunction or
        its subclasses;  this can be suppressed by specifying the relevant argument(s) as `NotImplemnted`.

    COMMENT:
    NOTES TO DEVELOPERS:
    - Constructors of subclasses should include **kwargs in their constructor method, to accomodate arguments required
      by some subclasses but not others (e.g., search_space needed by `GridSearch` but not `GradientOptimization`) so
      that subclasses are meant to be used interchangeably by OptimizationMechanisms.

    - Subclasses with attributes that depend on one of the OptimizationFunction's parameters should implement the
      `reinitialize <OptimizationFunction.reinitialize>` method, that calls super().reinitialize(*args) and then
      reassigns the values of the dependent attributes accordingly.  If an argument is not needed for the subclass,
      `NotImplemented` should be passed as the argument's value in the call to super (i.e., the OptimizationFunction's
      constructor).
    COMMENT


    Arguments
    ---------

    default_variable : list or ndarray : default None
        specifies a template for (i.e., an example of the shape of) the samples used to evaluate the
        `objective_function <OptimizationFunction.objective_function>`.

    objective_function : function or method : default None
        specifies function used to evaluate sample in each iteration of the `optimization process
        <OptimizationFunction_Process>`; if it is not specified, a default function is used that simply returns
        the value passed as its `variable <OptimizationFunction.variable>` parameter (see `note
        <OptimizationFunction_Defaults>`).

    search_function : function or method : default None
        specifies function used to select a sample for `objective_function <OptimizationFunction.objective_function>`
        in each iteration of the `optimization process <OptimizationFunction_Process>`.  It **must be specified**
        if the `objective_function <OptimizationFunction.objective_function>` does not generate samples on its own
        (e.g., as does `GradientOptimization`).  If it is required and not specified, the optimization process
        executes exactly once using the value passed as its `variable <OptimizationFunction.variable>` parameter
        (see `note <OptimizationFunction_Defaults>`).

    search_space : list or np.ndarray : default None
        specifies samples used to evaluate `objective_function <OptimizationFunction.objective_function>`
        in each iteration of the `optimization process <OptimizationFunction_Process>`. It **must be specified**
        if the `objective_function <OptimizationFunction.objective_function>` does not generate samples on its own
        (e.g., as does `GradientOptimization`).  If it is required and not specified, the optimization process
        executes exactly once using the value passed as its `variable <OptimizationFunction.variable>` parameter
        (see `note <OptimizationFunction_Defaults>`).

    search_termination_function : function or method : None
        specifies function used to terminate iterations of the `optimization process <OptimizationFunction_Process>`.
        It **must be specified** if the `objective_function <OptimizationFunction.objective_function>` is not
        overridden.  If it is required and not specified, the optimization process executes exactly once
        (see `note <OptimizationFunction_Defaults>`).

    save_samples : bool
        specifies whether or not to save and return the values of the samples used to evalute `objective_function
        <OptimizationFunction.objective_function>` over all iterations of the `optimization process
        <OptimizationFunction_Process>`.

    save_values : bool
        specifies whether or not to save and return the values of `objective_function
        <OptimizationFunction.objective_function>` for samples evaluated in all iterations of the
        `optimization process <OptimizationFunction_Process>`.

    max_iterations : int : default 1000
        specifies the maximum number of times the `optimization process <OptimizationFunction_Process>` is allowed
        to iterate; if exceeded, a warning is issued and the function returns the last sample evaluated.


    Attributes
    ----------

    variable : ndarray
        first sample evaluated by `objective_function <OptimizationFunction.objective_function>` (i.e., one used to
        evaluate it in the first iteration of the `optimization process <OptimizationFunction_Process>`).

    objective_function : function or method
        used to evaluate the sample in each iteration of the `optimization process <OptimizationFunction_Process>`.

    search_function : function, method or None
        used to select a sample evaluated by `objective_function <OptimizationFunction.objective_function>`
        in each iteration of the `optimization process <OptimizationFunction_Process>`.  `NotImplemented` if
        the `objective_function <OptimizationFunction.objective_function>` generates its own samples.

    search_space : list or np.ndarray
        samples used to evaluate `objective_function <OptimizationFunction.objective_function>`
        in each iteration of the `optimization process <OptimizationFunction_Process>`;  `NotImplemented` if
        the `objective_function <OptimizationFunction.objective_function>` generates its own samples.

    search_termination_function : function or method
        used to terminate iterations of the `optimization process <OptimizationFunction_Process>`.

    iteration : int
        the current iteration of the `optimization process <OptimizationFunction_Process>`.

    max_iterations : int : default 1000
        specifies the maximum number of times the `optimization process <OptimizationFunction_Process>` is allowed
        to iterate; if exceeded, a warning is issued and the function returns the last sample evaluated.

    save_samples : bool
        determines whether or not to save the values of the samples used to evalute `objective_function
        <OptimizationFunction.objective_function>` over all iterations of the `optimization process
        <OptimizationFunction_Process>`.

    save_values : bool
        determines whether or not to save and return the values of `objective_function
        <OptimizationFunction.objective_function>` for samples evaluated in all iterations of the
        `optimization process <OptimizationFunction_Process>`.
    """

    componentType = OPTIMIZATION_FUNCTION_TYPE

    class Params(Function_Base.Params):
        variable = Param(np.array([0, 0, 0]), read_only=True)

        objective_function = Param(lambda x: 0, stateful=False, loggable=False)
        search_function = Param(lambda x: x, stateful=False, loggable=False)
        search_termination_function = Param(lambda x, y, z: True, stateful=False, loggable=False)
        search_space = Param([0], stateful=False, loggable=False)

        # these are created as parameter states, but should they be?
        save_samples = Param(False, modulable=True)
        save_values = Param(False, modulable=True)
        max_iterations = Param(None, modulable=True)

        saved_samples = Param([], read_only=True)
        saved_values = Param([], read_only=True)

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 objective_function:tc.optional(is_function_type)=None,
                 search_function:tc.optional(is_function_type)=None,
                 search_space=None,
                 search_termination_function:tc.optional(is_function_type)=None,
                 save_samples:tc.optional(bool)=False,
                 save_values:tc.optional(bool)=False,
                 max_iterations:tc.optional(int)=None,
                 params=None,
                 owner=None,
                 prefs=None,
                 context=None):

        self._unspecified_args = []

        if objective_function is None:
            self.objective_function = lambda x:0
            self._unspecified_args.append(OBJECTIVE_FUNCTION)
        else:
            self.objective_function = objective_function

        if search_function is None:
            self.search_function = lambda x:x
            self._unspecified_args.append(SEARCH_FUNCTION)
        else:
            self.search_function = search_function

        if search_termination_function is None:
            self.search_termination_function = lambda x,y,z:True
            self._unspecified_args.append(SEARCH_TERMINATION_FUNCTION)
        else:
            self.search_termination_function = search_termination_function

        if search_space is None:
            self.search_space = [0]
            self._unspecified_args.append(SEARCH_SPACE)
        else:
            self.search_space = search_space

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(save_samples=save_samples,
                                                  save_values=save_values,
                                                  max_iterations=max_iterations,
                                                  params=params)

        super().__init__(default_variable=default_variable,
                         params=params,
                         owner=owner,
                         prefs=prefs,
                         context=context)

    def reinitialize(self, *args, execution_id=None):
        '''Reinitialize parameters of the OptimizationFunction

        Parameters to be reinitialized should be specified in a parameter specification dictionary, in which they key
        for each entry is the name of one of the following parameters, and its value is the value to be assigned to the
        parameter.  The following parameters can be reinitialized:

            * `default_variable <OptimizationFunction.default_variable>`
            * `objective_function <OptimizationFunction.objective_function>`
            * `search_function <OptimizationFunction.search_function>`
            * `search_termination_function <OptimizationFunction.search_termination_function>`
        '''

        if DEFAULT_VARIABLE in args[0]:
            self.instance_defaults.variable = args[0][DEFAULT_VARIABLE]
        if OBJECTIVE_FUNCTION in args[0] and args[0][OBJECTIVE_FUNCTION] is not None:
            self.objective_function = args[0][OBJECTIVE_FUNCTION]
            if OBJECTIVE_FUNCTION in self._unspecified_args:
                del self._unspecified_args[self._unspecified_args.index(OBJECTIVE_FUNCTION)]
        if SEARCH_FUNCTION in args[0] and args[0][SEARCH_FUNCTION] is not None:
            self.search_function = args[0][SEARCH_FUNCTION]
            if SEARCH_FUNCTION in self._unspecified_args:
                del self._unspecified_args[self._unspecified_args.index(SEARCH_FUNCTION)]
        if SEARCH_TERMINATION_FUNCTION in args[0] and args[0][SEARCH_TERMINATION_FUNCTION] is not None:
            self.search_termination_function = args[0][SEARCH_TERMINATION_FUNCTION]
            if SEARCH_TERMINATION_FUNCTION in self._unspecified_args:
                del self._unspecified_args[self._unspecified_args.index(SEARCH_TERMINATION_FUNCTION)]
        if SEARCH_SPACE in args[0] and args[0][SEARCH_SPACE] is not None:
            self.parameters.search_space.set(args[0][SEARCH_SPACE], execution_id)
            if SEARCH_SPACE in self._unspecified_args:
                del self._unspecified_args[self._unspecified_args.index(SEARCH_SPACE)]

    def function(self,
                 variable=None,
                 execution_id=None,
                 params=None,
                 context=None,
                 **kwargs):
        '''Find the sample that yields the optimal value of `objective_function
        <OptimizationFunction.objective_function>`.

        See `optimization process <OptimizationFunction_Process>` for details.

        Returns
        -------

        optimal sample, optimal value, saved_samples, saved_values : array, array, list, list
            first array contains sample that yields the optimal value of the `optimization process
            <OptimizationFunction_Process>`, and second array contains the value of `objective_function
            <OptimizationFunction.objective_function>` for that sample.  If `save_samples
            <OptimizationFunction.save_samples>` is `True`, first list contains all the values sampled in the order
            they were evaluated; otherwise it is empty.  If `save_values <OptimizationFunction.save_values>` is `True`,
            second list contains the values returned by `objective_function <OptimizationFunction.objective_function>`
            for all the samples in the order they were evaluated; otherwise it is empty.
        '''

        if self._unspecified_args and self.parameters.context.get(execution_id).initialization_status == ContextFlags.INITIALIZED:
            warnings.warn("The following arg(s) were not specified for {}: {} -- using default(s)".
                          format(self.name, ', '.join(self._unspecified_args)))
            self._unspecified_args = []

        sample = self._check_args(variable=variable, execution_id=execution_id, params=params, context=context)

        current_sample = sample
        current_value = call_with_pruned_args(self.objective_function, current_sample, execution_id=execution_id)

        samples = []
        values = []

        # Initialize variables used in while loop
        iteration = 0

        # Set up progress bar
        _show_progress = False
        if hasattr(self, OWNER) and self.owner and self.owner.prefs.reportOutputPref:
            _show_progress = True
            _progress_bar_char = '.'
            _progress_bar_rate_str = ""
            _search_space_size = len(self.search_space)
            _progress_bar_rate = int(10 ** (np.log10(_search_space_size)-2))
            if _progress_bar_rate > 1:
                _progress_bar_rate_str = str(_progress_bar_rate) + " "
            print("\n{} executing optimization process (one {} for each {}of {} samples): ".
                  format(self.owner.name, repr(_progress_bar_char), _progress_bar_rate_str, _search_space_size))
            _progress_bar_count = 0

        # Iterate optimization process
        while call_with_pruned_args(self.search_termination_function, current_sample, current_value, iteration, execution_id=execution_id):

            if _show_progress:
                increment_progress_bar = (_progress_bar_rate < 1) or not (_progress_bar_count % _progress_bar_rate)
                if increment_progress_bar:
                    print(_progress_bar_char, end='', flush=True)
                _progress_bar_count +=1

            # Get next sample of sample
            new_sample = call_with_pruned_args(self.search_function, current_sample, iteration, execution_id=execution_id)

            # Compute new value based on new sample
            new_value = call_with_pruned_args(self.objective_function, new_sample, execution_id=execution_id)

            iteration += 1
            max_iterations = self.parameters.max_iterations.get(execution_id)
            if max_iterations and iteration > max_iterations:
                warnings.warn("{} failed to converge after {} iterations".format(self.name, max_iterations))
                break

            current_sample = new_sample
            current_value = new_value

            if self.parameters.save_samples.get(execution_id):
                samples.append(new_sample)
                self.parameters.saved_samples.set(samples, execution_id, override=True)
            if self.parameters.save_values.get(execution_id):
                values.append(current_value)
                self.parameters.saved_values.set(values, execution_id, override=True)

        return new_sample, new_value, samples, values


ASCENT = 'ascent'
DESCENT = 'descent'


class GradientOptimization(OptimizationFunction):
    """
    GradientOptimization(            \
        default_variable=None,       \
        objective_function=None,     \
        direction=ASCENT,            \
        step_size=1.0,               \
        annealing_function=None,     \
        convergence_criterion=VALUE, \
        convergence_threshold=.001,  \
        max_iterations=1000,         \
        save_samples=False,          \
        save_values=False,           \
        params=None,                 \
        owner=None,                  \
        prefs=None                   \
        )

    Sample variable by following gradient with respect to the value of `objective_function
    <GradientOptimization.objective_function>` it generates, and return the sample that generates either the
    highest (**direction=*ASCENT*) or lowest (**direction=*DESCENT*) value.

    .. _GradientOptimization_Process:

    **Optimization Process**

    When `function <GradientOptimization.function>` is executed, it iterates over the folowing steps:

        - `compute gradient <GradientOptimization_Gradient_Calculation>` using the `gradient_function
          <GradientOptimization.gradient_function>`;
        ..
        - adjust `variable <GradientOptimization.variable>` based on the gradient, in the specified
          `direction <GradientOptimization.direction>` and by an amount specified by `step_size
          <GradientOptimization.step_size>` and possibly `annealing_function
          <GradientOptimization.annealing_function>`;
        ..
        - compute value of `objective_function <GradientOptimization.objective_function>` using the adjusted value of
          `variable <GradientOptimization.variable>`;
        ..
        - adjust `step_size <GradientOptimization.udpate_rate>` using `annealing_function
          <GradientOptimization.annealing_function>`, if specified, for use in the next iteration;
        ..
        - evaluate `convergence_criterion <GradientOptimization.convergence_criterion>` and test whether it is below
          the `convergence_threshold <GradientOptimization.convergence_threshold>`.

    The current iteration is contained in `iteration <GradientOptimization.iteration>`. Iteration continues until
    `convergence_criterion <GradientOptimization.convergence_criterion>` falls below `convergence_threshold
    <GradientOptimization.convergence_threshold>` or the number of iterations exceeds `max_iterations
    <GradientOptimization.max_iterations>`.  The `function <GradientOptimization.function>` returns the last sample
    evaluated by `objective_function <GradientOptimization.objective_function>` (presumed to be the optimal one),
    the value of the function, as well as lists that may contain all of the samples evaluated and their values,
    depending on whether `save_samples <OptimizationFunction.save_samples>` and/or `save_vales
    <OptimizationFunction.save_values>` are `True`, respectively.

    .. _GradientOptimization_Gradient_Calculation:

    **Gradient Calculation**

    The gradient is evaluated by `gradient_function <GradientOptimization.gradient_function>`,
    which is the derivative of the `objective_function <GradientOptimization.objective_function>`
    with respect to `variable <GradientOptimization.variable>` at its current value:
    :math:`\\frac{d(objective\\_function(variable))}{d(variable)}`

    `Autograd's <https://github.com/HIPS/autograd>`_ `grad <autograd.grad>` method is used to
    generate `gradient_function <GradientOptimization.gradient_function>`.


    Arguments
    ---------

    default_variable : list or ndarray : default None
        specifies a template for (i.e., an example of the shape of) the samples used to evaluate the
        `objective_function <GradientOptimization.objective_function>`.

    objective_function : function or method
        specifies function used to evaluate `variable <GradientOptimization.variable>`
        in each iteration of the `optimization process  <GradientOptimization_Process>`;
        it must be specified and it must return a scalar value.

    direction : ASCENT or DESCENT : default ASCENT
        specifies the direction of gradient optimization: if *ASCENT*, movement is attempted in the positive direction
        (i.e., "up" the gradient);  if *DESCENT*, movement is attempted in the negative direction (i.e. "down"
        the gradient).

    step_size : int or float : default 1.0
        specifies the rate at which the `variable <GradientOptimization.variable>` is updated in each
        iteration of the `optimization process <GradientOptimization_Process>`;  if `annealing_function
        <GradientOptimization.annealing_function>` is specified, **step_size** specifies the intial value of
        `step_size <GradientOptimization.step_size>`.

    annealing_function : function or method : default None
        specifies function used to adapt `step_size <GradientOptimization.step_size>` in each
        iteration of the `optimization process <GradientOptimization_Process>`;  must take accept two parameters —
        `step_size <GradientOptimization.step_size>` and `iteration <GradientOptimization_Process>`, in that
        order — and return a scalar value, that is used for the next iteration of optimization.

    convergence_criterion : *VARIABLE* or *VALUE* : default *VALUE*
        specifies the parameter used to terminate the `optimization process <GradientOptimization_Process>`.
        *VARIABLE*: process terminates when the most recent sample differs from the previous one by less than
        `convergence_threshold <GradientOptimization.convergence_threshold>`;  *VALUE*: process terminates when the
        last value returned by `objective_function <GradientOptimization.objective_function>` differs from the
        previous one by less than `convergence_threshold <GradientOptimization.convergence_threshold>`.

    convergence_threshold : int or float : default 0.001
        specifies the change in value of `convergence_criterion` below which the optimization process is terminated.

    max_iterations : int : default 1000
        specifies the maximum number of times the `optimization process<GradientOptimization_Process>` is allowed to
        iterate; if exceeded, a warning is issued and the function returns the last sample evaluated.

    save_samples : bool
        specifies whether or not to save and return all of the samples used to evaluate `objective_function
        <GradientOptimization.objective_function>` in the `optimization process<GradientOptimization_Process>`.

    save_values : bool
        specifies whether or not to save and return the values of `objective_function
        <GradientOptimization.objective_function>` for all samples evaluated in the `optimization
        process<GradientOptimization_Process>`

    Attributes
    ----------

    variable : ndarray
        sample used as the starting point for the `optimization process <GradientOptimization_Process>` (i.e., one
        used to evaluate `objective_function <GradientOptimization.objective_function>` in the first iteration).

    objective_function : function or method
        function used to evaluate `variable <GradientOptimization.variable>`
        in each iteration of the `optimization process <GradientOptimization_Process>`;
        it must be specified and it must return a scalar value.

    gradient_function : function
        function used to compute the gradient in each iteration of the `optimization process
        <GradientOptimization_Process>` (see `Gradient Calculation <GradientOptimization_Gradient_Calculation>` for
        details).

    direction : ASCENT or DESCENT
        direction of gradient optimization:  if *ASCENT*, movement is attempted in the positive direction
        (i.e., "up" the gradient);  if *DESCENT*, movement is attempted in the negative direction (i.e. "down"
        the gradient).

    step_size : int or float
        determines the rate at which the `variable <GradientOptimization.variable>` is updated in each
        iteration of the `optimization process <GradientOptimization_Process>`;  if `annealing_function
        <GradientOptimization.annealing_function>` is specified, `step_size <GradientOptimization.step_size>`
        determines the initial value.

    annealing_function : function or method
        function used to adapt `step_size <GradientOptimization.step_size>` in each iteration of the `optimization
        process <GradientOptimization_Process>`;  if `None`, no call is made and the same `step_size
        <GradientOptimization.step_size>` is used in each iteration.

    iteration : int
        the currention iteration of the `optimization process <GradientOptimization_Process>`.

    convergence_criterion : VARIABLE or VALUE
        determines parameter used to terminate the `optimization process<GradientOptimization_Process>`.
        *VARIABLE*: process terminates when the most recent sample differs from the previous one by less than
        `convergence_threshold <GradientOptimization.convergence_threshold>`;  *VALUE*: process terminates when the
        last value returned by `objective_function <GradientOptimization.objective_function>` differs from the
        previous one by less than `convergence_threshold <GradientOptimization.convergence_threshold>`.

    convergence_threshold : int or float
        determines the change in value of `convergence_criterion` below which the `optimization process
        <GradientOptimization_Process>` is terminated.

    max_iterations : int
        determines the maximum number of times the `optimization process<GradientOptimization_Process>` is allowed to
        iterate; if exceeded, a warning is issued and the function returns the last sample evaluated.

    save_samples : bool
        determines whether or not to save and return all of the samples used to evaluate `objective_function
        <GradientOptimization.objective_function>` in the `optimization process<GradientOptimization_Process>`.

    save_values : bool
        determines whether or not to save and return the values of `objective_function
        <GradientOptimization.objective_function>` for all samples evaluated in the `optimization
        process<GradientOptimization_Process>`
    """

    componentName = GRADIENT_OPTIMIZATION_FUNCTION

    class Params(OptimizationFunction.Params):
        variable = Param([[0], [0]], read_only=True)

        # these should be removed and use switched to .get_previous()
        previous_variable = Param([[0], [0]], read_only=True)
        previous_value = Param([[0], [0]], read_only=True)

        annealing_function = Param(None, stateful=False, loggable=False)

        step_size = Param(1.0, modulable=True)
        convergence_threshold = Param(.001, modulable=True)
        max_iterations = Param(1000, modulable=True)

        direction = ASCENT
        convergence_criterion = VALUE

    paramClassDefaults = Function_Base.paramClassDefaults.copy()

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 objective_function:tc.optional(is_function_type)=None,
                 direction:tc.optional(tc.enum(ASCENT, DESCENT))=ASCENT,
                 step_size:tc.optional(tc.any(int, float))=1.0,
                 annealing_function:tc.optional(is_function_type)=None,
                 convergence_criterion:tc.optional(tc.enum(VARIABLE, VALUE))=VALUE,
                 convergence_threshold:tc.optional(tc.any(int, float))=.001,
                 max_iterations:tc.optional(int)=1000,
                 save_samples:tc.optional(bool)=False,
                 save_values:tc.optional(bool)=False,
                 params=None,
                 owner=None,
                 prefs=None,
                 **kwargs):

        search_function = self._follow_gradient
        search_termination_function = self._convergence_condition
        self.gradient_function = None

        if direction is ASCENT:
            self.direction = 1
        else:
            self.direction = -1
        self.annealing_function = annealing_function

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(step_size=step_size,
                                                  convergence_criterion=convergence_criterion,
                                                  convergence_threshold=convergence_threshold,
                                                  params=params)

        super().__init__(default_variable=default_variable,
                         objective_function=objective_function,
                         search_function=search_function,
                         search_space=NotImplemented,
                         search_termination_function=search_termination_function,
                         max_iterations=max_iterations,
                         save_samples=save_samples,
                         save_values=save_values,
                         params=params,
                         owner=owner,
                         prefs=prefs,
                         context=ContextFlags.CONSTRUCTOR)

    def reinitialize(self, *args):
        super().reinitialize(*args)
        if OBJECTIVE_FUNCTION in args[0]:
            try:
                from autograd import grad
                self.gradient_function = grad(self.objective_function)
            except:
                warnings.warn("Unable to use autograd with {} specified for {} Function: {}.".
                              format(repr(OBJECTIVE_FUNCTION), self.__class__.__name__,
                                     args[0][OBJECTIVE_FUNCTION].__name__))

    def function(self,
                 variable=None,
                 execution_id=None,
                 params=None,
                 context=None,
                 **kwargs):
        '''Return the sample that yields the optimal value of `objective_function
        <GradientOptimization.objective_function>`, and possibly all samples evaluated and their corresponding values.

        Optimal value is defined by `direction <GradientOptimization.direction>`:
        - if *ASCENT*, returns greatest value
        - if *DESCENT*, returns least value

        Returns
        -------

        optimal sample, optimal value, saved_samples, saved_values : ndarray, list, list
            first array contains sample that yields the highest or lowest value of `objective_function
            <GradientOptimization.objective_function>`, depending on `direction <GradientOptimization.direction>`,
            and the second array contains the value of the function for that sample.
            If `save_samples <GradientOptimization.save_samples>` is `True`, first list contains all the values
            sampled in the order they were evaluated; otherwise it is empty.  If `save_values
            <GradientOptimization.save_values>` is `True`, second list contains the values returned by
            `objective_function <GradientOptimization.objective_function>` for all the samples in the order they were
            evaluated; otherwise it is empty.
        '''

        optimal_sample, optimal_value, all_samples, all_values = super().function(variable=variable,execution_id=execution_id, params=params, context=context)
        return_all_samples = return_all_values = []
        if self.parameters.save_samples.get(execution_id):
            return_all_samples = all_samples
        if self.parameters.save_values.get(execution_id):
            return_all_values = all_values
        # return last_variable
        return optimal_sample, optimal_value, return_all_samples, return_all_values

    def _follow_gradient(self, variable, sample_num, execution_id=None):

        if self.gradient_function is None:
            return variable

        # Update step_size
        if sample_num == 0:
            _current_step_size = self.parameters.step_size.get(execution_id)
        elif self.annealing_function:
            _current_step_size = call_with_pruned_args(self.annealing_function, self._current_step_size, sample_num, execution_id=execution_id)

        # Compute gradients with respect to current variable
        _gradients = call_with_pruned_args(self.gradient_function, variable, execution_id=execution_id)

        # Update variable based on new gradients
        return variable + self.parameters.direction.get(execution_id) * _current_step_size * np.array(_gradients)

    def _convergence_condition(self, variable, value, iteration, execution_id=None):
        previous_variable = self.parameters.previous_variable.get(execution_id)
        previous_value = self.parameters.previous_value.get(execution_id)

        if iteration is 0:
            # self._convergence_metric = self.convergence_threshold + EPSILON
            self.parameters.previous_variable.set(variable, execution_id, override=True)
            self.parameters.previous_value.set(value, execution_id, override=True)
            return True

        # Evaluate for convergence
        if self.convergence_criterion == VALUE:
            convergence_metric = np.abs(value - previous_value)
        else:
            convergence_metric = np.max(np.abs(np.array(variable) -
                                               np.array(previous_variable)))

        self.parameters.previous_variable.set(variable, execution_id, override=True)
        self.parameters.previous_value.set(value, execution_id, override=True)

        return convergence_metric > self.parameters.convergence_threshold.get(execution_id)


MAXIMIZE = 'maximize'
MINIMIZE = 'minimize'


class GridSearch(OptimizationFunction):
    """
    GridSearch(                      \
        default_variable=None,       \
        objective_function=None,     \
        direction=MAXIMIZE,          \
        max_iterations=1000,         \
        save_samples=False,          \
        save_values=False,           \
        params=None,                 \
        owner=None,                  \
        prefs=None                   \
        )

    Search over all samples in `search_space <GridSearch.search_space>` for the one that optimizes the value of
    `objective_function <GridSearch.objective_function>`.

    .. _GridSearch_Process:

    **Grid Search Process**

    When `function <GridSearch.function>` is executed, it iterates over the folowing steps:

        - get next sample from `search_space <GridSearch.search_space>`;
        ..
        - compute value of `objective_function <GridSearch.objective_function>` for that sample;

    The current iteration is contained in `iteration <GridSearch.iteration>`. Iteration continues until all values of
    `search_space <GridSearch.search_space>` have been evaluated, or `max_iterations <GridSearch.max_iterations>` is
    execeeded.  The function returns the sample that yielded either the highest (if `direction <GridSearch.direction>`
    is *MAXIMIZE*) or lowest (if `direction <GridSearch.direction>` is *MINIMIZE*) value of the `objective_function
    <GridSearch.objective_function>`, along with the value for that sample, as well as lists containing all of the
    samples evaluated and their values if either `save_samples <GridSearch.save_samples>` or `save_values
    <GridSearch.save_values>` is `True`, respectively.

    Arguments
    ---------

    default_variable : list or ndarray : default None
        specifies a template for (i.e., an example of the shape of) the samples used to evaluate the
        `objective_function <GridSearch.objective_function>`.

    objective_function : function or method
        specifies function used to evaluate sample in each iteration of the `optimization process <GridSearch_Process>`;
        it must be specified and must return a scalar value.

    search_space : list or array
        specifies samples used to evaluate `objective_function <GridSearch.objective_function>`.

    direction : MAXIMIZE or MINIMIZE : default MAXIMIZE
        specifies the direction of optimization:  if *MAXIMIZE*, the highest value of `objective_function
        <GridSearch.objective_function>` is sought;  if *MINIMIZE*, the lowest value is sought.

    max_iterations : int : default 1000
        specifies the maximum number of times the `optimization process<GridSearch_Process>` is allowed to iterate;
        if exceeded, a warning is issued and the function returns the optimal sample of those evaluated.

    save_samples : bool
        specifies whether or not to return all of the samples used to evaluate `objective_function
        <GridSearch.objective_function>` in the `optimization process <GridSearch_Process>`
        (i.e., a copy of the `search_space <GridSearch.search_space>`.

    save_values : bool
        specifies whether or not to save and return the values of `objective_function <GridSearch.objective_function>`
        for all samples evaluated in the `optimization process <GridSearch_Process>`.

    Attributes
    ----------

    variable : ndarray
        first sample evaluated by `objective_function <GridSearch.objective_function>` (i.e., one used to evaluate it
        in the first iteration of the `optimization process <GridSearch_Process>`).

    objective_function : function or method
        function used to evaluate sample in each iteration of the `optimization process <GridSearch_Process>`.

    search_space : list or array
        contains samples used to evaluate `objective_function <GridSearch.objective_function>` in iterations of the
        `optimization process <GridSearch_Process>`.

    direction : MAXIMIZE or MINIMIZE : default MAXIMIZE
        determines the direction of optimization:  if *MAXIMIZE*, the greatest value of `objective_function
        <GridSearch.objective_function>` is sought;  if *MINIMIZE*, the least value is sought.

    iteration : int
        the currention iteration of the `optimization process <GridSearch_Process>`.

    max_iterations : int
        determines the maximum number of times the `optimization process<GridSearch_Process>` is allowed to iterate;
        if exceeded, a warning is issued and the function returns the optimal sample of those evaluated.

    save_samples : True
        determines whether or not to save and return all samples evaluated by the `objective_function
        <GridSearch.objective_function>` in the `optimization process <GridSearch_Process>` (if the process
        completes, this should be identical to `search_space <GridSearch.search_space>`.

    save_values : bool
        determines whether or not to save and return the value of `objective_function
        <GridSearch.objective_function>` for all samples evaluated in the `optimization process <GridSearch_Process>`.
    """

    componentName = GRID_SEARCH_FUNCTION

    class Params(OptimizationFunction.Params):
        variable = Param([[0], [0]], read_only=True)

        # these are created as parameter states, but should they be?
        save_samples = Param(True, modulable=True)
        save_values = Param(True, modulable=True)

        direction = MAXIMIZE

    paramClassDefaults = Function_Base.paramClassDefaults.copy()

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 objective_function:tc.optional(is_function_type)=None,
                 # search_space:tc.optional(tc.any(list, np.ndarray))=None,
                 search_space=None,
                 direction:tc.optional(tc.enum(MAXIMIZE, MINIMIZE))=MAXIMIZE,
                 save_values:tc.optional(bool)=False,
                 params=None,
                 owner=None,
                 prefs=None,
                 **kwargs):

        search_function = self._traverse_grid
        search_termination_function = self._grid_complete
        self._return_values = save_values

        self.direction = direction

        # Assign args to params and functionParams dicts (kwConstants must == arg names)
        params = self._assign_args_to_param_dicts(params=params)

        super().__init__(default_variable=default_variable,
                         objective_function=objective_function,
                         search_function=search_function,
                         search_space=search_space,
                         search_termination_function=search_termination_function,
                         save_samples=True,
                         save_values=True,
                         params=params,
                         owner=owner,
                         prefs=prefs,
                         context=ContextFlags.CONSTRUCTOR)

    def function(self,
                 variable=None,
                 execution_id=None,
                 params=None,
                 context=None,
                 **kwargs):
        '''Return the sample that yields the optimal value of `objective_function <GridSearch.objective_function>`,
        and possibly all samples evaluated and their corresponding values.

        Optimal value is defined by `direction <GridSearch.direction>`:
        - if *MAXIMIZE*, returns greatest value
        - if *MINIMIZE*, returns least value

        Returns
        -------

        optimal sample, optimal value, saved_samples, saved_values : ndarray, list, list
            first array contains sample that yields the highest or lowest value of `objective_function
            <GridSearch.objective_function>`, depending on `direction <GridSearch.direction>`, and the
            second array contains the value of the function for that sample. If `save_samples
            <GridSearch.save_samples>` is `True`, first list contains all the values sampled in the order they were
            evaluated; otherwise it is empty.  If `save_values <GridSearch.save_values>` is `True`, second list
            contains the values returned by `objective_function <GridSearch.objective_function>` for all the samples
            in the order they were evaluated; otherwise it is empty.
        '''

        return_all_samples = return_all_values = []

        if MPI_IMPLEMENTATION:

            from mpi4py import MPI

            Comm = MPI.COMM_WORLD
            rank = Comm.Get_rank()
            size = Comm.Get_size()

            self.search_space = np.atleast_2d(self.search_space)

            chunk_size = (len(self.search_space) + (size-1)) // size
            start = chunk_size * rank
            end = chunk_size * (rank+1)
            if start > len(self.search_space):
                start = len(self.search_space)
            if end > len(self.search_space):
                end = len(self.search_space)

            # # TEST PRINT
            # print("\nContext: {}".format(self.context.flags_string))
            # print("search_space length: {}".format(len(self.search_space)))
            # print("Rank: {}\tSize: {}\tChunk size: {}".format(rank, size, chunk_size))
            # print("START: {0}\tEND: {1}\tPROCESSED: {2}".format(start,end,end-start))

            # FIX:  INITIALIZE TO FULL LENGTH AND ASSIGN DEFAULT VALUES (MORE EFFICIENT):
            samples = np.array([[]])
            sample_optimal = np.empty_like(self.search_space[0])
            values = np.array([])
            value_optimal = float('-Infinity')
            sample_value_max_tuple = (sample_optimal, value_optimal)

            # Set up progress bar
            _show_progress = False
            if hasattr(self, OWNER) and self.owner and self.owner.prefs.reportOutputPref:
                _show_progress = True
                _progress_bar_char = '.'
                _progress_bar_rate_str = ""
                _search_space_size = len(self.search_space)
                _progress_bar_rate = int(10 ** (np.log10(_search_space_size)-2))
                if _progress_bar_rate > 1:
                    _progress_bar_rate_str = str(_progress_bar_rate) + " "
                print("\n{} executing optimization process (one {} for each {}of {} samples): ".
                      format(self.owner.name, repr(_progress_bar_char), _progress_bar_rate_str, _search_space_size))
                _progress_bar_count = 0

            for sample in self.search_space[start:end,:]:

                if _show_progress:
                    increment_progress_bar = (_progress_bar_rate < 1) or not (_progress_bar_count % _progress_bar_rate)
                    if increment_progress_bar:
                        print(_progress_bar_char, end='', flush=True)
                    _progress_bar_count +=1

                # Evaluate objective_function for current sample
                value = self.objective_function(sample)

                # Evaluate for optimal value
                if self.direction is MAXIMIZE:
                    value_optimal = max(value, value_optimal)
                elif self.direction is MINIMIZE:
                    value_optimal = min(value, value_optimal)
                else:
                    assert False, "PROGRAM ERROR: bad value for {} arg of {}: {}".\
                        format(repr(DIRECTION),self.name,self.direction)

                # FIX: PUT ERROR HERE IF value AND/OR value_max ARE EMPTY (E.G., WHEN EXECUTION_ID IS WRONG)
                # If value is optimal, store corresponing sample
                if value == value_optimal:
                    # Keep track of state values and allocation policy associated with EVC max
                    sample_optimal = sample
                    sample_value_max_tuple = (sample_optimal, value_optimal)

                # Save samples and/or values if specified
                if self.save_values:
                    # FIX:  ASSIGN BY INDEX (MORE EFFICIENT)
                    values = np.append(values, np.atleast_1d(value), axis=0)
                if self.save_samples:
                    if len(samples[0])==0:
                        samples = np.atleast_2d(sample)
                    else:
                        samples = np.append(samples, np.atleast_2d(sample), axis=0)

            # Aggregate, reduce and assign global results
            # combine max result tuples from all processes and distribute to all processes
            max_tuples = Comm.allgather(sample_value_max_tuple)
            # get tuple with "value_max of maxes"
            max_value_of_max_tuples = max(max_tuples, key=lambda max_tuple: max_tuple[1])
            # get value_optimal, state values and allocation policy associated with "max of maxes"
            return_optimal_sample = max_value_of_max_tuples[0]
            return_optimal_value = max_value_of_max_tuples[1]

            # if self._return_samples:
            #     return_all_samples = np.concatenate(Comm.allgather(samples), axis=0)
            if self._return_values:
                return_all_values = np.concatenate(Comm.allgather(values), axis=0)

        else:
            last_sample, last_value, all_samples, all_values = super().function(
                variable=variable,
                execution_id=execution_id,
                params=params,
                context=context
            )
            return_optimal_value = max(all_values)
            return_optimal_sample = all_samples[all_values.index(return_optimal_value)]
            # if self._return_samples:
            #     return_all_samples = all_samples
            if self._return_values:
                return_all_values = all_values

        return return_optimal_sample, return_optimal_value, return_all_samples, return_all_values

    def _traverse_grid(self, variable, sample_num, execution_id=None):
        return self.parameters.search_space.get(execution_id)[sample_num]

    def _grid_complete(self, variable, value, iteration, execution_id=None):
        return iteration != len(self.parameters.search_space.get(execution_id))