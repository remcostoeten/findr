"""
Command-line interface implementation.
"""
import sys
from .core import SearchTool
from .ui import UI
from .config import Config

def main():
    """Main entry point for the CLI"""
    try:
        config = Config()
        ui = UI()
        tool = SearchTool()
        
        params = ui.prompt_user(config.load_config())
        config.save_search_history(params)
        
        tool.search(params)
        ui.display_results(tool.results)
        
    except KeyboardInterrupt:
        print("\nSearch cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
