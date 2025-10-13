# tools/checkpoint_system.py
import json
import shutil
from datetime import datetime
from pathlib import Path

class CheckpointSystem:
    """Sistema para crear puntos de restauración"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.checkpoint_dir = self.project_path / ".patcode" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def create_checkpoint(self, description: str) -> str:
        """Crea un checkpoint del estado actual"""
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        
        # Copiar archivos importantes
        shutil.copytree(
            self.project_path,
            checkpoint_path,
            ignore=shutil.ignore_patterns('.git', '__pycache__', 'venv')
        )
        
        # Guardar metadata
        metadata = {
            'id': checkpoint_id,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str):
        """Restaura un checkpoint previo"""
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        
        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint {checkpoint_id} no encontrado")
        
        # Restaurar archivos
        for item in checkpoint_path.iterdir():
            if item.name == "metadata.json":
                continue
            
            dest = self.project_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            else:
                shutil.copytree(item, dest, dirs_exist_ok=True)
    
    def list_checkpoints(self) -> List[Dict]:
        """Lista todos los checkpoints disponibles"""
        checkpoints = []
        for cp_dir in sorted(self.checkpoint_dir.iterdir(), reverse=True):
            metadata_file = cp_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    checkpoints.append(json.load(f))
        return checkpoints