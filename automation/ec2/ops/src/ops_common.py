import json
import logging
import os
import subprocess
import sys
import traceback
import xml.dom.minidom

# From ----------------------------------------------------------------------------
from datetime import datetime
from enum import Enum, unique
from io import StringIO
from pprint import pprint
from uuid import UUID, uuid4

# Spec+PIP ------------------------------------------------------------------------
import click
import yaml

from ops_xsl import XmlFragmentOps

# Local ---------------------------------------------------------------------------
from ops_yaml import (  # Level,; get_file_timestamp,
    APP,
    AuthRoles,
    EnvConfig,
    InfoBoard,
    RequestConfig,
    UserConfig,
)

# =================================================================================

def is_uuid_valid(uuid_to_test, version=4) -> bool:
    uuid_obj = None
    if uuid_to_test:
        try:
            APP.debug(f'\nBefore Validation{uuid_to_test=}\t{version=}')
            uuid_obj = UUID(uuid_to_test, version=version)
            APP.debug(f'\nAfter Validation{uuid_to_test=}\t{version=}')
        except ValueError:
            return False
    return str(uuid_obj) == uuid_to_test
#==================================================================================

class CommandRunner(object):

    def __init__(self) -> None:
        super().__init__()
        self.result: str = None
        self.out: str = None
        self.error: str = None
        self.code: str = None
        self.reset_status()
        self.commands = dict()
    # -----------------------------------------------------------------------------

    def reset_status(self):
        """ Simple reset of the status-state variables
        """
        self.result: str = None
        self.out: str = None
        self.error: str = None
        self.code: str = None
    # -----------------------------------------------------------------------------

    def get_command_text(self, command: list)-> str:
        return ' '.join(command)    
    # -----------------------------------------------------------------------------

    def get_newly_created_cognito_uuid_from_json(self, json_str:str) -> str : # | None ( Only Works in Python 3.11+)     
        APP.debug(f'Parsing JSON:\n{str(json.dumps(json_str, indent=2))}')
        try:
            info = json.load(StringIO(json_str))
            id = None
            if 'User' in info.keys() and 'Attributes' in info['User'].keys():
                id = [attribute['Value'] 
                    for attribute in info['User']['Attributes'] 
                    if attribute['Name']=='sub'] 
                APP.debug(f'UUID:{id[0]} from list:{id}')
            if id and len(id)==1 and is_uuid_valid(id[0]):
                APP.debug(f'UUID:{id[0]} from list:{id}')
                return id[0]
        except Exception as exc:
            self.error = '\n'.join(traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__))
            InfoBoard.pin_error(self.error + f'\nError in Json:\n"\n{json_str}\n"')
        return None
    # -----------------------------------------------------------------------------

    def get_preexisting_cognito_uuid_from_json(self, json_str:str) -> str : # | None ( Only Works in Python 3.11+)     
        APP.debug(f'Parsing JSON:\n{json.dumps(json_str, indent=2)}')
        try:
            info = json.load(StringIO(json_str))
            id = None
            if 'UserAttributes' in info.keys():
                id = [attribute['Value'] 
                    for attribute in info['UserAttributes'] 
                    if attribute['Name']=='sub'] 
                APP.debug(f'UUID:{id[0]} from list:{id}')
            if id and len(id)==1 and is_uuid_valid(id[0]):
                APP.debug(f'UUID:{id[0]} from list:{id}')
                return id[0]
        except Exception as e:
            self.error = str(e)
            InfoBoard.pin_error(self.error + f'\nError in Json:\n"\n{json_str}\n"')
        return None
    # -----------------------------------------------------------------------------
    def has_command_ran_correctly(self, 
                            command_to_run: list,
                            ) -> bool:        
        (cmd_stdOut, cmd_Err, os_retCode) = self.execute_command(command_to_run)
        # Example on how to execute commands with the error check
        if not cmd_Err and not os_retCode:
            APP.print(cmd_stdOut)
            id = self.get_cognito_uuid_from_json(cmd_stdOut)
            APP.print(cmd_stdOut)
            APP.print(f'{id=}')
        else:
            # log error using all available information:
            error_message =(  f"FAILED COMMAND:\n\t{' '.join(command_to_run)}\n"
                        f" Std-Out::\n\t{cmd_stdOut}\n"     # stdOut user_result_tuple[0],
                        f" Error:\n\t{cmd_Err}\n"           # stdError user_result_tuple[1], and 
                        f" OS-Code:\n\t{os_retCode}\n"      # bash error code user_result_tuple[2]
                      )
            InfoBoard.pin_error(error_message)
            return False
    # -----------------------------------------------------------------------------

    def execute_command(self, 
                        command:list[str], 
                        output_extractor: callable = None, 
                        quiet_mode:bool = False) -> tuple[str, str, int]:
        """ Runs the command provided as param
        Args:
            command (list): Command list[str] as required by Python subprocess module
        Returns:
            tuple[str, str, str]: Tuple consisting of: (stdOut, stdErr, OS-ReturnCode)
        """
        if APP.CLI_DEBUG_MODE=='debug' or APP.CMD_ONLY_PRINT:
            self.print_command(command)
            if APP.CMD_ONLY_PRINT:
                return ('', '', 0)

        self.reset_status()
        self.result = None
        proc = None
        if command and isinstance(command, list) and len(command)>0:
            try:
                proc = subprocess.run(command, encoding='utf-8', 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    stdin=subprocess.PIPE)
                ### If called needs post-processing of output
                ### (e.g. YAML/JSON parsing of the output)
                if output_extractor and callable(output_extractor) :
                    self.result = output_extractor(proc.stdout)
                else:
                    self.result = proc.stdout
            except Exception as ex:
                self.error = f"Command \n\t{command}\nFailed with exception: \n\t{ex}"
                self.code = f"-101"
            finally:
                # Finalize information gathering
                if proc:
                    self.result=proc.stdout
                    self.error=proc.stderr
                    self.code=proc.returncode
        else:
            self.error = f"No Command!!!"
            self.code = f"-1010"

        # if APP.CLI_DEBUG_MODE=='debug' or APP.CMD_ONLY_PRINT:
        #     InfoBoard.pin_info(f'Command: {self.get_command_text(command)}\n{self.result=}\n{self.error=}\n{self.code=}')
        self.report_command_status(command, quiet_mode)
            # print(f'\n Command:\n{self.get_command_text(command)}\nResult:{str(self.result)}\nError(s):{self.error}\nCode:{self.code}\n')
        return (self.result, self.error, self.code)
    # -----------------------------------------------------------------------------

    def report_command_status(self, command, quiet_mode = False, depth:int =5):
        if self.error and self.code!=0:
            InfoBoard.pin_error(f'Command: {self.get_command_text(command)}\n{self.result=}\n{self.error=}\n{self.code=}\n', depth=depth)
        elif not quiet_mode:
            InfoBoard.cmd_status(self.get_command_text(command),str(self.result), str(self.error), self.code, stack_depth=depth)
    # -----------------------------------------------------------------------------

    def execute_batch(self, commands:list) -> tuple[dict, list]:
        if APP.CMD_ONLY_PRINT or APP.CLI_DEBUG_MODE:
            self.print_commands(commands)
        if APP.CMD_ONLY_PRINT: ### Safety breaker for print-debugging
            return 
        
        results_special = []
        results_out = {}
        for index, command in enumerate(commands):
            cmd_stdout, cmd_error, sys_code, cmd_text = (None, None, None, None)
            ### For regular commands run command as usual
            if (isinstance(command, list) 
                and not isinstance(command, tuple)):
                cmd_stdout, cmd_error, sys_code = self.execute_command(command, quiet_mode=True)
                cmd_text = self.get_command_text(command)
                self.report_command_status(command, depth=6)
            ### For post-proc extended commands run stdout-parsing logic
            if (not isinstance(command, list) 
                and isinstance(command, tuple)) :
                if (    len(command) == 2 
                    and isinstance(command[0], list) 
                    and callable(command[1]) ):
                    cmd_stdout, cmd_error, sys_code = self.execute_command(command[0], command[1], quiet_mode=True)                    
                    cmd_text = self.get_command_text(command[0])
                    self.report_command_status(command[0], depth=6)
            ### Process the command result and unpack result is needed
            results_out[index] = (cmd_stdout, cmd_error, sys_code, cmd_text,)
            if (not cmd_error 
                and isinstance(command, tuple) 
                and self.result):
                    results_special.append(self.result)
        return (results_out, results_special)
    # -----------------------------------------------------------------------------

    def execute_batch_by_ids(self, command_ids:list) :
        if APP.CMD_ONLY_PRINT or APP.CLI_DEBUG_MODE:
            self.print_commands_by_ids(command_ids)
        if APP.CMD_ONLY_PRINT: ### Safety breaker for print-debugging
            return 
        
        commands = []
        commands_keys = self.commands.keys()
        for command_id in command_ids :
            if command_id not in commands_keys:
                InfoBoard.pin_error(f"Error! Command-ID: {command_id} is not found")
            else:
                commands.append(self.commands[command_id])
        return self.execute_batch(commands)
    # -----------------------------------------------------------------------------
    def print_commands(self, prefix: str = '', commands: dict = None) -> None:
        """ Prints commands in a simple form
        Args:
            commands (dict, optional): Prints Dict if passed, Prints self.commands in nothing was passed. Defaults to None.
        """
        print(f'Would Execute the Following Commands Batch:\n')
        if prefix:
            print(prefix)
        else:
            print(f'Instance of "{type(self).__name__}" Commands:')
        if not commands:
            commands = self.commands
        [print(f'{k}:\n\t{" ".join(v)}') for (k, v) in commands.items()]
    # -----------------------------------------------------------------------------

    def print_commands_by_ids(self, command_ids: list = None, prefix: str = '') -> None:
        """ Prints commands in a simple form
        Args:
            commands (dict, optional): Prints Dict if passed, Prints self.commands in nothing was passed. Defaults to None.
        """
        print(f'Would Execute the Following Commands Batch (by IDs):\n')
        if prefix:
            print(f'\n{prefix}')
        else:
            print(f'\nInstance of "{type(self).__name__}" Commands:')
        if self.commands:
            commands_keys = self.commands.keys()
            [print(f'{id}:\n\t{" ".join(self.commands[id])}') for id in command_ids if id in commands_keys]            
    # -----------------------------------------------------------------------------
    def print_command(self, command, prefix:str = None) -> None:
        print(f'Would Execute the Following Commands Batch:\n')
        if prefix:
            print(prefix)
        else:
            print(f'Instance of "{type(self).__name__}" Commands:')
        print(f"{self.get_command_text(command)}")
    # -----------------------------------------------------------------------------
#==================================================================================

@unique
class CommandEC2(Enum):

    # IDP Commands
    IDP_CREATE_USER = 1
    IDP_READ_USER = 2
    IDP_UPDATE_USER = 3
    IDP_DELETE_USER = 4


    # S3 Commands
    S3_FILE_EXISTS = 11
    S3_MOVE_FILE = 12

    # SSP Commands
    SSP_CREATE_USER = 21
    SSP_READ_USER = 22
    SSP_UPDATE_USER = 23
    SSP_DELETE_USER = 24

    # AMB Commands
    AMB_REGISTER_USER = 31
    AMB_ENROLL_USER = 32
    AMB_DEACTIVATE_USER = 33
    AMB_REMOVE_USER = 34
    AMB_READ_USER = 35

    # SYS Commands
    SYS_REMOVE_GIT_DIR = 41
    SYS_COPY_CMD_FILE = 42

    # GIT Commands
    GIT_CLONE_REPO = 51
    GIT_PULL_ALL = 52
    GIT_ADD_CHANGES = 53
    GIT_COMMIT_CHANGES = 54
    GIT_PUSH_CHANGES = 55
    GIT_CHECKOUT_BRANCH = 56

    # SSM Commands
    SSM_PUT_CERT = 60
    SSM_PUT_MSPID = 61
    SSM_PUT_PK = 62

    # GIT Commands
    DEB_PRINT_ENV = 70

    def cmd_key(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name

    # -----------------------------------------------------------------------------
#==================================================================================
class RepoOperations(CommandRunner):
    def __init__(   self, 
                    reqInfo: RequestConfig,
                    envInfo: EnvConfig,
                ) -> None:
        super().__init__()
        self.userReq = reqInfo
        self.envInfo = envInfo
        self.commands=self.init_commands()
        self.cmd_file = None
        ### Just in case we need to iterate through modified list 
        # ## Since Python 3.7 - the keys() PRESERVE the insertion order!
        self.exec_prep = self.commands.keys() 
    # -----------------------------------------------------------------------------
    def get_init_git_repo_commands(self,):
        return [
            CommandEC2.DEB_PRINT_ENV ,             
            CommandEC2.SYS_REMOVE_GIT_DIR,
            CommandEC2.GIT_CLONE_REPO,
            CommandEC2.GIT_PULL_ALL,
            CommandEC2.GIT_CHECKOUT_BRANCH,
            ]
    # -----------------------------------------------------------------------------+
    def get_finish_git_repo_commands(self,):
        return [
                CommandEC2.GIT_ADD_CHANGES,
                CommandEC2.GIT_COMMIT_CHANGES,
                CommandEC2.GIT_PUSH_CHANGES,
            ]
    # -----------------------------------------------------------------------------+

    def init_commands(self, ) -> dict:
        self.commands = dict()

        self.commands[CommandEC2.DEB_PRINT_ENV] = [ 'printenv', ]            
        ### Clean up the repo directory to make sure it is clean repo
        self.commands[CommandEC2.SYS_REMOVE_GIT_DIR] = [
                'rm', '-rf', self.envInfo.get_git_repo_dir()]
        
        REPO_SSH = self.envInfo.get_git_repo()
        REPO_PATH = self.envInfo.get_git_repo_dir()
        USER_DIR = self.envInfo.get_bat_user_dir()
        CMD_FILE = self.userReq.get_cmd_file_name()
        self.ssp_xml = self.envInfo.get_ssp_xml()
        self.sap_xml = self.envInfo.get_sap_xml()
        self.sar_xml = self.envInfo.get_sar_xml()
        self.poam_xml = self.envInfo.get_poam_xml()

        ### E.G. git clone git@github.com:USER-NIST/blossom-oscal-auto.git ./x/y
        self.commands[CommandEC2.GIT_CLONE_REPO] = [
                'git', 'clone', 
                REPO_SSH, 
                REPO_PATH, ]        
        ### checkout example 
        self.commands[CommandEC2.GIT_CHECKOUT_BRANCH] = [
                'git', '-C', f'{REPO_PATH}', 
                'checkout', '-b', 
                f'{self.userReq.get_branch_name()}',
                f'origin/{self.userReq.get_branch_name()}',] 
                ### '--track', f'origin/{self.userReq.get_branch_name()}' ### Works only if branch already exists in remote
        ### Git pull         
        self.commands[CommandEC2.GIT_PULL_ALL] = [
                'git', '-C', f'{REPO_PATH}',  
                'pull', '--all', ] 
        ### Copy User-File
        self.commands[CommandEC2.SYS_COPY_CMD_FILE] = [
                'cp', os.path.join(REPO_PATH, CMD_FILE) , USER_DIR]
        ### Preserve the cmd_file for further use
        self.cmd_file = os.path.join(USER_DIR, CMD_FILE)        
        ### Add SSP to change-set
        self.commands[CommandEC2.GIT_ADD_CHANGES] = [
                'git', '-C', f'{REPO_PATH}', 
                'add', f'{self.ssp_xml}', ] 
        ### Write commit message
        self.commands[CommandEC2.GIT_COMMIT_CHANGES] = [
                'git', '-C', f'{REPO_PATH}', 
                'commit', '-m', 
                (f"'BloSS🌻M auto-process addressed request in ticket #{self.userReq.get_issue_number()}'"
                 ), ] 
        ### Git push         
        self.commands[CommandEC2.GIT_PUSH_CHANGES] = [
                'git', '-C', f'{REPO_PATH}', 
                'push', '--set-upstream','origin',f'{self.userReq.get_branch_name()}', 
                ]  
        return self.commands
    
    # -----------------------------------------------------------------------------
#==================================================================================
class UserOperations(CommandRunner):

    def __init__(   self, 
                    reqInfo: RequestConfig,
                    userInfo: UserConfig, 
                    envInfo: EnvConfig,
                ) -> None:
        super().__init__()
        self.userReq = reqInfo
        self.envInfo = envInfo
        self.userInfo = userInfo
        self.commands = self.init_commands()
     # -----------------------------------------------------------------------------
    def get_party_path(self):
        return os.path.join(self.envInfo.get_bat_user_dir(), self.userReq.get_party_xml_file())
     # -----------------------------------------------------------------------------
    def get_idp_attributes(self, attr: dict)-> str:
        str_list = [f'Name={k},Value="{v}"' for (k,v) in attr.items()]
        pprint(str_list)
        return ' '.join(str_list)
    # -----------------------------------------------------------------------------+
    def get_idp_attributes_list(self, attr: dict)-> str:
        str_list = [f'Name={k},Value="{v}"' for (k,v) in attr.items()]
        pprint(str_list)
        return str_list
    # -----------------------------------------------------------------------------+
    def get_user_attributes_as_idp_string(self) -> str:
        """ Produces aws cognito-idp-shaped string of attributes from YAML files
        Returns:
            str: Max-possible attributes string
        """
        idp_attributes = self.userInfo.create_cognito_attributes()
        return self.get_idp_attributes(idp_attributes)
    # -----------------------------------------------------------------------------+
    def get_user_attributes_as_idp_list(self) -> str:
        """ Produces aws cognito-idp-shaped string of attributes from YAML files
        Returns:
            str: Max-possible attributes string
        """
        idp_attributes = self.userInfo.create_cognito_attributes()
        return self.get_idp_attributes_list(idp_attributes)
    # -----------------------------------------------------------------------------+
    def get_create_idp_user_commands(self,):
        return [
                CommandEC2.IDP_CREATE_USER,
                CommandEC2.IDP_READ_USER,
            ]
    # -----------------------------------------------------------------------------+
    def get_delete_idp_user_commands(self,):
        return [
                CommandEC2.IDP_DELETE_USER,
                CommandEC2.IDP_READ_USER,
            ]
    # -----------------------------------------------------------------------------+
    def get_create_fabric_user_commands(self,):
        return [
                CommandEC2.AMB_REGISTER_USER,
                CommandEC2.AMB_ENROLL_USER,
            ]
    # -----------------------------------------------------------------------------+


    def init_commands(self, ) -> dict:
        x=''
        commands = dict()
        self.commands=None
        # aws cognito-idp admin-create-user \
        # --user-pool-id us-east-1_wioSQKwya 
        # --username z-test-27 
        # --user-attributes Name=email,Value=blossom@nist.gov Name=profile,Value='some weird value' Name=email_verified,Value=false
        # print(dir(self.userInfo))

        commands[CommandEC2.IDP_CREATE_USER] = [
                'aws', 'cognito-idp', 'admin-create-user', 
                '--user-pool-id',   f'{self.envInfo.get_aws_idp_pool()}',   # !!! ENV Configuration Derived !!! 
                '--username',       f'{self.userInfo.get_user_id()}',         # !!! USER Configuration Derived !!! 
                '--user-attributes', self.get_user_attributes_as_idp_string(),
                '--temporary-password', '"B@TempPass~123"', 
                '--output', 'json']
        ### !!! Special treatment of the attributes - otherwise Python Execution fails
        commands[CommandEC2.IDP_CREATE_USER].append('--user-attributes') 
        commands[CommandEC2.IDP_CREATE_USER].extend(self.get_user_attributes_as_idp_list()) 
        # aws cognito-idp admin-delete-user --user-pool-id us-east-1_wioSQKwya --username z-test-27
        commands[CommandEC2.IDP_READ_USER] = [
                'aws', 'cognito-idp', 'admin-get-user', 
                '--user-pool-id',   f'{self.envInfo.get_aws_idp_pool()}',   # !!! ENV Configuration Derived !!! 
                '--username',       f'{self.userInfo.get_user_id()}',         # !!! USER Configuration Derived !!! 
                '--output', 'json']
        commands[CommandEC2.IDP_UPDATE_USER] = [
                'aws', 'cognito-idp', 'admin-update-user-attributes', 
                '--user-pool-id',   f'{self.envInfo.get_aws_idp_pool()}',   # !!! ENV Configuration Derived !!! 
                '--username',       f'{self.userInfo.get_user_id()}',         # !!! USER Configuration Derived !!! 
                '--user-attributes', self.get_user_attributes_as_idp_string(),
                '--output', 'json']
        
        commands[CommandEC2.SYS_REMOVE_GIT_DIR] = ['rm', '-rf', '', self.envInfo.get_git_repo_dir()]  

        ### E.G. git clone git@github.com:USER-NIST/blossom-oscal-auto.git ./x/y
        commands[CommandEC2.GIT_CLONE_REPO] = [
                'git', 'clone', 
                self.envInfo.get_git_repo(), 
                self.envInfo.get_git_repo_dir()]  
        # checkout example
        commands[CommandEC2.GIT_CHECKOUT_BRANCH] = [
                'git', '-C', f'{self.envInfo.get_git_repo_dir()}', 
                'checkout',
                f'-b {self.userReq.get_branch_name()}', 
                ### '--track', f'origin/{self.userReq.get_branch_name()}' ### Works only if branch already exists in remote
                ]  
        # 
        commands[CommandEC2.GIT_COMMIT_CHANGES] = [
                'git', '-C', f'{self.envInfo.get_git_repo_dir()}', 
                'commit,' f'-m {self.userReq.get_branch_name()}', 
                ]  
        ### SSP XML Update
        commands[CommandEC2.SSP_CREATE_USER] = [
                    'python', 'ops_xsl.py', 'insert-party' 
                    '-s', self.userInfo.get_ssp_path(),
                    '-u', self.get_party_path(),
                ]
        ###
        commands[CommandEC2.SSM_PUT_CERT]  = [

                ]

        commands[CommandEC2.AMB_READ_USER] = ['fabric-ca-client', 
                'identity', 'list', 
                '--id', self.userInfo.get_user_id(),  
                '--tls.certfiles', self.envInfo.get_amb_tls_cert()]
        ### ./fabric-ca-client register -d 
        ### --id.name org1admin --id.secret org1-adminpw 
        ### -u https://example.com:7054 
        ### --mspdir ./org1-ca/msp 
        ### --id.type admin --tls.certfiles ../tls/tls-ca-cert.pem       
        commands[CommandEC2.AMB_REGISTER_USER] = [
                'fabric-ca-client', 'register',
                '-d',   # FLAG FOR DEBUGGING
                '-u',               f'{self.envInfo.get_amb_ca_url()}',  # <CA_URL> https://<ENROLL_ID>:<ENROLL_SECRET><@CA_URL>:<PORT>
                '--mspdir',         f'{self.envInfo.get_amb_msp_dir()}',  # <CA_ADMIN> 
                '--id.name',        f'{self.userInfo.get_user_id()}',  # <ID_NAME>
                '--id.secret',      f'{self.envInfo.get_amb_default_secret()}',  # <ID_SECRET> 
                '--id.type',        'client',  # <ID_TYPE> 
                '--id.attrs',       f"'blossom.role={self.userInfo.get_role().strip()}'",  # $ID_ATTRIBUTES - JSON Object 
                '--tls.certfiles',  f'{self.envInfo.get_amb_tls_cert()}',  # TLS-CA-Root path-file
                ]
        ### 
        commands[CommandEC2.AMB_ENROLL_USER] = [
                'fabric-ca-client', 'enroll' ,
                ### https://{u_id}:{u_pwd}@ca.m-dtlkikvwwzer3duhqudh43i7yq.n-flxxkm7invcdxgqmuah633e6pq.managedblockchain.us-east-1.amazonaws.com:30006   \
                '-u', (f'https://{self.userInfo.get_user_id()}:{self.envInfo.get_amb_default_secret()}'
                       f'{self.envInfo.get_amb_enroll_url()}'
                       ), 
                '-M', os.path.join( self.envInfo.get_amb_clients_dir() , self.userInfo.get_user_id(), 'msp'),
                '--tls.certfiles',  f'{self.envInfo.get_amb_tls_cert()}',
                '--enrollment.attrs', f"'blossom.role={self.userInfo.get_role().strip()}'",
                ]
        return commands
    # ---------------------------------------------------------------------------------
    def get_idp_user(self, ) -> tuple[str, str]:
        user_uuid = ''
        user_name = ''
        read_user_cmd = self.commands[CommandEC2.IDP_READ_USER]
        # [   'aws', 'cognito-idp', 'admin-get-user', 
        #     '--user-pool-id',   f'{self.envInfo.get_aws_idp_pool()}',   # !!! ENV Configuration Derived !!! 
        #     '--username',       f'{self.userInfo.get_user_id()}',         # !!! USER Configuration Derived !!! 
        #     '--output', 'json']
        (maybe_json, err, code) = self.execute_command(read_user_cmd)

        if maybe_json.strip().startswith('{'):
            APP.debug(f"Before pulling user uuid in get_idp_user {user_uuid=}")
            user_uuid = self.get_preexisting_cognito_uuid_from_json(maybe_json.strip())
            user_name = self.userInfo.get_user_id()
            APP.debug(f"After querying user {user_name} uuid in get_idp_user {user_uuid=}")

        elif (  code==254 
                or 'User does not exist' in err 
                or 'UserNotFoundException' in err):
            APP.debug(f"User {self.userInfo.get_name()}/{self.userInfo.get_user_id()} does not exist")

        APP.debug(f"in create_idp_user {user_uuid=}")
        return (user_name, user_uuid)
    # ---------------------------------------------------------------------------------
    def create_idp_user(self,) -> tuple[str, str]:
        existing_user_uuid = ''
        new_user_uuid = ''
        user_name = ''

        (user_name, existing_user_uuid) = self.get_idp_user()

        APP.debug(f"in create_idp_user {existing_user_uuid=}")

        if not existing_user_uuid:
            create_idp_user_cmd = self.commands[CommandEC2.IDP_CREATE_USER]
            (maybe_json, err, code) = self.execute_command(create_idp_user_cmd)
            new_user_uuid = self.get_newly_created_cognito_uuid_from_json(maybe_json)
            APP.debug(f"New User UUID create_idp_user {new_user_uuid=}")

        return (user_name, existing_user_uuid if existing_user_uuid else  new_user_uuid)
    # ---------------------------------------------------------------------------------+
    def create_fabric_user(self,) -> tuple[str, str]:
        ### VErify that the user doesn't yet exist
        read_amb_user_cmd = self.commands[CommandEC2.AMB_READ_USER] 
        (maybe_amb_user, error, code) = self.execute_command(read_amb_user_cmd )
        APP.debug(f"{maybe_amb_user=}, {error=}, {code=}")
        if code!=0: ### This means that the user already was registered
            error_63 = 'Error Code: 63'
            if error_63 in error:
                ### This is actually the HAPPY PATH - User doesn't Exist in AMB
                APP.debug(f"Command [{self.get_command_text(read_amb_user_cmd)}]\n"
                        f"Returned Code:{code} and Error:{error}\n"
                        )
                ### Register AMB User
                register_user = self.commands[CommandEC2.AMB_REGISTER_USER]
                (maybe_amb_user, error, code) = self.execute_command(register_user )
                ### Enroll AMB User
                enroll_user = self.commands[CommandEC2.AMB_ENROLL_USER]
                (maybe_amb_user, error, code) = self.execute_command(enroll_user )
                ## APP.debug(f'Ready to Run Commands:\n{self.get_command_text(register_user)}\n{self.get_command_text(enroll_user)}')
        else:
            ### This is name already registered or enrolled case - User EXISTS in AMB            
            APP.debug(f"Command: {self.get_command_text(read_amb_user_cmd)}\n"
                      f"Returned User: {maybe_amb_user}\n"
                      )

        return('', '')        
    # ---------------------------------------------------------------------------------+
    def create_ssm_entries(self, ) -> None:
        pass
    # ---------------------------------------------------------------------------------+
    def compose_create_party_fragment_file(self, party_uuid: str) -> str: 

        first, middle, last = self.userInfo.get_split_names(self.userInfo.get_name())
        short_name = (  f'<short-name>{first}-{last[0]}</short-name>' 
                        if first and last 
                        else 
                        f'<short-name>{first}</short-name>'
                        )
        user_title = f'<prop name="job-title" value="{self.userInfo.get_role()}" />'        
        is_priv = "privileged" if self.userInfo.is_ssp_role_privileged() else "non-privileged"
        prop_priv = f'<prop name="privilege-level" value="{is_priv}" ns="https://github.com/marketplace/actions/upload-s3" />'

        ## Should we add default organization UUID to ENV-File to allow membership to flow and be preserved?
        # member = f"<member-of-organization>8aed7ffd-5158-445d-8d7c-eec5cf240cba</member-of-organization>"
        draft_xml = (
        f"""<insert  xmlns="http://csrc.nist.gov/ns/oscal/1.0">
            
            <!-- The Actual Party -->
            <party uuid="{party_uuid}" type="person">
                <email-address>{self.userInfo.get_email()}</email-address>
                <name>{self.userInfo.get_name()}</name>
                {short_name}
                {user_title}
                {prop_priv}
            </party>

            <!-- Responsible Party -->
            <responsible-party role-id="{self.userInfo.get_role_enum()}">
                <party-uuid>{party_uuid}</party-uuid>
            </responsible-party>

        </insert>"""
        )
        pretty_xml = XmlFragmentOps.prettify_xml(draft_xml)

        self.create_fragment_file = os.path.join(
            self.envInfo.get_bat_user_dir(), 
            self.userReq.get_party_xml_file())
                
        with open(self.create_fragment_file, 'w', encoding='utf-8') as xml_file:
            xml_file.write(pretty_xml)
        return self.create_fragment_file
    # ---------------------------------------------------------------------------------+
    def get_amb_user(self, ) -> tuple[str, str]:
        user_uuid = ''
        user_name = ''
        read_user_cmd = self.commands[CommandEC2.AMB_READ_USER]
        ### ['fabric-ca-client', 
        ###         'identity', 'list', 
        ###         '--id', self.userInfo.get_user_id(),  
        ###         '--tls.certfiles', self.envInfo.get_amb_tls_cert()]
        (maybe_amb_guts, err, code) = self.execute_command(read_user_cmd)
        ### Name: AOrt, 
        # Type: client, 
        # Affiliation: NIST, 
        # Max Enrollments: 6, 
        # Attributes: [
        # {     Name:blossom.role 
        #       Value:Authorizing Official 
        #       ECert:false} 
        # {     Name:hf.EnrollmentID
        #       Value:AOrt 
        #       ECert:true} 
        # {     Name:hf.Type 
        #       Value:client 
        #       ECert:true} 
        # {     Name:hf.Affiliation 
        #       Value:NIST 
        #       ECert:true}]
        if maybe_amb_guts.strip().startswith('{'):
            APP.debug(f"Before pulling user uuid in get_idp_user {user_uuid=}")
            user_uuid = self.get_preexisting_cognito_uuid_from_json(maybe_json.strip())
            user_name = self.userInfo.get_user_id()
            APP.debug(f"After querying user {user_name} uuid in get_idp_user {user_uuid=}")

        elif (  code==254 
                or 'User does not exist' in err 
                or 'UserNotFoundException' in err):
            APP.debug(f"User {self.userInfo.get_name()}/{self.userInfo.get_user_id()} does not exist")

        APP.debug(f"in create_idp_user {user_uuid=}")
        return (user_name, user_uuid)
    # ---------------------------------------------------------------------------------
#======================================================================================

class S3Operations(CommandRunner):

    def __init__(   self, 
                    s3_file: str,
                    envInfo: EnvConfig,
                ) -> None:
        super().__init__()
        self.s3_file = s3_file
        self.s3_file_url = f'{envInfo.get_aws_s3_drop_url()}{s3_file}'
        self.envInfo = envInfo
        self.rec_file =f'{envInfo.get_bat_user_dir()}/{s3_file}'
        self.commands=self.init_commands(self.envInfo, self.s3_file)
     # -----------------------------------------------------------------------------

    def init_commands(self,envInfo: EnvConfig, s3_file:str ) -> dict:
        self.commands=None
        commands = dict()
        ### is_s3_file
        commands[CommandEC2.S3_FILE_EXISTS] = [ 
                        'aws', 's3api', 'head-object', 
                        '--bucket', envInfo.get_aws_s3_drop_name(),
                        '--key',  f'{s3_file}',
                        ]
        ### Move S3 file to User-Dir
        # move_s3_file 
        commands[CommandEC2.S3_MOVE_FILE]  = [ 
                        'aws', 's3',  
                        'mv', 
                            self.s3_file_url,  
                            self.rec_file,
                        ]
        return commands
     # -----------------------------------------------------------------------------

    def s3_file_exists(self) -> bool:
        stdOut, stdErr, err =  self.execute_command(
                self.commands[CommandEC2.S3_FILE_EXISTS])        
        return err==0
    # -----------------------------------------------------------------------------

    def s3_file_move(self) -> bool:
        stdOut, stdErr, err =  self.execute_command(
            self.commands[CommandEC2.S3_MOVE_FILE])
        return err==0
    # -----------------------------------------------------------------------------
#==================================================================================


def move_s3_file(   s3_ops: S3Operations, 
                ) -> str:
    """ Moves S3 File to Local Directory Making REC-File
    Args:
        s3_ops (str): S3-Operations command aggregation object
        env_file (str): Path-File for environment configuration
    """
    ### Verify that S3-Ops is object, S3 file EXISTS, and IS-FILE
    if not( s3_ops and s3_ops.s3_file_exists() ):
        ### Break-Up Fix Logic [Trying to Reduce Error-Conditions]
        if not(s3_ops.rec_file and os.path.isfile(s3_ops.rec_file)):
            InfoBoard.pin_error(f'S3-File {s3_ops.s3_file} Not Found')
            return None
        if s3_ops.rec_file and os.path.isfile(s3_ops.rec_file):
            ### File was ALREADY copied [Possible Condition]
            InfoBoard.pin_info(f'\tNo S3-File Detected, but:\n\t{s3_ops.rec_file}\n\tis local and is ready to use')
            return s3_ops.rec_file
    else:
        ### Move S3 file to User-Dir
        if s3_ops.s3_file_move():
            ### Return the newest local REC-file
            return s3_ops.rec_file
        else:
            InfoBoard.pin_error(f'File {s3_ops.s3_file} Not Moved')
            return None
    return None
# ---------------------------------------------------------------------------------
def create_fabric_user(recInfo, userInfo, envInfo) -> str:
    return ''

# ---------------------------------------------------------------------------------
def dispatch_command(envInfo: EnvConfig, recInfo: RequestConfig) -> bool:

    ### Read UserConfig:
    ###     Clean Repo-DIR
    ###     Clone Repo
    ###     Pull the branch from reqInfo
    ###     Copy the User-Command File to Users-Dir
    ###     Safely INIT the userInfo

    ### Determine Command ( Create|Read|Update|Delete|??? )
    ### Dispatch the command execution
    if not (envInfo and recInfo):
        if not envInfo:
            InfoBoard.pin_error(f'Missing valid Environment file')
            return False
        if not recInfo:
            InfoBoard.pin_error(f'Missing valid Request file')
            return False
    else:
        ### Here we have 2 Required files and can try 
        ### Using Git-User-File determine COMMAND and Dispatch
        repo_ops = RepoOperations(recInfo, envInfo)
        print('\n\n')
        repo_ops.print_commands()

        
        ### Git-Repo Preparation logic
        repo_ops.execute_batch_by_ids(repo_ops.get_init_git_repo_commands())
        user_ops = None
        APP.debug(f'Concatenating:\n{recInfo.get_cmd_file_name()=}\nand\n{envInfo.get_git_repo_dir()=}')
        user_file = os.path.join(envInfo.get_git_repo_dir(), recInfo.get_cmd_file_name())
        APP.debug(f'Working on {user_file=}')        
        if not os.path.isfile(user_file):
            APP.debug(f'The FILE:\n{user_file=}\ncould not be found!!!')
        if os.path.isfile(user_file):
            userInfo = UserConfig(user_file)
            APP.debug(user_file)
            APP.print_dir(userInfo)

            ### Alt-Implementation for Python <3.10
            ### Read COMMAND from the user-command-file
            user_ops = UserOperations(recInfo, userInfo, envInfo)
            user_command = userInfo.get_command()
            if user_ops:
                APP.debug(f'Executing User Command: {user_command}')
                ### CREATING USER
                if user_command=='create-user': 
                    ### Create or Read (if Exists) User & Get UUID                
                    (user_name, cognito_user_uuid) = user_ops.create_idp_user()
                    APP.debug(f'Created user: {user_name} with UUID: {cognito_user_uuid}')
                    ### Register User in AMB [if needed]
                    user_role = userInfo.get_role()

                    ### Create Fabric-User if Required
                    if AuthRoles.is_fabric_role( user_role ):
                        user_ops.create_fabric_user()
                        ### Create User SSM Entries [if needed]
                        user_ops.create_ssm_entries()
                    elif AuthRoles.is_fabric_read_role( user_role ):
                        ### Create User SSM Entries [if read-rights are needed]
                        ### Map the user to read only service AMB-service role
                        user_ops.create_read_ssm_entries()
                        pass

                ### Update SSP-Document
                if is_uuid_valid(cognito_user_uuid):
                    ### Create XML equivalent of User-File
                    user_ops.compose_create_party_fragment_file(cognito_user_uuid)
                    ### Update SSP
                    pass
                    # user_xml = userInfo.get
                ### DELETING USER
                elif user_command=='delete-user': 
                    ### Read User if Exists (Blow Otherwise) => Get UserID & UUID 
                    ### Remove User from AMB [if needed]
                    ### KILL User SSM Entries [if needed]
                    ### Create XML equivalent of User-Delete-File
                    ### Update SSP
                    pass

            """ Doesn't work in Python below 3.10
            user_command = userInfo.get_command()
            match user_command:
                case 'create-user': 
                    ### Create User & Get UUID                
                    user_uuid = create_idp_user(recInfo, userInfo, envInfo)
                    if AuthRoles.is_fabric_role( userInfo.get_role()):
                        ### Create FAbric-User if Required
                        create_fabric_user(recInfo, userInfo, envInfo)
                    ### Update SSP
                    if user_ops.is_uuid_valid(user_uuid):
                        user_xml = userInfo.get
                case 'delete-user':
                    delete_user()
                case 'update-user':
                    pass
            """

        ### Git-Repo Finishing Logic [i.e. Add-Commit-Push]
        if APP.CMD_ONLY_PRINT or APP.CLI_DEBUG_MODE:
            repo_ops.print_commands_by_ids(repo_ops.get_finish_git_repo_commands())
        if not APP.CMD_ONLY_PRINT:
            # repo_ops.execute_batch_by_ids(repo_ops.get_finish_git_repo_commands())
            pass

    return True
# ---------------------------------------------------------------------------------
# =================================================================================


@click.command(help="process-s3-file: Creates BloSS🌻M User as required per role")
@click.option('--s3_file', '-s3',
                help="BloSS🌻M original S3-sourced YAML-file-trigger")
# @click.option('--user_file', '-u',
#                 help="BloSS🌻M user-to-create YAML-file request")
@click.option('--env_file', '-e', default='./env-ec2-prod.yaml',
                help="BloSS🌻M AWS-EC2-AMB-GitHub env-description YAML-file")
def process_s3_file(s3_file:str, 
                    env_file: str, ):
    """ Launches whole S3-processing process
    Args:
        s3_file (str): The name of the S3 file to move and process
        env_file (str): The name of the AWS-EC2 environment file
    """
    envInfo = recInfo = None        ### Create ENV and REC empty objects
    InfoBoard.pin_info(              ### Print-Log info about the REC-file being processed
        f'Starting PROCESS-S3-FILE for:\nS3-File:\t{s3_file}\nEnv-File:\t{env_file}'
        ) 
    
    ### ❌❌❌ BREAK EARLY if parameters or files are missing 
    if not(env_file and os.path.isfile(env_file) and s3_file):
        ### Make click-help message stdout about incorrect use
        click.echo(click.get_current_context().get_help()) ### Show CLI HELP
        return
    
    ### ✅✅✅ If we are here - all the params were OK 👍👍👍
    envInfo = EnvConfig(env_file)       ### Read the environment descriptor from the EC2-Located-File
    APP.init_log(envInfo)               ### Init Logging and stdOut reporting
    ### Init S3 operations and move the requirements file if needed
    s3_ops = S3Operations(s3_file, envInfo)     ### Init the commands object for the S3-Ops
    rec_file = move_s3_file(s3_ops)             ### Get moved file or existing and moved previously

    ### ❌❌❌ BREAK EARLY if S3 file did not get moved locally
    if not( rec_file and os.path.isfile(rec_file) ):
        InfoBoard.pin_error(f'S3 File {s3_ops.s3_file_url} Not Moved') ### Show Error Message
        return
    
    ### ✅✅✅ Work with the local REC-file
    if rec_file and os.path.isfile(rec_file):
        InfoBoard.pin_info(f'\tLocal S3 File {s3_ops.s3_file_url}\n\tMoved to {s3_ops.rec_file}')
        if os.path.isfile(rec_file):
            recInfo = RequestConfig(rec_file)
            if not dispatch_command(envInfo, recInfo): ### Dispatch command processing
                ### ❌❌❌ BREAK EARLY if failed to dispatch
                InfoBoard.pin_error(f'Failed to dispatch command from REC-file {rec_file}')
                return
            else:
                InfoBoard.pin_info(f'Successfully dispatched command from REC-file {rec_file}')
        else:
            InfoBoard.pin_error(f'REC-File {rec_file} Not Found')
            return 
# -----------------------------------------------------------------------------

@click.command(help="create-user: Creates BloSS🌻M User as required per role")
@click.option('--s3_file', '-s3',
                help="BloSS🌻M original S3-sourced YAML-file-trigger")
# @click.option('--user_file', '-u',
#                 help="BloSS🌻M user-to-create YAML-file request")
@click.option('--env_file', '-e',
                help="BloSS🌻M AWS-EC2-AMB-GitHub env-description YAML-file")
def create_user(req_file:str, 
                env_file: str, 
                ):
    ### 1. Validate Input, Prep git-repo and User-CMD-File
    ### 2. Verify Command is Create USER
    ### →3.a-(Create) Create IDP-Cognito User based on Env&User Files
    ###     4. Query User, Get (sub-value) i.e. UUID
    ###     5.? If User is Fabric-User Create (register-enroll) Fabric User
    ###     6. Clone Repo + Checkout Branch
    ###     7. Create Insert-XML file from YAML
    ###     8. Update SSP with party and  responsible-party
    ###     9. Add-Commit-Push Repo + Remove Repo Directory
    print(f'\n\n\t!!!===---Create-User---===!!!\n\n')
    if not(env_file and req_file):
        ### Make click-noise about incorrect use
        click.echo(click.get_current_context().get_help())
        return

    if not os.path.isfile(env_file):
        ### Make noise (!!! Also Log the Error !!!)
        InfoBoard.pin_error(f"The file {env_file} does not exist or isn't a file")
        return
    else:
        envInfo = EnvConfig(env_file)       ### EC2-Located-File
    if not os.path.isfile(req_file):
        ### Make noise  (!!! Also Log the Error !!!)
        InfoBoard.pin_error(f"The file {req_file} does not exist or isn't a file")
        return
    ### Read the files
    reqInfo = RequestConfig(req_file)     ### S3-Transferred-File

    ### Here we have 2 Required files
    prep_ops = RepoOperations(reqInfo, envInfo)
    print('\n\n')
    prep_ops.print_commands()

    user_file = None
    ###
    if user_file:
        userInfo = UserConfig(user_file)
        runner = UserOperations(reqInfo, userInfo, envInfo)

        print(f"\n\t{userInfo.generate_create_user_xml('UUID', '')=}\n")
        userInfo.make_party_file('./20240923-170738_party2create.xml', uuid4(), '')
        
        cmd = runner.init_commands()
        pprint(cmd[CommandEC2.IDP_CREATE_USER])
        runner.execute_command(cmd[CommandEC2.IDP_CREATE_USER])

        runner = UserOperations(reqInfo, userInfo, envInfo)
        user_result_tuple = runner.execute_command(
                [
                "aws", "cognito-idp", "admin-get-user", '--user-pool-id', 'us-east-1_wioSQKwya', '--username', 'z-test-25'
                ]
            )
        # Example on how to execute commands with the error check
        if not user_result_tuple[1] and not user_result_tuple[2]:
            print(user_result_tuple[0])
            id = runner.get_cognito_uuid_from_json(user_result_tuple[0])
            print(user_result_tuple[0])
            print(f'{id=}')
        else:
            # log error using all available information:
            # stdOut user_result_tuple[0],
            # stdError user_result_tuple[1], and 
            # bash error code user_result_tuple[2]
            pass

        print(CommandEC2.AMB_DEACTIVATE_USER.cmd_key())
# -----------------------------------------------------------------------------

@click.command(help="delete-user: Deletes BloSS🌻M User from IDP+Fabric if exists")
@click.option('--env_file', '-e',
                help="BloSS🌻M AWS-EC2-AMB-GitHub environment-description YAML-fle"
                )
@click.option('--user_file', '-u',
                help="BloSS🌻M user-to-delete YAML-file request"
                )
def delete_user(ctx):
    ### 1. Validate Input
    ### 2. Verify Command is Delete USER
    ### ⇉3.b-(Delete) Create User based on Env&User Files
    ###     4. Query User to make sure it EXISTS - read PROFILE & UUID
    ###     5. Delete User in IDP-Cognito [Optional for Fabric-User Deactivate]
    ###     6. Clone Repo + Checkout Branch
    ###     7. Remove the user (as Party & Resp-Party) from SSP using UUID
    ###     8. Add-Commit-Push Repo + Remove Repo Directory
    pass
# -----------------------------------------------------------------------------
#==================================================================================

#==================================================================================
# -----------------------------------------------------------------------------
# ---- Click-Based Entry Point for Methods ----
# -----------------------------------------------------------------------------
# group = click.Group()
@click.group(   invoke_without_command=False, 
                help='BloSS🌻M ATO-automation CLI'
            )
@click.option(  '--print', '-p', 'execute_flag', 
                default='', show_default=True, flag_value='print', 
                help="BloSS🌻M CLI would run in commands print-only-mode")
@click.option('--execute', '-x', 'execute_flag', 
                default='execute', show_default=True, flag_value='execute',
                help="BloSS🌻M CLI will execute and print commands")
@click.option('--debug', '-d', 'debug_flag', 
                default='', show_default=True, flag_value='debug',
                help="BloSS🌻M CLI will execute with all debug messages")
@click.pass_context
def cli_entries(ctx, execute_flag:str, debug_flag: str):
    """My command-line tool."""
    pass
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

    APP.CMD_ONLY_PRINT = True if execute_flag=='print' else False
    APP.CLI_DEBUG_MODE = True if debug_flag=="debug" else False

    APP.print(f'{execute_flag=}')
    APP.print(f'{APP.CMD_ONLY_PRINT=}')
# -----------------------------------------------------------------------------

cli_entries.add_command(delete_user)
cli_entries.add_command(create_user)
cli_entries.add_command(process_s3_file)
#==================================================================================


if __name__ == "__main__":  

    # envInfo = EnvConfig('/Users/dac4/github/M.A.D.-ToolKit/BLOSSOM/xml-py/config_nist.yaml')
    # userInfo = UserConfig('/Users/dac4/github/M.A.D.-ToolKit/BLOSSOM/xml-py/users-yaml-s3-ec2/20241001-143153_created_user.yaml')
    # print(f"\n\t{userInfo.generate_xml('UUID', '')=}\n")
    # userInfo.make_party_file('/Users/dac4/github/M.A.D.-ToolKit/BLOSSOM/xml-py/xml-oscal/party-to-add/20240923-170738_party2create.xml', uuid4(), '')
    
    # runner = UserOperations(userInfo, envInfo)
    # pprint(runner.execute_command(["pwd"]))


    # print(CommandEC2.AMB_DEACTIVATE_USER.cmd_key())

    # print(f'{Level.__members__=}')
    # print(f'{Level.__members__.items()=}')
    # print(f'{Level.__members__.keys()=}')
    # print(f'{Level.__members__.values()=}')
    # print(f'{Level.get_by_str("info")=}')
    # print(f'{Level.INFO=}')

    cli_entries()
    pass