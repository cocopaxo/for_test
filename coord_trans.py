from pyproj import Proj
import datetime

my_proj = Proj(proj='utm', zone=48, ellps='WGS84', preserve_units=False)
my_proj_dict = {}
for i in range(31, 55):
    my_proj_dict[i] = Proj(proj='utm', zone=i, ellps='WGS84', preserve_units=False)


class CoordTrans(object):
    def __init__(self):
        self.zone = 48

    def gps2utm(self, lon, lat):
        self.zone = int(int(lon) / 6) + 31
        proj = my_proj_dict[self.zone]
        UTMx, UTMy = proj(lon, lat)
        return UTMx, UTMy, self.zone

    def utm2gps(self, UTMx, UTMy, zone=48):
        proj = my_proj_dict[zone]
        lon, lat = proj(UTMx, UTMy, inverse=True)
        return lon, lat


if __name__ == '__main__':
    ct = CoordTrans()
    print(ct.gps2utm(1035342171 / 1e7, 310269552 / 1e7))

    print(ct.utm2gps(1257068.7640208434, 3536317.9404416876))

    print(ct.gps2utm(103.5330155, 31.0262005))
    print(ct.gps2utm(118.9750199, 31.7171267))
    print(ct.gps2utm(118.9750250, 31.7171378))
    print(ct.gps2utm(118.9749983, 31.7170836))
    t3 = datetime.datetime.now()
    for _ in range(1):
        ct = CoordTrans()
        t0 = datetime.datetime.now()
        print(ct.gps2utm(118.9754514110332, 31.71649714878627))
        t1 = datetime.datetime.now()

        print(ct.utm2gps(1257099.4691229041, 3536316.922062569))
        print(ct.utm2gps(40613282.300000000, 3462665.5600000000))

        t2 = datetime.datetime.now()
        print((t2 - t1).microseconds)
        print((t1 - t0).microseconds)
        print("_____________")
    t4 = datetime.datetime.now()
    print((t4 - t3).microseconds)

"""
{'id': 17195963, 'refPos': {'longitude': 0, 'latitude': 0, 'altitude': 0}, 'time': '1613723281412', 'participants': [{'ptcType': 1, 'plateNo': '', 'ptcId': '0', 'size': {'length': 500, 'width': 200, 'height': 35}, 'pos': {'longitude': 1216117902, 'latitude': 312538388, 'altitude': 30}, 'heading': 12875, 'speed': 0, 'obuId': 0, 'vehicleClass': 10}, {'ptcType': 3, 'plateNo': '', 'ptcId': '1081179', 'size': {'length': 68, 'width': 68, 'height': 35}, 'pos': {'longitude': 1216118649, 'latitude': 312535041, 'altitude': 109}, 'heading': 4335, 'speed': 0, 'obuId': 0, 'vehicleClass': 10}, {'ptcType': 3, 'plateNo': '', 'ptcId': '14336714', 'size': {'length': 68, 'width': 68, 'height': 35}, 'pos': {'longitude': 1216119274, 'latitude': 312536653, 'altitude': 112}, 'heading': 19807, 'speed': 0, 'obuId': 0, 'vehicleClass': 10}, {'ptcType': 1, 'plateNo': '', 'ptcId': '2743557', 'size': {'length': 421, 'width': 193, 'height': 29}, 'pos': {'longitude': 1216120403, 'latitude': 312532959, 'altitude': 88}, 'heading': 25979, 'speed': 0, 'obuId': 0, 'vehicleClass': 10}]}
"""
