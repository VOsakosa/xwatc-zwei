# xwatc-zwei

### Installation

Wenn `pipenv` installiert ist, kann im Ordner
```
pipenv sync
```
ausgeführt werden. Dann kann xwatc-zwei mit
```
pipenv run python -m xwatc_zwei.gui
```
gestartet werden.

#### Troubleshooting

Bei "this application failed to start because no Qt platform plugin could be initialized. 
Could not load the Qt platform plugin "xcb" in "" even though it was found" auf Ubuntu etc. hilft
```
sudo apt install libxcb-xinerama0 libxcb-cursor0 libnss3
```