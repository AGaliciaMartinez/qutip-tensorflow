import qutip
from .tftensor import TfTensor
from .matmul import matmul_tftensor
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import tensorflow as tf

__all__ = ["pow_tftensor"]


def pow_tftensor(matrix, n):
    """Matrix power."""

    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"""Trace can only be performed in square matrix. This
                         matrix has shape={matrix.shape}"""
        )

    out = tf.eye(matrix.shape[0], matrix.shape[1], dtype=tf.complex128)
    pow = matrix._tf

    out = pow if n & 1 else out

    n >>= 1
    while n:
        pow = pow @ pow

        if n & 1:
            out = out @ pow
        n >>= 1

    return TfTensor._fast_constructor(out, shape=matrix.shape)


qutip.data.expm.add_specialisations(
    [
        (TfTensor, TfTensor, pow_tftensor),
    ]
)
