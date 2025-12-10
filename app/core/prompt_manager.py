import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages loading and rendering of prompts from YAML files.
    """
    
    def __init__(self, prompts_dir: str = "app/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts: Dict[str, Any] = {}
        self.partials: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load all YAML prompt files from the prompts directory."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return

        # Load partials first
        partials_path = self.prompts_dir / "partials.yaml"
        if partials_path.exists():
            try:
                with open(partials_path, "r", encoding="utf-8") as f:
                    self.partials = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Error loading partials: {e}")

        for file_path in self.prompts_dir.glob("**/*.yaml"):
            if file_path.name == "partials.yaml":
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data:
                        # Namespace by filename (without extension)
                        # e.g., agents/coder.yaml -> agents.coder
                        relative_path = file_path.relative_to(self.prompts_dir)
                        parts = relative_path.with_suffix("").parts
                        
                        # Build nested dict
                        current_level = self.prompts
                        for part in parts[:-1]:
                            if part not in current_level:
                                current_level[part] = {}
                            current_level = current_level[part]
                            if not isinstance(current_level, dict):
                                logger.warning(f"Conflict at {part} in {file_path}")
                                break
                        
                        # Set the final part
                        current_level[parts[-1]] = data
            except Exception as e:
                logger.error(f"Error loading prompt file {file_path}: {e}")

    def get_prompt(self, key: str, **kwargs) -> str:
        """
        Get a prompt by key (format: 'namespace.prompt_key') and render it.
        Supports injecting partials automatically.
        """
        try:
            parts = key.split(".")
            if len(parts) < 2:
                # Try top-level keys if namespace is not explicit? 
                # For now, enforce namespace.
                raise ValueError(f"Invalid prompt key format: {key}. Expected 'namespace.prompt_key'")
            
            # Navigate to the template
            template = self.prompts
            for part in parts:
                if isinstance(template, dict) and part in template:
                    template = template[part]
                else:
                    raise KeyError(f"Prompt key '{key}' not found.")
            
            if not isinstance(template, str):
                raise ValueError(f"Prompt for key '{key}' is not a string.")

            # Merge partials into kwargs so they can be used in format()
            # User kwargs override partials if same name
            render_kwargs = {**self.partials, **kwargs}

            # Simple f-string style formatting
            return template.format(**render_kwargs)
            
        except KeyError as e:
            logger.error(f"Prompt not found: {e}")
            return f"Error: Prompt {key} not found"
        except Exception as e:
            logger.error(f"Error rendering prompt {key}: {e}")
            return f"Error: Could not render prompt {key}"

# Global instance
prompt_manager = PromptManager()
