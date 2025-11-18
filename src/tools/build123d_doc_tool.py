"""
Build123D Documentation Search Tool using RAG.

This tool enables agents to search Build123D documentation for accurate
syntax, examples, and best practices.
"""

from crewai.tools import BaseTool
from typing import Optional, Type, ClassVar, Dict
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path


class Build123DDocSearchToolInput(BaseModel):
    """Input schema for Build123DDocSearchTool."""
    query: str = Field(..., description="Search query for Build123D documentation")


class Build123DDocSearchTool(BaseTool):
    """
    Tool for searching Build123D documentation.
    
    This is a simplified version that searches the online documentation.
    For production, implement a full RAG system with vector embeddings.
    """
    
    name: str = "Build123D Documentation Search"
    description: str = (
        "Searches the Build123D documentation for specific topics, code examples, "
        "API references, and best practices. Use this whenever you need to verify "
        "Build123D syntax, find usage examples, or look up class/method parameters. "
        "Example queries: 'how to use BuildSketch', 'extrude parameters', "
        "'fillet edges selector', 'revolve example'"
    )
    args_schema: Type[BaseModel] = Build123DDocSearchToolInput
    
    # Class-level constants (documentation pages)
    DOC_PAGES: ClassVar[Dict[str, str]] = {
        "introduction": "introduction.html",
        "key_concepts": "key_concepts.html",
        "builder_mode": "key_concepts_builder.html",
        "algebra_mode": "key_concepts_algebra.html",
        "examples": "introductory_examples.html",
        "objects": "objects.html",
        "operations": "operations.html",
        "selectors": "selector.html",
        "builders": "builders.html",
        "import_export": "import_export.html",
        "faq": "faq.html",
        "cheat_sheet": "cheat_sheet.html",
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize cache directory
        cache_path = Path("./cache/build123d_docs")
        cache_path.mkdir(parents=True, exist_ok=True)
    
    def _run(self, query: str) -> str:
        """
        Search Build123D documentation for the given query.
        
        Args:
            query: Search query string
            
        Returns:
            Relevant documentation excerpts
        """
        query_lower = query.lower()
        results = []
        
        # Keywords to page mapping for smart routing
        page_keywords = {
            "sketch": ["builders", "examples"],
            "extrude": ["operations", "examples"],
            "fillet": ["operations", "examples"],
            "chamfer": ["operations", "examples"],
            "revolve": ["operations", "examples"],
            "loft": ["operations", "examples"],
            "selector": ["selectors", "examples"],
            "filter": ["selectors"],
            "circle": ["objects", "examples"],
            "rectangle": ["objects", "examples"],
            "box": ["objects", "examples"],
            "cylinder": ["objects", "examples"],
            "import": ["import_export"],
            "export": ["import_export"],
            "step": ["import_export"],
            "stl": ["import_export"],
        }
        
        # Determine which pages to search based on query
        pages_to_search = set()
        for keyword, pages in page_keywords.items():
            if keyword in query_lower:
                pages_to_search.update(pages)
        
        # If no specific pages, search key pages
        if not pages_to_search:
            pages_to_search = ["examples", "operations", "builders"]
        
        # Search selected pages
        for page_key in pages_to_search:
            if page_key in self.DOC_PAGES:
                content = self._fetch_page_content(page_key)
                if content:
                    relevant_sections = self._extract_relevant_sections(
                        content, query_lower
                    )
                    if relevant_sections:
                        results.append({
                            'page': page_key,
                            'url': "https://build123d.readthedocs.io/en/latest/" + self.DOC_PAGES[page_key],
                            'content': relevant_sections
                        })
        
        # Format results
        if not results:
            return self._get_default_guidance(query_lower)
        
        formatted_results = "Build123D Documentation Search Results:\n\n"
        for result in results[:3]:  # Top 3 results
            formatted_results += f"**Source: {result['page']}**\n"
            formatted_results += f"URL: {result['url']}\n\n"
            formatted_results += f"{result['content']}\n\n"
            formatted_results += "---\n\n"
        
        return formatted_results
    
    def _fetch_page_content(self, page_key: str) -> Optional[str]:
        """Fetch and cache page content."""
        cache_path = Path("./cache/build123d_docs")
        cache_path.mkdir(parents=True, exist_ok=True)
        cache_file = cache_path / f"{page_key}.txt"
        
        # Check cache first
        if cache_file.exists():
            return cache_file.read_text(encoding='utf-8')
        
        # Fetch from web
        try:
            url = "https://build123d.readthedocs.io/en/latest/" + self.DOC_PAGES[page_key]
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            main_content = soup.find('div', {'role': 'main'})
            if main_content:
                # Remove navigation elements
                for element in main_content.find_all(['nav', 'footer']):
                    element.decompose()
                
                text = main_content.get_text(separator='\n', strip=True)
                
                # Cache it
                cache_file.write_text(text, encoding='utf-8')
                return text
        except Exception as e:
            print(f"Error fetching {page_key}: {e}")
            return None
    
    def _extract_relevant_sections(self, content: str, query: str) -> str:
        """Extract sections relevant to the query."""
        lines = content.split('\n')
        relevant_lines = []
        context_window = 5  # Lines before and after match
        
        for i, line in enumerate(lines):
            if query in line.lower():
                # Add context
                start = max(0, i - context_window)
                end = min(len(lines), i + context_window + 1)
                section = '\n'.join(lines[start:end])
                
                if section not in relevant_lines:
                    relevant_lines.append(section)
        
        return '\n\n...\n\n'.join(relevant_lines[:5]) if relevant_lines else ""
    
    def _get_default_guidance(self, query: str) -> str:
        """Provide default guidance when no specific results found."""
        guidance = {
            "sketch": """
Build123D Sketch Basics:

```python
from build123d import *

# Create a 2D sketch
with BuildSketch() as sketch:
    Circle(radius=10)
    Rectangle(20, 30)
```

Documentation: https://build123d.readthedocs.io/en/latest/builders.html#buildsketch
""",
            "extrude": """
Build123D Extrude Operation:

```python
from build123d import *

# Extrude a sketch to 3D
with BuildPart() as part:
    with BuildSketch():
        Circle(radius=10)
    extrude(amount=5)  # Extrude 5mm
```

Parameters: amount, dir, mode
Documentation: https://build123d.readthedocs.io/en/latest/operations.html
""",
            "fillet": """
Build123D Fillet Operation:

```python
from build123d import *

with BuildPart() as part:
    Box(10, 10, 10)
    fillet(part.edges(), radius=1)
```

Use selectors to target specific edges.
Documentation: https://build123d.readthedocs.io/en/latest/operations.html
"""
        }
        
        # Find matching guidance
        for key, content in guidance.items():
            if key in query:
                return content
        
        return f"""
No specific documentation found for: {query}

General Build123D Resources:
- Documentation: https://build123d.readthedocs.io/en/latest/
- Examples: https://build123d.readthedocs.io/en/latest/introductory_examples.html
- Cheat Sheet: https://build123d.readthedocs.io/en/latest/cheat_sheet.html

Try more specific terms like:
- "BuildSketch example"
- "extrude parameters"
- "fillet edges"
- "selector syntax"
"""


class Build123DExamplesTool(BaseTool):
    """
    Tool for retrieving curated Build123D code examples.
    
    This provides tested, working code examples for common patterns.
    """
    
    name: str = "Build123D Code Examples"
    description: str = (
        "Retrieve working Build123D code examples for common operations. "
        "Use this to find tested code patterns for: sketches, extrusions, "
        "revolves, fillets, chamfers, holes, selectors, and more. "
        "Returns complete, runnable code examples."
    )
    
    # Store examples as class variable
    EXAMPLES: ClassVar[Dict[str, Dict]] = None  # Will be initialized on first use
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize examples if not already done
        if Build123DExamplesTool.EXAMPLES is None:
            Build123DExamplesTool.EXAMPLES = self._load_examples()
    
    def _load_examples(self) -> Dict[str, Dict]:
        """Load curated examples."""
        return {
            "simple_box": {
                "title": "Simple Box",
                "description": "Create a basic 3D box",
                "code": """from build123d import *

with BuildPart() as box:
    Box(10, 20, 30)

# Export
box.part.export_step("box.step")""",
                "keywords": ["box", "basic", "3d", "simple"]
            },
            "filleted_cylinder": {
                "title": "Cylinder with Fillets",
                "description": "Create a cylinder with filleted edges",
                "code": """from build123d import *

with BuildPart() as cyl:
    Cylinder(radius=10, height=50)
    fillet(cyl.edges(), radius=2)

cyl.part.export_step("cylinder.step")""",
                "keywords": ["cylinder", "fillet", "edges", "round"]
            },
            "extruded_rectangle": {
                "title": "Extruded Rectangle",
                "description": "Create a rectangular profile and extrude it",
                "code": """from build123d import *

with BuildPart() as part:
    with BuildSketch():
        Rectangle(20, 30)
    extrude(amount=10)

part.part.export_step("rectangle.step")""",
                "keywords": ["rectangle", "extrude", "sketch", "2d"]
            },
            "holes": {
                "title": "Part with Holes",
                "description": "Create a plate with multiple holes",
                "code": """from build123d import *

with BuildPart() as plate:
    Box(50, 50, 5)
    with GridLocations(30, 30, 2, 2):
        Hole(radius=3, depth=5)

plate.part.export_step("plate.step")""",
                "keywords": ["hole", "holes", "grid", "pattern", "plate"]
            },
            "revolve": {
                "title": "Revolved Profile",
                "description": "Create a revolved solid",
                "code": """from build123d import *

with BuildPart() as revolved:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            l1 = Line((0, 0), (10, 0))
            l2 = Line(l1 @ 1, (10, 20))
            l3 = Line(l2 @ 1, (5, 20))
            Line(l3 @ 1, (0, 0))
        make_face()
    revolve(axis=Axis.Z)

revolved.part.export_step("revolved.step")""",
                "keywords": ["revolve", "rotation", "profile", "spin"]
            },
        }
    
    def _run(self, query: str = "") -> str:
        """Retrieve relevant examples."""
        query_lower = query.lower()
        matches = []
        
        for ex_id, example in self.EXAMPLES.items():
            if any(kw in query_lower for kw in example['keywords']):
                matches.append(example)
        
        # If no matches, return all examples
        if not matches:
            matches = list(self.EXAMPLES.values())
        
        # Format results
        result = "Build123D Code Examples:\n\n"
        for ex in matches[:3]:  # Top 3
            result += f"**{ex['title']}**\n"
            result += f"{ex['description']}\n\n"
            result += f"```python\n{ex['code']}\n```\n\n"
            result += "---\n\n"
        
        return result

