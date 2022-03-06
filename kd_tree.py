import numpy as np


class Node(object):

    def __init__(self, item=None, label=None, dim=None, parent=None, left_child=None, right_child=None):
        self.item = item
        self.label = label
        self.dim = dim
        self.parent = parent
        self.left_child = left_child
        self.right_child = right_child

    @property
    def brother(self):

        if not self.parent:
            bro = None
        else:
            if self.parent.left_child is self:
                bro = self.parent.right_child
            else:
                bro = self.parent.left_child
        return bro


class KDTree(object):

    def __init__(self, aList, labelList):
        self.__length = 0
        self.__root = self.__create(aList, labelList)

    def __create(self, aList, labelList, parentNode=None):

        dataArray = np.array(aList)
        m, n = dataArray.shape
        labelArray = np.array(labelList).reshape(m, 1)
        if m == 0:
            return None

        var_list = [np.var(dataArray[:, col]) for col in range(n)]
        max_index = var_list.index(max(var_list))

        max_feat_ind_list = dataArray[:, max_index].argsort()
        # print(max_feat_ind_list)
        mid_item_index = max_feat_ind_list[m // 2]
        if m == 1:
            self.__length += 1
            return Node(dim=max_index, label=labelArray[mid_item_index], item=dataArray[mid_item_index],
                        parent=parentNode, left_child=None, right_child=None)

        node = Node(dim=max_index, label=labelArray[mid_item_index], item=dataArray[mid_item_index],
                    parent=parentNode)

        value = dataArray[mid_item_index, max_index]
        left = list(filter(lambda x: dataArray[x, max_index] < value, max_feat_ind_list[:m // 2]))
        right = list(filter(lambda x: dataArray[x, max_index] == value, max_feat_ind_list[:m // 2]))

        left_tree = dataArray[left]
        left_label = labelArray[left]
        left_child = self.__create(left_tree, left_label, node)
        if m == 2:
            right_tree = dataArray[right]
            right_label = labelArray[right]
            right_child = self.__create(right_tree, right_label, node)
        else:
            right = np.append(right, max_feat_ind_list[m // 2 + 1:]).astype(int)
            right_tree = dataArray[right]
            right_label = labelArray[right]
            right_child = self.__create(right_tree, right_label, node)
            # self.__length += 1

        node.left_child = left_child
        node.right_child = right_child
        self.__length += 1
        return node

    @property
    def length(self):
        return self.__length

    @property
    def root(self):
        return self.__root

    def euclidean_distance(self, point1, point2):
        dis = np.sqrt((point1[0] - point2[0]) ** 2 + ((point1[1] - point2[1])) ** 2)
        return dis

    def get_hyper_plane_dist(self, node, item):
        cur_dim = node.dim
        dis = abs(item[cur_dim] - node.item[cur_dim])
        return dis

    def find_nearest_leaf(self, node, item):
        if node.left_child == None and node.right_child == None:
            return node
        while True:
            cur_dim = node.dim
            if node.left_child == None and node.right_child == None:
                return node
            if item[cur_dim] < node.item[cur_dim]:
                if node.left_child == None:
                    return node.right_child
                node = node.left_child
            else:
                if node.right_child == None:
                    return node.left_child
                node = node.right_child

    def backtracking(self, root, node, n_node, item):
        global s_dis
        dis = self.euclidean_distance(node.item, item)
        if dis < s_dis:
            n_node = node
            s_dis = dis
        if node == root:
            return n_node
        if node.brother and s_dis > self.get_hyper_plane_dist(node.parent, item):
            p_node = self.find_nearest_leaf(node.brother, item)
            n_node = self.backtracking(node.brother, p_node, n_node, item)

        n_node = self.backtracking(root, node.parent, n_node, item)

        return n_node

    def find_nearest_neighbour(self, item):
        global s_dis

        if self.length == 0:
            return None

        node = self.__root
        n_node = self.find_nearest_leaf(node, item)
        s_dis = float("inf")
        n_node = self.backtracking(node, n_node, n_node, item)
        return n_node
