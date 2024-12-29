import os
import pathlib
import shutil
import xml.dom.minidom as miniDOM
from datetime import datetime
from uuid import uuid4

import click
from saxonche import PySaxonProcessor

import ops_yaml as oy
from ops_yaml import APP

# def get_timestamp(datetime: datetime = None)

def get_work_directories_Old() -> tuple[str, str]:
    # Addressing the notebook vs script-file weirdness
    this_file_path = None
    notebook_path = None
    if '_dh'in globals().keys() and globals()['_dh'] and globals()['_dh'][0]: 
        notebook_path = globals()['_dh'][0]
    if not notebook_path and __file__:
        this_file_path = os.path.dirname(os.path.abspath(__file__))
        print(f'\t{this_file_path=}\n')
    else :
        this_file_path = notebook_path
        print(f'\n\t{notebook_path=}\n')
    trans_temp_dir = f'{this_file_path}/xml-oscal/src-docs/tmp'
    return (this_file_path, trans_temp_dir)
### ----------------------------------------------------------------------------------- 

def get_work_directories() -> tuple[str, str]:
    return (os.getcwd(), f'{os.getcwd()}/xml-oscal/src-docs/tmp')
### ----------------------------------------------------------------------------------- 

def get_abs_path(path:str) -> str:
    ### this_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        return abs_path
    else:
        return ''
### ----------------------------------------------------------------------------------- 
### =======================================================================================



class XmlFragmentOps:

    @staticmethod
    def prettify_xml(draft_xml: str)->str:
        ### For debugging XML errors
        ### print('Draft Party XML:'.center(50,"="), '\n',draft_xml)
        ### Start-of-Prettifying-XML
        temp = miniDOM.parseString(draft_xml,) 
        APP.print(f'{temp=}\n')
        new_xml = temp.toprettyxml(indent='  ')
        chunks = [xml_chunk for xml_chunk in new_xml.split('\n') 
                        if '<' in xml_chunk and '>'in xml_chunk]
        chunks = [('\n'+xml_chunk 
                    if '<!--' in xml_chunk or '</ins' in xml_chunk 
                    else xml_chunk) 
                    for xml_chunk in chunks ]
        correctly_spaced_xml = '\n'.join(chunks)
        ### End-of-Prettifying-XML
        APP.print(correctly_spaced_xml) 
        return correctly_spaced_xml

class saxon_operations:
    
    def __init__(self, source:str ='' , target:str=''):
        
        (self.root_dir, self.temp) = get_work_directories()
        if source:
            self.root_dir = os.path.dirname(source)
        if target:
            self.temp = os.path.dirname (target)      
    ### -----------------------------------------------------------------------------------  

    def get_file_timestamp(self,) -> str:
        return datetime.now().isoformat().replace('-', '-').replace(':', '').replace('.', 'p').lower()  
    ### -----------------------------------------------------------------------------------  

    def get_temp_file(self, file: str, default_extension='.xml') -> tuple[str, str, str]:
        full_name, path, just_file = ('', '', '')
        ### Assure correct '.'-starting extension
        ext = ''
        if default_extension and default_extension.startswith('.'):
            ext = default_extension
        elif default_extension and (not default_extension.startswith('.')):
            ext = '.{default_extension}'
        else:
            ext = '.xml'
        ### File-Dir split logic
        if os.path.isfile(file):
            full_name, path, just_file = (
                file,
                os.path.dirname(os.path.abspath(file)),
                pathlib.Path(file).name,                                
            )
        elif os.path.isdir(file):
            new_file = f'tmp-{self.get_file_timestamp()}{ext}'
            new_full = os.path.join(file, new_file)
            full_name, path, just_file = (
                new_full,
                os.path.abspath(file),
                pathlib.Path(new_full).name,                                
            )
        else:
            this_dir, temp_dir = get_work_directories()
            new_file = f'tmp-{self.get_file_timestamp()}{ext}'
            new_full = os.path.join(file, new_file)
            full_name, path, just_file = (
                new_full,
                os.path.abspath(file),
                pathlib.Path(new_full).name,                                
            )

        return (full_name, path, just_file)
    ### -----------------------------------------------------------------------------------  

    def insert_party( self, 
                    src_file: str, frag_file: str, trans_file: str,
                    transform_to_temp:bool = True, ) -> str:
        
        updated_xml = ''
        frag_uri = str(pathlib.Path(f'{get_abs_path(frag_file)}').as_uri())
        with open(src_file, 'r') as file:
            src_xml  = file.read()
        

        with PySaxonProcessor(license=False) as proc:
            print(f'{proc.version=}\n{"="*90}')	

            xslt_proc = proc.new_xslt30_processor()
            xslt_proc.set_parameter('fragmentURI', proc.make_string_value(frag_uri))
            xslt_proc.set_parameter('docUUID', proc.make_string_value(str( uuid4() )) ) 
            xslt_proc.set_parameter('changedDateTime', proc.make_string_value(datetime.now().isoformat()) ) 
                                    
            document = proc.parse_xml(xml_text=src_xml)
            executable = xslt_proc.compile_stylesheet(stylesheet_file=trans_file)
            output = executable.transform_to_string(xdm_node=document)

            ### print(output)

            # UPDATE MASTER XML
            timestamp = self.get_file_timestamp()   
            print(f'\n\t{timestamp=}')
            updated_xml = src_file.replace('.xml', f"-v{timestamp}.xml")
            ### print(f'\tTarget File: {updated_xml}')

            # WRITE TRANSFORMED TREE INTO FILE
            with open(updated_xml, 'wb') as s:
                s.write(output.encode("utf-8"))

        return updated_xml        
    ### -----------------------------------------------------------------------------------  

    def cleanup_responsible( self, src_file:str, trans_file: str,
                            transform_to_temp:bool = True,) -> str:
        updated_xml = ''
        with open(src_file, 'r') as file:
            src_xml  = file.read()

        with PySaxonProcessor(license=False) as proc:
            print(f'{proc.version=}\n{"="*90}')	

            xslt_proc = proc.new_xslt30_processor()
                                    
            document = proc.parse_xml(xml_text=src_xml)
            executable = xslt_proc.compile_stylesheet(stylesheet_file=trans_file)
            output = executable.transform_to_string(xdm_node=document)

            ### print(output)

            # UPDATE MASTER XML
            timestamp = self.get_file_timestamp()   
            print(f'\n\t{timestamp=}')
            updated_xml = src_file.replace('.xml', f"-v{timestamp}.xml")
            ### print(f'\tTarget File: {updated_xml}')

            # WRITE TRANSFORMED TREE INTO FILE
            with open(updated_xml, 'wb') as s:
                s.write(output.encode("utf-8"))

        return updated_xml        
    ### -----------------------------------------------------------------------------------  
### =======================================================================================
@click.command(help="insert-party: Inserts BloSS🌻M User into SSP")
@click.option('--ssp_file', '-s',
                help="BloSS🌻M SSP-file in XMLformat")
@click.option('--user_info', '-u',
                 help="BloSS🌻M XML-fragment user-to-insert information")
@click.option('--copy_to', '-c',
                help="BloSS🌻M SSP file for final copying of the result")
@click.option('--xsl_config', '-x',
                help="BloSS🌻M XSl Config YAML-file")
def insert_party(
                ssp_file:str,
                user_info: str,
                copy_to: str,
                xsl_config: str,
            ) -> None:
    
    transInfo = oy.TransConfig(get_abs_path(xsl_config))
    xsl_dir = transInfo
    insert_xsl,cleanup_xsl = tuple(transInfo.get_ssp_files_abs())
    src_insert_xsl = get_abs_path(insert_xsl)
    src_cleanup_xsl = get_abs_path(cleanup_xsl)
    
    src_ssp_file = get_abs_path(ssp_file)
    src_insert_fragment = get_abs_path(user_info)
    if not (src_ssp_file and src_insert_fragment and src_insert_xsl and src_cleanup_xsl):
        ### Complain and print instructions
        pass    
    
    ### Perform Insert-Party/Resp-Party Transformations With Saxon-CHE
    trans_status_OK = True
    sax = saxon_operations()
    try:
        print(f"Insert-transforming {src_ssp_file}")
        temp_file = sax.insert_party(
                    src_file = src_ssp_file,
                    frag_file = src_insert_fragment,
                    trans_file = src_insert_xsl,
                    transform_to_temp = True
                )
        print(f"Cleanup-transforming {temp_file}")
        temp_file = sax.cleanup_responsible(
                    src_file = temp_file,
                    trans_file = src_cleanup_xsl,
                    transform_to_temp = True
                )
    except Exception as ex:
        print(ex)
        trans_status_OK = False
    finally:
        if trans_status_OK:
            ssp_updated = get_abs_path(temp_file)
            if temp_file and os.path.isfile(ssp_updated):
                shutil.copy2(ssp_updated, copy_to)
                ### Make a FINAL copy instead of the last version
                dir_name = os.path.dirname(ssp_updated)
                shutil.move(ssp_updated, 
                             os.path.join(
                                    dir_name,
                                    f"ssp-Ext-FINAL-{sax.get_file_timestamp()}.xml")
                                    )
        else:
            print('failure')
    ### ---------------------------------------------------------------------------  
### ===============================================================================
#==================================================================================
# -----------------------------------------------------------------------------
# ---- Click-Based Entry Point for MEthods Execution ----
# -----------------------------------------------------------------------------
# group = click.Group()
@click.group(   invoke_without_command=False, 
                help='BloSS🌻M Documentation Update CLI'
            )
@click.pass_context
def cli_entries(ctx):
    """My command-line tool."""
    pass
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
# -----------------------------------------------------------------------------

cli_entries.add_command(insert_party)
# cli_entries.add_command(create_user)
# cli_entries.add_command(process_s3_file)
#==================================================================================

if __name__ == "__main__":
    cli_entries()