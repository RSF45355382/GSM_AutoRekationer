import sqlite3

class MyDB():
    def __init__(self,path):
        '''
        连接数据库, 获取锚点
        :param path: 数据库本地路径
        '''
        self.db = sqlite3.connect(path,isolation_level=None)
        # connect对象也有execute方法, 这个方案其实是间接的调用了cursor的execute方法, 所以,无论使用cursor的execute方法
        # 还是使用connect的execute方法, 效果都是一样的.
        self.curs = self.db.cursor()

    def createTable(self,tablename,dict_coltype):
        '''
        创建表
        :param tablename: 表名
        :param dict_coltype:{COL_NAME:[TYPE, ADDITIONAL_INFOR]}格式的字典
            这里ADDITIONAL_INFOR用于指定主键以及非NULL等信息
        :return: 无
        '''
        keys_str = ''
        for each_key,val in dict_coltype.items():
            keys_str += each_key + '\t' + '\t'.join(val) + ',\n'
        creating_str = 'CREATE TABLE {} ({});'.format(tablename,keys_str)
        self.db.execute(creating_str)
        self.db.commit()

    def delTable(self,tablename):
        '''
        删除表
        :param tablename: 表名
        :return: 无
        '''
        self.db.execute('DROP TABLE {};'.format(tablename))
        self.db.commit()

    def addCol(self,tablename,colname, coltype):
        '''
        添加一列
        :param tablename: 表名
        :param colname: 添加的列名
        :param coltype: 列的数据类型
        :return: 无
        '''
        self.db.execute('ALTER TABLE {} ADD COLUMN {} {}'.format(tablename,colname,coltype))
        self.db.commit()

    def selectItem(self,tablename,col_list,condition):
        '''
        SELECT功能
        :param tablename: 表名
        :param col_list: 需要获取的列名的list
        :param condition: WHERE选择语句,可以加OSDER BY
        :return: 二维数组个数的数据
        '''
        return list(self.db.execute('SELECT {} FROM {} {};'.format(', '.join(col_list),tablename,condition)))


    def update(self,tablename,update_dict,condition):
        '''
        更新数据库,本函数是单次更新,效率较低, 推荐使用batch_update函数
        :param tablename: 表名
        :param update_dict: {COL_NAME:VALUE}格式的更新值的字典, 可以同时更新多个值
        :param condition: 更新的位置的WHERE语句
        :return: 无
        '''
        set_str = ''
        for key,val in update_dict.items():
            set_str += '='.join((str(key),str(val)))
            set_str += ','

        set_str = set_str[:-1]
        self.db.execute('UPDATE {} SET {} {};'.format(tablename,set_str,condition))
        self.db.commit()

    def batchUpdate(self,tablename, update_dict):
        '''
        批量更新数据可, 使用事务功能完成更新,效率较高, 一次更新多个条目
        :param tablename: 表名
        :param update_dict: {'WHERE语句':update_str,...}格式的更新字典
        update_str是已经组织好的'SITE=3,INDEX_POINT=4,...'这样的sql语句
        :return: 无
        '''
        self.db.execute('BEGIN TRANSACTION;')
        for each_condition,each_updatestr in update_dict.items():
            self.db.execute('UPDATE {} SET {} {};'.format(tablename,each_updatestr,each_condition))
        self.db.execute('COMMIT;')


    def batchInsertItem(self,tablename,values_list):
        '''
        批量插入条目
        :param tablename:
        :param value_list:[(values,...),...]
        :return: 无
        '''
        self.db.execute('BEGIN TRANSACTION;')
        for each_item in values_list:
            insret_str = 'INSERT INTO {} VALUES {};'.format(tablename,tuple(each_item))
            self.db.execute(insret_str)
        self.db.execute('COMMIT;')

    def batchDeleteItem(self,tablename,conditions_list):
        '''
        批量删除条目
        :param tablename: 表名
        :param conditions_list: 删除的条件s列表, 如果条件是空,则全部删除
        :return: 无
        '''
        self.db.execute('BEGIN TRANSACTION;')
        for each_condition in conditions_list:
            del_str = 'DELETE FROM {} {}'.format(tablename,each_condition)
            self.db.execute(del_str)
        self.db.execute('COMMIT;')
