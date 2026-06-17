import numpy as np


class CubicWarp2D:

    def __init__(self, measured_pts, true_pts):

        self.measured_pts = np.asarray(measured_pts, dtype=float)
        self.true_pts = np.asarray(true_pts, dtype=float)

        A = np.array([
            self._basis(x, y)
            for x, y in self.measured_pts
        ])

        bx = self.true_pts[:, 0]
        by = self.true_pts[:, 1]

        # Least-squares fit
        self.coeff_x, _, _, _ = np.linalg.lstsq(
            A, bx, rcond=None
        )

        self.coeff_y, _, _, _ = np.linalg.lstsq(
            A, by, rcond=None
        )

    @staticmethod
    def _basis(x, y):

        return np.array([
            1.0,
            x,
            y,
            x*x,
            x*y,
            y*y,
            x*x*x,
            x*x*y,
            x*y*y,
            y*y*y
        ])

    def correct(self, x, y):

        b = self._basis(x, y)

        x_corr = float(
            np.dot(self.coeff_x, b)
        )

        y_corr = float(
            np.dot(self.coeff_y, b)
        )

        return x_corr, y_corr


# ---------------------------------------------------------
# Calibration data
# ---------------------------------------------------------

MEASURED_POINTS = np.array([
    [1.0667, 0.9699],
    [1.0824, 1.9235],
    [1.0825, 2.8886],
    [1.0511, 3.9148],

    [2.0392, 0.9725],
    [2.0549, 1.9136],
    [2.0707, 2.8704],
    [2.0863, 3.8820],

    [3.0118, 0.9572],
    [3.0431, 1.8979],
    [3.0588, 2.8547],
    [3.1059, 3.8742],

    [4.0159, 0.9411],
    [4.0157, 1.8979],
    [4.0784, 2.8547],
    [4.1412, 3.8899]
])

TRUE_POINTS = np.array([
    [1,1],
    [1,2],
    [1,3],
    [1,4],

    [2,1],
    [2,2],
    [2,3],
    [2,4],

    [3,1],
    [3,2],
    [3,3],
    [3,4],

    [4,1],
    [4,2],
    [4,3],
    [4,4]
], dtype=float)


# ---------------------------------------------------------
# Build model once
# ---------------------------------------------------------

_poly_model = CubicWarp2D(
    MEASURED_POINTS,
    TRUE_POINTS
)


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

def correct_position(x, y):
    """
    Convert measured coordinates
    into corrected coordinates.
    """
    return _poly_model.correct(x, y)


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":

    x_meas = 2.30
    y_meas = 2.45

    x_corr, y_corr = correct_position(
        x_meas,
        y_meas
    )

    print(
        f"Measured : ({x_meas:.4f}, {y_meas:.4f})"
    )

    print(
        f"Corrected: ({x_corr:.4f}, {y_corr:.4f})"
    )