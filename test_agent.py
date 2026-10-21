
import asyncio

from agents import Runner
from dockagent.agent import build_agent


async def main():
    agent = build_agent()

    result = await Runner.run(
        agent,
        (
            "Compare the docking results for PFHxA using "
            "./testdata/307-24-4_1qkua_noteq_s230706800_log.txt "
            "and "
            "./testdata/307-24-4_3uucb_noteq_s230706800_log.txt. "
            "Report the docking energies, agVina1-score, "
            "threshold, and predicted agonist activity."
        )
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
