from typing import Sequence, Union

import numpy as np
import numpy.typing as npt

Vector3i = npt.NDArray[np.int_]
Vector3f = npt.NDArray[np.float_]

Vector3 = Union[Vector3f, Vector3i]

Matrix = npt.NDArray

Paths = Union[npt.NDArray, Sequence[Matrix]]
