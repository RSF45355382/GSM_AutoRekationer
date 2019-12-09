from DataPreparation import Cell,layerNum, ta_percentage
from CommonFunction.ExcelReading import validate_DataFrameCol,validate_DataFrameColType,read_Excel
import tensorflow as tf
import pandas,os,copy
from shapely.geometry import Polygon
from DataTraining import preprocess,TRAINING_COL_LIST
from CommonFunction.Calculation import (SingCell_FaceTo_degreeCalc,
                                        gen_SiteAddr2Cell_dict,
                                        get_coaddr_sitelist,
                                        get_DelaunayNeigh)

model_save_path = r'.\model_save\relationmodel_withAngle_3layer_neigh_5e-3_8layersNeuralNetwork.h5'  # 需要导入的模型的路径
coltype_dict = {'BSCID': 'int32',  # 工参文件中各个列需要的数据类型
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
colname_list = ['BSCID', 'SiteID', 'CellID', 'CI', 'LAC', 'BSIC', 'BCCH', 'longitude', 'Latitude',
                    'Antenna Azimuth','SiteName', 'CellName', 'TCH', 'MA']# 工参文件中需要的列
filepath_SiteDB = r'D:\TF2.0_GsmRelation\阿尔邻区数据\Project Parameters-1-LAN1-201911251518(Site Type)_纯宏站.xls' # 工参文件路径
filepath_RelationPlan = r'D:\TF2.0_GsmRelation\阿尔邻区数据\RelationPlan.xlsx' # 待加邻区的小区列表文件, 模板参见附件[使用的是CNO的模板]
back_traininf_col_list = TRAINING_COL_LIST[:]
back_traininf_col_list[3],back_traininf_col_list[4] = back_traininf_col_list[4],back_traininf_col_list[3] # 反向邻区只需要将SFaceToN_Degree和NFaceToS_Degree倒置即可


def read_DataFramefromExcel(filepath,sheetname_list):
    '''
    从Excel中读取某个特定名称的sheet页,并且制定获取某些列
    :param filepath:  文件路径
    :param sheetname_list: sheet名称列表, 顺序获取, 只要有其中一个, 直接返回该sheet
    :return:
    '''
    data = read_Excel(filepath, sheetname_list)
    if not data.empty and validate_DataFrameCol(data, colname_list):
        check_result = validate_DataFrameColType(data, coltype_dict)
        if check_result == 'Data Validated, All columns type correct.':
            return data[colname_list]
        else:
            return pandas.DataFrame(columns=['Empty'])
    return data

def read_relationList(filepath_RelationPlan,SiteDB_DataFrame):
    '''
    读取待加邻区的小区列表文件
    :param filepath_RelationPlan: 待加邻区的小区列表文件路径
    :param SiteDB_DataFrame: 工参DataFrame
    :return: 待加邻区的小区信息DataFrame
    '''
    relation_DataFrame = read_DataFramefromExcel(filepath_RelationPlan, ['RelationAdditionPlan'])
    if not relation_DataFrame.empty:
        indices_list_relation = relation_DataFrame.index.tolist()
        for i in indices_list_relation:
            BSCID = int(relation_DataFrame.loc[i, 'BSCID'])
            SiteID = int(relation_DataFrame.loc[i, 'SiteID'])
            CellID = int(relation_DataFrame.loc[i, 'CellID'])
            orig_cell_in_SiteDB_indices = SiteDB_DataFrame.loc[(SiteDB_DataFrame['BSCID'] == BSCID)&
                                                            (SiteDB_DataFrame['SiteID'] == SiteID)&
                                                            (SiteDB_DataFrame['CellID'] == CellID)].index.tolist()
            if len(orig_cell_in_SiteDB_indices):
                SiteDB_DataFrame.drop(index=orig_cell_in_SiteDB_indices[0],inplace=True)
        return relation_DataFrame
    return relation_DataFrame

def read_ProjParam4Plan(filepath_SiteDB,filepath_RelationPlan):
    '''
    读取工参, 供邻区添加使用
    :param filepath_SiteDB:工参文件路径
    :param filepath_RelationPlan: 待加邻区的小区列表文件路径
    :return:
    '''
    dict_cell = {}
    dict_cell_add_neigh = {}

    output_dir = os.path.split(filepath_RelationPlan)[0]
    print('Reading Project Parameter...')
    table_projparams = read_DataFramefromExcel(filepath_SiteDB, ['Sheet1', 'ProjParam', 'sheet1', 'ProjectParameter', 'Project Parameters'])
    print('Finished reading Project Parameter file...')
    if not table_projparams.empty:
        table_projparams['need_relationadd'] = [0 for i in range(table_projparams.__len__())]
        print('Reading Relation...')
        relation_DataFrame = read_relationList(filepath_RelationPlan,table_projparams)
        print('Finished reading Relation...')
        if not relation_DataFrame.empty:
            relation_DataFrame['need_relationadd'] = [1 for i in range(relation_DataFrame.__len__())]

            final_col_list = colname_list + ['need_relationadd']
            # 条例DataFrame列的顺序
            table_projparams = table_projparams[final_col_list]
            relation_DataFrame = relation_DataFrame[final_col_list]
            data_total = pandas.concat([table_projparams,relation_DataFrame],axis=0)
            data_total.reset_index(drop=True, inplace=True)
            data_total.fillna('')
            indices_list = data_total.index.tolist()
            len_cell = len(indices_list)
            # print(data_total)

            for index in indices_list:

                BSCID = int(data_total.loc[index, 'BSCID'])
                SiteID = int(data_total.loc[index, 'SiteID'])
                CellID = int(data_total.loc[index, 'CellID'])
                CI = int(data_total.loc[index, 'CI'])
                BTS_name = str(data_total.loc[index, 'SiteName'])
                Cell_name = str(data_total.loc[index, 'CellName'])
                LAC = int(data_total.loc[index, 'LAC'])
                BSIC = int(data_total.loc[index, 'BSIC'])
                BCCH = int(data_total.loc[index, 'BCCH'])
                Long = float(data_total.loc[index, 'longitude'])
                Lat = float(data_total.loc[index, 'Latitude'])
                Antenna_azimuth = float(data_total.loc[index, 'Antenna Azimuth'])

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
                    output_dir=output_dir
                )
                cell.need_relationadd = int(data_total.loc[index, 'need_relationadd'])

                if cell.need_relationadd == 1:
                    dict_cell_add_neigh[index] = cell
                    print('{} planed cell got.'.format(len(dict_cell_add_neigh.keys())))

                dict_cell[index] = cell  # 实例化对象赋予小区字典中对应的小区序号,小区序号为Excel中小区所在行数-1
                if index % 500 == 0:
                    print('{}/{} cells reading finished.'.format(index, len_cell))

            # 生成{(经度，纬度):[此经纬度上的小区编号列表]}列表
            dict_SiteAddr_to_Cell = gen_SiteAddr2Cell_dict(dict_cell)

            # 获取共站小区列表
            get_coaddr_sitelist(dict_SiteAddr_to_Cell, dict_cell)

            # 获取指定层内的站点信息, 构建德劳内三角剖分
            get_DelaunayNeigh(dict_SiteAddr_to_Cell, dict_cell, layerNum)

            print('Start to calculate polygen for cells.')
            # 为每个小区读取TA信息, 如果没有TA信息则对应的字典对象为空
            for key, value in dict_cell.items():
                value.get_polygen_points(ta_percentage)
            print('Finished calculating polygen for cells.')

            del table_projparams
            return dict_cell, dict_SiteAddr_to_Cell,dict_cell_add_neigh
        else:
            print('Error occured when reading RelationPlan file.')
            return {}, {},{}
    else:
        print('Error occured when reading Project Parameter file.')
        return {}, {},{}

def predict_relations(model,neigh_infor_data,training_col_list,forw_direc):
    '''
    预测邻区是否添加, 正向反向都可以, 正向反向的区别在于training_col_list不同,相同的小区邻区DataFrame, SFaceToN_Degree和NFaceToS_Degree颠倒即可, 其他信息都一样
    :param model: 网络模型
    :param neigh_infor_data: 小区邻区DataFrame
    :param training_col_list: 获取预测数据的列名列表
    :param forw_direc: 正向邻区还是反向邻区
    :return: 扩展后的小区邻区DataFrame,多了邻区添加列
    '''
    predict_values = preprocess(neigh_infor_data, training_col_list=training_col_list, for_training=False)
    # 数据预处理
    predict_values = tf.data.Dataset.from_tensor_slices([predict_values])
    output_values = model.predict(predict_values)
    # 进行预测
    neigh_infor_data['Predict_result'] = output_values
    neigh_infor_data.sort_values(by=['Predict_result'], inplace=True, ascending=False)
    # 倒叙排序, 得分最高排前面

    # 经过经验判断并不是大于0的邻区就够了, 应该选用大约-1的, 需要稍微放开, 如果大于-1的邻区太多, 则只取其中24个邻区
    Predict_values_sorted = list(neigh_infor_data['Predict_result'])

    if forw_direc:
        newcol_name = 'Forward_relation'
    else:
        newcol_name = 'Backward_relation'

    Predict_values_sorted_trigger = [1 if x > -1 else 0 for x in Predict_values_sorted]
    total_cell_num_larger_minus_1 = sum(Predict_values_sorted_trigger)

    if total_cell_num_larger_minus_1 > 24:
        relation_num = 24
        relation_add_col = [1 if x < relation_num else 0 for x in range(len(Predict_values_sorted))]
    else:
        relation_num = total_cell_num_larger_minus_1
        relation_add_col = [1 if x < relation_num else 0 for x in range(len(Predict_values_sorted))]
    neigh_infor_data[newcol_name] = relation_add_col
    return neigh_infor_data


if __name__ == '__main__':
    predict_col_name = ['Dist_time',
                     'LayerNum',
                     'cover_coef',
                     'SFaceToN_Degree',
                     'NFaceToS_Degree',]
    print('Loading model...')
    model = tf.keras.models.load_model(model_save_path)
    print('Finished loading model.')
    print('Reading Project Parameter and Relation Plan...')
    dict_cell, dict_SiteAddr_to_Cell,dict_cell_add_neigh = read_ProjParam4Plan(filepath_SiteDB,filepath_RelationPlan)
    print('Finished reading Project Parameter and Relation Plan...')
    if dict_cell_add_neigh:
        for i in dict_cell_add_neigh:
            neigh_infor_data_orig = pandas.DataFrame(columns=['S_BSCID',
                                                        'S_SiteID',
                                                        'S_CellID',
                                                         'S_CellName',
                                                         'BSCID',
                                                         'SiteID',
                                                         'CellID',
                                                         'CellName',
                                                         'CI',
                                                         'LAC',
                                                         'BSIC',
                                                         'BCCH',
                                                         'Dist_time',
                                                         'LayerNum',
                                                         'cover_coef',
                                                         'SFaceToN_Degree',
                                                         'NFaceToS_Degree'])
            temp_cell = dict_cell_add_neigh[i]
            arrd_celllist = temp_cell.arroundCellDict
            # 生成周边邻区对信息
            for each_layer in arrd_celllist:
                for each_cell in arrd_celllist[each_layer]:
                    # 生成主小区-邻小区对的信息DataFrame
                    neigh_index = each_cell[0]
                    neigh_index_dist = each_cell[1]
                    dist_time = each_cell[1]/temp_cell.min_dis

                    polygen_S = Polygon(temp_cell.polyg_points_gis)
                    polygen_N = Polygon(dict_cell[neigh_index].polyg_points_gis)
                    cover_avg = polygen_S & polygen_N
                    cover_coef = cover_avg.area / min(polygen_S.area, polygen_N.area)
                    SFaceToN_Degree = SingCell_FaceTo_degreeCalc(temp_cell.Long,
                                                                 temp_cell.Lat,
                                                                 dict_cell[neigh_index].Long,
                                                                 dict_cell[neigh_index].Lat,
                                                                 temp_cell.Antenna_azimuth)
                    NFaceToS_Degree = SingCell_FaceTo_degreeCalc(dict_cell[neigh_index].Long,
                                                                 dict_cell[neigh_index].Lat,
                                                                 temp_cell.Long,
                                                                 temp_cell.Lat,
                                                                 dict_cell[neigh_index].Antenna_azimuth)
                    neigh_infor_data_orig.loc[neigh_infor_data_orig.__len__()] = [
                                                                        temp_cell.BSCID,
                                                                        temp_cell.SiteID,
                                                                        temp_cell.CellID,
                                                                        temp_cell.Cell_name,
                                                                        dict_cell[neigh_index].BSCID,
                                                                        dict_cell[neigh_index].SiteID,
                                                                        dict_cell[neigh_index].CellID,
                                                                        dict_cell[neigh_index].Cell_name,
                                                                        dict_cell[neigh_index].CI,
                                                                        dict_cell[neigh_index].LAC,
                                                                        dict_cell[neigh_index].BSIC,
                                                                        dict_cell[neigh_index].BCCH,
                                                                        dist_time,
                                                                        each_layer,
                                                                        cover_coef,
                                                                        SFaceToN_Degree,
                                                                        NFaceToS_Degree
                                                                        ]
            # 正向邻区预测
            neigh_infor_data_forw = copy.deepcopy(neigh_infor_data_orig)
            neigh_infor_data_forw = predict_relations(model, neigh_infor_data_forw, TRAINING_COL_LIST, forw_direc = True)

            dict_cell_add_neigh[i].Forw_RelationResult = neigh_infor_data_forw


            # 反向邻区预测
            neigh_infor_data_back = copy.deepcopy(neigh_infor_data_orig)
            neigh_infor_data_back = predict_relations(model, neigh_infor_data_back, back_traininf_col_list, forw_direc=False)

            dict_cell_add_neigh[i].Back_RelationResult = neigh_infor_data_back
        for i in dict_cell_add_neigh:
            # 输出邻区DataFrame, 暂时不做可视化处理
            dict_cell_add_neigh[i].Forw_RelationResult.to_csv(dict_cell_add_neigh[i].relation_resultpath)
            dict_cell_add_neigh[i].Back_RelationResult.to_csv(dict_cell_add_neigh[i].backrelation_resultpath)












