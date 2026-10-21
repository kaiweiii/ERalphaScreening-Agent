"""Optional natural-language front end; does not compute scores using an LLM."""

import json


import os

from agents import (
    Agent,
    function_tool,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from dockagent.core import parse_vina_log, summarize_pair
from dockagent.batch import batch_agvina1


def build_agent():

    # Disable OpenAI tracing when using DeepSeek only.
    set_tracing_disabled(True)

    api_key = os.environ["DEEPSEEK_API_KEY"]

    deepseek_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    deepseek_model = OpenAIChatCompletionsModel(
        model="deepseek-flash",
        openai_client=deepseek_client,
    )

    # Keep your three existing @function_tool
    # definitions below this section.

    # Tool 1: Read individual Vina docking results
    @function_tool
    def read_vina_result(log_file: str) -> str:
        """Read poses and docking energies from a Vina log file."""
        try:
            poses = parse_vina_log(log_file)

            return json.dumps({
                "status": "ok",
                "poses": poses
            })

        except (OSError, ValueError) as exc:
            return json.dumps({
                "status": "error",
                "message": str(exc)
            })

    # Tool 2: Compare two receptors and classify agonist activity
    @function_tool
    def compare_two_receptors(
        agonist_log: str,
        antagonist_log: str
    ) -> str:
        """
        Calculate the calibrated ERalpha agVina1-score
        using 1QKUA and 3UUCB docking results.
        """
        try:
            result = summarize_pair(
                agonist_log,
                antagonist_log
            )

            return json.dumps({
                "status": "ok",
                **result
            })

        except (OSError, ValueError) as exc:
            return json.dumps({
                "status": "error",
                "message": str(exc)
            })

    # Tool 3: Score a batch of existing docking results
    @function_tool
    def score_existing_docking_results(
        log_directory: str,
        output_csv: str = "results/agvina1_batch.csv"
    ) -> dict:
        """Calculate agVina1 scores for existing docking logs."""
        try:
            df = batch_agvina1(
                log_directory,
                output_csv
            )

            successful = (
                int((df["status"] == "success").sum())
                if "status" in df.columns else 0
            )

            return {
                "status": "ok",
                "processed": len(df),
                "successful": successful,
                "failed": len(df) - successful,
                "output_file": output_csv
            }

        except (OSError, ValueError, KeyError) as exc:
            return {
                "status": "error",
                "message": str(exc)
            }

    # Create agent after all tools have been defined

    return Agent(
        name="ERalpha-DockAgent",

        model=deepseek_model,

        instructions=(
            "You are a scientific assistant specializing "
            "in ERalpha molecular docking and PFAS screening. "

            "Use the provided tools for calculations. "
            "Never invent docking energies or scores. "

            "The agVina1-score is calculated as "
            "E(3UUCB) - E(1QKUA). "
            "Classify as active if score > 0.179475. "

            "Report tool failures and missing data. "
            "Distinguish computational predictions "
            "from experimental evidence."
        ),

        tools=[
            read_vina_result,
            compare_two_receptors,
            score_existing_docking_results,
        ],
    )

