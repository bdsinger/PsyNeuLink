#
# Princeton University licenses this file to You under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may obtain a copy of the License at:
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
#
#
# *******************************************  SELECTION FUNCTIONS *****************************************************
'''

* `OneHot`

COMMENT:
* TBI Threshold
* TBI MaxVal
* `KWTA`
COMMENT

Functions that selects a subset of elements to maintain or transform, while nulling the others.

'''

__all__ = ['SelectionFunction', 'OneHot', 'max_vs_avg', 'max_vs_next', 'MAX_VS_NEXT', 'MAX_VS_AVG']

import numpy as np
import typecheck as tc

from psyneulink.core import llvm as pnlvm
from psyneulink.core.components.component import DefaultsFlexibility
from psyneulink.core.components.functions.function import \
    Function, Function_Base, MULTIPLICATIVE_PARAM, FunctionError, ADDITIVE_PARAM
from psyneulink.core.components.functions.transferfunctions import MODE
from psyneulink.core.globals.keywords import \
    SELECTION_FUNCTION_TYPE, ONE_HOT_FUNCTION, PARAMETER_STATE_PARAMS, \
    MAX_VAL, MAX_ABS_VAL, MAX_INDICATOR, MAX_ABS_INDICATOR, PROB, PROB_INDICATOR, kwPreferenceSetName, MIN_VAL, \
    MIN_ABS_VAL, MIN_INDICATOR, MIN_ABS_INDICATOR
from psyneulink.core.globals.parameters import Parameter
from psyneulink.core.globals.context import ContextFlags
from psyneulink.core.globals.preferences.componentpreferenceset import \
    kpReportOutputPref, PreferenceEntry, PreferenceLevel, is_pref_set
from psyneulink.core.globals.utilities import get_global_seed


MAX_VS_NEXT = 'max_vs_next'
MAX_VS_AVG = 'max_vs_avg'

# FIX: IMPLEMENT AS Functions
def max_vs_next(x):
    x_part = np.partition(x, -2)
    max_val = x_part[-1]
    next = x_part[-2]
    return max_val - next


def max_vs_avg(x):
    x_part = np.partition(x, -2)
    max_val = x_part[-1]
    others = x_part[:-1]
    return max_val - np.mean(others)


class SelectionFunction(Function_Base):
    """Functions that selects a particular value to maintain or transform, while nulling the others.
    """
    componentType = SELECTION_FUNCTION_TYPE

    # IMPLEMENTATION NOTE: THESE SHOULD SHOULD BE REPLACED WITH ABC WHEN IMPLEMENTED
    def __init__(self, default_variable,
                 params,
                 owner,
                 prefs,
                 context):

        if not hasattr(self, MULTIPLICATIVE_PARAM):
            raise FunctionError("PROGRAM ERROR: {} must implement a {} attribute".
                                format(self.__class__.__name__, MULTIPLICATIVE_PARAM))

        if not hasattr(self, ADDITIVE_PARAM):
            raise FunctionError("PROGRAM ERROR: {} must implement an {} attribute".
                                format(self.__class__.__name__, ADDITIVE_PARAM))

        super().__init__(default_variable=default_variable,
                         params=params,
                         owner=owner,
                         prefs=prefs,
                         context=context)

    @property
    def multiplicative(self):
        return getattr(self, self.multiplicative_param)

    @multiplicative.setter
    def multiplicative(self, val):
        setattr(self, self.multiplicative_param, val)

    @property
    def additive(self):
        return getattr(self, self.additive_param)

    @additive.setter
    def additive(self, val):
        setattr(self, self.additive_param, val)


class OneHot(SelectionFunction):
    """
    OneHot(                \
         default_variable, \
         mode=MAX_VAL,     \
         params=None,      \
         owner=None,       \
         name=None,        \
         prefs=None        \
         )

    Return an array with one non-zero value.

    .. _OneHot:

    `function <Selection.function>` returns an array the same length as the first item in `variable <OneHot.variable>`,
    with all of its values zeroed except one as specified by `mode <OneHot.mode>`:

        * *MAX_VAL*: element with the maximum signed value in first item of `variable <OneHot.variable>`;
        ..
        * *MAX_ABS_VAL*: element with the maximum absolute value;
        ..
        * *MAX_INDICATOR*: 1 in place of the element with the maximum signed value;
        ..
        * *MAX_ABS_INDICATOR*: 1 in place of the element with the maximum absolute value;
        ..
        * *MIN_VAL*: element with the minimum signed value in first item of `variable <OneHot.variable>`;
        ..
        * *MIN_ABS_VAL*: element with the minimum absolute value;
        ..
        * *MIN_INDICATOR*: 1 in place of the element with the minimum signed value;
        ..
        * *MIN_ABS_INDICATOR*: 1 in place of the element with the minimum absolute value;
        ..
        * *PROB*: probabilistically chosen element based on probabilities passed in second item of variable;
        ..
        * *PROB_INDICATOR*: same as *PROB* but chosen item is assigned a value of 1.


    Arguments
    ---------

    variable : 2d np.array : default class_defaults.variable
        First (possibly only) item specifies a template for the array to be transformed;  if `mode <OneHot.mode>` is
        *PROB* then a 2nd item must be included that is a probability distribution with same length as 1st item.

    mode : MAX_VAL, MAX_ABS_VAL, MAX_INDICATOR, MAX_ABS_INDICATOR, MIN_VAL, MIN_ABS_VAL, MIN_INDICATOR,
    MIN_ABS_INDICATOR, PROB or PROB_INDICATOR : default MAX_VAL
        specifies the nature of the single non-zero value in the array returned by `function <OneHot.function>`
        (see `mode <OneHot.mode>` for details).

    params : Dict[param keyword: param value] : default None
        a `parameter dictionary <ParameterState_Specification>` that specifies the parameters for the
        function.  Values specified for parameters in the dictionary override any assigned to those parameters in
        arguments of the constructor.

    bounds : None

    owner : Component
        `component <Component>` to which to assign the Function.

    name : str : default see `name <Function.name>`
        specifies the name of the Function.

    prefs : PreferenceSet or specification dict : default Function.classPreferences
        specifies the `PreferenceSet` for the Function (see `prefs <Function_Base.prefs>` for details).

    Attributes
    ----------

    variable : number or np.array
        1st item contains value to be transformed;  if `mode <OneHot.mode>` is *PROB*, 2nd item is a probability
        distribution, each element of which specifies the probability for selecting the corresponding element of the
        1st item.

    mode : MAX_VAL, MAX_ABS_VAL, MAX_INDICATOR, MAX_ABS_INDICATOR, MIN_VAL, MIN_ABS_VAL, MIN_INDICATOR,
    MIN_ABS_INDICATOR, PROB or PROB_INDICATOR
        determines the nature of the single non-zero value in the array returned by `function <OneHot.function>`
        (see `above <OneHot>` for options).

    owner : Component
        `component <Component>` to which the Function has been assigned.

    name : str
        the name of the Function; if it is not specified in the **name** argument of the constructor, a
        default is assigned by FunctionRegistry (see `Naming` for conventions used for default and duplicate names).

    prefs : PreferenceSet or specification dict : Function.classPreferences
        the `PreferenceSet` for function; if it is not specified in the **prefs** argument of the Function's
        constructor, a default is assigned using `classPreferences` defined in __init__.py (see :doc:`PreferenceSet
        <LINK>` for details).
    """

    componentName = ONE_HOT_FUNCTION

    bounds = None
    multiplicative_param = None
    additive_param = None

    classPreferences = {
        kwPreferenceSetName: 'OneHotClassPreferences',
        kpReportOutputPref: PreferenceEntry(False, PreferenceLevel.INSTANCE),
    }

    paramClassDefaults = Function_Base.paramClassDefaults.copy()
    paramClassDefaults.update({
        PARAMETER_STATE_PARAMS: None
    })

    class Parameters(SelectionFunction.Parameters):
        """
            Attributes
            ----------

                mode
                    see `mode <OneHot.mode>`

                    :default value: `MAX_VAL`
                    :type: str

                random_state
                    see `random_state <OneHot.random_state>`

                    :default value: None
                    :type:

        """
        mode = Parameter(MAX_VAL, stateful=False)
        random_state = Parameter(None, stateful=True)

        def _validate_mode(self, mode):
            options = {MAX_VAL, MAX_ABS_VAL, MAX_INDICATOR, MAX_ABS_INDICATOR,
                       MIN_VAL, MIN_ABS_VAL, MIN_INDICATOR, MIN_ABS_INDICATOR,
                       PROB, PROB_INDICATOR}
            if mode in options:
                # returns None indicating no error message (this is a valid assignment)
                return None
            else:
                # returns error message
                return 'not one of {0}'.format(options)

    @tc.typecheck
    def __init__(self,
                 default_variable=None,
                 mode: tc.enum(MAX_VAL, MAX_ABS_VAL, MAX_INDICATOR, MAX_ABS_INDICATOR,
                               MIN_VAL, MIN_ABS_VAL, MIN_INDICATOR, MIN_ABS_INDICATOR,
                               PROB, PROB_INDICATOR)=MAX_VAL,
                 seed=None,
                 params=None,
                 owner=None,
                 prefs: is_pref_set = None):

        if seed is None:
            seed = get_global_seed()

        random_state = np.random.RandomState(np.asarray([seed]))
        if not hasattr(self, "stateful_attributes"):
            self.stateful_attributes = ["random_state"]

        # Assign args to params and functionParams dicts
        params = self._assign_args_to_param_dicts(mode=mode,
                                                  random_state=random_state,
                                                  params=params)

        reset_default_variable_flexibility = False
        if mode in {PROB, PROB_INDICATOR} and default_variable is None:
            default_variable = [[0], [0]]
            reset_default_variable_flexibility = True


        super().__init__(default_variable=default_variable,
                         params=params,
                         owner=owner,
                         prefs=prefs,
                         context=ContextFlags.CONSTRUCTOR)

        if reset_default_variable_flexibility:
            self._default_variable_flexibility = DefaultsFlexibility.FLEXIBLE

    def _validate_params(self, request_set, target_set=None, context=None):

        if request_set[MODE] in {PROB, PROB_INDICATOR}:
            if not self.defaults.variable.ndim == 2:
                raise FunctionError("If {} for {} {} is set to {}, variable must be 2d array".
                                    format(MODE, self.__class__.__name__, Function.__name__, PROB))
            values = self.defaults.variable[0]
            prob_dist = self.defaults.variable[1]
            if len(values)!=len(prob_dist):
                raise FunctionError("If {} for {} {} is set to {}, the two items of its variable must be of equal "
                                    "length (len item 1 = {}; len item 2 = {}".
                                    format(MODE, self.__class__.__name__, Function.__name__, PROB,
                                           len(values), len(prob_dist)))
            if not all((elem>=0 and elem<=1) for elem in prob_dist)==1:
                raise FunctionError("If {} for {} {} is set to {}, the 2nd item of its variable ({}) must be an "
                                    "array of elements each of which is in the (0,1) interval".
                                    format(MODE, self.__class__.__name__, Function.__name__, PROB, prob_dist))
            if self.context.initialization_status == ContextFlags.INITIALIZING:
                return
            if not np.sum(prob_dist)==1:
                raise FunctionError("If {} for {} {} is set to {}, the 2nd item of its variable ({}) must be an "
                                    "array of probabilities that sum to 1".
                                    format(MODE, self.__class__.__name__, Function.__name__, PROB, prob_dist))

    def _gen_llvm_function_body(self, ctx, builder, _, state, arg_in, arg_out):
        idx_ptr = builder.alloca(ctx.int32_ty)
        builder.store(ctx.int32_ty(0), idx_ptr)

        if self.mode in {PROB, PROB_INDICATOR}:
            rng_f = ctx.get_llvm_function("__pnl_builtin_mt_rand_double")
            dice_ptr = builder.alloca(ctx.float_ty)
            mt_state_ptr = ctx.get_state_ptr(self, builder, state, "random_state")
            builder.call(rng_f, [mt_state_ptr, dice_ptr])
            dice = builder.load(dice_ptr)
            sum_ptr = builder.alloca(ctx.float_ty)
            builder.store(ctx.float_ty(-0.0), sum_ptr)
            prob_in = builder.gep(arg_in, [ctx.int32_ty(0), ctx.int32_ty(1)])
            arg_in = builder.gep(arg_in, [ctx.int32_ty(0), ctx.int32_ty(0)])

        with pnlvm.helpers.array_ptr_loop(builder, arg_in, "search") as (builder, index):
            idx = builder.load(idx_ptr)
            prev_ptr = builder.gep(arg_in, [ctx.int32_ty(0), idx])
            current_ptr = builder.gep(arg_in, [ctx.int32_ty(0), index])
            prev = builder.load(prev_ptr)
            current = builder.load(current_ptr)

            prev_res_ptr = builder.gep(arg_out, [ctx.int32_ty(0), idx])
            cur_res_ptr = builder.gep(arg_out, [ctx.int32_ty(0), index])
            if self.mode not in {PROB, PROB_INDICATOR}:
                fabs = ctx.get_builtin("fabs", [current.type])
            if self.mode is MAX_VAL:
                cmp_op = ">="
                cmp_prev = prev
                cmp_curr = current
                val = current
            elif self.mode is MAX_ABS_VAL:
                cmp_op = ">="
                cmp_prev = builder.call(fabs, [prev])
                cmp_curr = builder.call(fabs, [current])
                val = current
            elif self.mode is MAX_INDICATOR:
                cmp_op = ">="
                cmp_prev = prev
                cmp_curr = current
                val = current.type(1.0)
            elif self.mode is MAX_ABS_INDICATOR:
                cmp_op = ">="
                cmp_prev = builder.call(fabs, [prev])
                cmp_curr = builder.call(fabs, [current])
                val = current.type(1.0)
            elif self.mode is MIN_VAL:
                cmp_op = "<="
                cmp_prev = prev
                cmp_curr = current
                val = current
            elif self.mode is MIN_ABS_VAL:
                cmp_op = "<="
                cmp_prev = builder.call(fabs, [prev])
                cmp_curr = builder.call(fabs, [current])
                val = current
            elif self.mode is MIN_INDICATOR:
                cmp_op = "<="
                cmp_prev = prev
                cmp_curr = current
                val = current.type(1.0)
            elif self.mode is MIN_ABS_INDICATOR:
                cmp_op = "<="
                cmp_prev = builder.call(fabs, [prev])
                cmp_curr = builder.call(fabs, [current])
                val = current.type(1.0)
            elif self.mode in {PROB, PROB_INDICATOR}:
                # Update prefix sum
                current_prob_ptr = builder.gep(prob_in, [ctx.int32_ty(0), index])
                sum_old = builder.load(sum_ptr)
                sum_new = builder.fadd(sum_old, builder.load(current_prob_ptr))
                builder.store(sum_new, sum_ptr)

                old_below = builder.fcmp_ordered("<=", sum_old, dice)
                new_above = builder.fcmp_ordered("<", dice, sum_new)
                cond = builder.and_(new_above, old_below)
                cmp_prev = ctx.float_ty(1.0)
                cmp_curr = builder.select(cond, cmp_prev, ctx.float_ty(0.0))
                cmp_op = "=="
                if self.mode is PROB:
                    val = current
                else:
                    val = ctx.float_ty(1.0)
            else:
                assert False, "Unsupported mode: {}".format(self.mode)

            # Make sure other elements are zeroed
            builder.store(cur_res_ptr.type.pointee(0), cur_res_ptr)

            cmp_res = builder.fcmp_ordered(cmp_op, cmp_curr, cmp_prev)
            with builder.if_then(cmp_res):
                builder.store(prev_res_ptr.type.pointee(0), prev_res_ptr)
                builder.store(val, cur_res_ptr)
                builder.store(index, idx_ptr)

        return builder

    def function(self,
                 variable=None,
                 execution_id=None,
                 params=None,
                 context=None):
        """

        Arguments
        ---------

        variable : 2d np.array : default class_defaults.variable
           1st item is an array to be transformed;  if `mode <OneHot.mode>` is *PROB*, 2nd item must be an array of
           probabilities (i.e., elements between 0 and 1) of equal length to the 1st item.

        params : Dict[param keyword: param value] : default None
            a `parameter dictionary <ParameterState_Specification>` that specifies the parameters for the
            function.  Values specified for parameters in the dictionary override any assigned to those parameters in
            arguments of the constructor.

        Returns
        -------

        array with single non-zero value : np.array
            specified by `mode <OneHot.mode>`.


        """

        variable = self._check_args(variable=variable, execution_id=execution_id, params=params, context=context)

        if self.mode is MAX_VAL:
            max_value = np.max(variable)
            result = np.where(variable == max_value, max_value, 0)

        elif self.mode is MAX_ABS_VAL:
            max_value = np.max(np.absolute(variable))
            result = np.where(variable == max_value, max_value, 0)

        elif self.mode is MAX_INDICATOR:
            max_value = np.max(variable)
            result = np.where(variable == max_value, 1, 0)

        elif self.mode is MAX_ABS_INDICATOR:
            max_value = np.max(np.absolute(variable))
            result = np.where(variable == max_value, 1, 0)

        if self.mode is MIN_VAL:
            min_value = np.min(variable)
            result = np.where(variable == min_value, min_value, 0)

        elif self.mode is MIN_ABS_VAL:
            min_value = np.min(np.absolute(variable))
            result = np.where(variable == min_value, min_value, 0)

        elif self.mode is MIN_INDICATOR:
            min_value = np.min(variable)
            result = np.where(variable == min_value, 1, 0)

        elif self.mode is MIN_ABS_INDICATOR:
            min_value = np.min(np.absolute(variable))
            result = np.where(variable == min_value, 1, 0)

        elif self.mode in {PROB, PROB_INDICATOR}:
            # 1st item of variable should be data, and 2nd a probability distribution for choosing
            v = variable[0]
            prob_dist = variable[1]
            # if not prob_dist.any() and INITIALIZING in context:
            if not prob_dist.any():
                return self.convert_output_type(v)
            cum_sum = np.cumsum(prob_dist)
            random_state = self.get_current_function_param("random_state", execution_id)
            random_value = random_state.uniform()
            chosen_item = next(element for element in cum_sum if element > random_value)
            chosen_in_cum_sum = np.where(cum_sum == chosen_item, 1, 0)
            if self.mode is PROB:
                result = v * chosen_in_cum_sum
            else:
                result = np.ones_like(v) * chosen_in_cum_sum
            # chosen_item = np.random.choice(v, 1, p=prob_dist)
            # one_hot_indicator = np.where(v == chosen_item, 1, 0)
            # return v * one_hot_indicator

        return self.convert_output_type(result)
