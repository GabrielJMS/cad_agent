#!/usr/bin/env python
"""
CAD Agent - Main Entry Point.

This is the main entry point for the CAD Agent application.
Run with: python -m src.main or crewai run
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crew.cad_generation_crew import generate_cad_from_text


def run():
    """
    Run the CAD generation crew with example inputs.
    
    Modify the inputs dictionary to test different design descriptions.
    """
    
    # Example 1: Simple cylinder
    print("Example 1: Simple Cylinder\n")
    result = generate_cad_from_text(
        user_input="""
        Create a cylinder with diameter 20mm and height 50mm.
        Add 2mm fillets on both circular edges.
        """,
        design_type="mechanical part"
    )
    print("\n" + "=" * 70 + "\n")
    
    # Uncomment additional examples as needed:
    
    # # Example 2: Shaft with keyway
    # print("Example 2: Shaft with Keyway\n")
    # result = generate_cad_from_text(
    #     user_input="""
    #     Create a shaft:
    #     - Diameter: 25mm
    #     - Length: 200mm
    #     - Add a keyway 5mm wide and 5mm deep, 30mm long
    #     - Position keyway centered at 50mm from left end
    #     - Add 3mm chamfers on both ends
    #     """,
    #     design_type="power transmission shaft"
    # )
    # print("\n" + "=" * 70 + "\n")
    
    # # Example 3: Mounting bracket with standard parts
    # print("Example 3: Mounting Bracket\n")
    # result = generate_cad_from_text(
    #     user_input="""
    #     Create a mounting bracket:
    #     - Base plate: 80mm x 60mm x 10mm
    #     - Add 4 mounting holes for M6 screws at corners (10mm from edges)
    #     - Include 2 ISO 4762 M6x20 socket head cap screws
    #     - Add 5mm fillets on all edges
    #     """,
    #     design_type="mechanical bracket"
    # )
    # print("\n" + "=" * 70 + "\n")


def run_interactive():
    """
    Run the CAD agent in interactive mode.
    
    Prompts user for design description and generates CAD.
    """
    print("=" * 70)
    print("CAD AGENT - Interactive Mode")
    print("=" * 70)
    print("\nDescribe the CAD model you want to create.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            user_input = input("\n🎨 Design description: ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input.strip():
                print("❌ Please provide a design description.")
                continue
            
            # Ask for design type
            design_type = input("🔧 Design type [mechanical part]: ").strip()
            if not design_type:
                design_type = "mechanical part"
            
            # Generate CAD
            print("\n")
            result = generate_cad_from_text(
                user_input=user_input,
                design_type=design_type
            )
            
            print("\n✅ Generation complete! Check outputs/ directory for files.")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different description.")


if __name__ == "__main__":
    """
    Entry point when running the module directly.
    
    Usage:
        python -m src.main              # Run examples
        python -m src.main --interactive # Interactive mode
    """
    
    # Check for interactive mode
    if len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '-i']:
        run_interactive()
    else:
        run()





