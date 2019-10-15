import math

def dd2dms(longitude, latitude):

    # math.modf() splits whole number and decimal into tuple
    # eg 53.3478 becomes (0.3478, 53)
    split_degx = math.modf(longitude)
    
    # the whole number [index 1] is the degrees
    degrees_x = int(split_degx[1])

    # multiply the decimal part by 60: 0.3478 * 60 = 20.868
    # split the whole number part of the total as the minutes: 20
    # abs() absoulte value - no negative
    minutes_x = abs(int(math.modf(split_degx[0] * 60)[1]))

    # multiply the decimal part of the split above by 60 to get the seconds
    # 0.868 x 60 = 52.08, round excess decimal places to 2 places
    # abs() absoulte value - no negative
    seconds_x = abs(round(math.modf(split_degx[0] * 60)[0] * 60,2))

    # repeat for latitude
    split_degy = math.modf(latitude)
    degrees_y = int(split_degy[1])
    minutes_y = abs(int(math.modf(split_degy[0] * 60)[1]))
    seconds_y = abs(round(math.modf(split_degy[0] * 60)[0] * 60,2))

    # account for E/W & N/S
    if degrees_x < 0:
        EorW = "W"
    else:
        EorW = "E"

    if degrees_y < 0:
        NorS = "S"
    else:
        NorS = "N"

    # abs() remove negative from degrees, was only needed for if-else above
    print "\t" + str(abs(degrees_x)) + u"\u00b0 " + str(minutes_x) + "' " + str(seconds_x) + "\" " + EorW
    print "\t" + str(abs(degrees_y)) + u"\u00b0 " + str(minutes_y) + "' " + str(seconds_y) + "\" " + NorS

# some coords of cities
coords = [
    ["Dublin", -6.2597, 53.3478],
    ["Paris", 2.3508, 48.8567],
    ["Sydney", 151.2094, -33.8650], 
    ["dolgoe", 30.2593857274565, 60.0171144431814], 
]

# test dd2dms() 
for city,x,y in coords:
    print city + ":"
    dd2dms(x, y)