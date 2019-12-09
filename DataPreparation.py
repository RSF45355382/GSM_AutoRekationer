import pandas, os, statistics
from CommonFunction.ExcelReading import validate_DataFrameCol,validate_DataFrameColType,read_Excel
from covTA_statistics import main_getTAcov
from shapely.geometry import Polygon
from CommonFunction.Calculation import (calc_polyg_points,
                                        distance_Calc,
                                        SingCell_FaceTo_degreeCalc,
                                        gen_SiteAddr2Cell_dict,
                                        get_coaddr_sitelist,
                                        get_DelaunayNeigh,
                                        SingCell_FaceTo)

# 获取周边邻区最大层数
layerNum = 3    # 最大邻区层数
dis_time = 8  # 周边邻站举例大于第一层邻区的中位数举例的若干倍数后, 认为是德劳内三角剖分时候产生的边界邻边, 对此类邻边进行排除, 这个参数表征这个倍数
file_size = 70000 # 生成的每个训练数据文件最多size
percentage_list = [0.98]  # 计算TA边界的若干TA样本包含百分比, 每个包含百分比对应一个边界, 这个值可以值选用其中一个, 此处为了分析方便, 所以取了多个百分比
ta_percentage = 0.98 # 最终选用小区覆盖范围时候所用的TA样本包含百分比
POLYG_DIST4ANGLE_LIST = [(-80,0.25),   # 刻画小区覆盖图的数据, 每个元素是(想醉方向角的角度偏执, TA最大边界的倍数)
                         (-70,0.4),
                         (-60,0.5),
                         (-50,0.75),
                         (-40,1.1),
                         (-32.5,1.25),
                         (-25.5,1.3),
                         (-17,1.4),
                         (-10,1.42),
                         (-5,1.43),
                         (0,1.45),
                         (5,1.43),
                         (10,1.42),
                         (17,1.4),
                         (25.5,1.3),
                         (32.5,1.25),
                         (40,1.1),
                         (50,0.75),
                         (60,0.5),
                         (70,0.4),
                         (80,0.25)]

class Cell():
    # 频率核查需要小区属性：小区名，站名，CI,CellID，SiteID，BSCID，BSIC，BCCH,TCH序列，MAList，经纬度，方位角（缺省方位角的置空），
    EARTH_RADIUS = 6371393  # 地球半径,单位米

    def __init__(
            self,  # 所有参数均是str输入
            BSCID=None,
            SiteID=None,
            CellID=None,
            CI=None,
            BTS_name=None,
            Cell_name=None,
            BSIC=None,
            BCCH=None,
            Long=None,
            Lat=None,
            Antenna_azimuth=None,
            LAC=None,
            index=None,
            output_dir = ''):  # 度数格式

        # 初始化赋值小区各个属性
        self.BSCID = BSCID
        self.SiteID = SiteID
        self.index = index
        self.CI = CI
        self.CellID = CellID
        self.BTS_name = BTS_name
        self.Cell_name = Cell_name
        self.BCCH = [BCCH]  # BCCH也整理成list格式的,与TCH统一
        self.BSIC = BSIC

        self.Long = Long
        self.Lat = Lat
        # self.x = 6371393*math.cos(self.Lat/180*math.pi)*math.cos(self.Long/180*math.pi)
        # self.y = 6371393*math.cos(self.Lat/180*math.pi)*math.sin(self.Long/180*math.pi)
        self.Antenna_azimuth = Antenna_azimuth
        self.LAC = LAC
        self.output_dir = output_dir
        self.relation_resultpath = output_dir + '\\relation_{}.csv'.format(self.Cell_name)
        self.maxTA = {}
        self.backrelation_resultpath = output_dir + '\\backrelation_{}.csv'.format(self.Cell_name)

    def readTA(self,TA_DataFrame,percentage):
        kpi_item = TA_DataFrame.loc[(TA_DataFrame['ME'] == self.BSCID)&
                                    (TA_DataFrame['SITE'] == self.SiteID)&
                                    (TA_DataFrame['BTS'] == self.CellID)].index.tolist()
        if len(kpi_item):
            self.maxTA[percentage] = TA_DataFrame.loc[kpi_item[0],'maxTA for {}'.format(percentage)]
        # print(self.maxTA)

    def calcAvgNeighSiteDist(self,ta_percentage):
        if self.maxTA.get(ta_percentage,None):
            self.avg_neighsite_dist_gis = self.maxTA[ta_percentage]*550 / 111000  # 地理上经纬度1度大约为111km
            # print(self.avg_neighsite_dist)
        else:
            # 计算正向方向平均站间距
            calc_avgdist = []
            for each_addr in self.arroundSiteList:
                if SingCell_FaceTo(self.Long, self.Lat, each_addr[0], each_addr[1], self.Antenna_azimuth,60):
                    # 检测正向对打邻站用60度(左右各60度),相当于120宽度范围
                    dist = distance_Calc(self.Long, self.Lat, each_addr[0], each_addr[1])
                    calc_avgdist.append(dist)
            calc_avgdist.sort()
            if len(calc_avgdist) >= 3:
                calc_avg_dis_list = calc_avgdist[:3]
            elif len(calc_avgdist):
                calc_avg_dis_list = calc_avgdist
            else:
                calc_avg_dis_list = [4000]
                # 没有对打小区的时候取4km为覆盖距离
            self.avg_neighsite_dist_gis = statistics.median(calc_avg_dis_list)/111000  # 经纬度1度代表111km

    # 获取与本小区共站的小区索引列表【列表内为小区索引】
    def get_CoSite_CellList(self, CoSite_CellList):
        self.CoSite_CellList = CoSite_CellList
        self.CoSite_CellList.remove(self.index)

    def getArroundSiteCellList(self, ArroundSiteAddrList):
        if (self.Long, self.Lat) in ArroundSiteAddrList:
            ArroundSiteAddrList.remove((self.Long, self.Lat))
        self.arroundSiteList = ArroundSiteAddrList

    def getArroundSiteCellDict(self, ArroundSiteAddrDict):
        # 剔除本站在字典中位置(三角剖分有时候会获取到本站的位置)
        for each in ArroundSiteAddrDict:
            if (self.Long, self.Lat) in ArroundSiteAddrDict[each]:
                ArroundSiteAddrDict[each].remove((self.Long, self.Lat))
        self.arroundSiteDict = ArroundSiteAddrDict
        print('For Cell (ID){}, Before:'.format(self.index),len(self.arroundSiteDict[1]),len(self.arroundSiteDict[2]))
        self.filterout_farAwaySites()
        print('\tFor Cell (ID){}, After:'.format(self.index),len(self.arroundSiteDict[1]),len(self.arroundSiteDict[2]))

    def getArroundCellDict(self,dict_cell, dict_SiteAddr_to_Cell):
        self.arroundCellDict = {x:[] for x in self.arroundSiteDict}
        self.addCositeCellDict()
        for each_layer in self.arroundSiteDict:
            for each_site in self.arroundSiteDict[each_layer]:
                tmp_cell_list = dict_SiteAddr_to_Cell[each_site]
                for each_cell_index in tmp_cell_list:
                    dist_temp = distance_Calc(self.Long,
                                              self.Lat,
                                              dict_cell[each_cell_index].Long,
                                              dict_cell[each_cell_index].Lat)
                    self.arroundCellDict[each_layer].append([each_cell_index,dist_temp])

    def addCositeCellDict(self):
        self.arroundCellDict[0] = []
        for each_cell in self.CoSite_CellList:
            self.arroundCellDict[0].append([each_cell, 0])

    def filterout_farAwaySites(self):
        # 计算1层站点的距离中位数
        dis_1layer = []
        for each_site_1layer in self.arroundSiteDict[1]:
            dis_1layer.append(distance_Calc(self.Long, self.Lat, each_site_1layer[0], each_site_1layer[1]))
        self.median_dis = statistics.median(dis_1layer)
        if self.median_dis > 4000:
            self.median_dis = 4000
        self.min_dis = min(dis_1layer)
        new_arroundSiteDict = {x:self.arroundSiteDict[x] for x in self.arroundSiteDict}
        for each_layer in self.arroundSiteDict:
            for each_site in self.arroundSiteDict[each_layer]:
                temp_dis = distance_Calc(self.Long, self.Lat, each_site[0], each_site[1])
                if  temp_dis> self.median_dis*dis_time:
                    new_arroundSiteDict[each_layer].remove(each_site)
                    print('For Cell (ID){}, Addr removed due to distance too large:{} > {} * {}'.format(self.index,temp_dis,self.median_dis,dis_time))
        self.arroundSiteDict = new_arroundSiteDict

    def calc_polygen_points(self):
        # 计算小区覆盖区域polygen点坐标序列
        self.polygen_dist4angle_list = POLYG_DIST4ANGLE_LIST[:]
        # self.polyg_points = calc_polyg_points(self.x,self.y,self.Antenna_azimuth,self.avg_neighsite_dist,self.polygen_dist4angle_list)
        self.polyg_points_gis = calc_polyg_points(self.Long, self.Lat, self.Antenna_azimuth, self.avg_neighsite_dist_gis,self.polygen_dist4angle_list)

    def get_polygen_points(self,ta_percentage):
        # 获取小区覆盖区域polygen点坐标序列
        self.calcAvgNeighSiteDist(ta_percentage)
        self.calc_polygen_points()


"""******************************************************************************************************************************"""
"""从DataFrame中读取Cell信息"""
def read_CellInfor(table_projparams,output_dir, layerNum):  # 从Excel读取所有站点信息
    '''
    读取小区信息,并且获取共站址站点信息, 构造德劳内三角剖分, 获取周边layerNum层内的邻站和邻小区
    :param table_projparams: 工参DataFrame
    :param output_dir: 输出文件路径
    :param layerNum: 最大周边邻区层数
    :return: 返回字典dict_cell, dict_SiteAddr_to_Cell, dict_cell是{小区索引:小区对象...}, dict_SiteAddr_to_Cell是{(long,lat):[这个地理位置上的所有小区索引的列表]}
    '''
    dict_cell = {}  # 总的小区集合[字典格式,小区序号：小区实例]，序号为Excel中小区所在行数-1

    table_projparams_indexList = table_projparams.index.tolist()
    len_cell = len(table_projparams_indexList)
    # 按照工参顺序读取小区信息
    for index in table_projparams_indexList:

        BSCID = int(table_projparams.loc[index, 'BSCID'])
        SiteID = int(table_projparams.loc[index, 'SiteID'])
        CellID = int(table_projparams.loc[index, 'CellID'])
        CI = int(table_projparams.loc[index, 'CI'])
        BTS_name = str(table_projparams.loc[index, 'SiteName'])
        Cell_name = str(table_projparams.loc[index, 'CellName'])
        LAC = int(table_projparams.loc[index, 'LAC'])
        BSIC = int(table_projparams.loc[index, 'BSIC'])
        BCCH = int(table_projparams.loc[index, 'BCCH'])
        Long = float(table_projparams.loc[index, 'longitude'])
        Lat = float(table_projparams.loc[index, 'Latitude'])
        Antenna_azimuth = float(table_projparams.loc[index, 'Antenna Azimuth'])

        cell = Cell(  # 类实例化，传入各个参数，生成这些实例
            BSCID=BSCID,
            SiteID=SiteID,
            CellID=CellID,
            CI=CI,
            BTS_name=BTS_name,
            Cell_name=Cell_name,
            LAC=LAC,
            BSIC=BSIC,
            BCCH=BCCH,
            Long=Long,
            Lat=Lat,
            Antenna_azimuth=Antenna_azimuth,
            index=index,
            output_dir = output_dir
        )
        dict_cell[index] = cell  # 实例化对象赋予小区字典中对应的小区序号,小区序号为Excel中小区所在行数-1
        if index%500 == 0:
            print('{}/{} cells reading finished.'.format(index,len_cell))

    # 生成{(经度，纬度):[此经纬度上的小区编号列表]}列表
    dict_SiteAddr_to_Cell = gen_SiteAddr2Cell_dict(dict_cell)

    # 获取共站小区列表
    get_coaddr_sitelist(dict_SiteAddr_to_Cell,dict_cell)


    # 获取指定层内的站点信息, 构建德劳内三角剖分
    get_DelaunayNeigh(dict_SiteAddr_to_Cell, dict_cell, layerNum)

    del table_projparams
    return dict_cell, dict_SiteAddr_to_Cell


"""******************************************************************************************************************************"""
"""从Excel文件中读取数据并格式化函数"""
def read_ProjParam(filename, layerNum,ta_percentage):  # 从Excel读取所有站点信息
    '''
    读取工参以及TA指标
    :param filename:工参文件路径, 内含TA信息页
    :param layerNum:最大周边邻区层数
    :param ta_percentage: 计算最大TA边界是需要覆盖xx%的TA样本数时候, 这个值就代表这个百分比
    :return:
    '''
    coltype_dict = {'BSCID': 'int32',
                    'SiteID': 'int32',
                    'CellID': 'int32',
                    'CI': 'int32',
                    'LAC': 'int32',
                    'BSIC': 'int32',
                    'BCCH': 'int32',
                    'longitude': 'float64',
                    'Latitude': 'float64',
                    'Antenna Azimuth': 'float64',
                    }
    colname_list = ['BSCID','SiteID','CellID','CI','LAC','BSIC','BCCH','longitude','Latitude','Antenna Azimuth',\
                    'SiteName','CellName','TCH','MA']
    output_dir = os.path.split(filename)[0]
    print('Start to read Project Parameter table.')
    table_projparams = read_Excel(filename, ['Sheet1','ProjParam','sheet1','ProjectParameter','Project Parameters'])
    print('Finished reading Project Parameter table.')
    print('Start to read TA table.')
    ta_kpi_table = main_getTAcov(filename, ['TA_KPI'], percentage_list)
    print('Finished reading TA table.')
    if not table_projparams.empty and validate_DataFrameCol(table_projparams,colname_list):
        table_projparams.fillna('', inplace=True)
        check_result = validate_DataFrameColType(table_projparams,coltype_dict)
        print(check_result)
        if check_result == 'Data Validated, All columns type correct.':
            dict_cell, dict_SiteAddr_to_Cell = \
                read_CellInfor(table_projparams,output_dir, layerNum)
        else:
            print('Error occured when tranforming data type for ProjectParameter DataFrame.')
            dict_cell, dict_SiteAddr_to_Cell = {},{}
    else:
        print('Error occured when reading ProjectParameter DataFrame or vadilating columns.')
        dict_cell, dict_SiteAddr_to_Cell = {}, {}

    print('Start to read TA for cells.')
    # 读取TA信息
    if not ta_kpi_table.empty:
        for key, value in dict_cell.items():
            for percentage in percentage_list:
                value.readTA(ta_kpi_table, percentage)
    print('Finished reading TA for cells.')

    print('Start to calculate polygen for cells.')
    for key, value in dict_cell.items():
        value.get_polygen_points(ta_percentage)
    print('Finished calculating polygen for cells.')

    return dict_cell, dict_SiteAddr_to_Cell


def gen_excel(dict_cell,output_dir):
    '''
    生成训练数据
    :param dict_cell: 小区字典dict_cell是{小区索引:小区对象...}
    :param output_dir: 输出文件路径
    :return: None
    '''
    DataFrame_relation = pandas.DataFrame(columns=['S_cellname','N_cellname','relation_name','Dist','Dist_time','LayerNum', 'S_Long','S_Lat',
                                                   'S_Azimuth','N_Long','N_Lat','N_Azimuth','cover_coef',
                                                   'SFaceToN_Degree','NFaceToS_Degree'])
    index_file = 0
    for index,cell in dict_cell.items():
        for each_layer in cell.arroundCellDict:
            for each_neig in cell.arroundCellDict[each_layer]:
                index_neigcell = each_neig[0]
                dist_temp = each_neig[1]
                dist_time_temp = each_neig[1]/cell.min_dis

                polygen_S = Polygon(cell.polyg_points_gis)
                polygen_N = Polygon(dict_cell[index_neigcell].polyg_points_gis)
                cover_avg = polygen_S & polygen_N
                #交叠覆盖区域面积计算
                cover_coef = cover_avg.area / min(polygen_S.area, polygen_N.area)
                #交叠覆盖系数

                SFaceToN_Degree = SingCell_FaceTo_degreeCalc(cell.Long,
                                            cell.Lat,
                                            dict_cell[index_neigcell].Long,
                                            dict_cell[index_neigcell].Lat,
                                            cell.Antenna_azimuth)
                NFaceToS_Degree = SingCell_FaceTo_degreeCalc(dict_cell[index_neigcell].Long,
                                                            dict_cell[index_neigcell].Lat,
                                                             cell.Long,
                                                            cell.Lat,
                                                            dict_cell[index_neigcell].Antenna_azimuth)
                relation_name = '=>'.join([cell.Cell_name,dict_cell[index_neigcell].Cell_name])
                DataFrame_relation.loc[DataFrame_relation.__len__()] = [cell.Cell_name,
                                                                        dict_cell[index_neigcell].Cell_name,
                                                                        relation_name,
                                                                        dist_temp,
                                                                        dist_time_temp,
                                                                        each_layer,
                                                                        cell.Long,
                                                                        cell.Lat,
                                                                        cell.Antenna_azimuth,
                                                                        dict_cell[index_neigcell].Long,
                                                                        dict_cell[index_neigcell].Lat,
                                                                        dict_cell[index_neigcell].Antenna_azimuth,
                                                                        cover_coef,
                                                                        SFaceToN_Degree,
                                                                        NFaceToS_Degree]
        if index %100 == 0:
            print('{} Cell Relations Generating Finished.'.format(index))

        # 每当DataFrame长度查过7W时, 生成csv文件并清除DataFrame, 重新开始生成文件
        if DataFrame_relation.__len__() >= file_size:
            output_dir_temp = output_dir + r'\NeighbourPair_{}_batch_{}.csv'.format(index_file,file_size)
            DataFrame_relation.to_csv(output_dir_temp)
            print('Generated file {}.'.format(output_dir_temp))

            DataFrame_relation = pandas.DataFrame(columns=['S_cellname','N_cellname','relation_name','Dist','Dist_time','LayerNum', 'S_Long','S_Lat',
                                                   'S_Azimuth','N_Long','N_Lat','N_Azimuth','cover_coef',
                                                   'SFaceToN_Degree','NFaceToS_Degree'])
            index_file += 1
    output_dir_temp = output_dir + r'\NeighbourPair_{}_batch_{}.csv'.format(index_file,file_size)
    DataFrame_relation.to_csv(output_dir_temp)
    print('Generated file {}.'.format(output_dir_temp))
    # 为了加速生成文件速度, 本段代码生每70000条数据生成一个文件, 最终使用是讲义将所有文件合并后再统一读取
    print('Finished generating csv file.')

if __name__ == '__main__':
    filename = r'D:\TF2.0_GsmRelation\阿尔邻区数据\Project Parameters-1-LAN1-201911251518(Site Type)_纯宏站.xls'
    output_dir = os.path.dirname(filename)
    dict_cell, dict_SiteAddr_to_Cell = read_ProjParam(filename, layerNum,ta_percentage)
    gen_excel(dict_cell,output_dir)

















