import json
import logging

from map_parse import HDMapParser
import datetime
from numpy import linalg


# rsu_group = RSUGroup()
# map_name_list = rsu_group.get_map_name_list()
map_name_list = ["Boshutm"]

class MapLaneInfo(object):
    def __init__(self, parser, road_link, corner_dic, data):
        self.parser = parser
        self.road_link = road_link
        self.corner_dic = corner_dic
        self.data = data


class LaneInfo(object):
    map_list = map_name_list
    map_dict = {}
    print()
    for map in map_list:
        map_json_file = '' + map + '.json'
        try:
            with open(map_json_file) as f:
                data = json.load(f)
            temp_parser = HDMapParser(data)
            road_link, corner_dic = None, None
            map_obj = MapLaneInfo(temp_parser, road_link, corner_dic, data)
            map_dict[map] = map_obj
        except Exception as e:
            logging.error(f"NO MAP, can not find {map_json_file}")
    print(map_dict)
    parser = map_dict[map_list[0]].parser
    
    def __init__(self):
        self.UTMx, self.UTMy = .0, .0
        self.nearest_point = 0
        self.x, self.y = 0, 0
        self.road_id, self.lane_id = 0, 0
        self.hdg = .0
        self.s = .0
        self.width = .0

    def get_point(self, UTMx, UTMy, map_name):
        try:
            self.parser = self.map_dict[map_name].parser
        except Exception as e:
            logging.error(e)
            self.x, self.y = 0, 0
            self.road_id, self.lane_id = 0, 0
            self.hdg = .0
            self.s = .0
            self.width = .0
            return
        self.UTMx, self.UTMy = UTMx, UTMy
        self.nearest_point = self.parser.nearest_neighbour([self.UTMx, self.UTMy])
        # print(linalg.norm(self.nearest_point[0] - [self.UTMx, self.UTMy]), self.nearest_point)
        if linalg.norm(self.nearest_point[0] - [self.UTMx, self.UTMy]) < float(self.nearest_point[1][4]) / 2:
            self.x, self.y = self.nearest_point[0]
            self.road_id = self.nearest_point[1][0]
            self.lane_id = self.nearest_point[1][1]
            self.hdg = float(self.nearest_point[1][2])
            self.s = float(self.nearest_point[1][3])
            self.width = float(self.nearest_point[1][4])
        else:
            self.x, self.y = 0, 0
            self.road_id, self.lane_id = 0, 0
            self.hdg = .0
            self.s = .0
            self.width = .0

    @property
    def xy(self):
        return self.x, self.y

    @property
    def ids(self):
        return int(self.road_id), int(self.lane_id)

    @property
    def utmxy(self):
        return self.UTMx, self.UTMy

    @property
    def limit(self):

        if self.road_id == 0:
            return 0
        return float(self.data['road'][self.road_id]['speed'])

    @property
    def signal_id(self):

        # print(self.data['road'][self.road_id]['lane'][self.lane_id]['signal_id'])
        if self.road_id == 0:
            return 0
        return self.data['road'][self.road_id]['lane'][self.lane_id]['signal_id']

    @property
    def remaining_s(self):

        if int(self.lane_id) >= 0:
            return self.s
        else:
            length = self.data['road'][self.road_id]['length']
            return length - self.s


if __name__ == '__main__':
        t0 = datetime.datetime.now()
        li = LaneInfo()
        s = li.parser.lane_edges
        t1 = datetime.datetime.now()
        # li.get_point(1512965.90, 3506669.07)
        # print(li.x, li.y, li.road_id, li.lane_id, li.hdg, li.width)
        t2 = datetime.datetime.now()
        li.get_point(165933.53695584583, 49.90689093553706, "Boshutm")
        li.get_point(166021.44308054057, 0.0, "Boshutm")
        # print(li.xy[0],li.xy[1])
        print(li.x, li.y, li.road_id, li.lane_id, li.hdg, li.width)
        print(li.signal_id)
        #
        # li.get_point(1256684.2530879425, 3536878.592955966)
        # print(li.x, li.y, li.road_id, li.lane_id, li.hdg, li.width)
        # print(li.signal_id)
        #
        # li.get_point(1256684.6473711615, 3536879.864351909)
        # print(li.x, li.y, li.road_id, li.lane_id, li.hdg, li.width)
        # print(li.signal_id)
        #
        # li.get_point(1257113.0525972154, 3536321.20371823)
        # print(li.x, li.y, li.road_id, li.lane_id, li.hdg, li.width)
        # print(li.signal_id)
        # # li.get_point(1513164.6461410148, 3506528.9460702606)
        # print(li.limit)
        # # print(li.remaining_s)
        # t3 = datetime.datetime.now()
        # print((t3-t2).microseconds)