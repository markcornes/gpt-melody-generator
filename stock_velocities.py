import numpy as np
import time
# import matplotlib.pyplot as plt

def date_to_days(dates):
    """Takes list of dates in YYYY-MM-DD format and
        converts to unix time relative to first date"""

    pattern = "%Y-%m-%d"
    str_times = []

    for date in dates:
        one_time = int(time.mktime(time.strptime(date, pattern)))
        str_times.append(one_time)

    non_zeroed_times = np.array(str_times)/86400

    return (non_zeroed_times - non_zeroed_times[0])

def stock_velocities(filename,piece_len):
    raw_data = np.loadtxt(filename, delimiter=",", skiprows=1, usecols=(1,6))
    raw_dates = np.loadtxt(filename, dtype="str", delimiter=",", skiprows=1, usecols=0)

    times = date_to_days(raw_dates)

    # length of piece in notes/events
    step_size = int(raw_data.shape[0]/piece_len)

    intensity_values = raw_data[::step_size,0]
    velocities = 64 + 63*intensity_values/np.max(intensity_values)

    return [int(value) for value in velocities.tolist()]

    # with open('velocity_data.txt', 'w') as f:
    #     output = ''
    #     for point in intensity_values:
    #         output += f'{point:.1f}' + '\n'
    #     f.write(output)