
<p align="center">
   <img src="albs.png" alt="AutoLabs Logo" width="100" />
</p>

# AutoLabs

AutoLabs is a Streamlit-based application for designing, simulating, and evaluating laboratory experiments using AI-powered agents and tagging systems. It supports multi-agent and single-agent workflows, experiment step tagging, and evaluation management.

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
- `evals/`: User queries and experiment evaluation data
- `non-expert-evals/`: Evaluation results and temporary files
- `data_files/`: Chemical units and parameter data

## Getting Started


1. **Install dependencies**:

   - Python 3.11+

   - Required packages: `streamlit`, `langchain`, `openai`, `pandas`, `numpy`, `python-dotenv`, `audio_recorder_streamlit`, etc.
   - Install with `pip install -r requirements.txt` (create this file if missing)
2. **Set up environment variables**:
   - Create a `.env` file with your Azure OpenAI API key:

     ```
     AZURE_OPENAI_API_KEY=your_key_here
     ```
3. **Run the app**:

   ```
   streamlit run app.py
   ```
4. **Use the UI**:
   - Enter experiment descriptions, select options, and follow prompts to design and tag experiments.

   - Save and download results as needed.

   ## Docker Usage

   You can run AutoLabs in a Docker container:

   1. **Build the Docker image**:
      ```sh
      docker build -t autolabs-app .
      ```

   2. **Run the container**:
      ```sh
      docker run -p 8501:8501 autolabs-app
      ```

   3. **Environment Variables**:
      - To use your `.env` file, add this option to the run command:
        ```sh
        docker run --env-file .env -p 8501:8501 autolabs-app
        ```

   4. **Access the app**:
      - Open your browser and go to `http://localhost:8501`



## Folder Structure
- `app.py` — Main application
- `src/` — Source code modules
- `evals/` — Experiment queries and evaluation data
- `non-expert-evals/` — Evaluation results
- `data_files/` — Supporting data files

## Notes
- The app uses Azure OpenAI for language model tasks.
- Experiment steps and tags are saved as pickled files and XML/LSR formats.
- Evaluation results can be downloaded as a zip file.

## License
Specify your license here.

## Contact
For questions or support, contact the repository owner.


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