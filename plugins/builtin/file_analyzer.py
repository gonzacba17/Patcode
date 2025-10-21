"""Plugin para analizar archivos y proyectos"""

import os
from pathlib import Path
from typing import Dict, List
from plugins.base import (
    Plugin,
    PluginMetadata,
    PluginContext,
    PluginResult,
    PluginPriority
)

class FileAnalyzerPlugin(Plugin):
    
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="file_analyzer",
            version="1.0.0",
            author="PatCode Team",
            description="Analiza estructura de proyectos",
            priority=PluginPriority.NORMAL
        )
    
    def can_handle(self, user_input: str, context: PluginContext) -> bool:
        keywords = [
            "analiza el proyecto",
            "estructura del proyecto",
            "archivos del proyecto",
            "analyze project",
            "project structure"
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in keywords)
    
    def execute(self, user_input: str, context: PluginContext) -> PluginResult:
        project_path = Path.cwd()
        analysis = self._analyze_project(project_path)
        
        summary = self._create_summary(analysis)
        
        enhanced_prompt = f"""{user_input}

Análisis del proyecto en {project_path}:

{summary}
"""
        
        context.set("enhanced_prompt", enhanced_prompt)
        context.set("project_analysis", analysis)
        
        return PluginResult(
            success=True,
            data=analysis,
            should_continue=True
        )
    
    def _analyze_project(self, path: Path) -> Dict:
        analysis = {
            "total_files": 0,
            "by_extension": {},
            "total_lines": 0,
            "directories": 0,
            "languages": set()
        }
        
        ignore_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll'}
        ignore_dirs = {'__pycache__', '.git', '.venv', 'venv', 'node_modules'}
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            analysis["directories"] += len(dirs)
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix
                
                if ext in ignore_extensions:
                    continue
                
                analysis["total_files"] += 1
                
                analysis["by_extension"][ext] = analysis["by_extension"].get(ext, 0) + 1
                
                lang = self._detect_language(ext)
                if lang:
                    analysis["languages"].add(lang)
                
                if ext in ['.py', '.js', '.java', '.cpp', '.c', '.rb', '.go']:
                    try:
                        if file_path.stat().st_size < 1_000_000:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                analysis["total_lines"] += sum(1 for _ in f)
                    except:
                        pass
        
        analysis["languages"] = list(analysis["languages"])
        return analysis
    
    def _detect_language(self, extension: str) -> str:
        lang_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        return lang_map.get(extension)
    
    def _create_summary(self, analysis: Dict) -> str:
        lines = [
            f"📁 Total de archivos: {analysis['total_files']}",
            f"📂 Directorios: {analysis['directories']}",
            f"📝 Líneas de código: {analysis['total_lines']:,}",
            f"🔤 Lenguajes: {', '.join(analysis['languages']) if analysis['languages'] else 'N/A'}",
            "",
            "Archivos por tipo:"
        ]
        
        sorted_extensions = sorted(
            analysis['by_extension'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for ext, count in sorted_extensions:
            ext_display = ext if ext else '(sin extensión)'
            lines.append(f"  {ext_display}: {count}")
        
        return "\n".join(lines)
