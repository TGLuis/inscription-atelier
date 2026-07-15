which python3
if [[ $? ]]; then
  sudo apt-get install python3
fi
python3 -m pip install -r requirements.txt
chmod +x solve.py
