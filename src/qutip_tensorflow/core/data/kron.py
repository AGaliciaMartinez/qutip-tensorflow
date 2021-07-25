import qutip
from .tftensor import TfTensor
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import tensorflow as tf


__all__ = ['kron_tftensor']

def kron_tftensor(left, right):
    return TfTensor._fast_constructor(
        tf.linalg.LinearOperatorKronecker([
            tf.linalg.LinearOperatorFullMatrix(left._tf),
            tf.linalg.LinearOperatorFullMatrix(right._tf),
        ]).to_dense(),
        shape=(left.shape[0]*right.shape[0], left.shape[1]*right.shape[1]),
    )
