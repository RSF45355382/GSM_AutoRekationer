import math,numpy
from scipy.spatial import Delaunay

"""******************************************************************************************************************************"""
"""根据小区覆盖的区域polygen的points坐标, 直角坐标"""
def calc_polyg_coor(angle, coef, length):
    '''
    计算TA对应的小区覆盖边界的坐标
    :param angle:
    :param coef:
    :param length:
    :return:
    '''
    return coef*math.cos(angle)*length,coef*math.sin(angle)*length

def calc_polyg_points(x,y,azimuth,length_dist,angle_list):
    '''
    计算TA对应的小区覆盖边界的坐标, 返回一个点列表
    :param x: 小区位置坐标long
    :param y: 小区位置坐标lat
    :param azimuth: 小区方位角
    :param length_dist:  TA边界对应的举例(转化为gis值)
    :param angle_list:  POLYG_DIST4ANGLE_LIST这个列表, 是构造边界点的常量列表
    :return:
    '''
    azimuth = 90-azimuth
    result_list = [[x+calc_polyg_coor((azimuth+angle)/180*math.pi, coef, length_dist)[0],
                    y+calc_polyg_coor((azimuth+angle)/180*math.pi, coef, length_dist)[1]] for (angle, coef) in angle_list]
    result_list.insert(0,[x,y])
    return result_list


"""******************************************************************************************************************************"""
'''根据德劳内三角剖分进行周边各层小区获取(新方法)'''
def get_neighborSite_by_layerNum(delaunay_object, index_point_list, layer_num,dict_layer_point = {},list_layer_point = [] ,curr_layer = 1):
    '''
    根据德劳内三角形获取周边若干层内的邻站位置
    :param delaunay_object:  德劳内三角剖分对象
    :param index_point_list:  站点位置在生成德劳内三角剖分时候用的numpy对象中的索引值
    :param layer_num:  需要获取的最大层数内的邻站
    :param dict_layer_point: 函数自构造对象, 是返回的{层数:[站址列表]}
    :param list_layer_point: 函数自构造对象, 是返回的[layer_num层数内的站址列表]
    :param curr_layer: 递归操作时候的当前层数
    :return: list_layer_point, dict_layer_point
    '''
    vertex_neighbor_vertices = delaunay_object.vertex_neighbor_vertices
    indices = vertex_neighbor_vertices[0]
    indptr = vertex_neighbor_vertices[1]
    # 获取三角剖分中一个点的周边相邻点方法：
    # Delaunay.vertex_neighbor_vertice属性获取两个ndarray元组：（indices，indptr）。
    # 顶点k的相邻顶点的索引是 indptr [indices [k]：indices [k + 1]]
    if curr_layer <= layer_num:
        dict_layer_point[curr_layer] = []
        for each_point in index_point_list:
            related_point_indices = indptr[indices[each_point]:indices[each_point+1]]
            for i in related_point_indices:
                if i not in list_layer_point:
                    list_layer_point.append(i)
                    dict_layer_point[curr_layer].append(i)
        curr_layer += 1
        get_neighborSite_by_layerNum(delaunay_object,
                          dict_layer_point[curr_layer-1],
                          layer_num,
                          dict_layer_point = dict_layer_point,
                          list_layer_point = list_layer_point ,
                          curr_layer = curr_layer)
    return list_layer_point, dict_layer_point


"""******************************************************************************************************************************"""
"""经纬度计算距离函数"""
def distance_Calc(lon_a, lat_a, lon_b, lat_b):  # 根据经纬度计算距离
    '''
    根据经纬度计算距离
    :param lon_a:
    :param lat_a:
    :param lon_b:
    :param lat_b:
    :return:
    '''
    lon_a_rad = (lon_a / 180) * math.pi  # 换算为弧度
    lon_b_rad = (lon_b / 180) * math.pi
    lat_a_rad = (lat_a / 180) * math.pi
    lat_b_rad = (lat_b / 180) * math.pi
    if lon_a == lon_b and lat_a == lat_b:
        dis = 0
    else:
        dis = 6371393 * math.acos((math.sin(lat_a_rad)) * math.sin(lat_b_rad) + math.cos(
            lat_a_rad) * math.cos(lat_b_rad) * math.cos(lon_b_rad - lon_a_rad))  # 经纬度距离计算公式
    return dis


"""******************************************************************************************************************************"""
"""小区方位计算——单向相对位置"""
def SingCell_FaceTo(x_cell_1, y_cell_1, x_cell_2, y_cell_2, dir_cell_1, width):
    '''
    判断两个小区是否对打
    :param x_cell_1: 小区1long
    :param y_cell_1: 小区1lat
    :param x_cell_2: 小区2long
    :param y_cell_2: 小区2lat
    :param dir_cell_1: 小区1方位角
    :param width: 判断对打的边界角度
    :return:
    '''
    if x_cell_1 == x_cell_2 and y_cell_1 == y_cell_2:  # 经纬度都相同（共站址）的情况下算在范围内
        return True
    len_orient_vector = math.sqrt((x_cell_2 - x_cell_1) ** 2 + (y_cell_2 - y_cell_1) ** 2)
    orient_vector = ((x_cell_2 - x_cell_1),(y_cell_2 - y_cell_1))
    # print("\t\t"+str(orient_vector))

    azimuth_vector = (math.cos((-dir_cell_1+90)/180*math.pi),math.sin((-dir_cell_1+90)/180*math.pi))
    # print("\t\t",x_cell_1, y_cell_1, x_cell_2, y_cell_2)
    # print("\t\t"+str(azimuth_vector))
    # print("\t\t" + str(dir_cell_1))

    degree_rad = (orient_vector[0]*azimuth_vector[0]+orient_vector[1]*azimuth_vector[1])/len_orient_vector
    degree = math.acos(degree_rad)/math.pi*180

    if  degree < width:
        # print("\t"+str(degree)+'<'+str(width))
        return True
    else:
        # print("\t"+str(degree)+'>'+str(width))
        return False


"""******************************************************************************************************************************"""
"""小区方位计算——单向相对角度"""
def SingCell_FaceTo_degreeCalc(x_cell_1, y_cell_1, x_cell_2, y_cell_2, dir_cell_1):
    '''
    判断周边小区与本小区的连线相对于本小区的方位角的偏置角度
    :param x_cell_1: 本小区的long
    :param y_cell_1: 本小区的lat
    :param x_cell_2: 邻小区的long
    :param y_cell_2: 本小区的lat
    :param dir_cell_1: 本小区的方位角
    :return: 返回偏置角度
    '''
    if x_cell_1 == x_cell_2 and y_cell_1 == y_cell_2:  # 经纬度都相同（共站址）的情况下算在范围内
        return 0
    len_orient_vector = math.sqrt((x_cell_2 - x_cell_1) ** 2 + (y_cell_2 - y_cell_1) ** 2)
    orient_vector = ((x_cell_2 - x_cell_1),(y_cell_2 - y_cell_1))

    azimuth_vector = (math.cos((-dir_cell_1+90)/180*math.pi),math.sin((-dir_cell_1+90)/180*math.pi))

    degree_rad = (orient_vector[0]*azimuth_vector[0]+orient_vector[1]*azimuth_vector[1])/len_orient_vector
    degree = math.acos(degree_rad)/math.pi*180
    return degree


def gen_SiteAddr2Cell_dict(dict_cell):
    '''
    生成{站址:[小区索引列表]}的字典
    :param dict_cell: 小区字典
    :return:
    '''
    # 生成{(经度，纬度):[此经纬度上的小区编号列表]}列表
    dict_SiteAddr_to_Cell = {}
    len_cell = len(dict_cell.keys())
    for i in range(len_cell):
        addr_temp = (dict_cell[i].Long, dict_cell[i].Lat)
        if dict_SiteAddr_to_Cell.get(addr_temp, None):  # 向{(经纬度):[小区列表]}字典中添加小区
            dict_SiteAddr_to_Cell[addr_temp].append(i)
        else:
            dict_SiteAddr_to_Cell[addr_temp] = [i]
    return dict_SiteAddr_to_Cell

def get_coaddr_sitelist(dict_SiteAddr_to_Cell,dict_cell):
    '''
    获取共站址(经纬度相同)位置上面的所有邻小区
    :param dict_SiteAddr_to_Cell: {站址:[小区索引列表]}字典
    :param dict_cell: 小区字典
    :return:
    '''
    # 获取共站小区列表
    for each_siteAddr in dict_SiteAddr_to_Cell:
        for each_cellIndex in dict_SiteAddr_to_Cell[each_siteAddr]:
            dict_cell[each_cellIndex].get_CoSite_CellList(
                dict_SiteAddr_to_Cell[each_siteAddr][:])


def get_DelaunayNeigh(dict_SiteAddr_to_Cell,dict_cell,layerNum):
    '''
    生成德劳内三角形并回去周边layerNum层内的所有周边邻小区
    :param dict_SiteAddr_to_Cell:{站址:[小区索引列表]}字典
    :param dict_cell:小区字典
    :param layerNum:获取周边邻区的最大层数
    :return:
    '''
    # 获取指定层内的站点信息, 构建德劳内三角剖分
    dict_SiteAddr_to_Cell_keys = list(dict_SiteAddr_to_Cell.keys())
    matrix_SiteAddr = [list(x) for x in dict_SiteAddr_to_Cell_keys]
    Delaunay_SiteAddr = Delaunay(numpy.array(matrix_SiteAddr))
    print('Calculating Delaunay connecting relation...')

    for eachIndex, each_siteAddr in enumerate(dict_SiteAddr_to_Cell_keys):
        ArroundSiteIndexList, ArroundSiteIndexDict = get_neighborSite_by_layerNum(
            delaunay_object=Delaunay_SiteAddr,
            index_point_list=[eachIndex],
            layer_num=layerNum,
            dict_layer_point={},
            list_layer_point=[eachIndex])
        ArroundSiteAddrList = [dict_SiteAddr_to_Cell_keys[x] for x in ArroundSiteIndexList]
        ArroundSiteAddrDict = {x: [dict_SiteAddr_to_Cell_keys[y] for y in ArroundSiteIndexDict[x]] for x in
                               ArroundSiteIndexDict}

        for eachcell_onSite in dict_SiteAddr_to_Cell[each_siteAddr]:
            dict_cell[eachcell_onSite].getArroundSiteCellList(ArroundSiteAddrList)
            dict_cell[eachcell_onSite].getArroundSiteCellDict(ArroundSiteAddrDict)
            dict_cell[eachcell_onSite].getArroundCellDict(dict_cell, dict_SiteAddr_to_Cell)
    print('Finished Calculating Delaunay Connecting Relation.')






































