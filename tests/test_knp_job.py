#! -*- coding: utf-8 -*-
from knp_utils import knp_job
from knp_utils.models import  Params
from knp_utils import db_handler
import unittest
import json
import os
import shutil
import six

class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # procedures before tests are started. This code block is executed only once

        cls.db_file_name = 'model_database.sqlite3'
        if 'tests' in os.getcwd():
            print(os.path.dirname(__file__))
            cls.path_input_documents = './resources/input_sample.json'
            cls.path_work_dir = './resources'
        else:
            cls.path_input_documents = 'tests/resources/input_sample.json'
            cls.path_work_dir = 'tests/resources'

        with open(cls.path_input_documents, 'r') as f:
            cls.seq_docs = json.loads(f.read())

        if os.path.exists('/usr/local/bin/knp'):
            cls.path_knp = '/usr/local/bin/knp'
        else:
            if six.PY2:
                doc_command_string = "echo '' | {}".format('knp')
                command_check = os.system(doc_command_string)
                if command_check == 0:
                    cls.path_knp = 'knp'
                else:
                    raise Exception("No command at {}".format('knp'))
            else:
                if shutil.which('knp'):
                    cls.path_knp = 'knp'
                else:
                    raise Exception("No command at {}".format('knp'))

        if os.path.exists('/usr/local/bin/juman'):
            cls.path_juman = '/usr/local/bin/juman'
        else:
            if six.PY2:
                doc_command_string = "echo '' | {}".format('juman')
                command_check = os.system(doc_command_string)
                if command_check == 0:
                    cls.path_juman = 'juman'
                else:
                    raise Exception("No command at {}".format('juman'))
            else:
                if shutil.which('knp'):
                    cls.path_juman = 'knp'
                else:
                    raise Exception("No command at {}".format('juman'))


    @classmethod
    def tearDownClass(cls):
        # procedures after tests are finished. This code block is executed only once
        if os.path.exists(os.path.join(cls.path_work_dir, cls.db_file_name)):
            os.remove(os.path.join(cls.path_work_dir, cls.db_file_name))

    def setUp(self):
        # procedures before every tests are started. This code block is executed every time
        pass

    def tearDown(self):
        # procedures after every tests are finished. This code block is executed every time
        pass

    def test_initialize_text_db(self):
        """作業用DBを初期化する"""
        knp_job.initialize_text_db(knp_job.generate_document_objects(self.seq_docs),
                                   work_dir=self.path_work_dir, file_name=self.db_file_name)

    def test_parse_one_sentence(self):
        """"""
        self.test_initialize_text_db()
        handler = db_handler.Sqlite3Handler(os.path.join(self.path_work_dir, self.db_file_name))
        knp_job.parse_text_block(seq_record_id=[4],
                                 path_sqlite3_db_handler=os.path.join(self.path_work_dir, self.db_file_name),
                                 knp_command=self.path_juman,
                                 juman_command=self.path_juman)

    def test_parse_texts(self):
        self.test_initialize_text_db()
        knp_job.parse_texts(path_sqlite3_db_handler=os.path.join(self.path_work_dir, self.db_file_name),
                            n_jobs=2,
                            knp_command=self.path_knp,
                            juman_command=self.path_juman)

    def test_stress_test_pattern1(self):
        """大量の入力文を与えた場合の挙動をチェックする
        ### with normalization is True
        """
        seq_long_test_input = self.seq_docs * 20

        result_obj = knp_job.main(
            seq_input_dict_document=seq_long_test_input,
            is_normalize_text=True)
        self.assertTrue(len(result_obj.seq_document_obj) == len(seq_long_test_input))

    def test_stress_test_pattern2(self):
        """大量の入力文を与えた場合の挙動をチェックする
        ### with normalization is False
        """
        seq_long_test_input = self.seq_docs * 20

        result_obj = knp_job.main(
            seq_input_dict_document=seq_long_test_input,
            is_normalize_text=False)
        self.assertTrue(len(result_obj.seq_document_obj) == len(seq_long_test_input))

    def test_exception_during_sentence(self):
        """KNPの解析結果文字列が例外を起こすときの処理"""
        seq_input = [
            {'text-id': 'test-1', 'text': 'ベッキー♪#も、なんかもう世代交代じゃね？'},
            {'text-id': 'test-2', 'text': 'ベッキー♪#も、なんかもう世代交代じゃね？'},
            {'text-id': 'test-3', 'text': 'ベッキー♪#も、なんかもう世代交代じゃね？'}
        ]

        result_obj = knp_job.main(
            seq_input_dict_document=seq_input,
            is_normalize_text=False,
            is_delete_working_db=True
        )


if __name__ == '__main__':
    unittest.main()