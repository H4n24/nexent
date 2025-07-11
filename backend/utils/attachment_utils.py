import yaml
from typing import Union, BinaryIO

from utils.config_utils import tenant_config_manager, get_model_name_from_config

from nexent.core.models.openai_vlm import OpenAIVLModel
from nexent.core.models.openai_long_context_model import OpenAILongContextModel
from nexent.core import MessageObserver


def load_analyze_prompts(language: str = 'zh'):
    """
    Load analyze file prompts from yaml file based on language
    
    Args:
        language: Language code ('zh' for Chinese, 'en' for English)
        
    Returns:
        dict: Loaded prompts configuration
    """
    template_file = 'backend/prompts/analyze_file.yaml' if language == 'zh' else 'backend/prompts/analyze_file_en.yaml'
    with open(template_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def convert_image_to_text(query: str, image_input: Union[str, BinaryIO], tenant_id: str, language: str = 'zh'):
    """
    Convert image to text description based on user query
    
    Args:
        query: User's question
        image_input: Image input (file path or binary data)
        tenant_id: Tenant ID for model configuration
        language: Language code ('zh' for Chinese, 'en' for English)
        
    Returns:
        str: Image description text
    """
    vlm_model_config = tenant_config_manager.get_model_config(key="VLM_ID", tenant_id=tenant_id)
    image_to_text_model = OpenAIVLModel(
        observer=MessageObserver(),
        model_id=get_model_name_from_config(vlm_model_config) if vlm_model_config else "",
        api_base=vlm_model_config.get("base_url", ""),
        api_key=vlm_model_config.get("api_key", ""),
        temperature=0.7,
        top_p=0.7,
        frequency_penalty=0.5,
        max_tokens=512
        )
    
    # Load prompts from yaml file
    prompts = load_analyze_prompts(language)
    system_prompt = prompts['image_analysis']['system_prompt'].format(query=query)
    
    return image_to_text_model.analyze_image(image_input=image_input, system_prompt=system_prompt).content


def convert_long_text_to_text(query: str, file_context: str, tenant_id: str, language: str = 'zh'):
    """
    Convert long text to summarized text based on user query
    
    Args:
        query: User's question
        file_context: Long text content to analyze
        tenant_id: Tenant ID for model configuration
        language: Language code ('zh' for Chinese, 'en' for English)
        
    Returns:
        str: Summarized text description
    """
    secondary_model_config = tenant_config_manager.get_model_config("LLM_SECONDARY_ID", tenant_id=tenant_id)
    long_text_to_text_model = OpenAILongContextModel(
        observer=MessageObserver(),
        model_id=get_model_name_from_config(secondary_model_config),
        api_base=secondary_model_config.get("base_url"),
        api_key=secondary_model_config.get("api_key")
    )
    
    # Load prompts from yaml file
    prompts = load_analyze_prompts(language)
    system_prompt = prompts['long_text_analysis']['system_prompt'].format(query=query)
    user_prompt = prompts['long_text_analysis']['user_prompt'].format(file_context=file_context)

    return long_text_to_text_model.analyze_long_text(file_context, system_prompt, user_prompt)
