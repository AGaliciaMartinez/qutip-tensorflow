import qutip as qt
import numpy as np

class TimeLA:
    """
    Minimal linear algebra benchmark.
    """
    params = [1,10,100, 1000]

    def setup(self, N):
        self.U = qt.rand_unitary(N)


    def time_multiplication_qt(self, N):
        U = self.U
        for i in range(2):
            U*U

    def time_multiplication_np(self, N):
        U = self.U
        for i in range(2):
            np.matmul(U.full(), U.full())
