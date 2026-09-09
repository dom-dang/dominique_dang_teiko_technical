setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

pipeline:
	.venv/bin/python step1_load_data.py
	.venv/bin/python step2_analyze.py
	.venv/bin/python step3_compare_response.py
	.venv/bin/python step4_subset_analysis.py

dashboard:
	.venv/bin/streamlit run dashboard.py