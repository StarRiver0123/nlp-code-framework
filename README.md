# model-training-framework

## 概述

本开源框架的目标是把模型训练过程中的通用流程和组件整理成可以复用的框架模板，使得开发者可以聚焦算法模型本身，同时提高模型配置和部署的灵活性。

框架代码写得还有许多需要优化的地方，比如对函数入参的合法性验证、性能优化等。注释写得也不全。

欢迎有缘者多多指正！

## 指导思想：

开发一个AI系统，可以从如下两个角度考虑：

#### 1. 从产品架构角度：

（1）首先把系统分成若干功能相对独立的应用子系统，比如把一个招聘机器人系统分成简历匹配机器人、会话客服机器人、面试机器人等应用子系统......<br>
（2）再把每个应用子系统提炼出核心的应用任务，比如关键词提取、意图识别......<br>
（3）然后把每个应用任务分解成NLP基础任务，比如命名实体识别、文本分类......<br>
（4）接下来根据业务需求和目标，针对每个NLP基础任务设计或选择组件模块：数据预处理、分词器、模型网络结构、目标函数、优化器、学习率调节器、性能评价指标......<br>

#### 2. 从流程角度：

（1）数据处理：数据获取、数据清洗、数据预处理......<br>
（2）模型训练：模型训练、模型验证、模型保存、断点续训......<br>
（3）模型测试：模型加载、模型测试、模型样品应用展示......<br>
（4）模型部署：模型服务接口、web部署......<br>

#### 3. 从工程部署角度：

项目会包含许多超参数等配置参数，要实现代码和配置参数相分离。<br>

## 框架特点：

（1）基于Pytorch框架。<br>
（2）实现应用系统、应用任务、NLP基础任务、NLP基础任务组件模块的层次化项目架构。<br>
（3）实现数据爬取、数据预处理、数据加载、模型训练、模型验证和模型测试、模型WEB服务发布的流程化配置管理。<br>
（4）实现分词器、模型网络结构、目标函数、优化器、评价指标、训练框架、测试框架的模块化配置管理。<br>
（5）实现配置和代码相分离的超参数配置管理。<br>
（6）包含了一些实用的技巧，比如数据预处理的多进程并发、断点续训、梯度裁剪等。<br>

## 框架代码目录结构：
> config_project.yaml ----------------------------*主框架文件及目录配置文件*<br>
> config_deploy.yaml ----------------------------*web服务部署的文件及目录配置文件*<br>
> run_modeling.py -------------------------------*模型训练项目程序执行入口文件*<br>
> run_deploying.py -----------------------------*模型部署项目程序执行入口文件*<br>
> src -----------------------------------------*源代码文件目录*<br>
> 
>> applications -------------------------------*应用子系统的总目录*<br>
>> 
>>> demo_app ----------------------------------*某应用子系统的目录*<br>
>>>
>>>> tasks -------------------------------------*存放应用任务的总目录*<br>
>>>>
>>>>> ner -------------------------------------*命名实体识别任务样例的目录*<br>
>>>>>
>>>>>> config_task_training.yaml ----------------*训练任务的配置文件*<br>
>>>>>> config_task_testing.yaml ---------- ------*测试任务的配置文件*<br>
>>>>>> preprocess.py ----------------------------*示例任务代码：划分数据集、数据清洗等模型训练前置任务*<br>
>>>>>> build_dataset.py -------------------------*示例任务代码：中文分词、创建数据生成器等*<br>
>>>>>> build_model.py ---------------------------*示例任务代码：创建模型对象*<br>
>>>>>> train_model.py ---------------------------*示例任务代码：训练模型*<br>
>>>>>> test_model.py ----------------------------*示例任务代码：测试模型*<br>
>>>>>> apply.py ---------------------------------*示例任务代码：应用模型*<br>
>>>>>
>>>>> answer_grade ----------------------------*问答评分任务样例的目录*<br>
>>>>> translation -----------------------------*机器翻译任务样例的目录*<br>
>>>>> model_distilling ------------------------*BERT蒸馏到LSTM任务样例的目录*<br>
>>>>> textbrewer_distilling -------------------*使用text_brewer进行模型蒸馏任务样例的目录*<br>
>>>>> data_crawling ---------------------------*爬虫任务样例的目录*<br>
>>>>> neo4j -----------------------------------*知识图谱检索任务样例的目录*<br>
>>>
>>> demo_app2 ---------------------------------*某应用子系统的目录*<br>
>>
>> modules -------------------------------------*存放模型代码的目录*<br>
>> 
>>> criteria ----------------------------------*目标函数*<br>
>>> evaluators --------------------------------*性能评价指标*<br>
>>> models ------------------------------------*模型结构*<br>
>>> optimizers --------------------------------*优化器*<br>
>>> tester ------------------------------------*测试框架*<br>
>>> tokenizers --------------------------------*分词器*<br>
>>> trainer -----------------------------------*训练框架*<br>
>>> vectors -----------------------------------*词向量*<br>
>>
>> tests --------------------------------------*存放接口测试代码文件的目录*<br>
>> utilities ----------------------------------*存放底层工具代码文件的目录*<br>
>
> resources ------------------------------------*存放各种数据资源的目录*<br>
>
>> datasets ------------------------------------*存放数据集资源的目录*<br>
>> bert_models ---------------------------------*bert模型*<br>
>> word_vectors --------------------------------*静态词向量*<br>
>
>data -----------------------------------------*存放系统产生的数据文件的目录*<br>
>
>> logs ----------------------------------------*日志*<br>
>> check_points - ------------------------------*保存的模型*<br>
> 
> deploy --------------------------------------*web服务部署的总目录*<br>
>
>> demo_app -----------------------------------*某应用子系统的部署目录*<br>
>> demo_app2 ----------------------------------*某应用子系统的部署目录*<br>
>>
>>> config_app.yaml ---------------------------*应用部署的配置文件*<br>
>>> services ----------------------------------*任务服务接口的部署目录*<br>
>>>
>>>> data -------------------------------------*服务接口的数据目录*<br>
>>>> src --------------------------------------*服务接口的代码目录*<br>
>>>
>>> django_server -----------------------------*基于django部署的目录*<br>
>>>
>>>> run_service.py ---------------------------*服务的启动文件*<br>
>>>> django_service ---------------------------*django服务器的目录*<br>
>>>
>>> flask_server ------------------------------*基于flask部署的目录*<br>
>>>
>>>> run_service.py ----------------------------*服务的启动文件*<br>
>>>
>>
>

## 基本使用方法：

- 在resources目录下存入收集整理的数据集、词向量等数据文件
- 在src/modules目录下相应位置编写模型模块代码
- 在src/applications/tasks目录下相应位置编写模型定义、数据预处理、模型训练和测试代码
- 在src/相关目录下相应位置编写配置参数
- 在src/tests目录下写必要的接口测试代码
- 训练和测试模型
- 发布成服务接口供其他调用
