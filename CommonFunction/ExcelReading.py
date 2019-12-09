import pandas

def read_Csv(filename):
    '''
    读取csv文件
    :param filename:文件路径
    :return:
    '''
    try:
        DataFrame = pandas.read_csv(filename)
    except Exception as e:
        print('Error occured when opening excel file: {}'.format(e))
        return pandas.DataFrame(columns=['Empty'])
    return DataFrame

def read_Excel(filename, sheetname_list):
    '''
    标准pandas读取Excel函数, 从filename路径读取sheetname_list中的任意一个sheet, 只要发现任意一个就返回
    打开文件失败或者没有sheetname,则返回空的DataFrame
    :param filename:  文件路径
    :param sheetname_list:  [可能的sheetname list]
    :return: DataFrame(打开文件失败或者没有sheetname,则返回空的DataFrame)
    '''
    try:
        DataFrame = pandas.ExcelFile(filename)
    except Exception as e:
        print('Error occured when opening excel file: {}'.format(e))
        return pandas.DataFrame(columns=['Empty'])

    DataFrame_sheetnames = DataFrame.sheet_names
    for each in sheetname_list:
        if each in DataFrame_sheetnames:
            return DataFrame.parse(each)
    print('No one sheet in {} Detected in file {}'.format(str(sheetname_list), filename))
    return pandas.DataFrame(columns=['Empty'])


def validate_DataFrameCol(DataFrame, colname_list):
    '''
    检验DataFrame中是否包含所需的所有column(按照colname来索引)
    :param DataFrame: 需要检验的DataFrame
    :param colname_list: [col_name...]格式的列表
    :return: 检查结果,布尔型
    '''
    col_names = DataFrame.columns
    for each in colname_list:
        if each not in col_names:
            print('Column {} Not Detected in DataFrame'.format(each))
            return False
    return True


def validate_DataFrameColType(DataFrame, coltype_dict):
    '''
    检验DataFrame中是否包含所需的所有column(按照colname来索引)
    :param DataFrame: 需要检验的DataFrame
    :param coltype_dict: {col_name:dtype}格式的字典
    :return: 检查结果的String
    '''
    for each_col, each_type in coltype_dict.items():
        try:
            DataFrame[each_col] = DataFrame[each_col].astype(each_type)
        except ValueError:
            'There are ValueError in "{}" Column. Data Type Should Be "{}". Please check.'.format(each_col, each_type)
            return 'There are ValueError in "{}" Column. Data Type Should Be "{}". Please check.'.format(each_col,
                                                                                                         each_type)
        except KeyError:
            return 'Column {} not detected.'.format(each_col)
    return 'Data Validated, All columns type correct.'


