import numpy as np
from numpy.testing import assert_almost_equal
import tensorflow as tf
import pytest

from qutip.core import data
from qutip.core.data import dense
from qutip_tensorflow.core.data import DenseTensor

from . import conftest


# Set up some fixtures for automatic parametrisation.

@pytest.fixture(params=[
    pytest.param((1, 5), id='ket'),
    pytest.param((5, 1), id='bra'),
    pytest.param((5, 5), id='square'),
    pytest.param((2, 4), id='wide'),
    pytest.param((4, 2), id='tall'),
])
def shape(request): return request.param


@pytest.fixture(params=[True, False], ids=['Fortran', 'C'])
def fortran(request): return request.param


def _valid_numpy():
    # Arbitrary valid numpy array.
    return conftest.random_numpy_dense((5, 5), False)

def _valid_tensor():
    # Arbitrary valid tensor array.
    return conftest.random_tensor_dense((5, 5))

def _valid_list():
    # Arbitrary valid tensor array.
    return conftest.random_numpy_dense((5, 5), False).tolist()


@pytest.fixture(scope='function')
def numpy_dense(shape, fortran):
    return conftest.random_numpy_dense(shape, fortran)

@pytest.fixture(scope='function')
def tensor_dense(shape):
    return conftest.random_tensor_dense(shape)


@pytest.fixture(scope='function')
def list_dense(shape):
    return conftest.random_numpy_dense(shape, fortran).tolist()

@pytest.fixture(scope='function')
def data_tensor_dense(tensor_dense):
    return DenseTensor(tensor_dense)


class TestClassMethods:
    def test_init_from_list(self, list_dense, shape):
        test = DenseTensor(list_dense, shape)
        assert test.shape == shape
        assert np.all(test.to_array() == np.array(list_dense))

    def test_init_from_ndarray(self, numpy_dense):
        test = DenseTensor(numpy_dense)
        assert test.shape == numpy_dense.shape
        assert np.all(test.to_array() == numpy_dense)

    def test_init_from_tensor(self, tensor_dense):
        test = DenseTensor(tensor_dense)
        assert test.shape == tuple(tensor_dense.shape.as_list())
        assert np.all(test.to_array() == tensor_dense)

        # by default we do not return a copy
        assert test._tf is tensor_dense

    @pytest.mark.parametrize('dtype', ['complex128',
                                       'float64',
                                       'int32', 'int64',
                                       'uint32'])
    def test_init_from_list_other_dtype(self, shape, dtype):
        _numpy_dense = np.random.rand(*shape).astype(dtype, casting='unsafe')
        _list_dense = _numpy_dense.tolist()
        test = DenseTensor(_list_dense)
        assert test.shape == shape
        assert test._tf.dtype == tf.complex128
        assert test._tf.shape == shape
        assert_almost_equal(test.to_array(), _list_dense)

    @pytest.mark.parametrize('dtype', ['complex128',
                                       'float64',
                                       'int32', 'int64',
                                       'uint32'])
    def test_init_from_ndarray_other_dtype(self, shape, dtype):
        _numpy_dense = np.random.rand(*shape).astype(dtype, casting='unsafe')
        test = DenseTensor(_numpy_dense)
        assert test.shape == shape
        assert test._tf.dtype == tf.complex128
        assert test._tf.shape == shape
        assert np.all(test.to_array() == _numpy_dense)

    @pytest.mark.parametrize('dtype', ['complex128',
                                       'float64',
                                       'int32', 'int64',
                                       'uint32'])
    def test_init_from_tensor_other_dtype(self, shape, dtype):
        numpy_dense = np.random.rand(*shape).astype(dtype, casting='unsafe')
        tensor = tf.constant(numpy_dense)
        test = DenseTensor(tensor)
        assert test.shape == shape
        assert test._tf.shape == shape
        assert test._tf.dtype == tf.complex128

        tensor = tf.cast(tensor, dtype=tf.complex128)
        assert np.all(test._tf == tensor)

    @pytest.mark.parametrize("data", [_valid_tensor,_valid_list,_valid_numpy],
                       ids= ["numpy", "list", "tensor"])
    @pytest.mark.parametrize("shape",[
        pytest.param(1, id="shape_no_tuple"),
        pytest.param((), id="shape_0_tuple"),
        pytest.param((1,), id="shape_1_tuple"),
        pytest.param((None, None), id="shape_None_tuple"),
        pytest.param([2,2], id="shape_list"),
        pytest.param((1, 2, 3), id="shape_3_tuple"),
        pytest.param((-1, 1), id="negative_shape"),
        pytest.param((-4, -4), id="both_negative_shape"),
        pytest.param((1213, 1217), id="differen_shape"),
    ])
    def test_init_from_wrong_shape(self, data, shape):
        """
        Test that the __init__ method raises a suitable error when passed
        incorrectly formatted inputs.
        """
        with pytest.raises(ValueError):
            DenseTensor(data, shape)

    def test_copy_returns_a_correct_copy(self, data_tensor_dense):
        """
        Test that the copy() method produces an actual copy, and that the
        result represents the same matrix.
        """
        original = data_tensor_dense
        copy = data_tensor_dense.copy()
        assert original is not copy
        assert np.all(original._tf == copy._tf)
        assert original._tf is not copy._tf


    def test_to_array_is_correct_result(self, data_tensor_dense):
        test_array = data_tensor_dense.to_array()
        assert isinstance(test_array, np.ndarray)
        assert test_array.ndim == 2
        assert test_array.shape == data_tensor_dense.shape

        tensor = tf.constant(test_array)
        assert np.all(test_array == data_tensor_dense._tf)

