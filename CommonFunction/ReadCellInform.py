import math

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
            TCH_list=None,
            MA_list=None,
            Long=None,
            Lat=None,
            Antenna_azimuth=None,
            LAC=None,
            index=None):  # 度数格式

        # 初始化赋值小区各个属性
        self.index = index
        self.CI = CI
        self.CellID = CellID
        self.BTS_name = BTS_name
        self.Cell_name = Cell_name
        self.BCCH = [BCCH]  # BCCH也整理成list格式的,与TCH统一

        self.Long = Long
        self.Lat = Lat
        self.x = 6371393*math.cos(self.Lat/180*math.pi)*math.cos(self.Long/180*math.pi)
        self.y = 6371393*math.cos(self.Lat/180*math.pi)*math.sin(self.Long/180*math.pi)
        self.Antenna_azimuth = Antenna_azimuth
        self.LAC = LAC
        self.BSCID = BSCID
        self.SiteID = SiteID
        self.BSIC = BSIC

        self.TCH_list = read_freqlist_from_str(TCH_list, Cell_name)
        if len(MA_list):
            if '/' in MA_list:
                sep_malist = MA_list.split('/')
                self.MA_list = [read_freqlist_from_str(sep_malist[0], Cell_name),
                                read_freqlist_from_str(sep_malist[1], Cell_name)]
            else:
                self.MA_list = [read_freqlist_from_str(MA_list, Cell_name),[]]
        else:
            self.MA_list = [[],[]]

        if BSIC < 10:  # 计算NCC和BCC
            self.NCC = 0
            self.BCC = int(BSIC)
        else:
            self.NCC = int(BSIC / 10)
            self.BCC = int(BSIC % 10)

"""******************************************************************************************************************************"""
'''从字符串中读取频点信息(CNO工参格式, 分隔符支持;和,)'''
def read_freqlist_from_str(freqstr,cellname):
    normal_freq_letter = [str(x) for x in range(10)] + [';',',','.']
    for each_letter in freqstr:
        if each_letter not in normal_freq_letter:
            print('Frequency format not right in cell: {}'.format(cellname))
            return []
    if freqstr:
        if ';' in freqstr:
            freqlist = freqstr.split(';')
            # 去除异常值
            for each_sep in [';',',','.']:
                while each_sep in freqlist:
                    freqlist.remove(each_sep)
            return [int(float(x)) for x in freqlist]
        elif ',' in freqstr:
            freqlist = freqstr.split(',')
            # 去除异常值
            for each_sep in [';', ',', '.']:
                while each_sep in freqlist:
                    freqlist.remove(each_sep)
            return [int(float(x)) for x in freqlist]
        else:
            if freqstr in ['.','..','...','....','.....','......','.......']:
                return []
            else:
                freqlist = [freqstr]
            return [int(float(x)) for x in freqlist]
    else:
        return []

"""******************************************************************************************************************************"""
'''正常读取小区信息'''
def readCellInfor(table_projparams):
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
        # 如果检查项不涉及TCH或MAlist,则不读入TCH信息，节省内存
        TCH_list = str(table_projparams.loc[index, 'TCH'])
        MA_list = str(table_projparams.loc[index, 'MA'])

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
            TCH_list=TCH_list,
            MA_list=MA_list,
            Long=Long,
            Lat=Lat,
            Antenna_azimuth=Antenna_azimuth,
            index=index
        )
        dict_cell[index] = cell  # 实例化对象赋予小区字典中对应的小区序号,小区序号为Excel中小区所在行数-1

        if index % 500 == 0:
            print('{}/{} cells reading finished.'.format(index, len_cell))
    return dict_cell