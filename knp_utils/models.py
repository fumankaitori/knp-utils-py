#! -*- coding: utf-8 -*-
# package module
from knp_utils.logger_unit import logger
# else
from datetime import datetime
import subprocess
import traceback
import six
import socket
import re
import shutil
import signal
import pexpect
import os
from typing import List, Dict, Any, Union
from six import text_type


if six.PY2:
    ConnectionRefusedError = Exception


# todo これは不要だから消すかも
class JumanppClient(object):
    """Class for receiving data as client"""
    def __init__(self, hostname, port, timeout=50, option=None):
        """"""
        # type:(str,int,int,None)->None
        if isinstance(port, str):
            port = int(port)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((hostname, port))
        except ConnectionRefusedError:
            raise Exception("There is no jumanpp server hostname={}, port={}".format(hostname, port))
        except:
            raise
        if option is not None:
            self.sock.send(option)
        data = b""
        self.sock.settimeout(timeout)

    def __del__(self):
        if self.sock:
            self.sock.close()

    def query(self, sentence, pattern):
        # type: (str, bytes) -> str
        assert (isinstance(sentence, six.text_type))
        self.sock.sendall(b"%s\n" % sentence.encode('utf-8').strip())
        data = self.sock.recv(1024)
        assert isinstance(data, bytes)
        recv = data
        while not re.search(pattern, recv):
            data = self.sock.recv(1024)
            recv = b"%s%s" % (recv, data)
        return recv.strip().decode('utf-8')


class UnixProcessHandler(object):
    """This class is a handler of any UNIX process. The class keeps UNIX process running.
    """
    def __init__(self,
                 unix_command,
                 option=None,
                 pattern='EOS',
                 timeout_second=10):
        """"""
        # type: (text_type,text_type,text_type,int)->None
        self.unix_command = unix_command
        self.timeout_second = timeout_second
        self.pattern = pattern
        self.option = option
        self.launch_process(unix_command)

    def __del__(self):
        if hasattr(self, "process_analyzer"):
            self.process_analyzer.kill(sig=9)

    def launch_process(self, command):
        """* What you can do
        - It starts jumanpp process and keep it.
        """
        # type: (text_type)->None
        if not self.option is None:
            command_plus_option = self.unix_command + " " + self.option
        else:
            command_plus_option = self.unix_command

        if six.PY3:
            if shutil.which(command) is None:
                raise Exception("No command at {}".format(command))
            else:
                self.process_analyzer = pexpect.spawnu(command_plus_option)
                self.process_id = self.process_analyzer.pid
        else:
            doc_command_string = "echo '' | {}".format(command)
            command_check = os.system(doc_command_string)
            if not command_check == 0:
                raise Exception("No command at {}".format(command))
            else:
                self.process_analyzer = pexpect.spawnu(command_plus_option)
                self.process_id = self.process_analyzer.pid

    def restart_process(self):
        """"""
        # type: ()->None
        if not self.option is None:
            command_plus_option = self.unix_command + " " + self.option
        else:
            command_plus_option = self.unix_command

        self.process_analyzer.kill(sig=9)
        self.process_analyzer = pexpect.spawnu(command_plus_option)
        self.process_id = self.process_analyzer.pid

    def stop_process(self):
        """* What you can do
        - You're able to stop the process which this instance has now.
        """
        # type: ()->bool
        if hasattr(self, "process_analyzer"):
            self.process_analyzer.kill(sig=9)
        else:
            pass

        return True

    def __query(self, input_string):
        """* What you can do
        - It takes the result of Juman++
        - This function monitors time which takes for getting the result.
        """
        # type: (text_type)->text_type
        print(input_string)
        self.process_analyzer.sendline(input_string)
        buffer = ""
        while True:
            line_string = self.process_analyzer.readline()  # type: text_type
            if line_string.strip() == input_string:
                """Skip if process returns the same input string"""
                continue
            elif line_string.strip() == self.pattern:
                buffer += line_string
                return buffer
            else:
                buffer += line_string

    def __notify_handler(self, signum, frame):
        raise Exception("""It takes longer time than {time} seconds. You're able to try, 
        1. Change your setting of 'timeout_second' parameter
        2. Run restart_process() method when the exception happens.""".format(**{"time": self.timeout_second}))

    def query(self, input_string):
        """* What you can do
        """
        # type: (text_type)->text_type
        try:
            return self.__query(input_string=input_string)
        except UnicodeDecodeError:
            logger.error(msg=traceback.format_exc())
            raise Exception()


# todo n_jobsを消すこと
class KnpSubProcess(object):
    """This class defines process to run KNP analysis."""
    def __init__(self,
                 knp_command,
                 juman_command,
                 knp_server_host=None,
                 knp_server_port=None,
                 juman_server_host=None,
                 juman_server_port=None,
                 is_use_jumanpp=None,
                 process_mode='pexpect',
                 path_juman_rc=None,
                 timeout_second=60,
                 n_jobs=None):
        """* Parameters
        - knp_command: Path into Bin of KNP
        - juman_command: Path into Bin of Juman(or Juman++)
        - knp_server_host: Host address where KNP server is working
        - knp_server_port: Port number where KNP server is working
        - juman_server_host: Host address where Juman server is working
        - juman_server_port: Port number where Juman server is working
        - is_use_jumanpp: Bool flag to use Juman++ instead of Juman. You're supposed to install Juman++ beforehand.
        - process_mode: Way to call UNIX commands. 1; You call UNIX commands everytime. 2; You keep UNIX commands running.
        - path_juman_rc: Path into Jumanrc file.
        - timeout_second: 
        - n_jobs: Un-needed option. 
        """
        # type: (str,str,str,int,str,int,bool,str,str,int,int)->None
        PROCESS_MODE = ('everytime', 'pexpect')

        self.knp_command = knp_command
        self.juman_command = juman_command
        self.knp_server_host = knp_server_host
        self.knp_server_port = knp_server_port
        self.juman_server_host = juman_server_host
        self.juman_server_port = juman_server_port
        self.path_juman_rc = path_juman_rc
        self.is_use_jumanpp = is_use_jumanpp
        self.process_mode = process_mode
        self.timeout_second = timeout_second

        # Check jumanrc file path #
        if not self.path_juman_rc is None and not os.path.exists(self.path_juman_rc):
            raise Exception("No jumanrc file at {}".format(self.path_juman_rc))
        else:
            pass

        # Check flag combination & show warning message for a user #
        if not self.path_juman_rc is None:
            if self.is_use_jumanpp:
                logger.warning("path_juman_rc is invalid when is_use_jumanpp is True.")
            elif not self.juman_server_host is None:
                logger.warning("path_juman_rc is invalid when you use juman server mode.")
            else:
                pass
        else:
            pass

        if not self.process_mode in PROCESS_MODE:
            raise Exception("No process_mode named {}".format(self.process_mode))
        else:
            pass

        if os.name=='nt' and self.process_mode=='pexpect':
            logger.warning(msg="You could not use process_mode='pexpect' in Windows. It forces set process_mode = 'everytime'")
        else:
            pass

        # choose a way to call unix commands #
        if (not self.juman_server_host is None and not self.juman_server_port is None) and (not self.knp_server_host is None and self.knp_server_port is None):
            self.__launch_server_model()
        elif self.process_mode == 'pexpect':
            self.__launch_pexpect_mode()
        elif self.process_mode == 'everytime':
            self.__launch_everytime_mode()
        else:
            raise Exception("It failed to initialize. Check your configurations.")


    def __launch_pexpect_mode(self):
        """* What you can do
        - It defines process with pexpect
        """
        self.validate_arguments()
        # set juman/juman++ unix process #
        if self.is_use_jumanpp:
            self.juman = UnixProcessHandler(unix_command=self.juman_command,
                                            timeout_second=self.timeout_second)
        else:
            if not self.path_juman_rc is None:
                option_string = ' '.join(['-r', self.path_juman_rc])
            else:
                option_string = None
            self.juman = UnixProcessHandler(unix_command=self.juman_command,
                                            option=option_string,
                                            timeout_second=self.timeout_second)
        # set KNP unix process #
        self.knp= UnixProcessHandler(unix_command=self.knp_command,
                                     option='-tab',
                                     timeout_second=self.timeout_second)


    def __launch_everytime_mode(self):
        """"""
        self.validate_arguments()
        # set juman/juman++ unix command #
        if self.is_use_jumanpp:
            self.juman = [self.juman_command]
        else:
            if not self.path_juman_rc is None:
                self.juman = [self.juman_command, '-B', '-e2', '-r', self.path_juman_rc]
            else:
                self.juman = [self.juman_command, '-B', '-e2']

        # set KNP unix command #
        self.knp = [self.knp_command, '-tab']

    def __launch_server_model(self):
        """"""
        self.juman = [self.juman_command, '-C', '{}:{}'.format(self.juman_server_host, self.juman_server_port)]
        self.knp = [self.knp_command, '-C', '{}:{}'.format(self.knp_server_host, self.knp_server_port), '-tab']


    def validate_arguments(self):
        # argumentの検証方法を考えること
        if six.PY3:
            if shutil.which(self.juman_command) is None:
                raise Exception("No command at {}".format(self.juman_command))
            if shutil.which(self.knp_command) is None:
                raise Exception("No command at {}".format(self.juman_command))
        else:
            doc_command_string = "echo '' | {}".format(self.juman_command)
            command_check = os.system(doc_command_string)
            if not command_check == 0:
                raise Exception("No command at {}".format(self.juman_command))

            doc_command_string = "echo '' | {}".format(self.knp_command)
            command_check = os.system(doc_command_string)
            if not command_check == 0:
                raise Exception("No command at {}".format(self.knp_command))

    def __run_pexpect_mode(self, input_string):
        """* What you can do"""
        # type: (text_type)->text_type
        assert isinstance(self.juman, UnixProcessHandler)
        assert isinstance(self.knp, UnixProcessHandler)
        juman_result = self.juman.query(input_string=input_string)
        knp_result = self.knp.query(input_string=juman_result)

        return knp_result


    def __run_everytime_mode(self, input_string):
        """"""
        # type: (text_type)->text_type
        assert isinstance(self.juman, list)
        assert isinstance(self.knp, list)
        echo_process = ["echo", input_string]
        try:
            echo_ps = subprocess.Popen(echo_process, stdout=subprocess.PIPE)
            echo_ps.wait()
            juman_ps = subprocess.Popen(self.juman, stdin=echo_ps.stdout, stdout=subprocess.PIPE)
            juman_ps.wait()
            parsed_result = subprocess.check_output(self.knp, stdin=juman_ps.stdout)

            if six.PY2:
                return parsed_result
            else:
                return parsed_result.decode('utf-8')
        except subprocess.CalledProcessError:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error with CalledProcessError. traceback={}'.format(traceback_message)
        except UnicodeDecodeError:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error with UnicodeDecodeError traceback={}'.format(traceback_message)
        except Exception:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error traceback={}'.format(traceback_message)


    def __run_server_model(self, input_string):
        """"""
        # type: (text_type)->text_type
        assert isinstance(self.juman, list)
        assert isinstance(self.knp, list)
        echo_process = ["echo", input_string]
        try:
            echo_ps = subprocess.Popen(echo_process, stdout=subprocess.PIPE)
            echo_ps.wait()
            juman_ps = subprocess.Popen(self.juman, stdin=echo_ps.stdout, stdout=subprocess.PIPE)
            juman_ps.wait()
            parsed_result = subprocess.check_output(self.knp, stdin=juman_ps.stdout)

            if six.PY2:
                return parsed_result
            else:
                return parsed_result.decode('utf-8')
        except subprocess.CalledProcessError:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error with CalledProcessError. traceback={}'.format(traceback_message)
        except UnicodeDecodeError:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error with UnicodeDecodeError traceback={}'.format(traceback_message)
        except Exception:
            traceback_message = traceback.format_exc()
            logger.error("Error with command={}".format(traceback.format_exc()))
            return 'error traceback={}'.format(traceback_message)


    def run_command(self, text):
        """* What you can do
        - You run analysis of Juman(Juman++) and KNP.
        - You have 2 ways to call commands. 
        """
        # type: (text_type)->text_type
        if (not self.juman_server_host is None and not self.juman_server_port is None) and (not self.knp_server_host is None and self.knp_server_port is None):
            self.__run_server_model(text)
        elif self.process_mode == 'pexpect':
            self.__run_pexpect_mode(text)
        elif self.process_mode == 'everytime':
            self.__run_everytime_mode(text)
        else:
            raise Exception("It failed to initialize. Check your configurations.")



## For keeping old version
Params = KnpSubProcess


class DocumentObject(object):
    __slots__ = ('record_id', 'status', 'text',
                 'is_success', 'timestamp', 'updated_at', 'sub_id', 'parsed_result')

    def __init__(self,
                 record_id,
                 text,
                 status,
                 parsed_result=None,
                 is_success=None,
                 sub_id=None,
                 timestamp = datetime.now(),
                 updated_at = datetime.now()):
        # type: (int,text_type,bool,Union[None,str],bool,str,datetime,datetime) -> None

        if six.PY2:
            if isinstance(text, str):
                self.text = text.decode('utf-8')
            else:
                self.text = text

            if isinstance(sub_id, str):
                self.sub_id = sub_id.decode('utf-8')
            else:
                self.sub_id = sub_id

            if isinstance(parsed_result, str):
                self.parsed_result = parsed_result.decode('utf-8')
            else:
                self.parsed_result = parsed_result
        else:
            self.text = text
            self.sub_id = sub_id
            self.parsed_result = parsed_result

        self.record_id = record_id
        self.status = status
        self.timestamp = timestamp
        self.updated_at = updated_at
        self.is_success = is_success

    def set_knp_parsed_result(self, parsed_result):
        """* What you can do
        - It sets KNP parsed result
        """
        # type: (str)->None
        is_success_flag = self.__check_knp_result(parsed_result=parsed_result)
        self.is_success = is_success_flag
        self.parsed_result = parsed_result

    def __check_knp_result(self, parsed_result):
        """* What you can do
        - It checks if knp result is error or not
        """
        # type: (str)->bool
        if parsed_result is None:
            return False
        elif 'error' in parsed_result.lower():
            return False
        else:
            return True

    def to_dict(self):
        """* What you can do
        - You see parsed result with dict format
        """
        # type: ()->Dict[str,Any]
        return {
            "record_id": self.record_id,
            "sub_id": self.sub_id,
            "status": self.status,
            "text": self.text,
            "is_success": self.is_success,
            "parsed_result": self.parsed_result,
            "timestamp": self.timestamp,
            "update_at": self.updated_at
        }


class ResultObject(object):
    def __init__(self,
                 seq_document_obj,
                 path_working_db,
                 db_handler):
        """"""
        # type: (List[DocumentObject],str,Any)->None
        self.seq_document_obj = seq_document_obj
        self.path_working_db = path_working_db
        self.db_handler = db_handler

    def to_dict(self):
        """* What you can do
        - You get parsed result with dict format
        """
        # type: ()->List[Dict[str,Any]]
        return [doc_obj.to_dict() for doc_obj in self.seq_document_obj]



