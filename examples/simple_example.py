"""
Simple Example - CAD Agent Usage.

This example demonstrates how to use the CAD Agent system to generate
a simple geometric part from a natural language description.
"""

# Note: This is a conceptual example showing the intended API
# The actual implementation will be built according to the IMPLEMENTATION_PLAN.md

def example_simple_box():
    """
    Generate a simple box with fillets from text description.
    
    This example will work once the full system is implemented.
    """
    from src.crew.cad_generation_crew import generate_cad_from_text
    
    # Simple box description
    description = """
    Create a rectangular box with the following specifications:
    - Length: 100mm
    - Width: 50mm
    - Height: 30mm
    - Add 2mm fillets on all edges
    - Export as STEP file
    """
    
    # Generate CAD model
    result = generate_cad_from_text(description)
    
    # Print results
    print(f"✅ CAD Generation Successful!")
    print(f"📄 Generated Code: {result['code_file']}")
    print(f"📦 STEP File: {result['step_file']}")
    print(f"⏱️  Generation Time: {result['generation_time']:.2f}s")
    
    return result


def example_shaft_with_features():
    """
    Generate a shaft with multiple features.
    
    Demonstrates more complex geometry with multiple operations.
    """
    from src.crew.cad_generation_crew import generate_cad_from_text
    
    description = """
    Create a mechanical shaft with these features:
    - Main cylinder: diameter 25mm, length 200mm
    - Add a 5mm x 5mm keyway, 30mm long, centered at 50mm from left end
    - Add 3mm chamfers on both ends
    - Create a groove: 3mm wide, 1mm deep, at 100mm from left end
    """
    
    result = generate_cad_from_text(description)
    
    print(f"✅ Shaft Generated!")
    print(f"📦 Output: {result['step_file']}")
    
    return result


def example_with_standard_parts():
    """
    Generate an assembly using standard parts from the library.
    
    Demonstrates integration of parametric standard components.
    """
    from src.crew.cad_generation_crew import generate_cad_from_text
    
    description = """
    Create a simple mounting bracket:
    - Base plate: 80mm x 60mm x 10mm
    - Add 4 mounting holes for M6 screws at corners (10mm from edges)
    - Add 2 ISO 4762 M6x20 socket head cap screws in opposite corners
    - Add 5mm fillets on all edges
    """
    
    result = generate_cad_from_text(description)
    
    print(f"✅ Bracket with fasteners generated!")
    print(f"📦 Assembly: {result['step_file']}")
    print(f"📋 Standard Parts Used:")
    for part in result.get('standard_parts', []):
        print(f"   - {part['type']}: {part['designation']}")
    
    return result


def example_bearing_housing():
    """
    Generate a bearing housing for a standard bearing.
    
    Demonstrates complex geometry with precise dimensional requirements.
    """
    from src.crew.cad_generation_crew import generate_cad_from_text
    
    description = """
    Design a bearing housing for a 6204 deep groove ball bearing:
    - Outer diameter: 60mm
    - Total height: 30mm
    - Bearing bore: 20mm diameter (inner race)
    - Bearing outer diameter: 47mm (outer race)
    - Bearing width: 14mm
    - Add 4 M6 mounting holes equally spaced on a 50mm bolt circle
    - Include 0.5mm chamfers on all edges
    - Housing wall thickness: 6mm minimum
    """
    
    result = generate_cad_from_text(description)
    
    print(f"✅ Bearing housing generated!")
    print(f"📦 STEP file: {result['step_file']}")
    print(f"📏 Validation:")
    print(f"   - Geometry valid: {result['validation']['geometry_valid']}")
    print(f"   - Dimensions accurate: {result['validation']['dimensions_accurate']}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("CAD Agent - Example Usage")
    print("=" * 70)
    print()
    
    print("Note: These examples demonstrate the intended API.")
    print("The full implementation is in progress according to IMPLEMENTATION_PLAN.md")
    print()
    
    # Uncomment when the system is implemented:
    
    # print("Example 1: Simple Box with Fillets")
    # print("-" * 70)
    # example_simple_box()
    # print()
    
    # print("Example 2: Shaft with Features")
    # print("-" * 70)
    # example_shaft_with_features()
    # print()
    
    # print("Example 3: Bracket with Standard Parts")
    # print("-" * 70)
    # example_with_standard_parts()
    # print()
    
    # print("Example 4: Bearing Housing")
    # print("-" * 70)
    # example_bearing_housing()
    # print()
    
    print("✅ Implementation ready to begin!")
    print("📖 See IMPLEMENTATION_PLAN.md for detailed development guide")





