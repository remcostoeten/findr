"""
Command-line interface implementation.
"""
import sys
import argparse
from pathlib import Path
from rich.console import Console
from .core import SearchTool
from .ui import UI
from .config import Config

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Findr - Interactive File Search Tool")
    parser.add_argument("-s", "--skip-intro", action="store_true", 
                       help="Skip the intro/help prompt")
    parser.add_argument("-p", "--preset", type=str,
                       help="Use a predefined search preset")
    parser.add_argument("-l", "--list-presets", action="store_true",
                       help="List available search presets")
    parser.add_argument("-d", "--directory", type=str,
                       help="Starting directory for search")
    parser.add_argument("--save-preset", type=str,
                       help="Save current search parameters as a new preset")
    return parser.parse_args()

def list_presets(config: Config, console: Console):
    """Display available presets"""
    from rich.table import Table
    
    table = Table(title="Available Search Presets")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Extensions", style="yellow")
    
    presets = config.get("presets", {})
    for key, preset in presets.items():
        table.add_row(
            preset["name"],
            preset["description"],
            ", ".join(preset["extensions"])
        )
    
    console.print(table)
    sys.exit(0)

def load_preset(config: Config, preset_name: str) -> dict:
    """Load a preset configuration"""
    presets = config.get("presets", {})
    if preset_name not in presets:
        raise ValueError(f"Preset '{preset_name}' not found")
        
    preset = presets[preset_name]
    return {
        "path": ".",  # Will be overridden by user input or command line
        "pattern": "*",  # Default pattern
        "extensions": preset.get("extensions", []),
        "exclude": preset.get("exclude_dirs", []),
        "min_size": preset.get("min_size"),
        "max_size": preset.get("max_size"),
        "content_pattern": "|".join(preset["content_patterns"]) if "content_patterns" in preset else None,
        "ignore_case": preset.get("ignore_case", True),
        "dirs_only": False
    }

def main():
    """Main entry point for the CLI"""
    console = Console()
    args = parse_args()
    
    try:
        config = Config()
        ui = UI()
        tool = SearchTool()
        
        # Handle preset listing
        if args.list_presets:
            list_presets(config, console)
            return
            
        # Load preset if specified
        initial_params = {}
        if args.preset:
            try:
                initial_params = load_preset(config, args.preset)
                if args.directory:
                    initial_params["path"] = args.directory
            except ValueError as e:
                console.print(f"[red]Error:[/red] {str(e)}")
                sys.exit(1)
        
        # Get search parameters from user
        params = ui.prompt_user(
            config=config.config,
            skip_intro=args.skip_intro,
            initial_params=initial_params
        )
        
        # Save as preset if requested
        if args.save_preset:
            new_preset = {
                "name": args.save_preset,
                "description": "Custom search preset",
                "extensions": params.get("extensions", []),
                "exclude_dirs": params.get("exclude", []),
                "min_size": params.get("min_size"),
                "max_size": params.get("max_size"),
                "content_patterns": [params.get("content_pattern")] if params.get("content_pattern") else []
            }
            presets = config.get("presets", {})
            presets[args.save_preset.lower()] = new_preset
            config.set("presets", presets)
            config.save_user_config()
            console.print(f"[green]✓ Saved preset:[/green] {args.save_preset}")
        
        # Execute search
        with console.status("[bold cyan]Searching...[/bold cyan]", spinner="dots"):
            tool.search(params)
        
        ui.display_results(tool.results)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Search cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]An error occurred:[/red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
