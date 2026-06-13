import numpy as np

## reference : "Position Detection Error" ; ChatGPT ; frenchuni26s

class ThinPlateSpline2D:
    def __init__(self, measured_pts, true_pts):
        self.measured_pts = np.asarray(measured_pts, dtype=float)
        self.true_pts = np.asarray(true_pts, dtype=float)

        n = len(self.measured_pts)

        K = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                r = np.linalg.norm(
                    self.measured_pts[i] - self.measured_pts[j]
                )

                if r > 0:
                    K[i, j] = r * r * np.log(r)
                else:
                    K[i, j] = 0.0

        P = np.hstack(
            (
                np.ones((n, 1)),
                self.measured_pts
            )
        )

        A = np.block([
            [K, P],
            [P.T, np.zeros((3, 3))]
        ])

        bx = np.concatenate([
            self.true_pts[:, 0],
            np.zeros(3)
        ])

        by = np.concatenate([
            self.true_pts[:, 1],
            np.zeros(3)
        ])

        params_x = np.linalg.solve(A, bx)
        params_y = np.linalg.solve(A, by)

        self.wx = params_x[:n]
        self.ax = params_x[n:]

        self.wy = params_y[:n]
        self.ay = params_y[n:]

    @staticmethod
    def _U(r):
        if r == 0:
            return 0.0
        return r * r * np.log(r)

    def correct(self, x, y):
        p = np.array([x, y])

        fx = (
            self.ax[0]
            + self.ax[1] * x
            + self.ax[2] * y
        )

        fy = (
            self.ay[0]
            + self.ay[1] * x
            + self.ay[2] * y
        )

        for i in range(len(self.measured_pts)):
            r = np.linalg.norm(
                p - self.measured_pts[i]
            )

            u = self._U(r)

            fx += self.wx[i] * u
            fy += self.wy[i] * u

        return float(fx), float(fy)


# ------------------------------------------------------------------
# Calibration data
# ------------------------------------------------------------------

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
    [1, 1],
    [1, 2],
    [1, 3],
    [1, 4],

    [2, 1],
    [2, 2],
    [2, 3],
    [2, 4],

    [3, 1],
    [3, 2],
    [3, 3],
    [3, 4],

    [4, 1],
    [4, 2],
    [4, 3],
    [4, 4]
], dtype=float)


# ------------------------------------------------------------------
# Create calibration model once
# ------------------------------------------------------------------

_tps_model = ThinPlateSpline2D(
    MEASURED_POINTS,
    TRUE_POINTS
)


# ------------------------------------------------------------------
# Public function
# ------------------------------------------------------------------

def correct_position(x, y):
    """
    Correct a measured position.

    Parameters
    ----------
    x : float
        Measured X coordinate.

    y : float
        Measured Y coordinate.

    Returns
    -------
    corrected_x : float
    corrected_y : float
    """

    return _tps_model.correct(x, y)


# ------------------------------------------------------------------
# Example
# ------------------------------------------------------------------

if __name__ == "__main__":

    measured_x = 2.30
    measured_y = 2.45

    corrected_x, corrected_y = correct_position(
        measured_x,
        measured_y
    )

    print(
        f"Measured : ({measured_x:.4f}, {measured_y:.4f})"
    )

    print(
        f"Corrected: ({corrected_x:.4f}, {corrected_y:.4f})"
    )