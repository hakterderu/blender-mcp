from blender_mcp.server import main as server_main
import sys

def main():
    """Entry point for the blender-mcp package.
    
    Runs the MCP server that connects Blender to AI assistants.
    
    Requires Python 3.10+ due to MCP library usage of match statements
    and newer typing features.
    """
    # Quick sanity check - MCP requires Python 3.10+
    if sys.version_info < (3, 10):
        print(f"Error: blender-mcp requires Python 3.10 or newer (current: {sys.version_info.major}.{sys.version_info.minor}).")
        sys.exit(1)
    server_main()

if __name__ == "__main__":
    main()
