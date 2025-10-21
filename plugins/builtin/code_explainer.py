"""Plugin para explicar código en detalle"""

from plugins.base import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginResult,
    PluginPriority
)
import re

class CodeExplainerPlugin(Plugin):
    
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="code_explainer",
            version="1.0.0",
            author="PatCode Team",
            description="Explica código línea por línea",
            priority=PluginPriority.HIGH
        )
    
    def can_handle(self, user_input: str, context: PluginContext) -> bool:
        keywords = [
            "explica este código",
            "qué hace este código",
            "analiza este código",
            "explain this code",
            "what does this code do"
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in keywords)
    
    def execute(self, user_input: str, context: PluginContext) -> PluginResult:
        code_blocks = self._extract_code_blocks(user_input)
        
        if code_blocks:
            enhanced_prompt = f"""
{user_input}

Por favor, proporciona:
1. Resumen de qué hace el código
2. Explicación línea por línea
3. Complejidad temporal y espacial (si aplica)
4. Posibles mejoras o problemas
5. Casos de uso
"""
            
            context.set("enhanced_prompt", enhanced_prompt)
            context.set("plugin_enriched", True)
            
            return PluginResult(
                success=True,
                data={"enhanced": True, "code_blocks": len(code_blocks)},
                should_continue=True
            )
        
        return PluginResult(success=True, should_continue=True)
    
    def _extract_code_blocks(self, text: str) -> list:
        code_blocks = []
        
        pattern = r"```[\w]*\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        code_blocks.extend(matches)
        
        return code_blocks
