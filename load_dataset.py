
import yaml, os, re, random, json
random.seed(0)

class DatasetLoader:
    def __init__(self, config_path, base_data_path, base_few_shot_prompt_path, dataset, data_mode='longest', num_samples=200):
        """
        Initialize the dataset loader with configuration.

        :param config_path: Path to the YAML config file.
        :param base_data_path: Base directory for dataset files.
        :param dataset: Name of the dataset to load.
        :param data_mode: Mode for data loading ('random' or 'longest').
        """
        self.config_path = config_path
        self.base_data_path = base_data_path
        self.base_few_shot_prompt_path = base_few_shot_prompt_path
        self.dataset = dataset
        self.data_mode = data_mode
        self.num_samples = num_samples
        
        self.config = self._load_config()
        self.data_path = self._get_data_path()
        self.data = self._read_data()
        
    def _load_few_shot_prompt(self, fs_mode):
        fewshot_prompt_path = os.path.join(self.base_few_shot_prompt_path, self.config['prompts'][fs_mode][self.dataset])
        
        with open(fewshot_prompt_path, 'r') as file:
            few_shot_prompt = file.read()
        return few_shot_prompt
    
    def _load_config(self):
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_data_path(self):
        return os.path.join(self.base_data_path, self.config['data_paths'][self.dataset])

    def _read_data(self):
        if 'jsonl' in self.data_path:
            return self._read_jsonl_file(self.data_path)
        else:
            with open(self.data_path, 'r') as file:
                return json.load(file)

    @staticmethod
    def _read_jsonl_file(path):
        with open(path, 'r') as file:
            return [json.loads(line) for line in file]

    def get_questions_and_ids(self):
        if self.data_mode == 'random':
            return self.get_random_questions_and_ids()
        elif self.data_mode == 'longest':
            return self.get_longest_questions_and_ids()
        elif self.data_mode == 'shortest':
            return self.get_shortest_questions_and_ids()
        elif self.data_mode == 'remain':
            return self.get_remain_questions_and_ids()
        else:
            return self.get_full_questions_and_ids()
        
    def get_full_questions_and_ids(self):
        """
        Process and extract questions and IDs based on dataset type.
        """
        if self.dataset == 'p_GSM8K':
            return self._process_generic('new_question', 'index')
        elif self.dataset == 'spartQA':
            return self._process_spartQA()
        elif self.dataset == 'reclor':
            return self._process_reclor()
        elif self.dataset in ['GSM_IC', 'GSM8K_Hard', 'GSM_Plus', 'medQA']:
            return self._process_simple()
        else:
            return self._process_generic('question', 'id')
    
    def get_shortest_questions_and_ids(self):
        """
        1. Get full questions and ids
        2. find shortest questions and ids based on the shortest question length
        """
        full_questions, full_ids = self.get_full_questions_and_ids()
        # Combine questions and IDs into a list of tuples
        full_questions_ids = list(zip(full_questions, full_ids))

        # Sort the tuples by the length of the questions
        sorted_full_questions_ids = sorted(full_questions_ids, key=lambda x: len(x[0]))

        # Select the shortest questions and their IDs
        shortest_ = sorted_full_questions_ids[:min(self.num_samples, len(sorted_full_questions_ids))]

        # Separate them back into two lists
        shortest_questions, shortest_ids = zip(*shortest_)

        # Convert to lists if necessary
        shortest_questions = list(shortest_questions)
        shortest_ids = list(shortest_ids)
        
        return shortest_questions, shortest_ids
    
    def get_longest_questions_and_ids(self):
        """
        1. Get full questions and ids
        2. find longest questions and ids based on the longest question length
        """
        full_questions, full_ids = self.get_full_questions_and_ids()
        # Combine questions and IDs into a list of tuples
        full_questions_ids = list(zip(full_questions, full_ids))
        
        # Sort the tuples by the length of the questions
        sorted_full_questions_ids = sorted(full_questions_ids, key=lambda x: len(x[0]), reverse=True)
        
        # Select the shortest questions and their IDs
        longest_ = sorted_full_questions_ids[:min(self.num_samples, len(sorted_full_questions_ids))]

        # Separate them back into two lists
        longest_questions, longest_ids = zip(*longest_)

        # Convert to lists if necessary
        longest_questions = list(longest_questions)
        longest_ids = list(longest_ids)
        
        return longest_questions, longest_ids
    
    def get_random_questions_and_ids(self):
        full_questions, full_ids = self.get_full_questions_and_ids()
        longest_questions, longest_ids = self.get_longest_questions_and_ids()
        
        # get randoms except max_len_questions
        random_questions, random_ids = [], []
        for question, id in zip(full_questions, full_ids):
            if question not in longest_questions:
                random_questions.append(question)
                random_ids.append(id)

        indices = random.sample(range(len(random_questions)), min(self.num_samples, len(random_questions)))

        # Create subsets based on the selected indices
        random_questions = [random_questions[i] for i in indices]
        random_ids = [random_ids[i] for i in indices]
        
        return random_questions, random_ids
        
    def get_remain_questions_and_ids(self, infered_ids):
        full_questions, full_ids = self.get_full_questions_and_ids()
        
        remain_questions, remain_ids = [], []
        for q, id in zip(full_questions, full_ids):
            if id not in infered_ids:
                remain_questions.append(q)
                remain_ids.append(id)
        
        return list(remain_questions), list(remain_ids)
        
    def _process_generic(self, question_key, id_key):
        questions = [x[question_key] for x in self.data]
        ids = [x[id_key] for x in self.data]
        return questions, ids

    def _process_spartQA(self):
        questions = [
            x['question'].replace('0:', '(a)').replace('1:', '(b)').replace('2:', '(c)').replace('3:', '(d)')
            for x in self.data
        ]
        ids = [x["id"] for x in self.data]
        
        # take 400 random questions and ids
        combined = list(zip(questions, ids))
        sampled = random.sample(combined, k=400)

        questions, ids = zip(*sampled)

        questions = list(questions)
        ids = list(ids)
        
        return questions, ids

    def _process_reclor(self):
        questions = [
            x['context'] + ' ' + x["question"] +
            '\n(a) ' + x['answers'][0] +
            '\n(b) ' + x['answers'][1] +
            '\n(c) ' + x['answers'][2] +
            '\n(d) ' + x['answers'][3]
            for x in self.data
        ]
        ids = [x["id_string"] for x in self.data]
        return questions, ids

    def _process_simple(self):
        questions = [
            x['new_question'] if 'new_question' in x else x['question']
            for x in self.data]
        ids = [i for i in range(len(questions))]
        return questions, ids  
        
    
    def retrieve_gts(self, ids):
        """
        ids: ids of the predictions (list)
        """        
        # read gt
        gts = []
        if self.dataset in ['GSM8K_Hard']:
            for id in ids:
                for i, temp in enumerate(self.data):
                    if id == i:
                        # print(temp['new_question'], id, temp['answer'])
                        # exit()
                        gt = temp['answer']
                        if self.dataset == 'coin':
                            if gt == 'yes':
                                gt = True
                            else:
                                gt = False
                        gts.append(gt)
            return gts
        
        if self.dataset == 'GSM_Plus':
            
            num_cannot_convert = 0
            num_none = 0
            for id in ids:
                for i, temp in enumerate(self.data):
                    if id == i:
                        # print(temp['new_question'], id, temp['answer'])
                        # exit()
                        gt = temp['answer']
                        if temp['answer'] == 'None':
                            gts.append(None)
                            num_none += 1
                        else:
                            try:
                                gts.append(float(gt))
                            except:
                                num_cannot_convert += 1
                                gts.append(None)
                                num_none += 1
            print(num_none)
            print(num_cannot_convert)
            # exit()
            
            return gts
    
        for id in ids:
            for temp in self.data:
                if self.dataset == 'squad':
                    if temp['id'] == id:
                        gt = temp['answer']
                        gts.append(gt)
                if self.dataset in ['drop_break', 'drop_cencus']:
                    if temp['id'] == id:
                        gt = temp['answer'][0][0]
                        gts.append(float(gt))
                if self.dataset == 'p_GSM8K':
                    if temp['index'] == id:
                        gt = temp['answer']
                        gts.append(float(gt))
                elif self.dataset == 'wikimultihopQA':
                    if temp['_id'] == id:
                        gt = temp['answer']
                        gts.append(gt)
                elif self.dataset == 'spartQA':
                    if temp['id'] == id:
                        gt = temp['answer']
                        if gt == 0:
                            gt = 'A'
                        elif gt == 1:
                            gt = 'B'
                        elif gt == 2:
                            gt = 'C'
                        elif gt == 3:
                            gt = 'D'
                        gts.append(gt)
                elif self.dataset == 'reclor':
                    if temp['id_string'] == id:
                        gt = temp['label']
                        if gt == 0:
                            gt = 'A'
                        elif gt == 1:
                            gt = 'B'
                        elif gt == 2:
                            gt = 'C'
                        elif gt == 3:
                            gt = 'D'
                        gts.append(gt)
                elif self.dataset == 'commonsenseQA':
                    if temp['id'] == id:
                        gt = temp['answerKey']
                        gts.append(gt)
                else:
                    if temp['id'] == id:
                        gt = temp['answer']
                        if self.dataset in ['GSM8K', 'MultiArith', 'SVAMP']:
                            gt = gt.split('####')[1].strip()
                            if ',' in gt:
                                gt = gt.replace(',', '')
                            gts.append(float(gt))
                        if self.dataset == 'CLUTRR':
                            gt = gt.split('####')[1].strip()
                            gts.append(gt)
                        if self.dataset == 'date':
                            gt = gt.split('####')[1].strip()
                            gts.append(gt)
                        if self.dataset == 'ASDiv':
                            #if gt is list, convert it to string
                            if type(gt) == list:
                                gt = gt[0]
                            gt = gt.replace(',', '')
                            gts.append(float(gt))
                        if self.dataset in ['StrategyQA', 'navigate', 'causal_judgement']:
                            gts.append(gt)
                        if self.dataset == 'web_of_lies':
                            if gt == 'yes':
                                gt = True
                            else:
                                gt = False
                            gts.append(gt)
                        if self.dataset in ['AQUA', 'logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'word_sorting', 'tracking_shuffled_objects_three_objects', 'tracking_shuffled_objects_five_objects', 'tracking_shuffled_objects_seven_objects', 'temporal_sequences']:
                            gts.append(gt)    
                        if self.dataset == 'object_counting':
                            gts.append(float(gt))
        
        return gts