import numpy as np
import psyneulink.core.components.functions.transferfunctions
import pytest

import psyneulink.core.components.functions.interfacefunctions as Functions
import psyneulink.core.globals.keywords as kw
import psyneulink.core.llvm as pnlvm

@pytest.mark.function
@pytest.mark.identity_function
@pytest.mark.parametrize("size", [1, 2, 4, 8, 16])
@pytest.mark.benchmark(group="IdentityFunction")
def test_basic(size, benchmark):
    variable = np.random.rand(size)
    f = psyneulink.core.components.functions.transferfunctions.Identity(default_variable=variable)
    res = benchmark(f.function, variable)
    assert np.allclose(res, variable)

@pytest.mark.llvm
@pytest.mark.function
@pytest.mark.identity_function
@pytest.mark.parametrize("size", [1, 2, 4, 8, 16])
@pytest.mark.benchmark(group="IdentityFunction")
def test_llvm(size, benchmark):
    variable = np.random.rand(size)
    f = psyneulink.core.components.functions.transferfunctions.Identity(default_variable=variable)
    m = pnlvm.execution.FuncExecution(f)
    res = benchmark(m.execute, variable)
    assert np.allclose(res, variable)

@pytest.mark.llvm
@pytest.mark.cuda
@pytest.mark.function
@pytest.mark.identity_function
@pytest.mark.parametrize("size", [1, 2, 4, 8, 16])
@pytest.mark.benchmark(group="IdentityFunction")
def test_ptx_cuda(size, benchmark):
    variable = np.random.rand(size)
    f = psyneulink.core.components.functions.transferfunctions.Identity(default_variable=variable)
    m = pnlvm.execution.FuncExecution(f)
    res = benchmark(m.cuda_execute, variable)
    assert np.allclose(res, variable)
