import geopandas as gpd
import json
import kd_tree as kd_tree
import pandas as pd
from pyproj import Proj
import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point
import datetime
import matplotlib.pyplot as plt


class HDMapParser(object):

    def __init__(self, json_data):
        self.data = json_data
        self.road_info = pd.DataFrame(columns=['road_id', 'junction_id', 'length'])
        self.central_points = pd.DataFrame(
            columns=['road_id', 'lane_id', 'junction_id', 'lane_index', 'geometry', 'coordinate', 'hdg', 's', 'width'])
        self.central_lines = pd.DataFrame(columns=['road_id', 'lane_id', 'geometry'])
        self.lane_edges = pd.DataFrame(columns=['road_id', 'lane_id', 'LR', 'geometry'])
        self.link_df = pd.DataFrame(columns=['road_from', 'lane_from', 'road_to', 'lane_to', 'one_way', 'length'])
        self.tp_graph = nx.DiGraph()
        self.parse()
        self.gen_TopologicalGraph()
        self.bulid_kd_tree()

    def WGS84_to_UTM49(self, location):
        lon = location[0]
        lat = location[1]
        my_proj = Proj(proj='utm', zone=49, ellps='WGS84', preserve_units=False)
        x, y = my_proj(lon, lat)
        return [x, y]

    def add_link(self, road_from, lane_from, road_to, lane_to, one_way, length):
        self.link_df.loc[len(self.link_df)] = [road_from, lane_from, road_to, lane_to, one_way, length]

    def remove_links(self, road_id, lanes):
        df = self.link_df[~((self.link_df.road_from == road_id) & (self.link_df.lane_from.isin(lanes)))]
        self.link_df = df.reset_index(drop=True)

    def add_length_info(self, road_id, road_len):
        self.link_df.loc[self.link_df.road_from == road_id, 'length'] = road_len

    def bulid_lane_link(self, road_id, lane_id, succ_id, lane_to, same_road=False, driving_lane=[]):
        if same_road:
            if len(driving_lane) > 1:
                a = 0
                while a < len(driving_lane) - 1:
                    lane_from = driving_lane[a]
                    lane_to = driving_lane[a + 1]
                    if int(lane_from) * int(lane_to) > 0:
                        self.add_link(road_id, lane_from, road_id, lane_to, 0, 0.5)
                    a += 1
        else:
            if succ_id != 'None' and lane_to != 'None':
                self.add_link(road_id, lane_id, succ_id, lane_to, 1, None)

    def add_central_points(self, road_id, lane_id, junction_id, gps_points, utm_points, hdg, s, width):
        num = len(gps_points)
        df = pd.DataFrame({'road_id': [road_id] * num, 'lane_id': [lane_id] * num, 'junction_id': junction_id,
                           'lane_index': np.arange(num), 'geometry': gps_points, 'coordinate': utm_points,
                           'hdg': hdg, 's': s, 'width': width})
        self.central_points = pd.concat([self.central_points, df])

    def add_central_line(self, road_id, lane_id, utm_points):
        central_line = LineString(utm_points)
        self.central_lines.loc[len(self.central_lines)] = [road_id, lane_id, central_line]

    def add_lane_edges(self, road_id, lane_id, lanes):
        lane_id_int = int(lane_id)
        if lane_id_int < 0:
            right_edge = LineString(lanes[lane_id]['lane_point_84'])
            left_edge = LineString(lanes[str(lane_id_int + 1)]['lane_point_84'])
            self.lane_edges.loc[len(self.lane_edges)] = [road_id, lane_id, 'L', left_edge]
            self.lane_edges.loc[len(self.lane_edges)] = [road_id, lane_id, 'R', right_edge]
        else:
            left_edge = LineString(lanes[lane_id]['lane_point_84'])
            right_edge = LineString(lanes[str(lane_id_int - 1)]['lane_point_84'])
            self.lane_edges.loc[len(self.lane_edges)] = [road_id, lane_id, 'L', left_edge]
            self.lane_edges.loc[len(self.lane_edges)] = [road_id, lane_id, 'R', right_edge]

    def parse_lanes(self, road_id, road_len, lanes, succ_id, junction_id):
        """
        解析道路里所有车道信息
        Args:
            road_id: 道路id
            road_len: 道路长度
            lanes: 车道里所有车道信息
            succ_id: 后续车道id
            junction_id: 车道所在的路口id
        """
        driving_lane = []
        other_lane = []
        # 解析所有车道
        for lane_id, lane in lanes.items():
            if lane['type'] == 'driving':
                if junction_id != '-1':
                    lane_id = str(np.sign(int(lane['to'])) * max(abs(int(lane['to'])), abs(int(lane['from']))))
                driving_lane.append(lane_id)
                lane_to = lane['to']
                # 建立连接关系
                self.bulid_lane_link(road_id, lane_id, succ_id, lane_to)
                hdg = np.array(lane['hdg'])
                # 添加中心线点以及中心线信息
                self.add_central_points(road_id, lane_id, junction_id, lane['center_point_84'],
                                        lane['center_point_utm49'], hdg, lane['s'],lane['width'])
                self.add_central_line(road_id, lane_id, lane['center_point_utm49'])

            else:
                other_lane.append(lane_id)
        # 移除非行车道的车道的连接关系
        self.remove_links(road_id, other_lane)
        # 添加车道长度
        # self.add_length_info(road_id, road_len)

    def parse_junctions(self):
        """
        解析所有路口区域内道路连接信息
        """
        road_lane = self.central_points[['road_id', 'lane_id']].drop_duplicates().set_index('road_id').to_dict()['lane_id']
        junctions = self.data['junction']
        # 从每一个路口里，提取道路连接信息
        for values in junctions.values():
            for value in values.values():
                road_from = value['incomingRoad']
                lane_from = value['from']
                road_to = value['connectingRoad']
                lane_to = road_lane[value['connectingRoad']]
                # 增加连接
                self.add_link(road_from, lane_from, road_to, lane_to, 1, None)
        # 删除重复信息
        self.link_df.drop_duplicates(inplace=True)
        # 添加车道长度
        for key in self.link_df['road_from']:
            self.link_df.loc[self.link_df.road_from==key, 'length'] = self.road_info.loc[self.road_info.road_id==key].iloc[0].at['length']
        # print('***')

    def parse_roads(self):
        """
        解析所有道路信息
        """
        roads = self.data['road']
        # 提取道路信息
        for road_id, road in roads.items():
            junction_id = str(road['junction'])
            road_len = road['length']
            succ_id = 'None' if road['link']['successor']['type'] == 'junction' else str(road['link']['successor']['id'])
            lanes = road['lane']
            # 更新道路信息到road_info DataFrame
            self.road_info.loc[len(self.road_info)] = [road_id, junction_id, road_len]
            # 解析道路里所有车道信息
            self.parse_lanes(road_id, road_len, lanes, succ_id, junction_id)

    def parse(self):
        self.parse_roads()
        self.parse_junctions()
    
        # self.central_points.join(self.road_info[])
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)  #
        # print(self.road_info[['road_id', 'junction_id']])

    def get_nodes_and_edges(self):
        nodes = set()
        edges = []
        for i, link in self.link_df.iterrows():
            lane_from = link.road_from + ',' + link.lane_from
            lane_to = link.road_to + ',' + link.lane_to
            nodes.add(lane_from)
            nodes.add(lane_to)
            if link.one_way == 0:
                edges.append((lane_to, lane_from, link.length))
            edges.append((lane_from, lane_to, link.length))
        return nodes, edges

    def gen_TopologicalGraph(self):
        nodes, edges = self.get_nodes_and_edges()
        self.tp_graph.add_nodes_from(nodes)
        self.tp_graph.add_weighted_edges_from(edges)
        for i in self.tp_graph.edges:
            self.tp_graph.edges[i]["length"] = self.tp_graph.edges[i]["weight"]

    def get_path(self, sn, en):
        if (sn[0] == en[0]) and (sn[1] == en[1]):

            if int(sn[2]) <= int(en[2]):
                df = self.central_points[(self.central_points.road_id == sn[0])
                                         & (self.central_points.lane_id == sn[1])].loc[int(sn[2]):int(en[2])]
                return df
            else:
                next_lane = list(self.tp_graph.successors(sn[0] + ',' + sn[1]))
                path = [sn[0] + ',' + sn[1]] + nx.astar_path(self.tp_graph, next_lane[0], en[0] + ',' + en[1])
        else:
            path = nx.astar_path(self.tp_graph, sn[0] + ',' + sn[1], en[0] + ',' + en[1])
        return path

    def gen_points_df(self, sn, en):

        path = self.get_path(sn, en)
        print(path)
        df = pd.DataFrame()

        a = 0
        lower = 0
        upper = 0
        while a < len(path) - 1:
            [road_id, lane_id] = path[a].split(',')
            [road_id2, lane_id2] = path[a + 1].split(',')
            if road_id == road_id2:
                road_len = self.road_info[self.road_info.road_id == road_id].length.item()
                lower = 0
                upper = int(road_len * 5)
                if a == 0:
                    lower = int(sn[2])
                    upper = int((upper * 2 - lower) / 2)
                if a + 1 == len(path) - 1:
                    upper = int(int(en[2]) / 2)
                    df2 = self.central_points[
                              (self.central_points.road_id == road_id) & (self.central_points.lane_id == lane_id)][
                          :upper]
                    df = df.append(df2, ignore_index=True)
                    lower = int(int(en[2]) / 2)
                    upper = int(en[2])
                    break

                df2 = self.central_points[(self.central_points.road_id == road_id)
                                          & (self.central_points.lane_id == lane_id)][lower:upper]
                df3 = self.central_points[(self.central_points.road_id == road_id)
                                          & (self.central_points.lane_id == lane_id2)][upper:]
                df = pd.concat([df, df2, df3], ignore_index=True)
                a += 2

            else:
                aaa = datetime.datetime.now()
                if a == 0:
                    df2 = self.central_points[
                              (self.central_points.road_id == road_id) & (self.central_points.lane_id == lane_id)][
                          int(sn[2]):]
                else:
                    lower = 0
                    upper = int(en[2])
                    df2 = self.central_points[
                        (self.central_points.road_id == road_id) & (self.central_points.lane_id == lane_id)]
                df = df.append(df2, ignore_index=True)
                a += 1
                bbb = datetime.datetime.now()
                print((bbb - aaa).microseconds)

        end = self.central_points[(self.central_points.road_id == en[0])
                                  & (self.central_points.lane_id == en[1])].loc[lower:upper]

        df = df.append(end, ignore_index=True)

        return df

    def test(self, path):
        [road_id, lane_id] = path[0].split(',')
        df = self.lane_edges[(self.lane_edges.road_id == road_id) & (self.lane_edges.lane_id == lane_id)]
        # & (self.lane_edges.LR == 'L')]
        for r in path[1:]:
            [road_id, lane_id] = r.split(',')
            aa = self.lane_edges[(self.lane_edges.road_id == road_id) & (self.lane_edges.lane_id == lane_id)]
            # & (self.lane_edges.LR == 'L')]
            df = df.append(aa, ignore_index=True)

        return list(df['geometry'].values)

    def bulid_kd_tree(self):
        point_list = list(self.central_points.coordinate.values)
        lable_df = self.central_points.road_id \
                   + ',' + self.central_points.lane_id \
                   + ',' + self.central_points.hdg.map(str) \
                   + ',' + self.central_points.s.map(str) \
                   + ',' + self.central_points.width.map(str) \
                   + ',' + self.central_points.lane_index.map(str)
        lable_list = list(lable_df.values)
        self.kd_tree = kd_tree.KDTree(point_list, lable_list)


    def nearest_neighbour(self, point):
        nst_p = self.kd_tree.find_nearest_neighbour(point)
        neighbour = nst_p.item
        location = nst_p.label[0].split(',')
        return neighbour, location

    def find_index(self, df, position):
        i = df[(df.road_id == position[0]) & (df.lane_id == position[1]) & (df.lane_index == int(position[2]))].index
        return i

    def get_global_path(self, start_point, end_point):
        sn, sl = self.nearest_neighbour(self.WGS84_to_UTM49(start_point))
        en, el = self.nearest_neighbour(self.WGS84_to_UTM49(end_point))
        self.path_points_df = self.gen_points_df(sl, el)

    def draw_path(self):
        x_format = lambda x: Point(x)
        gps_points = self.path_points_df['geometry'].map(x_format)
        path_plot = gpd.GeoSeries(list(gps_points.values))
        path_plot[::100].plot()
        plt.show()


if __name__ == '__main__':
    with open('../../map/longchi20210732.json') as f:
        data = json.load(f)
    parser = HDMapParser(data)
    df = parser.link_df
    todic = {}
    fromdic = {}
    print(df)
    for index, row in df.iterrows():
        if row['road_to'] == row['road_from'] :
            continue
        if row['road_to'] not in todic :
            todic[row['road_to']] = row['road_from']
        else:
            s1 = todic[row['road_to']]
            s2 = row['road_from']           
            todic[row['road_to']] = (s1 + ',' + s2)
    for key, value in todic.items():
        print(key, ' : ', value) 
    print("=================")
    for index, row in df.iterrows():
        s = row['road_from']
        if row['road_from'] not in  todic:
            print("============================" + s)
        if row['road_to'] == row['road_from'] :
            continue
        if row['road_from'] not in fromdic :
            fromdic[row['road_from']] = row['road_to']
        else:
            s1 = fromdic[row['road_from']]
            s2 = row['road_to']           
            fromdic[row['road_from']] = (s1 + ',' + s2)
    head_road = ''
    for index, row in df.iterrows():  
         if row['road_from'] not in  todic and head_road == '' :
                head_road = row['road_from']
    from_road = head_road            
    to_road = from_road
    road_list = []
    corner_dic = {}
    road_list.append(from_road)
    while to_road != '':
        if from_road in fromdic :
            to_road = fromdic[from_road]
            to_road_arr = to_road.split(',')
            if len(to_road_arr) > 1 :
                for str in to_road_arr :
                    corner_dic[str] = to_road_arr[0]
            from_road = to_road_arr[0]
            road_list.append(from_road)
        else :
            to_road = '' 
    print(road_list)
    print(corner_dic)
              
           
