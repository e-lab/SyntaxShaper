from pydantic import BaseModel
from typing import List, Optional, Type, Dict

class ModelParser:
    @staticmethod
    def extract_variables_with_descriptions(model_classes: List[Type[BaseModel]]) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Extracts and returns a dictionary containing descriptions of variables
        from a list of Pydantic model classes.
        """
        variables = {}


        for count, model in enumerate(model_classes):
            temp = {} 
            for field_name, field_info in model.__fields__.items():
                try: 
                    temp[field_name] = {
                        'type': field_info.outer_type_,
                        'default': field_info.default,
                        'description': field_info.field_info.description,  
                    }
                except:
                    temp[field_name] = {
                        'type': field_info.annotation,
                        'default': field_info.default,
                        'description': field_info.description,  
                    }

                try: 
                    temp[field_name]['value'] = getattr(model, field_name)
                except:
                    pass 
                
                if hasattr(temp[field_name]['type'], '__name__'):
                    temp[field_name]['type'] = temp[field_name]['type'].__name__
                else:
                    temp[field_name]['type'] = temp[field_name]['type'].__class__.__name__

                if 'str' in str(temp[field_name]['type']):
                    temp[field_name]['type'] = str(temp[field_name]['type']).replace('str', '"str"')
                
                if 'typing.' in str(temp[field_name]['type']):
                    temp[field_name]['type'] = str(temp[field_name]['type']).replace('typing.', '').replace('__main__.', '')
                
            if hasattr(model, '__name__'):
                variables[model.__name__] = temp
            else:
                variables[model.__class__.__name__] = temp 

        return variables