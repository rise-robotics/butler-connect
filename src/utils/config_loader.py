"""
Configuration loader utility for Butler Connect
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging


class ConfigLoader:
    """Utility class for loading configuration files"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load a single configuration file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            return config if config else {}
            
        except Exception as e:
            logging.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    @staticmethod
    def load_all_configs() -> Dict[str, Any]:
        """Load all configuration files"""
        config_dir = Path("config")
        
        configs = {}
        
        # Load robot configuration
        robot_config_path = config_dir / "robot_config.yaml"
        if robot_config_path.exists():
            configs.update(ConfigLoader.load_config(str(robot_config_path)))
        
        # Load control configuration
        control_config_path = config_dir / "control_config.yaml"
        if control_config_path.exists():
            control_config = ConfigLoader.load_config(str(control_config_path))
            configs['control'] = control_config
        
        # Load safety configuration
        safety_config_path = config_dir / "safety_config.yaml"
        if safety_config_path.exists():
            safety_config = ConfigLoader.load_config(str(safety_config_path))
            configs['safety'] = safety_config
        
        return configs
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate configuration parameters"""
        required_keys = ['robot', 'communication']
        
        for key in required_keys:
            if key not in config:
                logging.error(f"Missing required configuration key: {key}")
                return False
        
        # Validate robot configuration
        robot_config = config.get('robot', {})
        required_robot_keys = ['ip_address', 'udp_port']
        
        for key in required_robot_keys:
            if key not in robot_config:
                logging.error(f"Missing required robot configuration key: {key}")
                return False
        
        return True
