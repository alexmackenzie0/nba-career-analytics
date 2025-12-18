# NBA Career Analytics

## Getting the notebook kernel working
- Create the virtual environment: `python3 -m venv .venv`
- Activate it (`source .venv/bin/activate` on macOS/Linux, `.venv\\Scripts\\activate` on Windows)
- Install deps: `pip install -r requirements.txt`
- Register the kernel so Jupyter/VS Code can see it: `python -m ipykernel install --name nba-career-analytics --display-name "Python 3 (nba-career-analytics)" --sys-prefix`
- Launch Jupyter (`jupyter lab` or `jupyter notebook`) from the activated env and open `notebooks/01_prepare_player_seasons.ipynb`; it now targets the generic `python3` kernel and will automatically bind to the environment you just set up.

If you still see an old kernel name, use `Kernel -> Change Kernel -> Python 3 (nba-career-analytics)` in the UI.
