"""Plugin para ayuda con Git"""

import subprocess
from pathlib import Path
from plugins.base import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginResult,
    PluginPriority
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

class GitHelperPlugin(Plugin):
    
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="git_helper",
            version="1.0.0",
            author="PatCode Team",
            description="Asiste con comandos y operaciones de Git",
            priority=PluginPriority.NORMAL
        )
    
    def can_handle(self, user_input: str, context: PluginContext) -> bool:
        keywords = ["git", "commit", "branch", "merge", "pull", "push", "diff"]
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in keywords)
    
    def execute(self, user_input: str, context: PluginContext) -> PluginResult:
        try:
            if self._is_git_repo():
                git_info = self._get_git_info()
                context.set("git_info", git_info)
                
                enhanced_prompt = f"""{user_input}

Contexto de Git:
- Branch actual: {git_info['branch']}
- Archivos modificados: {git_info['modified_files']}
- Último commit: {git_info['last_commit']}
"""
                
                context.set("enhanced_prompt", enhanced_prompt)
                
                return PluginResult(
                    success=True,
                    data=git_info,
                    should_continue=True
                )
        
        except Exception as e:
            logger.warning(f"Error obteniendo info de Git: {e}")
        
        return PluginResult(success=True, should_continue=True)
    
    def _is_git_repo(self) -> bool:
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except:
            return False
    
    def _get_git_info(self) -> dict:
        info = {}
        
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2
            )
            info['branch'] = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                timeout=2
            )
            modified = [line.strip() for line in result.stdout.split('\n') if line]
            info['modified_files'] = len(modified)
            
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                timeout=2
            )
            info['last_commit'] = result.stdout.strip()[:50]
        
        except Exception as e:
            logger.debug(f"Error en _get_git_info: {e}")
        
        return info
