"""
Code Analyzer - FASE 3: Orchestrator Agentic y Code Analyzer

Herramienta de análisis estático de código para múltiples lenguajes.
"""

import ast
import re
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Información sobre una función."""
    name: str
    line_start: int
    line_end: int
    params: List[str]
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    return_annotation: Optional[str] = None


@dataclass
class ClassInfo:
    """Información sobre una clase."""
    name: str
    line_start: int
    line_end: int
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Información sobre imports."""
    module: str
    names: List[str]
    alias: Optional[str] = None
    line: int = 0


@dataclass
class AnalysisResult:
    """Resultado del análisis de código."""
    file_path: str
    language: str
    lines_of_code: int
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    syntax_errors: List[str] = field(default_factory=list)
    complexity_score: Optional[int] = None
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "functions": [
                {
                    "name": f.name,
                    "line_start": f.line_start,
                    "params": f.params,
                    "is_async": f.is_async
                }
                for f in self.functions
            ],
            "classes": [
                {
                    "name": c.name,
                    "line_start": c.line_start,
                    "methods": [m.name for m in c.methods]
                }
                for c in self.classes
            ],
            "imports": [
                {"module": i.module, "names": i.names}
                for i in self.imports
            ],
            "exports": self.exports,
            "syntax_errors": self.syntax_errors,
            "summary": self.summary
        }


class PythonAnalyzer:
    """Analizador de código Python usando AST."""
    
    @staticmethod
    def analyze(file_path: str, content: str) -> AnalysisResult:
        """Analiza código Python."""
        result = AnalysisResult(
            file_path=file_path,
            language="python",
            lines_of_code=len(content.splitlines())
        )
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result.imports.append(ImportInfo(
                            module=alias.name,
                            names=[],
                            alias=alias.asname,
                            line=node.lineno
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    names = [alias.name for alias in node.names]
                    result.imports.append(ImportInfo(
                        module=node.module or "",
                        names=names,
                        line=node.lineno
                    ))
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    result.functions.append(
                        PythonAnalyzer._parse_function(node)
                    )
                
                elif isinstance(node, ast.ClassDef):
                    result.classes.append(
                        PythonAnalyzer._parse_class(node)
                    )
            
            result.complexity_score = len(result.functions) + len(result.classes)
            
        except SyntaxError as e:
            result.syntax_errors.append(f"Line {e.lineno}: {e.msg}")
            logger.error(f"Syntax error in {file_path}: {e}")
        
        except Exception as e:
            result.syntax_errors.append(f"Parsing error: {str(e)}")
            logger.error(f"Error parsing {file_path}: {e}")
        
        return result
    
    @staticmethod
    def _parse_function(node: ast.FunctionDef) -> FunctionInfo:
        """Extrae información de una función."""
        params = [arg.arg for arg in node.args.args]
        docstring = ast.get_docstring(node)
        decorators = [
            PythonAnalyzer._get_decorator_name(dec)
            for dec in node.decorator_list
        ]
        
        return_annotation = None
        if node.returns:
            return_annotation = ast.unparse(node.returns)
        
        return FunctionInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            params=params,
            docstring=docstring,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            return_annotation=return_annotation
        )
    
    @staticmethod
    def _parse_class(node: ast.ClassDef) -> ClassInfo:
        """Extrae información de una clase."""
        bases = [ast.unparse(base) for base in node.bases]
        
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(PythonAnalyzer._parse_function(item))
        
        decorators = [
            PythonAnalyzer._get_decorator_name(dec)
            for dec in node.decorator_list
        ]
        
        return ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            bases=bases,
            methods=methods,
            docstring=ast.get_docstring(node),
            decorators=decorators
        )
    
    @staticmethod
    def _get_decorator_name(decorator: ast.expr) -> str:
        """Obtiene el nombre de un decorador."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return ast.unparse(decorator)


class JavaScriptAnalyzer:
    """Analizador de código JavaScript/TypeScript usando regex."""
    
    @staticmethod
    def analyze(file_path: str, content: str, language: str = "javascript") -> AnalysisResult:
        """Analiza código JavaScript/TypeScript."""
        result = AnalysisResult(
            file_path=file_path,
            language=language,
            lines_of_code=len(content.splitlines())
        )
        
        try:
            import_pattern = r'import\s+(?:{([^}]+)}|(\w+)|(\*))\s+from\s+["\']([^"\']+)["\']'
            for match in re.finditer(import_pattern, content):
                names_group = match.group(1)
                default_import = match.group(2)
                star_import = match.group(3)
                module = match.group(4)
                
                if star_import:
                    names = ["*"]
                elif default_import:
                    names = [default_import]
                else:
                    names = [n.strip() for n in names_group.split(",")]
                
                result.imports.append(ImportInfo(
                    module=module,
                    names=names
                ))
            
            require_pattern = r'(?:const|let|var)\s+(?:{([^}]+)}|(\w+))\s*=\s*require\(["\']([^"\']+)["\']\)'
            for match in re.finditer(require_pattern, content):
                destructured = match.group(1)
                single_var = match.group(2)
                module = match.group(3)
                
                if destructured:
                    names = [n.strip() for n in destructured.split(",")]
                else:
                    names = [single_var]
                
                result.imports.append(ImportInfo(
                    module=module,
                    names=names
                ))
            
            export_pattern = r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)'
            for match in re.finditer(export_pattern, content):
                result.exports.append(match.group(1))
            
            func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
            for match in re.finditer(func_pattern, content):
                func_name = match.group(1)
                params_str = match.group(2)
                params = [p.strip().split("=")[0].strip() for p in params_str.split(",") if p.strip()]
                
                is_async = "async" in content[max(0, match.start() - 10):match.start()]
                
                result.functions.append(FunctionInfo(
                    name=func_name,
                    line_start=content[:match.start()].count("\n") + 1,
                    line_end=0,
                    params=params,
                    is_async=is_async
                ))
            
            arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
            for match in re.finditer(arrow_pattern, content):
                func_name = match.group(1)
                is_async = "async" in match.group(0)
                
                result.functions.append(FunctionInfo(
                    name=func_name,
                    line_start=content[:match.start()].count("\n") + 1,
                    line_end=0,
                    params=[],
                    is_async=is_async
                ))
            
            class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                base_class = match.group(2)
                
                result.classes.append(ClassInfo(
                    name=class_name,
                    line_start=content[:match.start()].count("\n") + 1,
                    line_end=0,
                    bases=[base_class] if base_class else [],
                    methods=[]
                ))
            
            result.complexity_score = len(result.functions) + len(result.classes)
            
        except Exception as e:
            result.syntax_errors.append(f"Parsing error: {str(e)}")
            logger.error(f"Error parsing {file_path}: {e}")
        
        return result


class CodeAnalyzer:
    """Facade para analizar código de múltiples lenguajes."""
    
    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript"
    }
    
    @staticmethod
    def analyze_file(file_path: str) -> Optional[AnalysisResult]:
        """Analiza un archivo de código."""
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        ext = path.suffix.lower()
        if ext not in CodeAnalyzer.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported file type: {ext}")
            return None
        
        language = CodeAnalyzer.SUPPORTED_LANGUAGES[ext]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if language == "python":
                result = PythonAnalyzer.analyze(file_path, content)
            else:
                result = JavaScriptAnalyzer.analyze(file_path, content, language)
            
            result.summary = CodeAnalyzer._generate_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    @staticmethod
    def analyze_directory(dir_path: str, recursive: bool = True) -> Dict[str, AnalysisResult]:
        """Analiza todos los archivos de código en un directorio."""
        results = {}
        path = Path(dir_path)
        
        if not path.exists():
            logger.error(f"Directory not found: {dir_path}")
            return results
        
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix in CodeAnalyzer.SUPPORTED_LANGUAGES:
                result = CodeAnalyzer.analyze_file(str(file_path))
                if result:
                    results[str(file_path)] = result
        
        logger.info(f"Analyzed {len(results)} files in {dir_path}")
        return results
    
    @staticmethod
    def _generate_summary(result: AnalysisResult) -> str:
        """Genera un resumen legible del análisis."""
        parts = []
        
        parts.append(f"{result.language.upper()} file with {result.lines_of_code} lines")
        
        if result.classes:
            class_names = [c.name for c in result.classes]
            parts.append(f"Classes: {', '.join(class_names)}")
        
        if result.functions:
            func_names = [f.name for f in result.functions[:5]]
            if len(result.functions) > 5:
                func_names.append(f"... and {len(result.functions) - 5} more")
            parts.append(f"Functions: {', '.join(func_names)}")
        
        if result.imports:
            import_modules = list(set([i.module for i in result.imports]))[:5]
            parts.append(f"Imports from: {', '.join(import_modules)}")
        
        if result.syntax_errors:
            parts.append(f"⚠️ {len(result.syntax_errors)} syntax errors")
        
        return " | ".join(parts)
    
    @staticmethod
    def find_dependencies(analysis_results: Dict[str, AnalysisResult]) -> Dict[str, Set[str]]:
        """Encuentra dependencias entre archivos analizados."""
        dependencies = {}
        
        module_to_file = {}
        for file_path, result in analysis_results.items():
            if result.language == "python":
                module_name = Path(file_path).stem
                module_to_file[module_name] = file_path
        
        for file_path, result in analysis_results.items():
            deps = set()
            
            for imp in result.imports:
                if imp.module in module_to_file:
                    deps.add(module_to_file[imp.module])
            
            dependencies[file_path] = deps
        
        return dependencies
