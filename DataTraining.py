import tensorflow as tf
from tensorflow import keras
import numpy as np
from CommonFunction.ExcelReading import validate_DataFrameColType,read_Csv
batchsz = 10000

trainging_data_size = 400000  # 训练集数量
learning_rate = 5e-3 # 模型学习率
TRAINING_COL_LIST = ['Dist_time',   # 训练过程中需要获取的列的数量以及顺序(顺序也很重要)
                     'LayerNum',
                     'cover_coef',
                     'SFaceToN_Degree',
                     'NFaceToS_Degree',
                     'relation_all_bin']
coltype_dict = {'Dist_time':'float',    # 对数据各列的数据类型要求
                'LayerNum':'float',
                'cover_coef':'float',
                'SFaceToN_Degree':'float',
                'NFaceToS_Degree': 'float',
                'relation_all_bin':'int'}
input_datapath = r'D:\TF2.0_GsmRelation\阿尔邻区数据\NeighbourPair_total_angle_45_add_covercoef_new.csv' # 训练数据输入文件路径

model_save_path = r'.\model_save\relationmodel_withAngle_3layer_neigh_5e-3_8layersNeuralNetwork.h5' # 训练之后模型保存路径
# np.random.seed(234)


def buildModel():
    '''
    生成一个8层神经网络, 并通过dropout层来防止过拟合
    :return:
    '''
    # 生成神经网络模型, 共8层
    model = keras.Sequential([
        keras.layers.Dense(1024, activation=tf.nn.relu), # 8层
        keras.layers.Dropout(0.3),
        keras.layers.Dense(512, activation=tf.nn.relu), # 7层
        keras.layers.Dropout(0.3),
        keras.layers.Dense(256, activation=tf.nn.relu), # 6层
        keras.layers.Dropout(0.3),
        keras.layers.Dense(128,activation = tf.nn.relu),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation=tf.nn.relu),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(32, activation=tf.nn.relu),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(16,activation = tf.nn.relu),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(1)
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),  # 1e-4效果比较好
                  loss=tf.losses.BinaryCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    return model

def preprocess(DataFrame,training_col_list,for_training):
    '''
    数据预处理, 训练数据会有label列,但是预测时候没有label列
    :param DataFrame: 数据DataFrame(pandas从csv所读取的DataFrame)
    :param for_training: 是否训练的标志,True或者False
    :return:
    '''
    DataFrame['SFaceToN_Degree'] = DataFrame['SFaceToN_Degree']/180.
    DataFrame['NFaceToS_Degree'] = DataFrame['NFaceToS_Degree'] / 180.
    # 归一化处理
    # DataFrame['Dist_time'] = DataFrame['Dist_time']/max(list(DataFrame['Dist_time']))
    # DataFrame['LayerNum'] = DataFrame['LayerNum'] / max(list(DataFrame['LayerNum']))
    # 经过测试, Dist_time和LayerNum不适合进行归一化处理


    if for_training:
        data = DataFrame[training_col_list].values
        # DataFrame列顺序调整,并取其中的numpy值
        np.random.shuffle(data)
        # 对数据进行打乱
    else:
        data = DataFrame[training_col_list[:-1]].values
        # DataFrame列顺序调整,并取其中的numpy值
        # 预测数据不进行打乱
    return data.astype(np.float)


if __name__ == '__main__':
    DataFrame = read_Csv(input_datapath)
    check_result = validate_DataFrameColType(DataFrame,coltype_dict)
    print(check_result)
    if check_result == 'Data Validated, All columns type correct.':
        data = preprocess(DataFrame,training_col_list = TRAINING_COL_LIST,for_training=True)
        print(data.shape)

        train_data = data[:trainging_data_size,:]
        # 获取训练集数据
        train_x, train_y = train_data[:,:-1],train_data[:,-1]


        test_data = data[trainging_data_size:,:]
        # 获取检测集数据
        test_x, test_y = test_data[:, :-1], test_data[:, -1]

        print(train_x.shape, train_y.shape)
        print(test_x.shape, test_y.shape)
        # (202893, 5) (202893,)
        train_db = tf.data.Dataset.from_tensor_slices((train_x,train_y))
        train_db = train_db.batch(batchsz)

        model = buildModel()
        model.fit(train_db,epochs=150)

        loss,accuracy = model.evaluate(test_x,test_y)

        model.save(model_save_path)

        imported_model = keras.models.load_model(model_save_path)
        # 保存150次训练之后的模型, 输入数据很多, 发现不用担心过拟合的情况, 所以直接保存最终150轮训练之后的模型

        loss, accuracy = imported_model.evaluate(test_x, test_y)
    else:
        print('Data not correct. please check again.')
