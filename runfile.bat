@echo off
setlocal enabledelayedexpansion

:: Ensure correct location
cd "C:\Users\Seatronic 1147\Documents\Data_Lexplore\git\idronaut-automatic-profiler"

:: Load input variables
call "scripts\input_batch.bat"

%pythonenv% %script% "live"

%pythonenv% %upload% -w

curl "https://api.datalakes-eawag.ch/update/667"
curl "https://api.datalakes-eawag.ch/update/666"


