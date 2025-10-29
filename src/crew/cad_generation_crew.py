"""
CAD Generation Crew - Main Crew Definition.

This module defines the CAD Agent crew using CrewAI's decorator pattern
following best practices from: https://docs.crewai.com/quickstart
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai_tools import CodeInterpreterTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import os
from pathlib import Path


@CrewBase
class CadGenerationCrew:
    """
    CAD Generation Crew for translating text to CAD models using Build123D.
    
    This crew orchestrates multiple specialized agents to:
    1. Extract design intent from natural language
    2. Generate Build123D Python code for sketches
    3. Create 3D operations (extrude, revolve, etc.)
    4. Add engineering features (fillets, chamfers, holes)
    5. Apply geometry selectors
    6. Perform engineering calculations
    7. Integrate standard parts
    8. Validate and export CAD models
    """
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    # Initialize tools
    code_interpreter = CodeInterpreterTool()
    
    def __init__(self):
        """Initialize the CAD Generation Crew."""
        super().__init__()
        self._ensure_output_directories()
    
    def _ensure_output_directories(self):
        """Ensure output directories exist."""
        output_dirs = [
            'outputs/generated_code',
            'outputs/cad_files/step',
            'outputs/cad_files/stl',
            'outputs/validation_reports'
        ]
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @before_kickoff
    def prepare_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and validate inputs before crew execution.
        
        :param inputs: Dictionary containing user_input and optional parameters
        :return: Processed inputs
        """
        print("=" * 70)
        print("CAD AGENT - TEXT-TO-CAD GENERATION")
        print("=" * 70)
        print(f"\n📝 User Input: {inputs.get('user_input', 'N/A')}")
        print(f"🎨 Design Type: {inputs.get('design_type', 'mechanical part')}")
        print("\n" + "=" * 70)
        print("🚀 Starting CAD generation workflow...\n")
        
        # Add default design_type if not provided
        if 'design_type' not in inputs:
            inputs['design_type'] = 'mechanical part'
        
        return inputs
    
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
            # Build123D documentation search tool will be added here
            # tools=[build123d_docs_search_tool]
        )
    
    @agent
    def operations_expert_agent(self) -> Agent:
        """3D Operations Expert Agent - Generates 3D modeling code."""
        return Agent(
            config=self.agents_config['operations_expert_agent'],
            # tools=[build123d_docs_search_tool]
        )
    
    @agent
    def selector_expert_agent(self) -> Agent:
        """Selector Expert Agent - Generates geometry selection code."""
        return Agent(
            config=self.agents_config['selector_expert_agent'],
            # tools=[build123d_docs_search_tool]
        )
    
    @agent
    def feature_expert_agent(self) -> Agent:
        """Feature Expert Agent - Adds engineering features."""
        return Agent(
            config=self.agents_config['feature_expert_agent'],
            # tools=[build123d_docs_search_tool]
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
            # tools=[geometry_validator_tool, export_validator_tool]
        )
    
    @agent
    def build123d_orchestrator(self) -> Agent:
        """Orchestrator Agent - Coordinates and integrates all code."""
        return Agent(
            config=self.agents_config['build123d_orchestrator'],
            # tools=[standard_parts_search_tool]
        )
    
    # ========================================================================
    # TASK DEFINITIONS
    # ========================================================================
    
    @task
    def extract_design_intent_task(self) -> Task:
        """Task: Extract design intent from user input."""
        return Task(
            config=self.tasks_config['extract_design_intent_task'],
            agent=self.design_intent_agent()
        )
    
    @task
    def generate_sketch_code_task(self) -> Task:
        """Task: Generate Build123D sketch code."""
        return Task(
            config=self.tasks_config['generate_sketch_code_task'],
            agent=self.sketch_expert_agent()
        )
    
    @task
    def generate_3d_operations_task(self) -> Task:
        """Task: Generate 3D operations code."""
        return Task(
            config=self.tasks_config['generate_3d_operations_task'],
            agent=self.operations_expert_agent()
        )
    
    @task
    def add_features_task(self) -> Task:
        """Task: Add engineering features to the model."""
        return Task(
            config=self.tasks_config['add_features_task'],
            agent=self.feature_expert_agent()
        )
    
    @task
    def apply_selectors_task(self) -> Task:
        """Task: Generate selector code for geometry selection."""
        return Task(
            config=self.tasks_config['apply_selectors_task'],
            agent=self.selector_expert_agent()
        )
    
    @task
    def perform_calculations_task(self) -> Task:
        """Task: Perform engineering calculations."""
        return Task(
            config=self.tasks_config['perform_calculations_task'],
            agent=self.calculation_expert_agent()
        )
    
    @task
    def integrate_standard_parts_task(self) -> Task:
        """Task: Integrate standard parts from database."""
        return Task(
            config=self.tasks_config['integrate_standard_parts_task'],
            agent=self.build123d_orchestrator()
        )
    
    @task
    def integrate_code_task(self) -> Task:
        """Task: Integrate all code into final script."""
        return Task(
            config=self.tasks_config['integrate_code_task'],
            agent=self.build123d_orchestrator(),
            output_file='outputs/generated_code/cad_model.py'
        )
    
    @task
    def validate_code_and_geometry_task(self) -> Task:
        """Task: Validate code execution and geometry."""
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
        Creates the CAD Generation Crew.
        
        The crew executes tasks sequentially:
        1. Extract design intent
        2. Generate sketches
        3. Create 3D operations
        4. Add features
        5. Apply selectors
        6. Perform calculations (parallel)
        7. Integrate standard parts (parallel)
        8. Integrate all code
        9. Validate and export
        
        :return: Configured Crew instance
        """
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorator
            tasks=self.tasks,    # Automatically created by @task decorator
            process=Process.sequential,
            verbose=True,
            # Can be upgraded to hierarchical process later for complex designs
            # process=Process.hierarchical,
            # manager_llm='openai/gpt-4-turbo-preview'
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

