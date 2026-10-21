# ERα screening-Agentic AI version

**Agentic AI for reproducible estrogen receptor α (ERα) docking-result analysis**

ERα-DockAgent is a research prototype that connects a tool-calling large language model to **deterministic molecular docking analysis**. The ultimate goal of this version is that it can generate docking data and proceed with the screening workflow in one pot. There is no need for a user to know what molecular docking is or how to analyze the docking data.  

The current version can assess the existing AutoDock Vina results and provide prediction based on the results. The local Python tools read existing docking data. An LLM may select the appropriate tool and explain its output, but does not invent docking energies or decide scientific scores independently.

## Architecture

```text
User: "Evaluate PFHxA for ERα agonist activity"
                       |
                       v
        DeepSeek LLM (via Agents SDK)
           Tool selection and synthesis
                       |
          +------------+--------------+
          |            |              |
          v            v              v
   read_vina_result  compare_two_  score_existing_
                      receptors    docking_results
          |            |              |
          +------------+--------------+
                       |
             Deterministic Python
                dockagent/core.py
                dockagent/batch.py
                       |
               Vina log files
                       |
             JSON/CSV + explanation
```

## Demonstration: PFHxA

Example logs for perfluorohexanoic acid (PFHxA, CAS **307-24-4**) produced:

| Output | Value |
|---|---:|
| Vina energy, 1QKUA | −7.147 kcal/mol |
| Vina energy, 3UUCB | −7.328 kcal/mol |
| agVina1 score | −0.181 |
| Screening threshold | 0.179475 |
| Predicted agonist activity | **Inactive** |

These values describe **one local run per receptor**; replicate seeds, protein preparation choices, and assay-based external validation are not established by this demo. The score measures relative docking preference across conformations, not absolute biological potency.
