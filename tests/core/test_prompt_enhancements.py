import pytest
from app.core.prompt_manager import prompt_manager

def test_prompt_partials():
    # Test that partials are loaded
    assert "code_expert" in prompt_manager.partials
    
    # Test that CoderAgent prompt renders correctly with partials
    prompt = prompt_manager.get_prompt("agents.coder.system_prompt")
    assert "You are an expert software engineer" in prompt
    assert "Do not generate harmful content" in prompt
