@echo off

python -m venv venv

call venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py --server.address 0.0.0.0 --server.port 8501

pause