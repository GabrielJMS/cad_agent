"""
CAD Generation Crew - Main Crew Definition.

This module defines the CAD Agent crew using CrewAI's decorator pattern
following best practices from: https://docs.crewai.com/quickstart
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
# Code execution now handled by LocalPythonExecutor
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
from pathlib import Path

# Import Build123D specialized tools
from src.tools import Build123DDocSearchTool, Build123DExamplesTool, SecureCADExecutor


@CrewBase
class CadGenerationCrew:
    """
    CAD Generation Crew for translating text to CAD models using Build123D.
    
    Uses a delegation-based workflow where a Build123D Orchestrator agent
    drives the process, creating plans and delegating to specialists as needed.
    
    Agents:
    - Design Intent Agent: Extracts requirements from natural language
    - Build123D Orchestrator: Main driver with strongest Build123D knowledge
    - Specialist Agents (available for delegation):
      • Sketch Expert: Complex 2D profiles
      • Operations Expert: Complex 3D operations
      • Selector Expert: Geometry selection and filtering
      • Feature Expert: Engineering features (fillets, chamfers, holes, patterns)
      • Calculation Expert: Engineering calculations
    - Validation Agent: Tests and validates generated code
    
    The orchestrator can write simple code itself and only delegates complex
    tasks to specialists, making the workflow dynamic and efficient.
    """
    
    # Configuration files
    # ========================================================================
    # MODEL SWITCHING - Easy ways to change LLM:
    # ========================================================================
    # Option 1: Use unified config + set LLM_MODEL in .env (RECOMMENDED)
    #   agents_config = '../../config/agents_unified.yaml'
    #   Then in .env: LLM_MODEL=zhipu/glm-4
    #
    # Option 2: Use model-specific configs
    #   agents_config = '../../config/agents_glm.yaml'      # GLM-4.6
    #   agents_config = '../../config/agents_ollama.yaml'  # Ollama
    #   agents_config = '../../config/agents.yaml'         # OpenAI
    # ========================================================================
    agents_config = '../../config/agents_ollama.yaml'
    tasks_config = '../../config/tasks.yaml'
    
    # Initialize tools
    code_interpreter = SecureCADExecutor()            # 🔒 Secure Docker CAD executor
    doc_search_tool = Build123DDocSearchTool()        # 📚 Documentation search
    examples_tool = Build123DExamplesTool()           # 💡 Code examples
    
    # Note: Don't override __init__ when using @CrewBase decorator
    # The metaclass handles initialization automatically
    
    @before_kickoff
    def prepare_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and validate inputs before crew execution.
        
        :param inputs: Dictionary containing user_input and optional parameters
        :return: Processed inputs
        """
        # Ensure output directories exist
        self._ensure_output_directories()
        
        print("=" * 70)
        print("CAD AGENT - TEXT-TO-CAD GENERATION")
        print("=" * 70)
        print(f"\n📝 User Input: {inputs.get('user_input', 'N/A')}")
        print(f"🎨 Design Type: {inputs.get('design_type', 'mechanical part')}")
        print("\n🔧 Available Tools:")
        print("  • Build123D Documentation Search (RAG)")
        print("  • Build123D Code Examples Database")
        print("  • Code Interpreter (if Docker enabled)")
        print("\n" + "=" * 70)
        print("🚀 Starting CAD generation workflow...\n")
        
        # Add default design_type if not provided
        if 'design_type' not in inputs:
            inputs['design_type'] = 'mechanical part'
        
        return inputs
    
    def _ensure_output_directories(self):
        """Ensure output directories exist."""
        output_dirs = [
            'outputs/generated_code',
            'outputs/cad_files/step',
            'outputs/cad_files/stl',
            'outputs/validation_reports',
            'cache/build123d_docs',  # For documentation caching
        ]
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @after_kickoff
    def finalize_output(self, result: Any) -> Any:
        """
        Process results after crew execution.
        
        :param result: Crew execution result
        :return: Processed result
        """
        print("\n" + "=" * 70)
        print("✅ CAD GENERATION COMPLETE")
        print("=" * 70)
        print("\n📦 Generated Files:")
        
        # List generated files
        code_files = list(Path('outputs/generated_code').glob('*.py'))
        step_files = list(Path('outputs/cad_files/step').glob('*.step'))
        stl_files = list(Path('outputs/cad_files/stl').glob('*.stl'))
        
        if code_files:
            print("\n  Python Code:")
            for f in code_files:
                print(f"    - {f}")
        
        if step_files:
            print("\n  STEP Files:")
            for f in step_files:
                print(f"    - {f}")
        
        if stl_files:
            print("\n  STL Files:")
            for f in stl_files:
                print(f"    - {f}")
        
        print("\n" + "=" * 70)
        
        return result
    
    # ========================================================================
    # AGENT DEFINITIONS
    # ========================================================================
    
    @agent
    def design_intent_agent(self) -> Agent:
        """Design Intent Extraction Agent - Interprets user requirements."""
        return Agent(
            config=self.agents_config['design_intent_agent'],
            # Add custom tools here if needed
            # tools=[standard_parts_search_tool]
        )
    
    @agent
    def sketch_expert_agent(self) -> Agent:
        """Sketch Expert Agent - Generates Build123D sketch code."""
        return Agent(
            config=self.agents_config['sketch_expert_agent'],
            tools=[
                self.doc_search_tool,
                self.examples_tool,
                self.code_interpreter,  # ✅ Execute and test sketch code
            ]
        )
    
    @agent
    def operations_expert_agent(self) -> Agent:
        """3D Operations Expert Agent - Generates 3D modeling code."""
        return Agent(
            config=self.agents_config['operations_expert_agent'],
            tools=[
                self.doc_search_tool,
                self.examples_tool,
                self.code_interpreter,  # ✅ Execute and test 3D operations
            ]
        )
    
    @agent
    def selector_expert_agent(self) -> Agent:
        """Selector Expert Agent - Generates geometry selection code."""
        return Agent(
            config=self.agents_config['selector_expert_agent'],
            tools=[
                self.doc_search_tool,
                self.code_interpreter,  # ✅ Execute and test selector code
            ]
        )
    
    @agent
    def feature_expert_agent(self) -> Agent:
        """Feature Expert Agent - Adds engineering features."""
        return Agent(
            config=self.agents_config['feature_expert_agent'],
            tools=[
                self.doc_search_tool,
                self.examples_tool,
                self.code_interpreter,  # ✅ Execute and test feature code
            ]
        )
    
    @agent
    def calculation_expert_agent(self) -> Agent:
        """Calculation Expert Agent - Performs engineering calculations."""
        return Agent(
            config=self.agents_config['calculation_expert_agent'],
        )
    
    @agent
    def validation_agent(self) -> Agent:
        """Validation Agent - Executes and validates CAD code."""
        return Agent(
            config=self.agents_config['validation_agent'],
            tools=[
                self.code_interpreter,  # ✅ REQUIRED: Must execute code for validation
                # Future: geometry_validator_tool, export_validator_tool
            ]
        )
    
    @agent
    def build123d_orchestrator(self) -> Agent:
        """
        Orchestrator Agent - Main driver with strongest Build123D knowledge.
        
        Has access to all Build123D tools for documentation search and examples.
        Can execute code to test and validate Build123D scripts.
        """
        return Agent(
            config=self.agents_config['build123d_orchestrator'],
            tools=[
                self.doc_search_tool,    # 📚 Search Build123D documentation
                self.examples_tool,      # 💡 Get working code examples
                self.code_interpreter,   # ✅ Execute and test Build123D code
            ]
        )
    
    # ========================================================================
    # TASK DEFINITIONS (Delegation-Based Workflow)
    # ========================================================================
    
    @task
    def extract_design_intent_task(self) -> Task:
        """Task 1: Extract design intent from user input."""
        return Task(
            config=self.tasks_config['extract_design_intent_task'],
            agent=self.design_intent_agent()
        )
    
    @task
    def orchestrate_cad_generation_task(self) -> Task:
        """
        Task 2: Main CAD generation task - Orchestrator drives the workflow.
        
        The orchestrator creates a plan, writes code, and delegates to specialists
        as needed (sketch expert, operations expert, selector expert, etc.)
        """
        return Task(
            config=self.tasks_config['orchestrate_cad_generation_task'],
            agent=self.build123d_orchestrator(),
            output_file='outputs/generated_code/cad_model.py'
        )
    
    @task
    def validate_code_and_geometry_task(self) -> Task:
        """Task 3: Validate code execution and geometry."""
        return Task(
            config=self.tasks_config['validate_code_and_geometry_task'],
            agent=self.validation_agent(),
            output_file='outputs/validation_reports/validation_report.json'
        )
    
    # ========================================================================
    # CREW DEFINITION
    # ========================================================================
    
    @crew
    def crew(self) -> Crew:
        """
        Creates the CAD Generation Crew with delegation-based workflow.
        
        Workflow (3 sequential tasks):
        1. Extract Design Intent (Design Intent Agent)
           → Analyzes user input and creates structured specification
        
        2. Orchestrate CAD Generation (Build123D Orchestrator) ⭐ Main Task
           → Creates pseudocode plan
           → Writes simple code directly
           → Delegates complex parts to specialists:
             • Sketch Expert (complex 2D profiles)
             • Operations Expert (complex 3D operations)
             • Selector Expert (tricky geometry selection)
             • Feature Expert (complex patterns/features)
             • Calculation Expert (engineering calculations)
           → Integrates everything into final script
        
        3. Validate Code & Geometry (Validation Agent)
           → Executes code, validates geometry, exports STEP/STL
        
        The orchestrator has allow_delegation=true and dynamically chooses
        when to delegate based on task complexity.
        
        :return: Configured Crew instance
        """
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorator
            tasks=self.tasks,    # Automatically created by @task decorator
            process=Process.sequential,
            verbose=True,
        )


def generate_cad_from_text(
    user_input: str,
    design_type: str = "mechanical part",
    output_format: str = "step"
) -> Any:
    """
    Main function to generate CAD from text description.
    
    :param user_input: Natural language description of the CAD model
    :param design_type: Type of design (mechanical part, assembly, etc.)
    :param output_format: Export format (step, stl, both)
    :return: Crew execution result
    
    Example:
        >>> result = generate_cad_from_text(
        ...     "Create a cylinder 20mm diameter and 50mm height with 2mm fillets"
        ... )
    """
    inputs = {
        'user_input': user_input,
        'design_type': design_type,
        'output_format': output_format
    }
    
    # Create and execute crew
    cad_crew = CadGenerationCrew()
    result = cad_crew.crew().kickoff(inputs=inputs)
    
    return result

