import sys, random
import pickle as pk
import copy, numpy
from torchtext.legacy.vocab import Vectors
from torchtext.legacy.data import Field, BucketIterator
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertModel, BertConfig
from collections import defaultdict
from src.utilities.load_data import *
from src.models.tokenizers.tokenizer import *


def load_train_valid_split_set(arguments):
    # return train set, valid set
    running_task = arguments['general']['running_task']
    project_root = arguments['general']['project_root']
    train_tagging = arguments['tasks'][running_task]['dataset']['train_tagging']
    valid_size = arguments['training'][running_task]['valid_size']
    train_tagging = get_txt_from_file(project_root + os.path.sep + train_tagging)
    data_set = []
    for text in train_tagging:
        data_set.append(tuple(text.strip().split()))
    train_set, valid_set = train_test_split(data_set, test_size=valid_size, shuffle=False)
    return train_set, valid_set


def load_test_set(arguments):
    # return test set
    running_task = arguments['general']['running_task']
    project_root = arguments['general']['project_root']
    test_tagging = arguments['tasks'][running_task]['dataset']['test_tagging']
    test_tagging = get_txt_from_file(project_root + os.path.sep + test_tagging)
    data_set = []
    for text in test_tagging:
        data_set.append(tuple(text.strip().split()))
    return data_set


def random_sample(data_set, max_len, bert_sos_token=None, bert_eos_token=None):
    # data_set input format: [('机','B-基本概念'),('器','I-基本概念')]
    # data_set output format: (['机','器'],['B-基本概念','器','I-基本概念'])
    assert (bert_sos_token is None and bert_eos_token is None) or (bert_sos_token is not None and bert_eos_token is not None)
    data_set_len = len(data_set)
    if bert_eos_token is not None:
        max_len -= 2     # sos_token 和eos_token占去了2位
    up_range = data_set_len - max_len
    while True:
        id0 = random.randint(0, up_range)
        id1 = id0 + max_len - 1
        while (id1 >= id0) and (data_set[id1][1][0] not in ['E', 'S', 'O']):
            id1 -= 1
        while (id1 >= id0) and (data_set[id0][1][0] not in ['B', 'S', 'O']):
            id0 += 1
        if (id1 >= id0):
            len_threshold = random.randint(max_len // 8, max_len // 2)
            could_be = copy.deepcopy(data_set[id0:id1 + 1])
            if (numpy.sum([i[1][0] == 'O' for i in could_be]) >= len(data_set[id0:id1 + 1])):
                continue
            seq_len = len(could_be)
            o_r = 0
            while o_r < seq_len:            # 减少'O'的数量，连续'O'的数量不能超过阈值，降低标签不平衡的影响。
                o_l = o_r
                while (o_l < seq_len) and (could_be[o_l][1][0] != 'O'):
                    o_l += 1
                if o_l >= seq_len:               #列表右端已经全部是’O‘了
                    break
                o_r = o_l + 1
                while (o_r < seq_len) and (could_be[o_r][1][0] == 'O'):
                    o_r += 1
                if (o_r - o_l) > len_threshold:
                    del could_be[o_l : o_r - len_threshold]
                    seq_len -= o_r - o_l -len_threshold
                    o_r -= o_r - o_l -len_threshold
            if (o_r - o_l) >= len(data_set[id0:id1 + 1]):    # 说明本次得到的全部是’O‘则丢弃不用，重新检索
                continue
            zipped_list = list(zip(*could_be))
            if bert_sos_token is None:
                return (list(zipped_list[0]), list(zipped_list[1]))
            else:
                return ([bert_sos_token] + list(zipped_list[0]) + [bert_eos_token], list(zipped_list[1]))
                        # source需要加上sos和eos符号，但是target不需要加，因为在iterator生成数据时根据field设置会自动加上。
        else:   # 如果找不到，则重新生成随机起始位去寻找
            continue

def load_ner_dataset(arguments, bert_sos_token=None, bert_eos_token=None):
    project_root = arguments['general']['project_root']
    running_task = arguments['general']['running_task']
    data_source = project_root + os.path.sep + arguments['tasks'][running_task]['dataset']['ner_parameter']
    parameter = pk.load(open(data_source, 'rb'))
    train_set = [([bert_sos_token] + pair[0] + [bert_eos_token], pair[1]) for pair in parameter['data_set']['train']]
    valid_set = [([bert_sos_token] + pair[0] + [bert_eos_token], pair[1]) for pair in parameter['data_set']['dev']]
    stoi = parameter['key2ind']
    itos = list(stoi.keys())
    return train_set, valid_set, stoi, itos


def get_data_iterator(arguments, train_set=None, valid_set=None, test_set=None):
    project_root = arguments['general']['project_root']
    running_task = arguments['general']['running_task']
    batch_size = arguments['training'][running_task]['batch_size']
    batch_size_for_test = arguments['testing'][running_task]['batch_size']
    device = arguments['general']['device']
    valid_size = arguments['training'][running_task]['valid_size']
    test_size = arguments['training'][running_task]['test_size']
    used_model = arguments['tasks'][running_task]['model']
    max_len = arguments['model'][used_model]['max_len']
    gen_num_total_examples = arguments['tasks'][running_task]['dataset']['gen_num_total_examples']
    bert_model_name = project_root + os.path.sep + arguments['tasks'][running_task]['bert_model']['bert_model_zh']
    tokenizer = BertTokenizer.from_pretrained(bert_model_name)
    bert_pad_token_id = tokenizer.pad_token_id
    bert_unk_token_id = tokenizer.unk_token_id
    bert_sos_token = tokenizer.cls_token
    bert_eos_token = tokenizer.sep_token
    general_pad_token = arguments['dataset']['general']['pad_token']
    general_unk_token = arguments['dataset']['general']['unk_token']
    general_sos_token = arguments['dataset']['general']['sos_token']
    general_eos_token = arguments['dataset']['general']['eos_token']

    # compute the field
    SOURCE_FIELD = Field(sequential=True, use_vocab=False, tokenize=None,  preprocessing=tokenizer.convert_tokens_to_ids, batch_first=True,
                     fix_length=None, init_token=None, eos_token=None, pad_token=bert_pad_token_id, unk_token=bert_unk_token_id)
    # 注意：如果不用bert的字典，则给Field需要传入pad和unk的话必须是'<pad>'和'<unk>'，因为生成batch源码中给写死了，根据use_vocab和sequential和pad_token来确定vocab中defaultdict的参数。
    # source_field不需要传入sos_token和eos_token。因为序列化已经在使用filed之前完成了，也不需要构建字典词表，sos_token和eos_token的添加不需要通过filed属性来完成，而是在random_sample采样生成数据时加上了。
    TARGET_FIELD = Field(sequential=True, use_vocab=True, tokenize=None,  batch_first=True,
                     fix_length=None, init_token=None, eos_token=general_eos_token, pad_token=general_pad_token, unk_token=general_unk_token)
    # target_filed不一定需要传入sos_token，eos_token，但必须传入unk_token和pad_token，因为在Vocab.py类源码中写死了要根据unk来初始化vocab的defaultdict。

    #！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    #这是直接用的老师的数据源，临时做对比用的，
    #！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！11
    # train_set, valid_set, stoi_loaded, itos_loaded = load_ner_dataset(arguments, bert_sos_token, bert_eos_token)


    if train_set is not None:
        train_examples = []
        for i in range(int(gen_num_total_examples * (1 - test_size) * (1 - valid_size))):
            train_examples.append(random_sample(train_set, max_len, bert_sos_token, bert_eos_token))
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        # 这是直接用的老师的数据源，临时做对比用的，
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！11
        # train_examples = train_set

        train_examples = DataExamples_withTorchText(train_examples, SOURCE_FIELD, TARGET_FIELD)
        train_iter = BucketIterator(dataset=train_examples, batch_size=batch_size, sort_key=lambda x: len(x.Source),
                                    shuffle=True, sort_within_batch=True, sort=True, device=device)
        # build the vocab
        tags = defaultdict(int)
        for line in train_set:
            tags[line[1]] += 1
        if valid_set is not None:     # 把验证集和测试集的标签也加入词典，增加匹配成功率。
            for line in valid_set:
                tags[line[1]] += 1
        if test_set is not None:     # 把验证集和测试集的标签也加入词典，增加匹配成功率。
            for line in test_set:
                tags[line[1]] += 1

        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        # 这是直接用的老师的数据源，临时做对比用的，
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！11
        # tags = stoi_loaded

        if ('bert_crf' not in arguments['model'].keys()) or (arguments['model']['bert_crf'] is None):
            arguments['model'].update({'bert_crf': {}})
        arguments['model']['bert_crf'].update({'num_tags': len(tags) + 3})   #考虑真正的标签加上pad和unk(sos,eos)
        stoi = dict(zip(tags.keys(), range(3, len(tags)+3)))  #考虑pad和unk（sos,eos）已经占据了前几位
        itos = list(tags.keys())

        # 注意：如果不用bert的字典，则给Field传入的pad和unk必须是'<pad>'和'<unk>'，因为源码中给写死了。
        # 否则stoi这个defaultdict的default_factory会为None，则跟dict一样了。这样在使用字典遇到字典中没有的关键词，则报KeyError错误。
        TARGET_FIELD.build_vocab()
        TARGET_FIELD.vocab.stoi.update(stoi)
        TARGET_FIELD.vocab.itos.extend(itos)

        # 如果train_set为空，则不管valid_set是否为空，都不做处理，因为valid是针对train的结果而言的。valid可以看作是train的一个过程。
        if valid_set is not None:
            valid_examples = []
            for i in range(int(gen_num_total_examples * (1 - test_size) * valid_size)):
                valid_examples.append(random_sample(valid_set, max_len, bert_sos_token, bert_eos_token))

            # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
            # 这是直接用的老师的数据源，临时做对比用的，
            # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！11
            # valid_examples = valid_set

            valid_examples = DataExamples_withTorchText(valid_examples, SOURCE_FIELD, TARGET_FIELD)
            valid_iter = BucketIterator(dataset=valid_examples, batch_size=batch_size,
                                        sort_key=lambda x: len(x.Source), shuffle=True, sort_within_batch=True,
                                        sort=True, train=False, device=device)
    if test_set is not None:
        test_examples = []
        for i in range(int(gen_num_total_examples * test_size)):
            test_examples.append(random_sample(test_set, max_len, bert_sos_token, bert_eos_token))

        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        # 这是直接用的老师的数据源，临时做对比用的，
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！11
        # test_examples = valid_set

        test_examples = DataExamples_withTorchText(test_examples, SOURCE_FIELD, TARGET_FIELD)
        test_iter = BucketIterator(dataset=test_examples, batch_size=batch_size_for_test, train=False,
                                   sort=False, device=device)
    if train_set is not None:
        if valid_set is not None:
            if test_set is not None:
                return train_iter, valid_iter, test_iter, SOURCE_FIELD, TARGET_FIELD
            else:
                return train_iter, valid_iter, SOURCE_FIELD, TARGET_FIELD
        else:
            if test_set is not None:
                return train_iter, test_iter, SOURCE_FIELD, TARGET_FIELD
            else:
                return train_iter, SOURCE_FIELD, TARGET_FIELD
    else:
        if valid_set is not None:
            if test_set is not None:
                return valid_iter, test_iter, SOURCE_FIELD, TARGET_FIELD
            else:
                return valid_iter, SOURCE_FIELD, TARGET_FIELD
        else:
            if test_set is not None:
                return test_iter, SOURCE_FIELD, TARGET_FIELD
            else:
                return SOURCE_FIELD, TARGET_FIELD