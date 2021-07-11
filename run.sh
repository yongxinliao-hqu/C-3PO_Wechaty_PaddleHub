pip install --upgrade pip
pip install wechaty==0.7dev17

#需要将PaddleHub和PaddlePaddle统一升级到2.0版本
pip install paddlehub==2.0.2
pip install paddlepaddle==2.1.0
pip install paddlenlp==2.0.0

# 下载模型
hub install animegan_v2_shinkai_33
hub install plato-mini==1.0.0

# 设置环境变量
export WECHATY_PUPPET=wechaty-puppet-service
export WECHATY_PUPPET_SERVICE_TOKEN=puppet_paimon_xxxxx #Your own token

# 设置使用GPU进行模型预测
export CUDA_VISIBLE_DEVICES=0

# 创建两个保存图片的文件夹
mkdir -p image

# 运行python文件
python paddlehub-chatbot.py