
<p align="center">
   <img src="images/logo.png" alt="AutoLabs Logo" width="100" />
</p>

# AutoLabs

AutoLabs is a Streamlit-based application for designing, simulating, and evaluating laboratory experiments using AI-powered agents and tagging systems. It supports multi-agent and single-agent workflows, experiment step tagging, and evaluation management.

Manuscript: [AutoLabs: Cognitive Multi-Agent Systems with Self-Correction for
Autonomous Chemical Experimentation](https://arxiv.org/abs/2509.25651)

## Features
- Interactive experiment design via chat and forms
- Multi-agent and single-agent graph options
- AI-powered query rewriting and step suggestion
- Tagging system for experiment steps (dispensing, processing, etc.)
- Optional tag selection based on experiment context
- Saving and downloading experiment history, steps, and evaluation results
- Generation of LSR (Lab Step Representation) files for experiments
- Downloadable zipped evaluation results

## Main Components
- `app.py`: Main Streamlit app, UI, and workflow logic
- `src/`: Core logic, agents, tagging utilities, configuration, and experiment graph modules


## Getting Started


1. **Install dependencies**:

   - Python 3.11+
   - Install with `pip install -r requirements.txt` (create this file if missing)
2. **Set up environment variables**:
   - Create a `.env` file with your API keys:

     ```
         OPENAI_API_KEY=""
         OPENAI_BASE_URL=""
         OPENAI_API_VERSION=""
         MODEL=""
     ```
3. **Run the app**:

   ```
   streamlit run app.py
   ```

----

<h1 style="text-align:center;">Disclaimer</h1>

This material was prepared as an account of work sponsored by an agency of the
United States Government.  Neither the United States Government nor the United
States Department of Energy, nor Battelle, nor any of their employees, nor any
jurisdiction or organization that has cooperated in the development of these
materials, makes any warranty, express or implied, or assumes any legal
liability or responsibility for the accuracy, completeness, or usefulness or
any information, apparatus, product, software, or process disclosed, or
represents that its use would not infringe privately owned rights.
 
Reference herein to any specific commercial product, process, or service by
trade name, trademark, manufacturer, or otherwise does not necessarily
constitute or imply its endorsement, recommendation, or favoring by the United
States Government or any agency thereof, or Battelle Memorial Institute. The
views and opinions of authors expressed herein do not necessarily state or
reflect those of the United States Government or any agency thereof.
 
                 PACIFIC NORTHWEST NATIONAL LABORATORY
                              operated by
                                BATTELLE
                                for the
                   UNITED STATES DEPARTMENT OF ENERGY
                    under Contract DE-AC05-76RL01830