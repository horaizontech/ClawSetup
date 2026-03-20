# Prompt Engineering Notes for OpenClaw Agents

This document outlines the design philosophy, structure, and tuning parameters for the 10 pre-configured AI agents included in ClawSetup.

## 1. System Prompt Structure

Every agent profile in `templates/agents/*.json` follows a strict, highly structured system prompt design to maximize the LLM's adherence to its specific role.

The structure is divided into four main sections:

1.  **Core Identity & Mission:** Defines *who* the agent is and its primary objective. This sets the persona and context immediately.
2.  **Methodology & Workflow:** Outlines *how* the agent should approach tasks. This provides a step-by-step framework (e.g., Analyze -> Plan -> Execute -> Verify) to prevent erratic behavior and ensure a systematic approach.
3.  **Tool Usage Guidelines:** Specifies *which* tools the agent is allowed to use and *when*. This is crucial for security and efficiency, preventing the agent from using inappropriate tools (e.g., a Data Analyst shouldn't be modifying core system files).
4.  **Output Constraints & Formatting:** Dictates *what* the final output should look like. This ensures consistency across different agents and makes the output easier for the user (or other systems) to parse.

## 2. Parameter Tuning Reasoning

Each agent is configured with specific `temperature` and `max_iterations` settings tailored to its role.

### Temperature

*   **Low Temperature (0.1 - 0.3):** Used for agents requiring high precision, determinism, and adherence to strict rules.
    *   *Examples:* `sec_audit` (Security Auditor), `db_architect` (Database Architect), `test_engineer` (Test Engineer).
    *   *Reasoning:* These roles cannot afford hallucinations or creative interpretations of code or schemas. They need to be analytical and exact.
*   **Medium Temperature (0.4 - 0.6):** Used for agents balancing logic with problem-solving and code generation.
    *   *Examples:* `fullstack_dev` (FullStack Developer), `bug_hunter` (Bug Hunter), `api_integrator` (API Integrator), `devops_engineer` (DevOps Engineer).
    *   *Reasoning:* These roles need some flexibility to find solutions to complex problems or write novel code, but still need to remain grounded in best practices.
*   **High Temperature (0.7 - 0.8):** Used for agents requiring creativity, natural language generation, or broad conceptual thinking.
    *   *Examples:* `doc_writer` (Documentation Writer), `agent_builder` (Agent Builder), `data_analyst` (Data Analyst - for generating insights).
    *   *Reasoning:* These roles benefit from more diverse vocabulary and creative structuring of information.

### Max Iterations

*   **Low Iterations (10 - 15):** Used for agents with focused, well-defined tasks.
    *   *Examples:* `doc_writer`, `sec_audit`.
    *   *Reasoning:* These tasks usually involve analyzing existing code and generating a report or documentation. They shouldn't need to engage in long, iterative debugging loops.
*   **Medium Iterations (20 - 30):** Used for general development and integration tasks.
    *   *Examples:* `fullstack_dev`, `api_integrator`, `db_architect`, `data_analyst`.
    *   *Reasoning:* These tasks often require writing code, testing it, and fixing minor errors, necessitating a moderate number of iterations.
*   **High Iterations (40 - 50):** Used for complex debugging, system-level tasks, or open-ended exploration.
    *   *Examples:* `bug_hunter`, `test_engineer`, `devops_engineer`, `agent_builder`.
    *   *Reasoning:* Finding elusive bugs, setting up complex CI/CD pipelines, or iteratively refining a new agent prompt often requires many steps of trial and error.

## 3. Fine-Tuning Agent Behavior

Users can customize these agents by editing the JSON files in their `agents/` directory after installation.

*   **To make an agent more creative:** Increase the `temperature` (up to 0.9).
*   **To make an agent more focused:** Decrease the `temperature` (down to 0.1).
*   **To allow an agent to tackle more complex problems:** Increase `max_iterations`.
*   **To restrict an agent's capabilities:** Remove tools from the `enabled_tools` list.
*   **To change an agent's core behavior:** Modify the `system_prompt`. Ensure you maintain the structured format (Identity, Methodology, Tools, Output) for best results.
