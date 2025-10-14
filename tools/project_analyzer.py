"""
Analizador de proyectos - Auditoría automática de calidad de código
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from tools.safe_executor import SafeExecutor, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class FileAnalysis:
    path: Path
    language: str
    lines: int
    size_bytes: int
    issues: List[str] = field(default_factory=list)
    score: float = 10.0


@dataclass
class ProjectReport:
    path: Path
    total_files: int
    total_lines: int
    total_size_bytes: int
    languages: Dict[str, int]
    structure_score: float
    quality_score: float
    test_coverage: Optional[float]
    suggestions: List[str]
    file_analyses: List[FileAnalysis] = field(default_factory=list)


class ProjectAnalyzer:
    def __init__(self):
        self.executor = SafeExecutor()
        
        self.code_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rs': 'Rust',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#'
        }
        
        self.ignored_dirs = {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'dist', 'build', '.next', 'target', 'bin', 'obj'
        }
    
    def analyze_project(self, path: str) -> ProjectReport:
        """
        Analiza un proyecto completo.
        
        Returns:
            ProjectReport con análisis detallado
        """
        project_path = Path(path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Ruta no existe: {path}")
        
        logger.info(f"Analizando proyecto: {project_path}")
        
        files = self._scan_files(project_path)
        
        total_lines = 0
        total_size = 0
        languages = defaultdict(int)
        file_analyses = []
        
        for file in files:
            analysis = self._analyze_file(file)
            file_analyses.append(analysis)
            
            total_lines += analysis.lines
            total_size += analysis.size_bytes
            languages[analysis.language] += 1
        
        structure_score = self._analyze_structure(project_path, files)
        quality_score = self._analyze_quality(project_path, file_analyses)
        test_coverage = self._check_test_coverage(project_path)
        suggestions = self._generate_suggestions(
            project_path, structure_score, quality_score, test_coverage
        )
        
        return ProjectReport(
            path=project_path,
            total_files=len(files),
            total_lines=total_lines,
            total_size_bytes=total_size,
            languages=dict(languages),
            structure_score=structure_score,
            quality_score=quality_score,
            test_coverage=test_coverage,
            suggestions=suggestions,
            file_analyses=file_analyses
        )
    
    def _scan_files(self, path: Path) -> List[Path]:
        """Escanea archivos de código en el proyecto."""
        files = []
        
        for item in path.rglob('*'):
            if item.is_file() and item.suffix in self.code_extensions:
                if not any(ignored in item.parts for ignored in self.ignored_dirs):
                    files.append(item)
        
        logger.info(f"Encontrados {len(files)} archivos de código")
        return files
    
    def _analyze_file(self, file: Path) -> FileAnalysis:
        """Analiza un archivo individual."""
        try:
            content = file.read_text(encoding='utf-8')
            lines = len(content.splitlines())
            size = file.stat().st_size
            language = self.code_extensions.get(file.suffix, 'Unknown')
            
            issues = []
            score = 10.0
            
            if lines > 500:
                issues.append(f"Archivo muy largo ({lines} líneas)")
                score -= 1.0
            
            if size > 100_000:
                issues.append(f"Archivo muy grande ({size/1024:.1f} KB)")
                score -= 0.5
            
            if 'TODO' in content or 'FIXME' in content:
                todo_count = content.count('TODO') + content.count('FIXME')
                issues.append(f"{todo_count} TODOs/FIXMEs")
                score -= 0.2 * todo_count
            
            return FileAnalysis(
                path=file,
                language=language,
                lines=lines,
                size_bytes=size,
                issues=issues,
                score=max(0, score)
            )
        
        except Exception as e:
            logger.error(f"Error analizando {file}: {e}")
            return FileAnalysis(
                path=file,
                language='Unknown',
                lines=0,
                size_bytes=0,
                issues=[f"Error al leer: {e}"],
                score=0.0
            )
    
    def _analyze_structure(self, path: Path, files: List[Path]) -> float:
        """
        Analiza la estructura del proyecto.
        
        Returns:
            Score de 0-10
        """
        score = 10.0
        
        has_readme = any((path / name).exists() for name in ['README.md', 'README.txt', 'README'])
        has_gitignore = (path / '.gitignore').exists()
        has_tests = any('test' in str(f).lower() for f in files)
        has_docs = (path / 'docs').exists() or (path / 'doc').exists()
        
        if not has_readme:
            score -= 2.0
        if not has_gitignore:
            score -= 1.0
        if not has_tests:
            score -= 2.0
        if not has_docs and len(files) > 10:
            score -= 1.0
        
        if len(files) > 100:
            has_modular_structure = any(
                d.name in ['src', 'lib', 'app', 'modules', 'components']
                for d in path.iterdir() if d.is_dir()
            )
            if not has_modular_structure:
                score -= 1.5
        
        return max(0, score)
    
    def _analyze_quality(self, path: Path, analyses: List[FileAnalysis]) -> float:
        """
        Analiza la calidad del código.
        
        Returns:
            Score de 0-10
        """
        if not analyses:
            return 0.0
        
        avg_score = sum(a.score for a in analyses) / len(analyses)
        
        has_linter = any(
            (path / name).exists() 
            for name in ['.flake8', '.eslintrc', 'pylintrc', '.eslintrc.json']
        )
        
        has_formatter = any(
            (path / name).exists()
            for name in ['.prettierrc', 'pyproject.toml', '.rustfmt.toml']
        )
        
        quality_score = avg_score
        
        if has_linter:
            quality_score += 0.5
        if has_formatter:
            quality_score += 0.5
        
        return min(10.0, quality_score)
    
    def _check_test_coverage(self, path: Path) -> Optional[float]:
        """
        Intenta obtener cobertura de tests.
        
        Returns:
            Porcentaje de cobertura o None
        """
        if (path / 'pytest.ini').exists() or (path / 'setup.py').exists():
            result = self.executor.run_command(
                'pytest --cov=. --cov-report=term-missing',
                cwd=path,
                timeout=60
            )
            
            if result.success and 'TOTAL' in result.stdout:
                try:
                    for line in result.stdout.splitlines():
                        if 'TOTAL' in line:
                            coverage = float(line.split()[-1].replace('%', ''))
                            return coverage
                except:
                    pass
        
        return None
    
    def _generate_suggestions(
        self,
        path: Path,
        structure_score: float,
        quality_score: float,
        test_coverage: Optional[float]
    ) -> List[str]:
        """Genera sugerencias de mejora."""
        suggestions = []
        
        if structure_score < 7:
            if not (path / 'README.md').exists():
                suggestions.append("📝 Añadir README.md con documentación del proyecto")
            if not (path / '.gitignore').exists():
                suggestions.append("🔒 Crear .gitignore para ignorar archivos innecesarios")
            if not any('test' in str(f) for f in path.rglob('*.py')):
                suggestions.append("🧪 Implementar tests (pytest recomendado)")
        
        if quality_score < 7:
            suggestions.append("🔧 Configurar linter (flake8, eslint) para mejorar calidad")
            suggestions.append("✨ Usar formatter automático (black, prettier)")
        
        if test_coverage is not None and test_coverage < 50:
            suggestions.append(f"📊 Aumentar cobertura de tests (actual: {test_coverage}%)")
        elif test_coverage is None:
            suggestions.append("🧪 Implementar tests con coverage tracking")
        
        if not (path / 'requirements.txt').exists() and not (path / 'package.json').exists():
            suggestions.append("📦 Crear archivo de dependencias (requirements.txt / package.json)")
        
        large_files = [
            f for f in path.rglob('*.py')
            if f.stat().st_size > 50_000 and not any(ig in f.parts for ig in self.ignored_dirs)
        ]
        if large_files:
            suggestions.append(f"📏 Refactorizar {len(large_files)} archivos grandes (>50KB)")
        
        return suggestions
    
    def format_report(self, report: ProjectReport) -> str:
        """Formatea el reporte como texto."""
        output = []
        output.append(f"# 📊 Análisis de Proyecto: {report.path.name}")
        output.append("")
        
        output.append("## Estadísticas Generales")
        output.append(f"- **Archivos:** {report.total_files}")
        output.append(f"- **Líneas de código:** {report.total_lines:,}")
        output.append(f"- **Tamaño:** {report.total_size_bytes / 1024:.1f} KB")
        output.append("")
        
        output.append("## Lenguajes")
        for lang, count in sorted(report.languages.items(), key=lambda x: x[1], reverse=True):
            output.append(f"- {lang}: {count} archivos")
        output.append("")
        
        output.append("## Scores")
        output.append(f"- **Estructura:** {report.structure_score:.1f}/10")
        output.append(f"- **Calidad:** {report.quality_score:.1f}/10")
        if report.test_coverage:
            output.append(f"- **Cobertura de Tests:** {report.test_coverage:.1f}%")
        else:
            output.append("- **Cobertura de Tests:** No disponible")
        output.append("")
        
        if report.suggestions:
            output.append("## 💡 Sugerencias de Mejora")
            for suggestion in report.suggestions:
                output.append(f"- {suggestion}")
            output.append("")
        
        top_issues = [a for a in report.file_analyses if a.issues][:5]
        if top_issues:
            output.append("## ⚠️ Archivos con Issues")
            for analysis in top_issues:
                output.append(f"- **{analysis.path.name}**: {', '.join(analysis.issues)}")
        
        return "\n".join(output)
