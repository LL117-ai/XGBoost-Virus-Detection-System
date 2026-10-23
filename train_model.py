import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from joblib import dump

# 1. 读取数据 (确保文件名和路径一致)
file_path = 'TUANDROMD.csv'
print("正在读取数据...")
df = pd.read_csv(file_path)

# 2. 数据清洗（处理标签）
y = df.iloc[:, -1]  # 最后一列是标签
X = df.iloc[:, :-1] # 前面所有列是特征

# 筛选仅包含 malware 和 goodware 的样本
df_filtered = df[(y == 'malware') | (y == 'goodware')]
X_filtered = df_filtered.iloc[:, :-1]
y_filtered = df_filtered.iloc[:, -1]

# 3. 标签编码 (字符串转换为数字)
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_filtered)

# 4. 划分训练集和测试集 (80%训练，20%测试)
X_train, X_test, y_train, y_test = train_test_split(
    X_filtered, y_encoded, test_size=0.2, random_state=42
)

# 保存测试集供后续Django系统演示用
test_df = pd.concat([X_test, pd.Series(y_test, name='Label', index=X_test.index)], axis=1)
test_df.to_csv('test_dataset.csv', index=False)
print("测试集已保存为 test_dataset.csv")

# 5. 训练XGBoost模型
print("开始训练模型...")
params = {
    'max_depth': 7,          # 论文中网格搜索得出的最佳深度
    'objective': 'binary:logistic',
    'nthread': 4,
    'eval_metric': ['auc', 'logloss'],
    'learning_rate': 0.05
}

dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

num_boost_rounds = 100
model = xgb.train(
    params,
    dtrain,
    num_boost_round=num_boost_rounds,
    evals=[(dtrain, 'train'), (dtest, 'eval')],
    early_stopping_rounds=10,
    verbose_eval=False
)

# 6. 评估并保存模型
predictions_prob = model.predict(dtest)
predictions = [1 if pred > 0.5 else 0 for pred in predictions_prob]
print(f"模型准确率: {accuracy_score(y_test, predictions):.4f}")

# 保存模型和LabelEncoder
model.save_model('malware_detection.model')
dump(label_encoder, 'app01/models_dir/label_encoder.joblib')
print("模型和编码器已保存！")