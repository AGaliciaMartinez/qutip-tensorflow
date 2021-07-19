import warnings

import numpy as np
import qutip
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import tensorflow as tf

from qutip_tensorflow.core.data import TfTensor


def random_numpy_dense(shape, fortran):
    """Generate a random numpy dense matrix with the given shape."""
    out = np.random.rand(*shape) + 1j * np.random.rand(*shape)
    if fortran:
        out = np.asfortranarray(out)
    return out


def random_tensor_dense(shape):
    """Generate a random `Tensor` dense matrix with the given shape."""
    out = np.random.rand(*shape) + 1j * np.random.rand(*shape)
    out = tf.constant(out)
    return out


def random_tftensor(shape):
    """Generate a random TfTensor matrix with the given shape."""
    return TfTensor(random_tensor_dense(shape))
