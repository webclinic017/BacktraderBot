from scipy import stats
import numpy as np
from sklearn import preprocessing
import math


class LinearRegressionStats(object):
    angle = None
    slope = None
    intercept = None
    r_value = None
    p_value = None
    std_err = None
    r_squared = None

    def __init__(self, angle, slope, intercept, r_value, r_squared, p_value, std_err):
        self.angle = angle
        self.slope = slope
        self.intercept = intercept
        self.r_value = r_value
        self.r_squared = r_squared
        self.p_value = p_value
        self.std_err = std_err


class LinearRegressionCalculator(object):
    def __init__(self):
        pass

    @staticmethod
    def calculate(equity_curve_data_dict):
        counter = 1
        equity_curve_data_points = {}
        for date, equity in equity_curve_data_dict.items():
            equity_curve_data_points[counter] = round(equity)
            counter += 1

        x_arr = list(equity_curve_data_points.keys())
        y_arr = list(equity_curve_data_points.values())
        if len(x_arr) > 1:
            #print("!!! netprofits_data={}".format(netprofits_data))
            #print("!!! y_arr={}".format(y_arr))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_arr, y_arr)
            r_squared = np.sign(r_value) * r_value * r_value

            x_arr_norm = preprocessing.normalize([x_arr])[0]
            y_arr_norm = preprocessing.normalize([y_arr])[0]
            slope_norm, intercept_norm, r_value_norm, p_value_norm, std_err_norm = stats.linregress(x_arr_norm, y_arr_norm)
            angle = math.degrees(math.atan(slope_norm))
            #print("angle={}, slope={}, intercept={}, r_value={}, p_value={}, std_err={}".format(angle, slope, intercept, r_value, p_value, std_err))
            return LinearRegressionStats(angle, slope, intercept, r_value, r_squared, p_value, std_err)
        else:
            return LinearRegressionStats(0, 0, 0, 0, 0, 0, 0)
