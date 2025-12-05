"""
Migration Executor.

Executes the migration actions (COPY/MOVE) and maintains an undo log.
"""

import os
import shutil
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from src.core.logger import get_logger
from src.core.simulator import MigrationAction

logger = get_logger(__name__)

class MigrationExecutor:
    """
    Executes migration actions and logs them for potential undo.
    """
    
    def __init__(self, undo_log_path: Path = Path("output/undo_log.jsonl")):
        self.undo_log_path = undo_log_path
        self.undo_log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def execute(self, actions: List[MigrationAction], move_mode: bool = False) -> List[Dict[str, Any]]:
        """
        Execute the given list of actions.
        
        Args:
            actions: List of MigrationAction objects.
            move_mode: If True, move files. If False, copy files.
            
        Returns:
            List of results (success/failure details).
        """
        results = []
        
        for action in actions:
            if action.status not in ["COPY", "MOVE"]: # Only process approved actions
                continue
                
            result = {
                "source": action.source_path,
                "target": action.target_path,
                "action": "MOVE" if move_mode else "COPY",
                "timestamp": time.time(),
                "success": False,
                "error": None
            }
            
            try:
                src = Path(action.source_path)
                dst = Path(action.target_path)
                
                # Create parent directory
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Perform operation
                if move_mode:
                    shutil.move(src, dst)
                else:
                    shutil.copy2(src, dst)
                    
                result["success"] = True
                logger.info(f"{result['action']} SUCCESS: {src} -> {dst}")
                
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"{result['action']} FAILED: {src} -> {dst} : {e}")
                
            # Log to undo file
            self._log_action(result)
            results.append(result)
            
        return results
        
    def _log_action(self, result: Dict[str, Any]):
        """Append action result to undo log."""
        try:
            with open(self.undo_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to undo log: {e}")
