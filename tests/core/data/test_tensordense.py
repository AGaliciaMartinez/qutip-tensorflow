import numpy as np
import tensorflow as tf
import pytest

from qutip.core import data
from qutip.core.data import dense
from qutip_tensorflow.core.data.tensorflow_dense import DenseTensor

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
    # Arbitrary valid numpy array.
    return conftest.random_tensor_dense((5, 5))


@pytest.fixture(scope='function')
def numpy_dense(shape, fortran):
    return conftest.random_numpy_dense(shape, fortran)

@pytest.fixture(scope='function')
def tensor_dense(shape):
    return conftest.random_tensor_dense(shape)

@pytest.fixture(scope='function')
def data_tensor_dense(tensor_dense):
    return DenseTensor(tensor_dense)


class TestClassMethods:
    def test_init_from_ndarray(self, numpy_dense):
        test = DenseTensor(numpy_dense)
        assert test.shape == numpy_dense.shape
        assert np.all(test.to_array() == numpy_dense)

    def test_init_from_tensor(self, tensor_dense):
        test = DenseTensor(tensor_dense)
        assert test.shape == tuple(tensor_dense.shape.as_list())
        assert np.all(test.to_array() == tensor_dense)

        # by default we return a copy
        assert test._tf is not tensor_dense

    @pytest.mark.parametrize('dtype', ['complex128',
                                       'float64',
                                       'int32', 'int64',
                                       'uint32'])
    def test_init_from_ndarray_other_dtype(self, shape, dtype):
        numpy_dense = np.random.rand(*shape).astype(dtype, casting='unsafe')
        test = DenseTensor(numpy_dense)
        assert test.shape == shape
        assert test._tf.dtype == tf.complex128
        assert test._tf.shape == shape
        assert np.all(test.to_array() == numpy_dense)

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

    #TODO: add test for instantiating with list.
    @pytest.mark.parametrize(['arg', 'kwargs', 'error'], [
        pytest.param(_valid_tensor(), {'shape': ()}, ValueError,
                     id="numpy-shape 0 tuple"),
        pytest.param(_valid_tensor(), {'shape': (1,)}, ValueError,
                     id="numpy-shape 1 tuple"),
        pytest.param(_valid_tensor(), {'shape': (None, None)}, ValueError,
                     id="numpy-shape None tuple"),
        pytest.param(_valid_tensor(), {'shape': [2, 2]}, ValueError,
                     id="numpy-shape list"),
        pytest.param(_valid_tensor(), {'shape': (1, 2, 3)}, ValueError,
                     id="numpy-shape 3 tuple"),
        pytest.param(_valid_tensor(), {'shape': (-1, 1)}, ValueError,
                     id="numpy-negative shape"),
        pytest.param(_valid_tensor(), {'shape': (-4, -4)}, ValueError,
                     id="numpy-both negative shape"),
        pytest.param(_valid_tensor(), {'shape': (1213, 1217)}, ValueError,
                     id="numpy-different shape"),
    ])
    def test_init_from_wrong_input(self, arg, kwargs, error):
        """
        Test that the __init__ method raises a suitable error when passed
        incorrectly formatted inputs.

        This test also serves as a *partial* check that Dense safely handles
        deallocation in the presence of exceptions in its __init__ method.  If
        the tests segfault, it's quite likely that the memory management isn't
        being done correctly in the hand-off us setting our data buffers up and
        marking the numpy actually owns the data.
        """
        with pytest.raises(error):
            DenseTensor(arg, **kwargs)

    def test_copy_returns_a_correct_copy(self, data_tensor_dense):
        """
        Test that the copy() method produces an actual copy, and that the
        result represents the same matrix.
        """
        original = data_tensor_dense
        copy = data_tensor_dense.copy()
        assert original is not copy
        assert np.all(original._tf == copy._tf)


    def test_to_array_is_correct_result(self, data_tensor_dense):
        test_array = data_tensor_dense.to_array()
        assert isinstance(test_array, np.ndarray)
        assert test_array.ndim == 2
        assert test_array.shape == data_tensor_dense.shape

        #TODO: thinks what to do with this.
        #assert test_array.strides == nd_view.strides
        #assert test_array.flags.c_contiguous == nd_view.flags.c_contiguous
        #assert test_array.flags.f_contiguous == nd_view.flags.f_contiguous
        # It's not enough to be accurate within a tolerance here - there's no
        # mathematics, so they should be _identical_.
        tensor = tf.constant(test_array)
        assert np.all(test_array == data_tensor_dense._tf)

    #TODO: Here I am.
    @pytest.mark.parametrize('new_fortran', [
        pytest.param(-1, id='swap'),
        pytest.param(False, id='C'),
        pytest.param(True, id='Fortran'),
    ])
    def test_reorder(self, data_dense, new_fortran):
        reordered = data_dense.reorder(new_fortran)
        assert isinstance(reordered, data.Dense)
        assert reordered.shape == data_dense.shape
        orig = data_dense.to_array()
        test = reordered.to_array()
        if new_fortran == -1:
            orig.flags.f_contiguous == test.flags.c_contiguous
            orig.flags.c_contiguous == test.flags.f_contiguous
        elif new_fortran is True:
            assert test.flags.f_contiguous
        else:
            assert test.flags.c_contiguous
        assert np.all(orig == test)

class TestFactoryMethods:
    def test_empty(self, shape):
        base = dense.empty(shape[0], shape[1])
        nd = base.as_ndarray()
        assert isinstance(base, data.Dense)
        assert base.shape == shape
        assert nd.shape == shape

    def test_zeros(self, shape):
        base = dense.zeros(shape[0], shape[1])
        nd = base.as_ndarray()
        assert isinstance(base, data.Dense)
        assert base.shape == shape
        assert nd.shape == shape
        assert np.count_nonzero(nd) == 0

    @pytest.mark.parametrize('dimension', [1, 5, 100])
    @pytest.mark.parametrize(
        'scale',
        [None, 2, -0.1, 1.5, 1.5+1j],
        ids=['none', 'int', 'negative', 'float', 'complex']
    )
    def test_identity(self, dimension, scale):
        # scale=None is testing that the default value returns the identity.
        base = (dense.identity(dimension) if scale is None
                else dense.identity(dimension, scale))
        nd = base.as_ndarray()
        numpy_test = np.eye(dimension, dtype=np.complex128)
        if scale is not None:
            numpy_test *= scale
        assert isinstance(base, data.Dense)
        assert base.shape == (dimension, dimension)
        assert np.count_nonzero(nd - numpy_test) == 0

    @pytest.mark.parametrize(['diagonals', 'offsets', 'shape'], [
        pytest.param([2j, 3, 5, 9], None, None, id='main diagonal'),
        pytest.param([1], None, None, id='1x1'),
        pytest.param([[0.2j, 0.3]], None, None, id='main diagonal list'),
        pytest.param([0.2j, 0.3], 2, None, id='superdiagonal'),
        pytest.param([0.2j, 0.3], -2, None, id='subdiagonal'),
        pytest.param([[0.2, 0.3, 0.4], [0.1, 0.9]], [-2, 3], None,
                     id='two diagonals'),
        pytest.param([1, 2, 3], 0, (3, 5), id='main wide'),
        pytest.param([1, 2, 3], 0, (5, 3), id='main tall'),
        pytest.param([[1, 2, 3], [4, 5]], [-1, -2], (4, 8), id='two wide sub'),
        pytest.param([[1, 2, 3, 4], [4, 5, 4j, 1j]], [1, 2], (4, 8),
                     id='two wide super'),
        pytest.param([[1, 2, 3], [4, 5]], [1, 2], (8, 4), id='two tall super'),
        pytest.param([[1, 2, 3, 4], [4, 5, 4j, 1j]], [-1, -2], (8, 4),
                     id='two tall sub'),
        pytest.param([[1, 2, 3], [4, 5, 6], [1, 2]], [1, -1, -2], (4, 4),
                     id='out of order'),
        pytest.param([[1, 2, 3], [4, 5, 6], [1, 2]], [1, 1, -2], (4, 4),
                     id='sum duplicates'),
    ])
    def test_diags(self, diagonals, offsets, shape):
        base = dense.diags(diagonals, offsets, shape)
        # Build numpy version test.
        if not isinstance(diagonals[0], list):
            diagonals = [diagonals]
        offsets = np.atleast_1d(offsets if offsets is not None else [0])
        if shape is None:
            size = len(diagonals[0]) + abs(offsets[0])
            shape = (size, size)
        test = np.zeros(shape, dtype=np.complex128)
        for diagonal, offset in zip(diagonals, offsets):
            test[np.where(np.eye(*shape, k=offset) == 1)] += diagonal
        assert isinstance(base, data.Dense)
        assert base.shape == shape
        np.testing.assert_allclose(base.to_array(), test, rtol=1e-10)

    @pytest.mark.parametrize(['shape', 'position', 'value'], [
        pytest.param((1, 1), (0, 0), None, id='minimal'),
        pytest.param((10, 10), (5, 5), 1.j, id='on diagonal'),
        pytest.param((10, 10), (1, 5), 1., id='upper'),
        pytest.param((10, 10), (5, 1), 2., id='lower'),
        pytest.param((10, 1), (5, 0), None, id='column'),
        pytest.param((1, 10), (0, 5), -5.j, id='row'),
        pytest.param((10, 2), (5, 1), 1+2j, id='tall'),
        pytest.param((2, 10), (1, 5), 10, id='wide'),
    ])
    def test_one_element(self, shape, position, value):
        test = np.zeros(shape, dtype=np.complex128)
        if value is None:
            base = data.one_element_dense(shape, position)
            test[position] = 1.0+0.0j
        else:
            base = data.one_element_dense(shape, position, value)
            test[position] = value
        assert isinstance(base, data.Dense)
        assert base.shape == shape
        assert np.allclose(base.to_array(), test, atol=1e-10)

    @pytest.mark.parametrize(['shape', 'position', 'value'], [
        pytest.param((0, 0), (0, 0), None, id='zero shape'),
        pytest.param((10, -2), (5, 0), 1.j, id='neg shape'),
        pytest.param((10, 10), (10, 5), 1., id='outside'),
        pytest.param((10, 10), (5, -1), 2., id='outside neg'),
    ])
    def test_one_element_error(self, shape, position, value):
        with pytest.raises(ValueError) as exc:
            base = data.one_element_dense(shape, position, value)
        assert str(exc.value).startswith("Position of the elements"
                                         " out of bound: ")
