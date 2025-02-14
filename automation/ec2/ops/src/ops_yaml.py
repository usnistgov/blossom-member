# =================================================================================
import logging
import os
import sys

# From ----------------------------------------------------------------------------
from datetime import datetime
from enum import Enum
from pprint import pprint

# Spec ----------------------------------------------------------------------------
import click
import yaml

# Local ---------------------------------------------------------------------------
#==================================================================================


def get_file_timestamp() -> str:
    return datetime.now().isoformat().replace('-', '').replace(':', '').replace('.', 'p').lower()  
### -------------------------------------------------------------------------------
#==================================================================================


class AuthRoles(Enum):

    @staticmethod
    def is_fabric_role(role_to_test: str)-> bool:
        APP.debug(f'{RoleMaps.FABRIC_ROLES=} of Type: {type(RoleMaps.FABRIC_ROLES)}')
        return (    role_to_test in RoleMaps.FABRIC_ROLES.keys() 
                or role_to_test in RoleMaps.FABRIC_ROLES.values()
                )
    # -----------------------------------------------------------------------------
    @staticmethod
    def is_fabric_read_role(role_to_test: str)-> bool:
        APP.debug(f'{RoleMaps.FABRIC_READ_ROLES=} of Type: {type(RoleMaps.FABRIC_ROLES)}')
        return (    role_to_test in RoleMaps.FABRIC_READ_ROLES.keys() 
                or role_to_test in RoleMaps.FABRIC_READ_ROLES.values()
                )
    # -----------------------------------------------------------------------------    @staticmethod
    def get_xml_role_id(role_to_find: str)-> bool:
        if role_to_find and role_to_find in RoleMaps.ALL_ROLES_RESPONSIBILITY.keys():
            return RoleMaps.ALL_ROLES_RESPONSIBILITY[role_to_find]
        else:
            return 'no-role-assigned'
    # -----------------------------------------------------------------------------
    No_Role_Assigned = 0
    # Authorization Users
    System_Owner = 2                  # system-owner
    Authorizing_Official = 4          # authorizing-official
    System_Sec_Assessor = 8           # sys-sec-assessor
    Technical_Point_of_Contact = 16   # tpoc
    System_Administrator = 32         # system-administrator
    # Business Users
    License_Owner = 64                # license-owner
    Acquisition_Officer = 128         # acquisition-officer
    # -----------------------------------------------------------------------------

    def get_ssp_attribute(self)-> str:
        maybe_key = self.name.replace("_", " ")
        if maybe_key in RoleMaps.ALL_ROLES_RESPONSIBILITY:
            return RoleMaps.ALL_ROLES_RESPONSIBILITY[maybe_key]
        else:
            return RoleMaps.ALL_ROLES_RESPONSIBILITY["No Role Assigned"]
    # -----------------------------------------------------------------------------
#==================================================================================

class RoleMaps:
    ALL_ROLES_RESPONSIBILITY = {
        "No Role Assigned": "no-role-assigned",
        "System Owner": 'system-owner',
        "Authorizing Official": 'authorizing-official',
        "System Sec Assessor": 'sys-sec-assessor',
        "Technical Point of Contact": 'tpoc',
        "System Administrator": 'system-administrator',
        "License Owner": 'license-owner',
        "Acquisition Officer": 'acquisition-officer',
    }

    FABRIC_ROLES = {
        "Authorizing Official": 'authorizing-official',
        "Acquisition Officer": 'acquisition-officer',
    }
    FABRIC_READ_ROLES = {
        "System Owner": 'system-owner',
        "System Sec Assessor": 'sys-sec-assessor',
        "System Administrator": 'system-administrator',
    }
    MAP_ENUM = {
            "System Owner": AuthRoles.System_Owner,
            "Authorizing Official": AuthRoles.Authorizing_Official,
            "System Sec Assessor": AuthRoles.System_Sec_Assessor,
            "Technical Point of Contact": AuthRoles.Technical_Point_of_Contact,
            "System Administrator": AuthRoles.System_Administrator,
            "License Owner": AuthRoles.License_Owner,
            "Acquisition Officer": AuthRoles.Acquisition_Officer,
        }
    # -----------------------------------------------------------------------------

    @staticmethod
    def get_role_enum(role: str) -> AuthRoles:
        maybe_role = role.strip()
        if maybe_role in RoleMaps.MAP_ENUM.keys():
            return RoleMaps.MAP_ENUM[maybe_role]
        else:
            return AuthRoles.No_Role_Assigned
    # -----------------------------------------------------------------------------

    @staticmethod
    def get_ssp_role(role: str) -> AuthRoles:
        return RoleMaps.get_role_enum(role).get_ssp_attribute()
    # -----------------------------------------------------------------------------
#==================================================================================


class YamlMap(object):
    def __init__(self, yaml_file):
        super().__init__()
        """Reads YAML file
        Args:
            yaml_file (path-to-file): The YAML file to read
        """
        self.yaml_file = yaml_file
        self.status = list()
        self.config = self.read_yaml_file(yaml_file)
        if len(self.status)<1:
            pprint(f'{self.config=}')
    # -----------------------------------------------------------------------------
    def is_valid(self,) -> bool:
        return True
    # -----------------------------------------------------------------------------
    def read_yaml_file(self, yaml_file) -> dict:
        """ Reads YAML file and returns content back
        Args:
            yaml_file (_type_): Path-File-Name to read as YAML
        Returns:
            dict: YAML file content
        """
        file_content = None
        if os.path.exists(yaml_file):
            with open(yaml_file) as stream:
                try:
                    file_content = yaml.safe_load(stream)
                except yaml.YAMLError as ex:
                    print(ex)
                    self.status.append( (f'{ex}', ex) )
                    file_content = None
        else:
            self.status.append( (f'File {yaml_file} not found ', FileExistsError(f'File {yaml_file} not found ')) )
        return file_content
    # -----------------------------------------------------------------------------

    def get_attr_by_path(self, path: str)-> any:
        """ Returns node value from YAML file by path string (e.g. "root/node1/child")
        Args:
            path (str): YAML XPath equivalent
        Returns:
            str: The value of the node - can be object, can be string.
        """
        current_node = self.config        
        parts = path.split("/")
        for part in parts:
            if current_node and part in current_node.keys() and current_node[part]:
                current_node = current_node[part]
            else:
                return None
        return current_node        
    # -----------------------------------------------------------------------------

    def get_attr_str(self, yPath: str) -> str:
        """ Get attribute value as string
        Args:
            yPath (str): YAML-Path as string (e.g. 'root/child/grand-child')
        Returns:
            str: String value of the path-defined attribute or empty string
        """
        ret_val = self.get_attr_by_path(yPath)
        if ret_val:
            return str(ret_val).strip() if ret_val else ''
        else:
            return ''
    # -----------------------------------------------------------------------------

    def get_attr_list(self, yPath: str) -> list[str]:
        """ Get attribute value as string
        Args:
            yPath (str): YAML-Path as string (e.g. 'root/child/grand-child')
        Returns:
            str: String value of the path-defined attribute or empty string
        """
        ret_val = self.get_attr_by_path(yPath)
        if ret_val and isinstance(ret_val, list):
            return ret_val
        elif isinstance(ret_val, tuple): 
            return list(ret_val)
        elif isinstance(ret_val, dict):
            return list(ret_val.values())
        return []
    # -----------------------------------------------------------------------------
#==================================================================================

class RequestConfig(YamlMap):
    def __init__(self, yaml_file):
        """Reads YAML file
        Args:a.split
            yaml_file (path-to-file): The YAML file to read
        """
        super().__init__(yaml_file)
        self.errors = []  
        if self.config and not self.is_valid():
            for entry in self.errors:
                print(f'\t{entry}')    
    # -----------------------------------------------------------------------------

    def is_valid(self)-> bool:
        """ VErifies the YAML validity
        Returns:
            bool: True is YAML is valid, False: otherwise
        """
        if ('branch_name' in self.config.keys()
            and 'file' in self.config.keys()
            and 'issue_number' in self.config.keys() ):
            # The status OK
            return True
        else:
            return False
    # -----------------------------------------------------------------------------

    def get_cmd_file_name(self)-> str:
        """ Returns branch name
        Returns: GitHub branch name to checkout and push into
            str: _description_
        """
        return self.get_attr_str('file')
    # -----------------------------------------------------------------------------
    
    def get_issue_number(self)-> str:
        """ Returns Issue Number
        Returns: GitHub issue number to add into commit note
            str: _description_
        """
        return self.get_attr_str('issue_number')
    # -----------------------------------------------------------------------------

    def get_branch_name(self)-> str:
        """ Returns branch name
        Returns: GitHub branch name to checkout and push into
            str: _description_
        """
        return self.get_attr_str('branch_name')
    # -----------------------------------------------------------------------------
    def get_party_xml_file(self,) -> str:
        src = self.get_cmd_file_name()
        post_slash = src.rfind('/') + 1
        ts_end = src.rfind('_created')
        return f'{src[post_slash:ts_end]}-party-frag.xml'
     # -----------------------------------------------------------------------------
#==================================================================================

class EnvConfig(YamlMap):
    def __init__(self, yaml_file):
        """Reads YAML file
        Args:
            yaml_file (path-to-file): The YAML file to read
        """
        super().__init__(yaml_file)
    # -----------------------------------------------------------------------------


    def get_bat_user_dir(self) -> str:
        return self.get_attr_str('env/bat/user-dir')
    # -----------------------------------------------------------------------------
    def get_bat_work_dir(self) -> str:
        return self.get_attr_str('env/bat/work-dir')
    # -----------------------------------------------------------------------------
    def get_bat_logs_dir(self) -> str:
        return self.get_attr_str('env/bat/logs-dir')
    # -----------------------------------------------------------------------------
    def get_bat_log_at(self) -> str:
        return self.get_attr_str('env/bat/log-at')
    # -----------------------------------------------------------------------------
    def get_bat_print_at(self) -> str:
        return self.get_attr_str('env/bat/print-at')
    # -----------------------------------------------------------------------------

    def get_git_repo(self) -> str:
        return self.get_attr_str('env/git/repo')
    # -----------------------------------------------------------------------------
    def get_git_repo_dir(self) -> str:
        return self.get_attr_str('env/git/repo-dir')
    # -----------------------------------------------------------------------------
    def get_git_default_branch(self) -> str:
        return self.get_attr_str('env/git/default-branch')
    # -----------------------------------------------------------------------------
    def get_ssp_xml(self) -> str:
        return self.get_attr_str('env/git/ssp')
    # -----------------------------------------------------------------------------
    def get_sap_xml(self) -> str:
        return self.get_attr_str('env/git/sap')
    # -----------------------------------------------------------------------------
    def get_sar_xml(self) -> str:
        return self.get_attr_str('env/git/sar')
    # -----------------------------------------------------------------------------
    def get_poam_xml(self) -> str:
        return self.get_attr_str('env/git/poam')
    # -----------------------------------------------------------------------------


    def get_aws_idp_pool(self) -> str:
        return self.get_attr_str('env/aws/idp-pool')
    # -----------------------------------------------------------------------------
    def get_aws_s3_drop_name(self) -> str:
        return self.get_attr_str('env/aws/s3-drop-name')
    # -----------------------------------------------------------------------------
    def get_aws_s3_drop_url(self) -> str:
        return self.get_attr_str('env/aws/s3-drop-url')
    # -----------------------------------------------------------------------------


    def get_amb_ca_url(self) -> str:       
        return self.get_attr_str('env/amb/ca-url')
    # -----------------------------------------------------------------------------
    def get_amb_ord_url(self) -> str:       
        return self.get_attr_str('env/amb/ord-url')
    # -----------------------------------------------------------------------------
    def get_amb_msp_cert(self) -> str:       
        return self.get_attr_str('env/amb/msp-cert')
    # -----------------------------------------------------------------------------
    def get_amb_msp_dir(self) -> str:       
        return self.get_attr_str('env/amb/msp-dir')
    # -----------------------------------------------------------------------------
    def get_amb_clients_dir(self) -> str:       
        return self.get_attr_str('env/amb/clients-dir')
    # -----------------------------------------------------------------------------
    def get_amb_ord_url(self) -> str:       
        return self.get_attr_str('env/amb/ord-url')
    # -----------------------------------------------------------------------------
    def get_amb_enroll_url(self) -> str:       
        return self.get_attr_str('env/amb/enroll-url')
    # -----------------------------------------------------------------------------
    def get_amb_default(self) -> str:       
        return self.get_attr_str('env/amb/default')
    # -----------------------------------------------------------------------------
    def get_amb_default_secret(self) -> str:       
        return self.get_attr_str('env/amb/default-secret')
    # -----------------------------------------------------------------------------    
    def get_amb_tls_cert(self) -> str:       
        return self.get_attr_str('env/amb/tls-cert')
    # -----------------------------------------------------------------------------

    def get_config(self) -> object:
        return self.config
    # -----------------------------------------------------------------------------
#==================================================================================

class UserConfig(YamlMap):
    def __init__(self, yaml_file):
        """Reads YAML file
        Args:
            yaml_file (path-to-file): The YAML file to read
        """
        super().__init__(yaml_file)
        self.errors = []  
        if not self.is_valid():
            for entry in self.errors:
                print(f'\t{entry}')

        self.all_roles   = [ 
            'system-owner',
            'authorizing-official',
            'sys-sec-assessor',
            'tpoc',
            'system-administrator',
            'license-owner',
            'acquisition-officer',
            ]
        self.map_role = {
            "System Owner": 'system-owner',
            "Authorizing Official": 'authorizing-official',
            "System Sec Assessor": 'sys-sec-assessor',
            "Technical Point of Contact": 'tpoc',
            "System Administrator": 'system-administrator',
            "License Owner": 'license-owner',
            "Acquisition Officer": 'acquisition-officer',
        }

        self.map_enum = {
            "System Owner": AuthRoles.System_Owner,
            "Authorizing Official": AuthRoles.Authorizing_Official,
            "System Sec Assessor": AuthRoles.System_Sec_Assessor,
            "Technical Point of Contact": AuthRoles.Technical_Point_of_Contact,
            "System Administrator": AuthRoles.System_Administrator,
            "License Owner": AuthRoles.License_Owner,
            "Acquisition Officer": AuthRoles.Acquisition_Officer,
        }

        self.priv_roles = [  
            'system-owner',
            'authorizing-official',
            'system-administrator'
            'license-owner',
            'acquisition-officer',
            ]
        self.non_priv_roles = [
            'sys-sec-assessor',
            'tpoc',
            ]
    # -----------------------------------------------------------------------------

    def get_split_names(self, name_str: str) -> tuple[str, str, str]:
        """ Addresses mapping of the name to the Cognito Attributes
        Args:
            name_str (str): Full Name string (e.g. John Paul Raven or Cher)
        Returns:
            tuple[str, str, str]:Name tuple in the form: [first, middle-part, last]
        """
        parts = name_str.split(" ")
        count = len(parts)  
        if count >2: # Usual Case
            return ( parts[0], ' '.join( parts[1 : -1] ), parts[-1] )
        if count ==2:  # Case of No Middle-Name Provided
            return ( parts[0], '', parts[-1] )
        if count ==1:  # Case of Cher or Madonna
            return ( parts[0], '', '')
    # -----------------------------------------------------------------------------

    def build_idp_attributes_string(self, attr: dict)-> str:
        """ Builds the attribute string in the cognito required shape
        Args:
            attr (dict): Dict of the key:value for attributes
        Returns:
            str: Packages attribute string for creating identity
        """
        str_list = [f'Name={k},Value={v}' for (k,v) in attr.items()]
        pprint(str_list)
        return ' '.join(str_list)
    # -----------------------------------------------------------------------------

    def create_cognito_attributes(self) -> dict:
        attrs={}
        # Must set up the email as verified to make process faster
        # If email exists in the body
        if self.get_email():
            attrs["email"]=self.get_email()
            attrs["email_verified"]="true"
        # Process name
        yaml_name = self.get_name() 
        if yaml_name:
            attrs["name"] = yaml_name
            # Part-Parse YAML name into parts
            name_parts = self.get_split_names( yaml_name )
            if name_parts[0] and name_parts[1] and name_parts[2] :
               attrs["given_name"] = name_parts[0]
               attrs["middle_name"] = name_parts[1]
               attrs["family_name"] = name_parts[2]
               attrs["preferred_username"] = name_parts[0] + " " + name_parts[2]
            elif name_parts[0] and (not name_parts[1]) and name_parts[2] :
               attrs["given_name"] = name_parts[0]
               attrs["family_name"] = name_parts[2]
               attrs["preferred_username"] = name_parts[0] + " " + name_parts[2]
            elif name_parts[0] and (not name_parts[1] and not name_parts[2]) :
               attrs["given_name"] = name_parts[0]
               attrs["preferred_username"] = name_parts[0]
        # Updated Date-Time - Was made read-only value
        ### attrs["updated_at"] = datetime.timestamp(datetime.now())*1000
        # "profile": 'enum.value',
        role = self.get_role()
        ### print(f'\n\n{role=}\n\n')
        if role in self.map_enum.keys():
            attrs['profile'] = self.map_enum[role].value
            ### print(f"\n\nAssigned PROFILE {attrs['profile']=}\n\n")
        else:
            attrs['profile'] = 0
        ### cp ./s3-user-files-test/20241106-215256_created_user.yaml ./blossom-oscal-auto/ato/oscal-artifacts/created_users/20241106-215256_created_user.yaml
        pprint(attrs)
        return attrs
    # -----------------------------------------------------------------------------
    
    def is_valid(self)->bool:
        """ CHecks validity of the YAML user-info file
        Returns:
            bool: True = Yaml is valid, False = Invalid
        Side-Effect:
            self.errors contains digest of ALL errors encountered
        """
        self.errors=[]
        if not self.get_command():      # MUST have Command
            self.errors.append(f"YAML File:'{self.yaml_file }' missing COMMAND !!!")

        if not self.get_user_dict():  # Must Have Top-Node for USER-Object
            self.errors.append(f"YAML File:'{self.yaml_file }' missing TOP-LEVEL USER-OBJECT !!!")

        if not self.get_user_id():          # MUST have User-Role
            self.errors.append(f"YAML File:'{self.yaml_file }' missing USER !!!")

        if not self.get_name():         # MUST have UserName or UID
            self.errors.append(f"YAML File:'{self.yaml_file }' missing USERNAME/LOGIN-UID !!!")

        if not self.get_role():         # MUST have UserName or UID
            self.errors.append(f"YAML File:'{self.yaml_file }' missing ROLE !!!")

        return len(self.errors) == 0
    # -----------------------------------------------------------------------------

    def get_command(self) -> str : # | None ( Only Works in Python 3.11+)     
        return self.config.get('command', None) if self.config else None
    # -----------------------------------------------------------------------------

    def get_user_dict(self) -> dict: # | None ( Only Works in Python 3.11+)
        if not self.config:
            return None
        return self.config.get('user', None)  if self.config else None
    # -----------------------------------------------------------------------------
    
    def get_user_id(self) -> str: # | None ( Only Works in Python 3.11+)
        return self.get_attr_str('user/username')
    # -----------------------------------------------------------------------------

    def get_email(self) -> str: # | None ( Only Works in Python 3.11+)
        return self.get_attr_str('user/email-address')
    # -----------------------------------------------------------------------------

    def get_name(self) -> str: # | None ( Only Works in Python 3.11+)  
        return self.get_attr_str('user/name')
    # -----------------------------------------------------------------------------
    def get_role(self) -> str : # | None ( Only Works in Python 3.11+)     
        return self.get_attr_str('user/role')
    # -----------------------------------------------------------------------------
    def get_role_enum(self) -> str : # | None ( Only Works in Python 3.11+)     
        return self.get_attr_str('user/role')
    # -----------------------------------------------------------------------------
    def get_ssp_role(self) -> str : # | None ( Only Works in Python 3.11+)     
        role = self.get_attr_str('user/role')
        if role and role in self.map_role.keys():
            return self.map_role[role]
        return None
    # -----------------------------------------------------------------------------
    def is_ssp_role_privileged(self) -> bool : 
        ssp_role = self.get_ssp_role()
        if ssp_role and ssp_role in self.priv_roles:
            return True
        return False
    # -----------------------------------------------------------------------------
    def get_location_uuid(self) -> str : # | None ( Only Works in Python 3.11+)     
        return self.get_attr_str('user/location-uuid')
    # -----------------------------------------------------------------------------

    def get_member_of_org_uuid(self) -> str : # | None ( Only Works in Python 3.11+)
        return self.get_attr_str('user/member-of-organization')
    # -----------------------------------------------------------------------------

    def get_config(self) -> dict:
        return self.config
    # -----------------------------------------------------------------------------

    def get_ssp_path(self) -> str: # | None ( Only Works in Python 3.11+)
        return self.get_attr_str('user/ssp-path')
    # -----------------------------------------------------------------------------

    def get_yaml_field(self, top: str, sub:str) -> str: # | None ( Only Works in Python 3.11+)
        if self.config and top in self.config.keys() and self.config[top].get(sub, None):
            return (self.config['user'].get(sub, None) 
                    if( self.config[top].get(sub, None) 
                      and 'none' != self.config[top].get(sub, '').lower() )
                    else None)
        return None
    # -----------------------------------------------------------------------------
    def generate_create_user_xml(self, party_uuid:str = '', ) -> str:
        """ Generates an insert-XML-fragment for the user information
        Args:
            user_uuid (str, optional): User login-name. Defaults to ''.
            user_job_title (str, optional): User role. Defaults to ''.
        Returns:
            str: _description_
        """
        s3_driven_ns = 'https://github.com/marketplace/actions/upload-s3'
        role_name = self.get_role()
        role_id = AuthRoles.get_xml_role_id( role_name )
        priv_status = ('non-privileged' if role_id in self.non_priv_roles
                        else ('privileged' if role_id in self.priv_roles
                              else 'undefined')
                        )

        xml_entries=['<?xml version="1.0" encoding="UTF-8"?>',
                '<insert xmlns="http://csrc.nist.gov/ns/oscal/1.0" >',
                f'\n\t<party uuid="{party_uuid}" type="person">',
                f'\t\t<name>{self.get_name()}</name>',
                f'\t\t<short-name>{self.get_user_id()}</short-name>',
                (f'\t\t<prop name="job-title" value="{role_name}" />'
                if role_name else ''),
                # f'\t\t<prop name="iam-manager" value="TPOC Driver" ns="{s3_driven_ns}" />',
                f'\t\t<prop name="privilege-level" value="{priv_status}" ns="{s3_driven_ns}" />',
                f'\t\t<email-address>{self.get_email()}</email-address>',
                (f'\t\t<location-uuid>{self.get_location_uuid()}</location-uuid>'
                    if self.get_location_uuid() else ''),
                (f'\t\t<member-of-organization>{self.get_member_of_org_uuid()}</member-of-organization>'
                    if self.get_member_of_org_uuid() else ''),        
                f'\t</party>',
                (( 
                    f'\n\t<responsible-party role-id="{role_id}">'
                    +f'\n\t\t<party-uuid>{party_uuid}</party-uuid>'
                    +'\n\t</responsible-party>')
                if  role_id else ''
                ),
                '</insert>',
            ] 
        non_empty_xml = [x for x in xml_entries if x] ### Drop empty lines
        return '\n'.join(non_empty_xml)
    # -----------------------------------------------------------------------------
    def make_party_file(self, path_to_file:str, user_uuid:str, user_job:str = ''):
        if user_uuid:
            content = self.generate_create_user_xml(user_uuid, user_job)
            with open(path_to_file, 'wt') as xml_file:
                xml_file.write(content)
    # -----------------------------------------------------------------------------
#==================================================================================

class TransConfig(YamlMap):
    def __init__(self, yaml_file):
        """Reads YAML file
        Args:yaml_file (path-to-file): The YAML file to read
        """
        super().__init__(yaml_file)
        self.errors = []  
        if not self.is_valid():
            for entry in self.errors:
                print(f'\t{entry}')    
    # -----------------------------------------------------------------------------
    def is_valid(self,)-> bool:
        return True
    # -----------------------------------------------------------------------------
    def get_ssp_dir(self,) -> str:
        return self.get_attr_str('ssp/dir')
    # -----------------------------------------------------------------------------
    def get_ssp_files(self,) -> list:
        return self.get_attr_list('ssp/create-user/files')
    # -----------------------------------------------------------------------------
    def get_ssp_files_abs(self,) -> list:
        dir = self.get_ssp_dir()
        if dir.startswith('~/'):
            dir = os.path.expanduser(dir)
        files = self.get_attr_list('ssp/create-user/files')
        abs_files = [os.path.abspath(os.path.join(dir, f)) for f in files]
        return abs_files
#==================================================================================


class Level(Enum):
     # ALL < INFO < WARN < ERROR < PROD
    ALL = 1,
    INFO = 2,
    WARN = 3,
    ERROR = 4,
    PROD = 5,

    @staticmethod
    def get_by_str( value: str) -> Enum:
        try:
            UP = value.upper()
            if UP in Level.__members__.keys():
                return Level[UP]
            return Level.ALL
        except ValueError:
            return Level.ALL

    def call_log_method(self, msg: str) -> None:
        if self==Level.ALL:
            return APP.LOGGER.info(msg)
        elif self==Level.INFO:
            return APP.LOGGER.info(msg)
        elif self == Level.WARN:
            return APP.LOGGER.warning(msg)
        elif self==Level.ERROR:
            return APP.LOGGER.error(msg)
        elif self==Level.PROD:
            return APP.LOGGER.error(msg)
    
    def log_at_level(self, ) -> str:
        if self==Level.ALL:
            return logging.INFO
        elif self==Level.INFO:
            return logging.INFO
        elif self == Level.WARN:
            return logging.WARNING
        elif self==Level.ERROR:
            return logging.ERROR
        elif self==Level.PROD:
            return logging.CRITICAL
    # -----------------------------------------------------------------------------
#==================================================================================

class APP:
    """_summary_ Container for static app-level settings
    """
    LOGGER: logging.Logger = logging.getLogger(__name__)
    LOG_AT: Level  = Level.ALL
    PRINT_AT: Level = Level.ALL
    LOG_DIR: str = ''
    ENV_CONFIG: EnvConfig = None

    CMD_ONLY_PRINT: bool = False
    CLI_DEBUG_MODE: bool = False

    @classmethod
    def init_log(cls, envInfo: EnvConfig) -> None:
        cls.ENV_CONFIG = envInfo
        cls.LOG_AT = Level.ALL if not envInfo.get_bat_log_at() else Level.get_by_str(envInfo.get_bat_log_at())
        cls.PRINT_AT = Level.ALL if not envInfo.get_bat_print_at() else Level.get_by_str(envInfo.get_bat_print_at())
        cls.LOG_DIR = envInfo.get_bat_logs_dir()
        if not APP.LOGGER:
            APP.LOGGER = logging.getLogger(__name__)
            InfoBoard.pin_warning("Not inited APP.LOGGER")            
        log_file = os.path.join(cls.LOG_DIR, f'b@-{get_file_timestamp()}.log' )
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(filename=log_file, level=cls.LOG_AT.log_at_level())
    # -----------------------------------------------------------------------------
    def print(info):
        if APP.CLI_DEBUG_MODE:
            print(info)
    # -----------------------------------------------------------------------------
    # -----------------------------------------------------------------------------
    _DEBUG_LOG_AT_LEVEL=Level.INFO
    _DEBUG_ON=True
    _DETAILS_ON=True
    _DEBUG_DO_LOG=True
    _DEBUG_DO_CLI=True
    _DEBUG_STR='🦋'
    # -----------------------------------------------------------------------------
    def debug(info, stack_depth:int=1):
        tick = APP._DEBUG_STR*2
        deb_str = APP._DEBUG_STR
        deb_bar = '[❌🐛 🐜 🐝 🪲 🐞 🦗🪳❌]'
        stack_txt = ''
        if APP._DEBUG_ON:
            if APP._DETAILS_ON:
                locator = sys._getframe(stack_depth) # elevate in stack to the previous position (the caller)
                stack_info = (
                        f' func: {locator.f_code.co_name}'
                        f' at line: {locator.f_lineno}'
                        f' of file: {locator.f_code.co_filename} ')
                
                stack_txt = ( f' {stack_info} '.center(111,deb_str)  
                                if len(stack_info)<105 
                                else
                              f'{tick}\t{stack_info}\t{tick}' 
                            )
                            

            mod_info = info.replace('\n', f'\n{tick}\t')
            title=('\tDebug Message :\t'.center(80,deb_str)
                   +'\n'
                   +f' {deb_bar} '.center(76,deb_str)
                   )
            debug_message = (  f'\n{title}\n{tick}'
                    f'\n{tick}\t{mod_info}\n{tick}\n'
                    f'{stack_txt}\n')
            
            if (APP._DEBUG_DO_LOG and APP._DEBUG_DO_CLI):
                InfoBoard.print_log_at(
                    debug_message,
                    APP._DEBUG_LOG_AT_LEVEL
                )
            elif APP._DEBUG_DO_CLI:
                print(debug_message)
            else:
                InfoBoard.print_log_at()
    # -----------------------------------------------------------------------------
    # -----------------------------------------------------------------------------
    def print_dir(obj: object, columns:int = 3, show_internals:bool = False):
        if APP.CLI_DEBUG_MODE:
            object_guts = dir(obj)
            data = {}
            for attr in object_guts:
                data[attr]=[f'{attr}']
                if attr.startswith('_'):
                    if attr in data.keys():
                        data[attr].append('i') 
                    else: 
                        data[attr]=['inside']
                if callable(getattr(obj, attr, None)):
                    if attr in data.keys():
                        data[attr].append('()') 
                    else: 
                        data[attr]=['()']
            print(f"\nParsing Instance of TYPE: {type(obj).__name__}")
            part = ''            
            for idx, atr_info in enumerate(data.values(),start=1):
                specs = ''.join([x for i, x in enumerate(atr_info, start=1) if i>1])
                part += f'{idx}. {atr_info[0]}:{specs}; '
                if idx%columns == 0:
                    print(part)
                    part=''
    # -----------------------------------------------------------------------------
# =================================================================================

class InfoBoard:

    def get_error_place(stack_depth: int = 1) -> str:
        locator = sys._getframe(stack_depth) # elevate in stack to the previous position (the caller)
        return (
                f' func: {locator.f_code.co_name}'
                f' at line: {locator.f_lineno}'
                f' of file: {locator.f_code.co_filename} '
                )
    # -----------------------------------------------------------------------------

    @classmethod
    def print_log_at(cls, msg: str, current_level: Level) -> None:
        if APP.PRINT_AT.value <= current_level.value:
            print(msg)
        if APP.LOG_AT.value <= current_level.value:
            log_msg = f'\n @@@ {datetime.now().isoformat()}\n{msg.lstrip()}'
            current_level.call_log_method(log_msg)
    # -----------------------------------------------------------------------------

    @classmethod
    def cmd_status(cls, 
                    command: str, 
                    result: str, 
                    error: str, 
                    code: int, 
                    stack_depth:int = 5) -> str:  
        marker = '✅' if code==0 else '🚧'
        mst_type = 'CMD-OK' if code==0 else 'CMD Warning'
        message = (f'CMD Ran:\t[{command.strip()}]\n'
                   +f'CMD Result:\t[{result.strip()}]\n'
                   +f'CMD Error:\t[{error.strip()}]\n'
                   +f'CMD Code:\t[{code}]'
                   )
        msg = cls.get_message(mst_type, message, marker, '\n', stack_depth=stack_depth)
        cls.print_log_at(msg, Level.INFO if code==0 else Level.WARN)
    # -----------------------------------------------------------------------------

    @classmethod
    def get_message(cls, msg_type: str, 
                    message: str, 
                    marker: str, 
                    spacer:str = '\n\n',
                    stack_depth:int = 3) -> str:  
        info = list()
        if message and msg_type and marker:
            info.append(f"{spacer}{marker} {msg_type} @ {cls.get_error_place(stack_depth = stack_depth)} {marker}")
            upd = message.replace("\n", f"\n{marker} ")
            info.append(f'\n{marker}\n{marker} {upd}\n{marker}{spacer}')
        return ''.join(info)
    # -----------------------------------------------------------------------------

    @classmethod
    def pin_error(cls, message: str = None, depth:int =3,) -> None:
        """ Gets location description for the call place to log exact function name, file, and line
        """
        marker = '❌❌❌'
        if message:
            msg = cls.get_message('Error', message, marker, stack_depth=depth)
            cls.print_log_at(msg, Level.ERROR)
    # -----------------------------------------------------------------------------

    @classmethod
    def pin_warning(cls, message: str = None, depth:int =3, ) -> None:
        """ Gets location description for the call place to log exact function name, file, and line
        """
        marker = '!!!'
        if message:
            msg = cls.get_message('Warning', message, marker, stack_depth=depth)
            cls.print_log_at(msg, Level.WARN)
    # -----------------------------------------------------------------------------

    @classmethod
    def pin_info(cls, message: str = None, depth:int =3, ) -> None:
        """ Gets location description for the call place to log exact function name, file, and line
        """
        marker = 'ⓘⓘⓘ'
        if message:
            msg = cls.get_message('Info', message, marker, spacer='\n', stack_depth=depth)
            cls.print_log_at(msg, Level.INFO)
    # -----------------------------------------------------------------------------
#==================================================================================

@click.command('read')
@click.option('--yaml_file', '-f',
              type=click.Path(exists=True),
              help= 'YAML-file to read')
def read_yaml(yaml_file) -> dict:
    """Reads YAML file
    Args:
        yaml_file (path-to-file): The YAML file to read
    """
    with open(yaml_file) as stream:
        try:
            x = yaml.safe_load(stream)
            pprint.pprint(f'{x=}')
            return x
        except yaml.YAMLError as exc:
            print(exc)
            return None
# -----------------------------------------------------------------------------


@click.group(   invoke_without_command=False, 
                help='BloSS🌻M CLI YAML-reading part'
            )
@click.pass_context
def cli_entry(ctx):
    """My command-line tool."""
    pass
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
# -----------------------------------------------------------------------------

cli_entry.add_command(read_yaml)
# -----------------------------------------------------------------------------
#==================================================================================


if __name__ == "__main__":  
    cli_entry()
